from openai import OpenAI
from app.config.settings import settings
from app.utils.prompts import EXIM_SYSTEM_PROMPT  # define this similar to IQVIA_SYSTEM_PROMPT
import json
import os
import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

client = OpenAI(
    api_key=settings.GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

logger = logging.getLogger("exim_agent")

COMTRADE_ROOT = os.getenv("COMTRADE_BASE_URL", "https://comtradeapi.un.org/public/v1").rstrip("/")
COMTRADE_TOKEN = os.getenv("COMTRADE_API_TOKEN")

PHARMA_CODES = {
    "pharmaceuticals": "3004",
    "medicaments": "3004",
    "vitamins": "2936",
    "antibiotics": "2941",
    "hormones": "2937",
    "alkaloids": "2939",
}

COUNTRIES = {
    "usa": "842",
    "united states": "842",
    "us": "842",
    "india": "699",
    "ind": "699",
    "china": "156",
    "chn": "156",
    "germany": "276",
    "uk": "826",
    "united kingdom": "826",
    "gb": "826",
    "japan": "392",
    "jpn": "392",
    "france": "250",
    "fra": "250",
}

session = requests.Session()
retry = Retry(total=5, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)


def auth_headers() -> Dict[str, str]:
    h: Dict[str, str] = {}
    if COMTRADE_TOKEN:
        h["Authorization"] = f"Bearer {COMTRADE_TOKEN}"
    return h


def call_endpoint(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{COMTRADE_ROOT}{path}"
    r = session.get(url, params=params, headers=auth_headers(), timeout=60)
    r.raise_for_status()
    return r.json()


def resolve_country(x: str) -> str:
    k = x.strip().lower()
    if k in COUNTRIES:
        return COUNTRIES[k]
    if k.isdigit():
        return k
    return k


def resolve_commodity(x: str) -> str:
    k = x.strip().lower()
    return PHARMA_CODES.get(k, x)


def year_param(start: int, end: int) -> str:
    return ",".join(str(y) for y in range(start, end + 1))


def get_tariffline_data(
    type_code: str,
    freq_code: str,
    cl_code: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    path = f"/getDATariffline/{type_code}/{freq_code}/{cl_code}"
    return call_endpoint(path, params)


def clean_dataframe(raw: Dict[str, Any]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    dataset = raw.get("dataset") or raw.get("data") or raw.get("results")
    if not dataset:
        return pd.DataFrame()
    df = pd.DataFrame(dataset)
    rename = {
        "yr": "year",
        "Year": "year",
        "period": "year",
        "timePeriod": "year",
        "TradeValue": "trade_value",
        "Value": "trade_value",
        "TradeQuantity": "quantity",
        "Quantity": "quantity",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    cols = [c for c in ("year", "trade_value", "quantity", "flow", "reporter", "partner") if c in df.columns]
    if cols:
        df = df[cols]
    if "trade_value" in df.columns:
        df["trade_value"] = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0)
    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(pd.Int64Dtype())
    return df


def fetch_exim_trends(
    commodity: str,
    reporter: str,
    partner: str,
    start_year: int,
    end_year: int,
    flow: str,
) -> Dict[str, Any]:
    hs = resolve_commodity(commodity)
    reporter_code = resolve_country(reporter)
    partner_code = partner
    flow_lower = flow.lower()
    if flow_lower == "both":
        flows = ["X", "M"]
    elif flow_lower in ("x", "export", "exports"):
        flows = ["X"]
    elif flow_lower in ("m", "import", "imports"):
        flows = ["M"]
    else:
        flows = [flow]

    frames: List[pd.DataFrame] = []
    for f in flows:
        params = {
            "fmt": "json",
            "reporterCode": reporter_code,
            "partnerCode": partner_code,
            "period": year_param(start_year, end_year),
            "cmdCode": hs,
            "flowCode": f,
        }
        try:
            raw = get_tariffline_data("C", "A", "HS", params)
            df = clean_dataframe(raw)
            if not df.empty:
                df["flow"] = "Export" if f == "X" else "Import"
                frames.append(df)
        except Exception as e:
            logger.error("Error fetching EXIM data: %s", e)

    if not frames:
        return {"status": "no_data", "message": "No trade data found for given parameters"}

    combined = pd.concat(frames, ignore_index=True)
    if "year" not in combined.columns or "trade_value" not in combined.columns:
        return {"status": "no_data", "message": "Missing required columns in response"}

    grouped = combined.groupby(["year", "flow"], as_index=False).agg({"trade_value": "sum"})
    yearly_trends = grouped.sort_values(["year", "flow"]).to_dict(orient="records")

    top_partners: List[Dict[str, Any]] = []
    if partner_code == "0":
        if "partner" in combined.columns:
            p = combined.groupby("partner", as_index=False)["trade_value"].sum()
            p = p.sort_values("trade_value", ascending=False).head(10)
            top_partners = p.to_dict(orient="records")
        elif "partnerCode" in combined.columns:
            p = combined.groupby("partnerCode", as_index=False)["trade_value"].sum()
            p = p.sort_values("trade_value", ascending=False).head(10)
            top_partners = p.to_dict(orient="records")

    def calc_cagr(rows: List[Dict[str, Any]]) -> Optional[float]:
        if len(rows) < 2:
            return None
        rows = sorted(rows, key=lambda r: int(r["year"]))
        start_val = rows[0]["trade_value"]
        end_val = rows[-1]["trade_value"]
        n = len(rows) - 1
        if start_val <= 0 or n <= 0:
            return None
        try:
            return round(((end_val / start_val) ** (1 / n) - 1) * 100, 2)
        except Exception:
            return None

    exports = [r for r in yearly_trends if r["flow"] == "Export"]
    imports = [r for r in yearly_trends if r["flow"] == "Import"]
    total_export = sum(r["trade_value"] for r in exports)
    total_import = sum(r["trade_value"] for r in imports)

    summary = {
        "total_export_value": total_export,
        "total_import_value": total_import,
        "data_points": len(yearly_trends),
    }

    return {
        "status": "success",
        "commodity_code": hs,
        "reporter_country": reporter_code,
        "partner_country": partner_code,
        "period": f"{start_year}-{end_year}",
        "yearly_trends": yearly_trends,
        "top_partners": top_partners,
        "cagr": {
            "export": calc_cagr(exports),
            "import": calc_cagr(imports),
        },
        "summary": summary,
    }


def compute_insights(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    if trade_data.get("status") != "success":
        return {"status": "error", "message": "Invalid trade data"}
    yearly = trade_data["yearly_trends"]
    imports = sorted([r for r in yearly if r["flow"] == "Import"], key=lambda x: int(x["year"]))
    exports = sorted([r for r in yearly if r["flow"] == "Export"], key=lambda x: int(x["year"]))

    def yoy(arr: List[Dict[str, Any]]) -> Optional[float]:
        if len(arr) < 2:
            return None
        prev_val = arr[-2]["trade_value"]
        curr_val = arr[-1]["trade_value"]
        if prev_val == 0:
            return None
        return round(((curr_val / prev_val) - 1) * 100, 2)

    imp_yoy = yoy(imports)
    exp_yoy = yoy(exports)

    summary = trade_data["summary"]
    total_import = float(summary["total_import_value"])
    total_export = float(summary["total_export_value"])
    total_trade = total_import + total_export
    import_ratio = (total_import / total_trade) * 100 if total_trade > 0 else 0.0

    insights = {
        "market_trends": {
            "import_yoy": imp_yoy,
            "export_yoy": exp_yoy,
            "import_cagr": trade_data["cagr"]["import"],
            "export_cagr": trade_data["cagr"]["export"],
        },
        "dependency_metrics": {
            "import_dependency_ratio": round(import_ratio, 2),
            "is_net_importer": total_import > total_export,
            "trade_balance": round(total_export - total_import, 2),
        },
        "top_suppliers": trade_data.get("top_partners", []),
    }
    return insights


tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_exim_trends",
            "description": "Fetch EXIM trade trends for a given HS code and reporter/partner over a time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {"type": "string"},
                    "reporter": {"type": "string"},
                    "partner": {"type": "string", "description": "Partner country code, '0' for World"},
                    "start_year": {"type": "integer"},
                    "end_year": {"type": "integer"},
                    "flow": {
                        "type": "string",
                        "description": "X for exports, M for imports, both for both directions",
                    },
                },
                "required": ["commodity", "reporter", "start_year", "end_year", "flow"],
            },
        },
    }
]


def handle_user_query(user_query: str):
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": EXIM_SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ],
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        fn_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if fn_name == "fetch_exim_trends":
            trade = fetch_exim_trends(
                commodity=args["commodity"],
                reporter=args["reporter"],
                partner=args.get("partner", "0"),
                start_year=int(args["start_year"]),
                end_year=int(args["end_year"]),
                flow=args["flow"],
            )
            if trade.get("status") != "success":
                return {
                    "tool": fn_name,
                    "args": args,
                    "trade_data": trade,
                }
            ins = compute_insights(trade)
            return {
                "tool": fn_name,
                "args": args,
                "trade_data": trade,
                "insights": ins,
            }

        return {"error": f"Unknown tool called: {fn_name}", "raw_args": args}

    return {"response": message.content}

class EXIMTrendsAgent(BaseAgent):

    async def run(self, query: str, context=None):

        # print("IQVIA Insights Agent CALLED")
        result = handle_user_query(query)

        return {
            "agent": "EXIM Trends Agent",
            "output": result
        }



def main():
    print("\nEXIM Trends Agent — CLI Mode")
    user_query = input("\nEnter your query: ")
    output = handle_user_query(user_query)
    print("\nFinal Output:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

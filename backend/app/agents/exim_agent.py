"""
Rewritten EXIM Trends Agent
- Cleaner structure
- Proper UN Comtrade `ps` parameter (comma-separated years)
- Optional API token support via environment or settings
- Robust error handling and logging
- Pydantic models for inputs/outputs
- Chart generation using Plotly (returns chart JSON + HTML)
- CLI example at the bottom

Requirements:
- requests
- pandas
- plotly
- pydantic

Usage:
$ python exim_agent.py --commodity 3004 --reporter India --start 2020 --end 2023 --flow both

"""

from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Optional, Any
import requests
import pandas as pd
import plotly.graph_objects as go
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("exim_agent")

# Base API endpoint (Comtrade Plus consolidated endpoint used in original snippet)
COMTRADE_BASE_URL = os.getenv("COMTRADE_BASE_URL", "https://comtradeplus.un.org/api/get")
# If you have a private token, place it in the environment variable COMTRADE_API_TOKEN
COMTRADE_API_TOKEN = os.getenv("COMTRADE_API_TOKEN")

# Common HS codes for pharmaceutical APIs/formulations
PHARMA_HS_CODES = {
    "pharmaceuticals": "3004",
    "medicaments": "3004",
    "vitamins": "2936",
    "antibiotics": "2941",
    "hormones": "2937",
    "alkaloids": "2939",
}

# Lightweight country name -> numeric reporter code map (extendable)
COUNTRY_CODE_MAP = {
    "usa": "842", "united states": "842", "us": "842",
    "india": "699", "ind": "699",
    "china": "156", "chn": "156",
    "germany": "276", "deu": "276",
    "uk": "826", "united kingdom": "826", "gb": "826",
    "japan": "392", "jpn": "392",
    "france": "250", "fra": "250",
}


class TradeDataRequest(BaseModel):
    commodity_code: str = Field(..., description="HS commodity code or friendly name (e.g., 'pharmaceuticals')")
    reporter_country: str = Field(..., description="Reporter country name or numeric ISO code")
    partner_country: str = Field("0", description="Partner country numeric code or '0' for World")
    start_year: int = Field(..., ge=1960, le=2100)
    end_year: int = Field(..., ge=1960, le=2100)
    flow_type: str = Field("both", description="one of: 'X' (exports), 'M' (imports), 'both'")

    @validator("flow_type")
    def normalize_flow(cls, v: str) -> str:
        v_low = v.lower()
        if v_low in ("both", "x", "exports", "export"):
            return "both" if v_low == "both" else "X"
        if v_low in ("m", "imports", "import"):
            return "M"
        return v

    @validator("commodity_code")
    def resolve_commodity(cls, v: str) -> str:
        # allow friendly names
        key = v.strip().lower()
        return PHARMA_HS_CODES.get(key, v)

    @validator("reporter_country")
    def resolve_reporter(cls, v: str) -> str:
        key = v.strip().lower()
        return COUNTRY_CODE_MAP.get(key, v)

    @validator("end_year")
    def check_years(cls, v: int, values: Dict[str, Any]) -> int:
        start = values.get("start_year")
        if start and v < start:
            raise ValueError("end_year must be >= start_year")
        return v


class TradeDataResponse(BaseModel):
    status: str
    commodity_code: str
    reporter_country: str
    partner_country: str
    period: str
    yearly_trends: List[Dict]
    top_partners: List[Dict]
    cagr: Dict[str, Optional[float]]
    summary: Dict[str, Any]


# -------------------- Helper functions -------------------- #

def _build_years_param(start_year: int, end_year: int) -> str:
    """Create a comma-separated list of years for the Comtrade `ps` parameter."""
    return ",".join(str(y) for y in range(start_year, end_year + 1))


def _call_comtrade_api(params: Dict[str, Any]) -> Dict[str, Any]:
    headers = {}
    if COMTRADE_API_TOKEN:
        headers["Authorization"] = f"Bearer {COMTRADE_API_TOKEN}"

    try:
        logger.debug("Calling Comtrade: %s with params=%s", COMTRADE_BASE_URL, params)
        resp = requests.get(COMTRADE_BASE_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("Comtrade API request failed: %s", exc)
        raise


def get_comtrade_data(
    commodity_code: str,
    reporter_code: str,
    partner_code: str = "0",
    start_year: int = 2020,
    end_year: int = 2023,
    flow_code: str = "X",
) -> pd.DataFrame:
    """
    Fetch trade data from UN Comtrade endpoint and return a cleaned pandas DataFrame.

    Notes:
    - `ps` is set to a comma-separated list of years between start_year and end_year inclusive.
    - We expect the resulting JSON to include a top-level 'dataset' key containing rows.
    """
    years_param = _build_years_param(start_year, end_year)

    params = {
        "fmt": "json",
        "r": reporter_code,
        "p": partner_code,
        "ps": years_param,
        "px": "HS",
        "cc": commodity_code,
        "freq": "A",
        "type": "C",
        "flow": flow_code,
    }

    raw = _call_comtrade_api(params)

    if not raw or "dataset" not in raw or not raw["dataset"]:
        logger.info("No dataset returned from Comtrade for params: %s", params)
        return pd.DataFrame()

    df = pd.DataFrame(raw["dataset"])

    # Normalise expected columns to our canonical names
    mapping = {
        "yr": "year",
        "Year": "year",
        "TradeValue": "trade_value",
        "TradeQuantity": "quantity",
        "Value": "trade_value",
    }
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

    # Keep only commonly used columns if present
    keep_cols = [c for c in ("year", "trade_value", "quantity", "flow", "reporter", "partner") if c in df.columns]
    if keep_cols:
        df = df[keep_cols]

    # Ensure numeric types
    if "trade_value" in df.columns:
        df["trade_value"] = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0)
    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(pd.Int64Dtype())

    return df


# -------------------- Core agent-like functions -------------------- #

def fetch_trade_data(request: TradeDataRequest) -> Dict[str, Any]:
    """High-level wrapper to fetch import/export trade data and summarise it."""
    # Resolve commodity + country codes already performed by pydantic validators
    hs_code = request.commodity_code
    reporter_code = request.reporter_country
    partner_code = request.partner_country

    flows: List[str] = []
    if request.flow_type == "both":
        flows = ["X", "M"]
    elif request.flow_type == "X":
        flows = ["X"]
    elif request.flow_type == "M":
        flows = ["M"]
    else:
        flows = [request.flow_type]

    data_frames = []

    for flow in flows:
        try:
            df = get_comtrade_data(hs_code, reporter_code, partner_code, request.start_year, request.end_year, flow)
        except Exception:
            df = pd.DataFrame()

        if df.empty:
            logger.info("Empty dataframe for flow=%s", flow)
            continue

        df = df.copy()
        df["flow"] = "Export" if flow == "X" else "Import"
        data_frames.append(df)

    if not data_frames:
        return {"status": "no_data", "message": "No trade data found for the given parameters", "data": []}

    combined = pd.concat(data_frames, ignore_index=True, sort=False)

    # Yearly trends
    group = combined.groupby(["year", "flow"], as_index=False).agg({"trade_value": "sum", "quantity": "sum"})
    yearly_trends = group.sort_values(["year", "flow"]).to_dict(orient="records")

    # Top partners (if partner_country == world)
    top_partners = []
    if request.partner_country == "0" and "partner" in combined.columns:
        partners_group = combined.groupby("partner", as_index=False)["trade_value"].sum()
        partners_group = partners_group.sort_values("trade_value", ascending=False).head(10)
        top_partners = partners_group.to_dict(orient="records")

    def _calculate_cagr(rows: List[Dict]) -> Optional[float]:
        if not rows:
            return None
        sorted_r = sorted(rows, key=lambda x: int(x["year"]))
        if len(sorted_r) < 2:
            return None
        start = sorted_r[0]["trade_value"]
        end = sorted_r[-1]["trade_value"]
        n = len(sorted_r) - 1
        if start <= 0 or n <= 0:
            return None
        try:
            cagr = ((end / start) ** (1 / n) - 1) * 100
            return round(float(cagr), 2)
        except Exception:
            return None

    exports = [r for r in yearly_trends if r.get("flow") == "Export"]
    imports = [r for r in yearly_trends if r.get("flow") == "Import"]

    return {
        "status": "success",
        "commodity_code": hs_code,
        "reporter_country": request.reporter_country,
        "partner_country": request.partner_country,
        "period": f"{request.start_year}-{request.end_year}",
        "yearly_trends": yearly_trends,
        "top_partners": top_partners,
        "cagr": {
            "export": _calculate_cagr(exports),
            "import": _calculate_cagr(imports),
        },
        "summary": {
            "total_export_value": sum(r.get("trade_value", 0) for r in yearly_trends if r.get("flow") == "Export"),
            "total_import_value": sum(r.get("trade_value", 0) for r in yearly_trends if r.get("flow") == "Import"),
            "data_points": len(yearly_trends),
        },
    }


def generate_trade_chart(trade_data: Dict[str, Any], chart_type: str = "line", title: Optional[str] = None) -> Dict[str, Any]:
    """Generate a Plotly chart (JSON + HTML) for yearly trade trends."""
    if trade_data.get("status") != "success":
        return {"status": "error", "message": "Invalid trade data"}

    df = pd.DataFrame(trade_data.get("yearly_trends", []))
    if df.empty:
        return {"status": "error", "message": "No data to plot"}

    fig = go.Figure()

    # add traces dynamically for each flow found
    for flow_name, group in df.groupby("flow"):
        x = group["year"].astype(int).tolist()
        y = group["trade_value"].astype(float).tolist()
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=flow_name))
        elif chart_type == "bar":
            fig.add_trace(go.Bar(x=x, y=y, name=flow_name))
        elif chart_type == "area":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=flow_name, fill="tozeroy"))
        else:
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=flow_name))

    chart_title = title or f"Trade Volume: {trade_data.get('commodity_code')} ({trade_data.get('period')})"
    fig.update_layout(title=chart_title, xaxis_title="Year", yaxis_title="Trade Value (USD)", hovermode="x unified", template="plotly_white", height=500)

    return {"status": "success", "chart_json": fig.to_json(), "html": fig.to_html(include_plotlyjs="cdn"), "title": chart_title}


def compute_sourcing_insights(trade_data: Dict[str, Any], focus_country: Optional[str] = None) -> Dict[str, Any]:
    """Compute high-level sourcing insights: top suppliers, growth, dependency metrics."""
    if trade_data.get("status") != "success":
        return {"status": "error", "message": "Invalid trade data"}

    insights: Dict[str, Any] = {"top_suppliers": [], "market_trends": [], "dependency_metrics": {}}

    # top suppliers: find top partners from trade_data
    top_partners = trade_data.get("top_partners", [])
    insights["top_suppliers"] = top_partners

    yearly = trade_data.get("yearly_trends", [])
    imports = sorted([t for t in yearly if t.get("flow") == "Import"], key=lambda x: int(x["year"]))
    exports = sorted([t for t in yearly if t.get("flow") == "Export"], key=lambda x: int(x["year"]))

    def _yoy_change(arr: List[Dict]) -> Optional[float]:
        if len(arr) < 2:
            return None
        try:
            return round(((arr[-1]["trade_value"] / arr[-2]["trade_value"]) - 1) * 100, 2) if arr[-2]["trade_value"] != 0 else None
        except Exception:
            return None

    imp_yoy = _yoy_change(imports)
    exp_yoy = _yoy_change(exports)
    if imp_yoy is not None:
        insights["market_trends"].append({"type": "import_yoy", "value": imp_yoy, "description": f"Import YoY change: {imp_yoy}%"})
    if exp_yoy is not None:
        insights["market_trends"].append({"type": "export_yoy", "value": exp_yoy, "description": f"Export YoY change: {exp_yoy}%"})

    summ = trade_data.get("summary", {})
    total_import = summ.get("total_import_value", 0)
    total_export = summ.get("total_export_value", 0)
    total_trade = total_import + total_export

    if total_trade > 0:
        import_ratio = (total_import / total_trade) * 100
        insights["dependency_metrics"] = {
            "import_dependency_ratio": round(import_ratio, 2),
            "is_net_importer": total_import > total_export,
            "trade_balance": round(total_export - total_import, 2),
        }

    # add CAGR if present
    cagr = trade_data.get("cagr", {})
    if cagr.get("import") is not None:
        insights["market_trends"].append({"type": "import_cagr", "value": cagr["import"], "description": f"Import CAGR: {cagr['import']}%"})
    if cagr.get("export") is not None:
        insights["market_trends"].append({"type": "export_cagr", "value": cagr["export"], "description": f"Export CAGR: {cagr['export']}%"})

    return {"status": "success", "insights": insights, "focus_country": focus_country or trade_data.get("reporter_country")}


def create_dependency_table(trade_data: Dict[str, Any], threshold_pct: float = 10.0) -> Dict[str, Any]:
    """Create an import dependency table with per-source contribution percentages."""
    if trade_data.get("status") != "success":
        return {"status": "error", "message": "Invalid trade data"}

    summary = trade_data.get("summary", {})
    total_import = summary.get("total_import_value", 0)
    top_sources = trade_data.get("top_partners", [])

    table: List[Dict[str, Any]] = []
    if total_import > 0 and top_sources:
        for row in top_sources:
            partner = row.get("partner") or row.get("Partner") or row.get("partner_code") or "Unknown"
            val = float(row.get("trade_value", 0))
            pct = (val / total_import) * 100 if total_import > 0 else 0
            if pct >= threshold_pct:
                table.append({"country": partner, "trade_value": round(val, 2), "dependency_percentage": round(pct, 2)})

    table = sorted(table, key=lambda x: x["dependency_percentage"], reverse=True)

    overall_dep = (total_import / (total_import + summary.get("total_export_value", 0)) * 100) if (total_import + summary.get("total_export_value", 0)) > 0 else 0

    return {"status": "success", "overall_dependency_ratio": round(overall_dep, 2), "dependency_table": table, "summary": summary}


# -------------------- Simple CLI for quick testing -------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EXIM Trends Agent - fetch trade data and generate charts")
    parser.add_argument("--commodity", required=True, help="HS code or friendly name (e.g., 'pharmaceuticals' or '3004')")
    parser.add_argument("--reporter", required=True, help="Reporter country name or numeric code (e.g., India)")
    parser.add_argument("--partner", default="0", help="Partner country code (default: 0 for World)")
    parser.add_argument("--start", type=int, default=2020, help="Start year")
    parser.add_argument("--end", type=int, default=2023, help="End year")
    parser.add_argument("--flow", default="both", help="Flow: X, M or both")
    parser.add_argument("--chart", default="line", help="Chart type: line, bar, area")
    parser.add_argument("--out", default="trade_chart.html", help="Output HTML filename for chart")

    args = parser.parse_args()

    req = TradeDataRequest(
        commodity_code=args.commodity,
        reporter_country=args.reporter,
        partner_country=args.partner,
        start_year=args.start,
        end_year=args.end,
        flow_type=args.flow,
    )

    result = fetch_trade_data(req)
    if result.get("status") != "success":
        logger.error("Failed to fetch trade data: %s", result)
        raise SystemExit(1)

    chart = generate_trade_chart(result, chart_type=args.chart)
    if chart.get("status") == "success":
        html = chart["html"]
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Chart written to %s", args.out)

    insights = compute_sourcing_insights(result)
    dep_table = create_dependency_table(result)

    # Print a short summary
    print(json.dumps({"summary": result.get("summary"), "cagr": result.get("cagr"), "insights": insights.get("insights"), "dependency": dep_table.get("overall_dependency_ratio")}, indent=2))

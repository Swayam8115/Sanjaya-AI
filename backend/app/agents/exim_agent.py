from __future__ import annotations
import os
import json
import logging
from typing import Dict, Any, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import plotly.graph_objects as go

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("exim_agent")

raw_base = os.getenv("COMTRADE_BASE_URL", "https://comtradeapi.un.org/public/v1")
if raw_base.endswith("/getComtradeReleases"):
    COMTRADE_ROOT = raw_base.rsplit("/getComtradeReleases", 1)[0]
else:
    COMTRADE_ROOT = raw_base.rstrip("/")

TOKEN = os.getenv("COMTRADE_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OpenAI and OPENAI_API_KEY else None

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
    "japan": "392",
    "france": "250",
}

session = requests.Session()
retry = Retry(total=5, backoff_factor=0.8, status_forcelist=[429,500,502,503,504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

def headers():
    h = {}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h

def call(endpoint: str, params: Dict[str, Any]):
    url = f"{COMTRADE_ROOT}{endpoint}"
    r = session.get(url, params=params, headers=headers(), timeout=60)
    r.raise_for_status()
    return r.json()

def resolve_country(code: str) -> str:
    c = code.strip().lower()
    if c in COUNTRIES:
        return COUNTRIES[c]
    if c.isdigit():
        return c
    return c

def resolve_commodity(code: str) -> str:
    c = code.strip().lower()
    return PHARMA_CODES.get(c, code)

def years(start: int, end: int) -> str:
    return ",".join(str(y) for y in range(start, end + 1))

def get_releases():
    return call("/getComtradeReleases", {"fmt": "json"})

def get_metadata():
    return call("/getMetadata/C/A/HS", {"fmt": "json"})

def fetch_raw(hs: str, reporter: str, partner: str, start: int, end: int, flow: str):
    params = {
        "fmt": "json",
        "r": reporter,
        "p": partner,
        "ps": years(start, end),
        "px": "HS",
        "cc": hs,
        "freq": "A",
        "type": "C",
        "flow": flow,
    }
    return call("/getDA/C/A/HS", params)

def clean_df(raw: Dict[str, Any]):
    if not raw or "dataset" not in raw or not raw["dataset"]:
        return pd.DataFrame()

    df = pd.DataFrame(raw["dataset"])
    rename = {
        "yr": "year",
        "Year": "year",
        "period": "year",
        "TradeValue": "trade_value",
        "Value": "trade_value",
        "TradeQuantity": "quantity",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    keep = [c for c in ("year", "trade_value", "quantity", "flow", "reporter", "partner") if c in df.columns]
    if keep:
        df = df[keep]

    if "trade_value" in df.columns:
        df["trade_value"] = pd.to_numeric(df["trade_value"], errors="coerce").fillna(0)
    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(pd.Int64Dtype())

    return df

def fetch_trade_data(commodity: str, reporter: str, partner: str, start: int, end: int, flow: str):
    hs = resolve_commodity(commodity)
    rc = resolve_country(reporter)
    pc = partner

    flows = ["X","M"] if flow == "both" else [flow]

    dfs = []
    for f in flows:
        try:
            raw = fetch_raw(hs, rc, pc, start, end, f)
            df = clean_df(raw)
            if not df.empty:
                df["flow"] = "Export" if f == "X" else "Import"
                dfs.append(df)
        except:
            pass

    if not dfs:
        return {"status": "no_data"}

    df = pd.concat(dfs, ignore_index=True)

    grp = df.groupby(["year","flow"], as_index=False).agg({"trade_value":"sum"})
    trends = grp.to_dict(orient="records")

    partners = []
    if partner == "0" and "partner" in df.columns:
        p = df.groupby("partner", as_index=False)["trade_value"].sum()
        partners = p.sort_values("trade_value", ascending=False).head(10).to_dict(orient="records")

    def cagr(rows: List[Dict[str,Any]]):
        if len(rows) < 2:
            return None
        rows = sorted(rows, key=lambda x: int(x["year"]))
        s = rows[0]["trade_value"]
        e = rows[-1]["trade_value"]
        n = len(rows)-1
        if s <= 0: return None
        return round(((e/s)**(1/n) - 1) * 100, 2)

    exp = [r for r in trends if r["flow"]=="Export"]
    imp = [r for r in trends if r["flow"]=="Import"]

    summary = {
        "total_export_value": sum(r["trade_value"] for r in exp),
        "total_import_value": sum(r["trade_value"] for r in imp),
        "data_points": len(trends),
    }

    return {
        "status": "success",
        "commodity_code": hs,
        "reporter_country": rc,
        "partner_country": pc,
        "period": f"{start}-{end}",
        "yearly_trends": trends,
        "top_partners": partners,
        "cagr": {"export": cagr(exp), "import": cagr(imp)},
        "summary": summary,
    }

def generate_chart(data: Dict[str,Any], chart_type="line"):
    df = pd.DataFrame(data["yearly_trends"])
    fig = go.Figure()
    for flow, g in df.groupby("flow"):
        x = g["year"].astype(int).tolist()
        y = g["trade_value"].astype(float).tolist()
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=flow))
        elif chart_type == "bar":
            fig.add_trace(go.Bar(x=x, y=y, name=flow))
        else:
            fig.add_trace(go.Scatter(x=x, y=y, fill="tozeroy", name=flow))
    fig.update_layout(title="Trade Trends", xaxis_title="Year", yaxis_title="Trade Value (USD)")
    return fig.to_html(include_plotlyjs="cdn")

def insights(data: Dict[str,Any]):
    y = data["yearly_trends"]
    imp = sorted([r for r in y if r["flow"]=="Import"], key=lambda x: int(x["year"]))
    exp = sorted([r for r in y if r["flow"]=="Export"], key=lambda x: int(x["year"]))

    def yoy(arr):
        if len(arr)<2: return None
        a,b = arr[-2]["trade_value"], arr[-1]["trade_value"]
        if a==0: return None
        return round(((b/a)-1)*100,2)

    inc = yoy(imp)
    exc = yoy(exp)

    s = data["summary"]
    ti, te = s["total_import_value"], s["total_export_value"]
    tt = ti+te

    dep = (ti/tt)*100 if tt>0 else 0

    return {
        "market_trends": {
            "import_yoy": inc,
            "export_yoy": exc,
            "import_cagr": data["cagr"]["import"],
            "export_cagr": data["cagr"]["export"]
        },
        "dependency_metrics": {
            "import_dependency_ratio": round(dep,2),
            "is_net_importer": ti>te,
            "trade_balance": round(te-ti,2),
        },
        "top_suppliers": data["top_partners"]
    }

def openai_summary(data: Dict[str,Any], ins: Dict[str,Any]):
    if not client:
        return {"status":"error","message":"OpenAI not configured"}
    payload = {"summary":data["summary"],"cagr":data["cagr"],"top":data["top_partners"],"insights":ins}
    prompt = f"Provide an EXIM analysis summary:\n{json.dumps(payload)}"
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=400
    )
    return {"status":"success", "summary": r.choices[0].message.content}

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--commodity", required=True)
    p.add_argument("--reporter", required=True)
    p.add_argument("--partner", default="0")
    p.add_argument("--start", type=int, default=2020)
    p.add_argument("--end", type=int, default=2023)
    p.add_argument("--flow", default="both")
    p.add_argument("--no-openai", action="store_true")
    args = p.parse_args()

    data = fetch_trade_data(args.commodity, args.reporter, args.partner, args.start, args.end, args.flow)
    if data["status"] != "success":
        print(json.dumps(data, indent=2))
        exit()

    ins = insights(data)

    out = {
        "summary": data["summary"],
        "cagr": data["cagr"],
        "insights": ins,
    }

    if not args.no_openai:
        out["openai"] = openai_summary(data, ins)

    print(json.dumps(out, indent=2))

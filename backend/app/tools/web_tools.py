import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
HEADERS = {"User-Agent": "WebIntelAgent/1.0"}


def search_europepmc(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """
    Query Europe PMC and produce normalized records with robust snippet selection.
    """
    params = {"query": query, "format": "json", "pageSize": limit}
    try:
        r = requests.get(EUROPE_PMC_BASE, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        j = r.json()
        hits = []
        for rec in j.get("resultList", {}).get("result", []):
            title = rec.get("title") or rec.get("sourceTitle") or ""
            # Europe PMC sometimes exposes abstract in different keys
            abstract = rec.get("abstractText") or rec.get("abstract") or rec.get("title")
            doi = rec.get("doi") or rec.get("doiText") or None
            pmid = rec.get("pmid") or rec.get("id")
            url = None
            if doi:
                url = f"https://doi.org/{doi}"
            else:
                src = rec.get("source", "")
                uid = rec.get("id")
                url = f"https://europepmc.org/article/{src}/{uid}" if src and uid else None

            rec_norm = {
                "id": doi or pmid or url,
                "doi": doi,
                "pmid": pmid,
                "title": title,
                "snippet": (abstract or "")[:1000] if abstract else None,
                "url": url,
                "date": rec.get("firstPublicationDate") or rec.get("pubYear"),
                "source": "europepmc",
                "type": "paper",
                "raw": rec,
                "full_text": ""  # to be filled later in search_all
            }
            hits.append(rec_norm)
        return hits
    except Exception as e:
        print("EuropePMC error:", e)
        return []

# HTML text extracion
def fetch_page_text(url: str, max_chars: int = 4000) -> str:
    """
    Fetch a web page and extract main paragraph text (simple).
    Returns up to `max_chars` characters.
    """
    if not url:
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        # Remove scripts/styles
        for s in soup(["script", "style", "noscript"]):
            s.extract()
        # Grab main <p> text (heuristic)
        texts = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
        joined = "\n\n".join([t for t in texts if len(t) > 40])
        return joined[:max_chars]
    except Exception as e:
        # fail silently for MVP
        return ""


def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure returned record has uniform keys:
    id, title, snippet, url, date, source, type, raw, full_text (optional)
    """
    return {
        "id": rec.get("id"),
        "title": rec.get("title"),
        "snippet": rec.get("snippet") or (rec.get("raw", {}).get("abstractText") if rec.get("raw") else None),
        "url": rec.get("url"),
        "date": rec.get("date"),
        "source": rec.get("source"),
        "type": rec.get("type"),
        "raw": rec.get("raw", {}),
        "full_text": rec.get("full_text", "")  # may be filled in search_all
    }

def search_all(query: str, limit: int = 3, types: List[str] = None) -> List[Dict[str, Any]]:
    """
    Fast-mode orchestrator: only query Europe PMC, no full-text fetch, smaller default limit.
    """
    raw_hits = search_europepmc(query, limit=limit)
    unique = {}
    out = []
    for rec in raw_hits:
        key = rec.get("doi") or rec.get("pmid") or rec.get("id") or rec.get("url")
        if not key or key in unique:
            continue
        unique[key] = True
        # do NOT fetch full_text in fast mode
        rec["full_text"] = ""  
        # ensure snippet exists (abstract fallback)
        if not rec.get("snippet") and rec.get("raw"):
            rec["snippet"] = (rec["raw"].get("abstractText") or rec["raw"].get("abstract") or "")[:800]
        out.append(normalize_record(rec))
    return out[:limit]

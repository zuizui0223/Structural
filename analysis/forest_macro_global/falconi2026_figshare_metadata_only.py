"""Source-only Figshare link and file metadata audit for Falconi-Lopez et al. 2026.

No specimen, species/OTU, abundance, emergence, plot, or log data-file download.
Public HTML/JSON repository metadata only, no authenticated/private API.
"""
import argparse
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

LINKS = {
    "publisher_html": "https://figshare.com/s/80ba8b612162e4a7ace7",
    "publisher_pdf": "https://figshare.com/s/80ba8b61262e4a7ace7",
}
TITLE = "Saproxylic beetle diversity and host-network data along a tropical forest recovery gradient"
LIMIT = 262144


class PageMeta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("property") in ("og:url", "og:title"):
            self.found[a["property"]] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.found["canonical"] = a.get("href", "")


def request(url, method="GET", payload=None, limit=LIMIT):
    req = urllib.request.Request(url, data=payload, method=method, headers={
        "User-Agent": "Structural-metadata-only-source-audit/1.0",
        "Accept": "application/json, text/html;q=0.9, */*;q=0.1",
    })
    try:
        with urllib.request.urlopen(req, timeout=18) as r:
            data = r.read(limit + 1)
            out = {"http": r.status, "final_url": r.geturl(),
                   "content_type": r.headers.get("Content-Type", "")}
            if len(data) > limit:
                return dict(out, status="METADATA_PAGE_TOO_LARGE_STOP"), None
            return dict(out, status="HTTP_RESPONSE_RECEIVED"), data
    except urllib.error.HTTPError as e:
        return {"status": "HTTP_STOP", "http": e.code, "final_url": e.geturl()}, None
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return {"status": "TRANSPORT_STOP", "error_class": type(e).__name__}, None


def simple(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def audit():
    x = {
        "schema": "structural.falconi2026_sourceonly.v1",
        "source_paper_doi": "10.1016/j.foreco.2026.124102",
        "published_plots": 62, "published_log_types_per_plot": 5,
        "published_logs_deployed": 310, "published_logs_recovered": 306,
        "published_zero_emergence_fraction_rounded": 0.43,
        "publisher_share_link_conflict": True,
        "share_link_statuses": {}, "public_search_candidate_metadata": [],
        "public_verified_file_metadata": [],
        "original_log_and_beetle_rows_opened": 0,
        "original_biological_source_files_downloaded": 0,
        "ecological_effects_scored": 0,
        "status": "SOURCE_METADATA_UNRESOLVED_HOLD",
        "preexisting_forests_and_mammal_scores_unchanged": True,
        "eBird_used": False, "TinyFish_used": False,
    }
    for k, url in LINKS.items():
        info, data = request(url)
        if data and "html" in info.get("content_type", "").lower():
            p = PageMeta()
            p.feed(data.decode("utf-8", errors="replace"))
            info["canonical_og_metadata_only"] = {
                name: value[:220] for name, value in p.found.items()
            }
        x["share_link_statuses"][k] = info

    q = json.dumps({"search_for": ":title: " + TITLE,
                    "page": 1, "page_size": 20}).encode("utf-8")
    info, data = request("https://api.figshare.com/v2/articles/search",
                         "POST", q, 131072)
    x["public_search_status"] = info
    hits = []
    if data:
        try:
            r = json.loads(data)
            if isinstance(r, list):
                hits = [o for o in r if isinstance(o, dict)
                        and "saproxylic beetle" in simple(o.get("title"))
                        and "forest recovery" in simple(o.get("title"))]
        except (ValueError, TypeError):
            x["public_search_parse"] = "SCHEMA_HOLD"
    x["public_search_candidate_metadata"] = [
        {"id": o.get("id"), "title": str(o.get("title", ""))[:180],
         "doi": str(o.get("doi", ""))[:140]} for o in hits[:5]
    ]
    if len(hits) == 1 and isinstance(hits[0].get("id"), int):
        article_id = hits[0]["id"]
        info, data = request("https://api.figshare.com/v2/articles/" + str(article_id),
                             limit=131072)
        x["public_article_status"] = info
        if data:
            try:
                o = json.loads(data)
                if (o.get("id") == article_id
                        and simple(o.get("title")) == simple(hits[0].get("title"))):
                    x["public_verified_file_metadata"] = [
                        {"name": str(f.get("name", ""))[:160],
                         "size": f.get("size")}
                        for f in o.get("files", []) if isinstance(f, dict)
                    ][:80]
                    x["public_article_identity_verified"] = True
            except (ValueError, TypeError):
                x["public_article_identity_verified"] = False

    if x.get("public_article_identity_verified") and x["public_verified_file_metadata"]:
        x["status"] = "SOURCE_FILE_METADATA_ONLY_VISIBLE_CROSSWALK_HOLD"
    return x


def test():
    p = PageMeta()
    p.feed('<meta property="og:title" content="test"/>'
           '<link rel="canonical" href="https://figshare.com/articles/dataset/a/1"/>')
    assert p.found["og:title"] == "test"
    assert p.found["canonical"].endswith("/1")
    assert len(set(LINKS.values())) == 2
    assert simple("Beetle & Tree!") == "beetle tree"
    print("SYNTHETIC_METADATA_TESTS_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--out", default="falconi2026_sourceonly/receipt.json")
    args = ap.parse_args()
    if args.test:
        test()
        return
    x = audit()
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("FALCONI_2026_SOURCE_GATE", x["status"])
    print("SHARE_LINK_HTTP", {k: v.get("http") for k,v in x["share_link_statuses"].items()})
    print("PUBLIC_FILE_METADATA_N", len(x["public_verified_file_metadata"]))
    print("NO_BIOLOGY_READ", x["original_log_and_beetle_rows_opened"] == 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch cited documentation and surface reviewable text signals; never adjudicates product claims."""
from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TOKENS = {
    "oauth": "OAuth",
    "api key": "API key",
    "bearer": "Bearer token",
    "basic auth": "Basic auth",
    "graphql": "GraphQL",
    "mcp": "MCP",
    "approval": "Approval/review",
    "pricing": "Plan/pricing",
    "rate limit": "Rate limits",
    "enterprise": "Enterprise access",
    "sandbox": "Sandbox",
}


class PageText(HTMLParser):
    """Collect page title and readable text while skipping executable/style content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.text: list[str] = []
        self.in_title = False
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self.in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        clean = re.sub(r"\s+", " ", data).strip()
        if not clean:
            return
        if self.in_title:
            self.title.append(clean)
        elif not self.skip_depth:
            self.text.append(clean)


def excerpts(text: str, phrase: str, limit: int = 2) -> list[str]:
    """Return bounded text around a literal signal so a reviewer can inspect context."""
    found: list[str] = []
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    for match in pattern.finditer(text):
        start, end = max(0, match.start() - 95), min(len(text), match.end() + 145)
        excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
        if excerpt not in found:
            found.append(excerpt)
        if len(found) >= limit:
            break
    return found


def inspect(row: dict[str, Any], timeout: float, retries: int, max_bytes: int) -> dict[str, Any]:
    url = row["evidence"]
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AppResearchTriage/0.2 (documentation research; contact: local-run)"},
    )
    last_error = "unknown fetch error"
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(max_bytes).decode("utf-8", "replace")
                final_url, status = response.url, response.status
            page = PageText()
            page.feed(raw)
            text = re.sub(r"\s+", " ", " ".join(page.text)).strip()
            signals = []
            for phrase, label in TOKENS.items():
                snippets = excerpts(text, phrase)
                if snippets:
                    signals.append({"signal": label, "excerpts": snippets})
            return {
                "id": row["id"],
                "app": row["app"],
                "url": final_url,
                "http": status,
                "title": " ".join(page.title)[:180],
                "signals": signals,
                "bytes_read_capped": len(raw.encode("utf-8")) >= max_bytes,
                "claim_status": "not_adjudicated",
                "human_review": "required; excerpts are discovery cues, not verified conclusions",
            }
        except urllib.error.HTTPError as error:
            last_error = f"HTTP {error.code}: {error.reason}"
            if error.code not in {408, 425, 429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = f"{type(error).__name__}: {error}"
        if attempt < retries:
            time.sleep(min(2**attempt, 8))
    return {
        "id": row["id"],
        "app": row["app"],
        "url": url,
        "error": last_error[:240],
        "claim_status": "not_adjudicated",
        "human_review": "required; fetch failure is not evidence that a product/API is unavailable",
    }


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=base / "apps.json")
    parser.add_argument("--output", type=Path, default=base / "research_signals.json")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--max-bytes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.limit < 1 or args.retries < 0 or args.max_bytes < 1 or args.workers < 1:
        parser.error("limit/max-bytes/workers must be positive and retries non-negative")
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    selected = rows[: args.limit]
    # Independent source URLs can be checked concurrently. Keep results in input order.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda row: inspect(row, args.timeout, args.retries, args.max_bytes), selected))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ok = sum("http" in result for result in results)
    print(f"Fetched {len(results)} rows: {ok} pages, {len(results) - ok} errors. No app claim was adjudicated.")
    print(f"Evidence cues: {args.output}")


if __name__ == "__main__":
    main()


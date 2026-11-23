# App API research case study

A single-file interactive case study for a 100-app API readiness triage, with structured app data, a concurrent documentation-signal runner, and a verification report. The evidence-led result is near-complete but still marks three product records unresolved and does not claim that the fetch runner adjudicates product claims.

## Evidence status (2026-11-23)

- **100 apps / 10 categories.** 86 additional rows have first-party evidence checked for core auth, access, and API claims; 11 purposive sample rows have dedicated source review; 3 remain unresolved: Commas (formerly FanBasis), Paygent Connect, and Reducto.
- **Measured sample only:** the selected 11-app access-gate sample moved from 7/11 (63.6%) on first pass to 11/11 (100%) after official-doc review. Four corrections are shown in the case study. This is not a random sample or a population accuracy estimate.
- **MCP:** 29 official/vendor MCP offerings or connectors confirmed; targeted status checks cover 39 app rows; 61 are still unchecked. Blank/unchecked does not mean absent.
- **Latest runner pass:** attempted all 100 cited URLs; 0 fetched and 100 returned Windows DNS-resolution errors (`getaddrinfo failed`). An earlier pass in the project recorded 90/100 fetches, but that runner only collected page signals. Neither run determines whether claims are true. The current JSON is the reproducible result from this workspace.
- **Public case study:** https://gargi11garad.github.io/ai-product-ops-app-research-case-study/
- **Source repository:** https://github.com/gargi11garad/ai-product-ops-app-research-case-study

## Run the research agent

Requires Python 3.10+ and network access to the cited vendor docs. It uses only the standard library and stores page title, URL/status, and bounded keyword excerpts. Each result remains `not_adjudicated`; a human must compare evidence and update `apps.json`.

```bash
python research_agent.py --workers 12 --timeout 8 --retries 0
```

Useful options: `--input`, `--output`, `--limit`, `--workers`, `--timeout`, `--retries`, and `--max-bytes`. Set retries to 1–2 on a reliable connection if transient errors are expected. Fetch failures are recorded, not treated as evidence of product unavailability.

## Files

- `index.html` — self-contained, searchable 100-row case study and findings
- `apps.json` — structured app findings, confidence labels, blockers, and evidence links
- `research_agent.py` — concurrent standard-library source-signal collector
- `research_signals.json` — latest 100-URL run (100 DNS failures in this network environment)
- `verification_report.json` — sample design, corrections, added source checks, MCP coverage, unresolved claims, and deployment status

Open `index.html` locally, or visit the public case-study URL above. GitHub Pages publishes from the `main` branch root.



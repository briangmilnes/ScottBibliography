---
round: 2
from: orchestrator
to: agent5
subject: scott-bibliography-correct-citations
project-tz: America/Los_Angeles
---

# Agent 5 — build a correctly-cited Dana Scott bibliography

Produce a clean, correctly-formatted bibliography of Dana S. Scott's works with
complete, verified citations.

## Inputs (ground truth for what exists)
- `~/projects/ScottBibliography.md` — the official numbered list (4 books a–d,
  99 papers) with title / venue / year / pages already transcribed.
- `~/projects/ScottLean4/docs/DanaScottPapers.md` — our earlier verified
  bibliography with many DOIs and OA links (reuse these).

## Task
For each of the 103 entries, generate a **correct, complete citation**:
1. **Prefer scholar.google.com** — search the title + "Dana Scott", open the
   entry, use its **Cite** panel (and "All versions" for DOIs/venues). Google
   Scholar is the requested primary source.
2. If Scholar blocks automated access (captcha), fall back to **DBLP**
   (`dblp.org` — clean BibTeX for CS items), **Crossref** (DOI + metadata via
   `api.crossref.org`), and the publisher page.
3. Do **not** fabricate. Keep the title/venue/year/pages from
   `ScottBibliography.md` as authoritative; fill in **DOI, publisher, editors,
   volume/series** where a source confirms them. Omit fields you can't verify.

## Outputs
- `~/projects/ScottBibliographyCited.md` — a numbered markdown bibliography
  (books a–d, then papers 1–99), each a single well-formed citation in a
  consistent style (Chicago-ish: Authors. "Title." *Venue* vol (year): pages.
  DOI/URL if known).
- `~/projects/scott.bib` — a BibTeX file, one entry per work
  (`@article`/`@incollection`/`@inproceedings`/`@book`), keys like
  `scott1976datatypes`; include doi/url where verified.

## Report
`~/projects/reports/r0002-report-from-agent5-to-orchestrator-scott-bibliography-citations.md`
— how many citations were verified/enriched via Scholar vs DBLP/Crossref, how
many DOIs found, and any entries left with incomplete data.

Do NOT run git.

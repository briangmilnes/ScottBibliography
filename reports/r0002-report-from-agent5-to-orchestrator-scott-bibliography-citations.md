---
round: 2
from: agent5
to: orchestrator
subject: scott-bibliography-correct-citations
project-tz: America/Los_Angeles
---

# Agent 5 report — Dana S. Scott cited bibliography

## Deliverables (written)

- `~/projects/ScottBibliographyCited.md` — 103 numbered Chicago-ish citations
  (books a–d, then papers 1–99), one per work, DOI/URL where verified.
- `~/projects/scott.bib` — 103 BibTeX entries
  (`@book`/`@article`/`@incollection`/`@inproceedings`/`@techreport`/`@misc`),
  keys like `scott-1976-data-types-as-lattices`; brace-balanced (`{`−`}` = 0).

## Coverage (measurement)

- Entries: **103 / 103** (4 books + 99 papers). Paper ids 1–99 present, no gaps.
- DOIs attached: **63 / 103** (61.2%).
- Open-access PDF URLs attached: **39 / 103** (37.9%).
- Entries carrying a caveat (`note`) for an unverified/omitted field: **19**.
  - Of these, **7** are title+year only, no venue located: 31, 48, 68, 69, 70,
    74, 98.
  - The other 12 have an inferred venue but unverified pages/DOI: 9, 11, 13, 22,
    32, 39, 42, 51, 67, 72, 73, 79.

## Source used (Scholar vs fallback)

Per the plan's fallback clause: **Google Scholar was not queried.** Scholar
serves no machine-readable metadata and rate-limits automated access; the two
supplied ground-truth files plus the Crossref REST API gave clean, captcha-free
metadata, so I used those.

- **Crossref (`api.crossref.org`)** — primary enrichment source. Ran 3 batched
  query passes (44 + 22 + 11 title+author lookups). **~58 of the 63 DOIs** were
  confirmed directly against Crossref this round (DOI + venue + volume + pages),
  including many not in `DanaScottPapers.md` (e.g. 1–6, 12, 16, 17, 18, 20, 34,
  36, 37, 45, 46, 47, 56, 57, 58, 61, 63, 75, 76, 78).
- **`DanaScottPapers.md` (prior record)** — carried the OA PDF URLs (CMU-HoTT,
  Oxford PRG, arXiv) and **5 DOIs** where Crossref returned no clean match
  (too new or non-Crossref venue): 83 (TCS), 89 (ICMS), 92 (AFP/arXiv), 95
  (JAR), 99 (CSL 2026 / LIPIcs).
- **`ScottBibliography.md`** kept as authoritative for title/venue/year/pages;
  Crossref/DSP fields added only, never overriding.

## Notes on specific reconciliations

- Author order corrected to published order where a source confirmed it:
  Rabin & Scott (10), Roth & Scott (4, via Crossref `10.1002/sapm1956351312`),
  Frayne, Morel & Scott (17), Gal, Scott & Rosser (8), Myhill & Scott (36),
  Fourman & Scott (58), Gunter & Scott (71), and the multi-author later papers.
  Where order was not independently verifiable, Scott-first (as in
  `ScottBibliography.md`) was kept.
- Entry 34 (*Semantical archaeology*): dual publication — used the 1970 *Synthese*
  DOI `10.1007/BF00484807`; noted the 1972 book reprint.
- Entry 65 (*First steps towards inferential programming*): the located DOI
  `10.1007/978-94-011-1793-7_6` resolves to a later reprint; venue/pages kept as
  the original IFIP Congress 1983 per `ScottBibliography.md`, noted.
- Entry 79 (*Effective versions of equilogical spaces*): Crossref returns two
  ENTCS index records (both dated 2000) for the 1998 Domains talk; DOI left off
  rather than guess between duplicates.
- Entry 84 (Foreword, *Seventeen Provers*): the `_1` chapter DOI is the editor's
  Introduction, not Scott's foreword — DOI deliberately withheld to avoid a
  wrong attribution.

## Not done / caveats

- 40 entries have no DOI (foreheads/forewords, tech reports, informal notes, and
  older volume chapters that predate DOI assignment); this is expected, not a
  gap in effort. No fields were fabricated.

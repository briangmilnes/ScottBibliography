---
round: 1
from: orchestrator
to: agent1
subject: scott-bib-acquire-batch1
project-tz: America/Los_Angeles
---

# Agent 1 — acquire Scott bibliography PDFs (batch 1: books + 1955–1966)

Source list: `~/projects/ScottBibliography.md` (coverage table). Your job: for
each entry below (currently **not held**), find a **legitimately open-access
PDF** and download it into `~/projects/papers/`, then write a report.

## Rules
- Legitimate sources only: arXiv, HAL, Archive of Formal Proofs, publisher OA,
  author pages (Scott / Benzmüller / CMU), institutional repositories,
  DOI-resolved OA, archive.org for public-domain items. **No** shadow libraries
  (sci-hub, epdf, scribd, etc.).
- Many of these are 1950s–60s journal papers / book chapters and will be
  **paywalled with no OA** — that's expected; mark them "no OA found" and move on.
- Verify each download is a real PDF (`file …`). Name files
  `Scott-YEAR-Short-Title.pdf` (match existing style in `papers/`).
- Do NOT run git.

## Entries (find OA PDF; download if found)
- a. Scott & Lemmon, *An Introduction to Modal Logic*, OUP, 1977 (book)
- b. Scott et al., *A Compendium of Continuous Lattices*, Springer, 1980 (book)
- c. Scott et al., *Continuous Lattices and Domains*, CUP, 2003 (book)
- d. Univalent Foundations Program, *Homotopy Type Theory*, IAS, 2013 (book — **OA, get it** from homotopytypetheory.org)
- 1. Scott & Kalicki. Equational completeness of abstract algebras. 1955
- 2. Scott. Equationally complete extensions of finite algebras. 1956
- 3. Scott. A symmetric primitive notion of Euclidean geometry. 1956  ← geometry
- 4. Scott & Roth. A vector method for solving linear equations / inverting matrices. 1956
- 5. Scott. Independence of certain distributive laws in Boolean algebras. TAMS 1957
- 6. Scott & Tarski. The sentential calculus with infinitely long expressions. 1958
- 8. Scott, Gal & Rosser. Generalization of a lemma of G.F. Rose. JSL 1958
- 9. Scott. Dimension in elementary Euclidean geometry. 1959  ← geometry
- 12. Scott. On a theorem of Rabin. 1960
- 13. Scott. More on the axiom of extensionality. 1961
- 17. Scott, Frayne & Morel. Reduced direct products. Fund. Math. 1962
- 18. Scott & Monk. Additions to some results of Erdős and Tarski. Fund. Math. 1964
- 19. Scott. Measurement structures and linear inequalities. J. Math. Psych. 1964
- 22. Scott & Krauss. Assigning probabilities to logical formulas. 1966

## Report
Write `~/projects/reports/r0001-report-from-agent1-to-orchestrator-scott-bib-batch1.md`
with a table: entry | found? (Y/N) | source URL | filename in papers/ | notes.
End with "M of N acquired".

---
round: 1
from: orchestrator
to: agent4
subject: scott-bib-acquire-batch4
project-tz: America/Los_Angeles
---

# Agent 4 — acquire Scott bibliography PDFs (batch 4: 1992–2025)

Source list: `~/projects/ScottBibliography.md`. Find a **legitimately open-access
PDF** for each not-held entry and download into `~/projects/papers/`, then report.
This batch is the **most OA-rich** — many are on arXiv, the Archive of Formal
Proofs, or authors' pages (Benzmüller's site, Panangaden, Awodey, Birkedal).

## Rules
- Legitimate sources only (arXiv, HAL, AFP `isa-afp.org`, publisher OA, author
  pages, DOI OA, LIPIcs/Dagstuhl, ENTCS OA). **No** shadow libraries.
- Verify each is a real PDF (`file …`); name `Scott-YEAR-Short-Title.pdf` (or
  lead-author-YEAR-… for multi-author).
- Do NOT run git.

## Entries
- 76. Scott, Freyd, Mulry & Rosolini. Extensional PERs. Inf. Comput. 1992
- 78. Scott. Symbolic Computation and Teaching. AISMC-3, 1996
- 79. Scott. Effective Versions of Equilogical Spaces. ENTCS 1998
- 80. Scott, Birkedal, Carboni, Rosolini. Type Theory via Exact Categories. LICS 1998
- 81. Scott. Some Reflections on Strachey and his Work. HOSC 2000
- 82. Scott, Awodey, Birkedal. Local Realizability Toposes… MSCS 2002
- 83. Scott, Bauer, Birkedal. Equilogical Spaces. TCS 2004
- 84. Scott. Foreword (*The Seventeen Provers of the World*). 2006
- 86. Scott & McCarty. Reconsidering ordered pairs. BSL 2008
- 87. Scott. Stochastic λ-calculi: an extended abstract. J. Applied Logic 2014
- 88. Scott, Plotkin, Bauer. Cartesian Closed Categories of Separable Scott Domains. TCS 2014
- 89. Scott & Benzmüller. Automating Free Logic in Isabelle/HOL. ICMS 2016
- 90. Scott, Fritz, Lederman, Liu. Can Modalities Save Naive Set Theory? RSL 2018
- 91. Scott & Benzmüller. Reflections on a Computer-aided Theory Exploration Study… AITP 2018
- 93. Bacci, Furber, Kozen, Mardare, Panangaden, Scott. Boolean-valued semantics for the stochastic λ-calculus. LICS 2018
- 94. Lando & Scott. A calculus of regions respecting both measure and topology. JPL 2019
- 95. Scott & Benzmüller. Automating Free Logic in HOL… JAR 2020
- 98. Scott & Benzmüller. Notes on Gödel's and Scott's Variants of the Ontological Argument. 2025

## Report
Write `~/projects/reports/r0001-report-from-agent4-to-orchestrator-scott-bib-batch4.md`
with a table: entry | found? | source URL | filename | notes. End with "M of N acquired".

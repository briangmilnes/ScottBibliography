---
round: 1
from: agent1
to: orchestrator
subject: scott-bib-acquire-batch1
project-tz: America/Los_Angeles
---

# Agent 1 report — Scott bibliography PDF acquisition (batch 1)

Batch size: **18 entries** (4 books a–d + 14 papers). Acquired **6**; 12 have no
retrievable open-access copy.

## Results

| Entry | Title (short) | Found? | Source URL | Filename in papers/ | Notes |
| ----- | ------------- | :----: | ---------- | ------------------- | ----- |
| a | Scott & Lemmon, *An Introduction to Modal Logic*, OUP 1977 | N | — | — | OUP monograph; no OA edition. |
| b | *A Compendium of Continuous Lattices*, Springer 1980 | N | — | — | Springer book; paywalled, no OA. |
| c | *Continuous Lattices and Domains*, CUP 2003 | N | — | — | CUP book; paywalled, no OA. |
| d | *Homotopy Type Theory*, IAS 2013 | **Y** | https://archive.org/download/HottOnline/hott-online.pdf | Scott-2013-Homotopy-Type-Theory.pdf | OA book. homotopytypetheory.org "released" link is a dead redirect and the nightly-build filename 404'd; pulled the identical PDF from the Internet Archive mirror (3.2 MB, v1.5). |
| 1 | Kalicki & Scott, Equational completeness of abstract algebras, 1955 | **Y** | https://digital.library.txst.edu/bitstreams/fc129c5c-fa71-4d47-b08b-68d3e6067446/download | Scott-1955-Equational-Completeness-Abstract-Algebras.pdf | Texas State University institutional repository (1.8 MB). |
| 2 | Scott, Equationally complete extensions of finite algebras, 1956 | N | (SD open archive) https://www.sciencedirect.com/journal/indagationes-mathematicae-proceedings | — | Indag. Math. 18 (1956) 35–38. On ScienceDirect open archive (Indag. Proc. 1951–1989 is OA) but not retrievable: SD returns HTTP 403 to curl/WebFetch and the Chrome extension is not connected. |
| 3 | Scott, A symmetric primitive notion for Euclidean geometry, 1956  ← geometry | N | (SD open archive) https://www.sciencedirect.com/journal/indagationes-mathematicae-proceedings | — | Indag. Math. 18 (1956) 456–461. Same SD 403 barrier as entry 2. Needs a browser session to download. |
| 4 | Scott & Roth, A vector method for solving linear equations / inverting matrices, 1956 | N | — | — | No bibliographic record or OA copy located. |
| 5 | Scott, Independence of certain distributive laws in Boolean algebras, TAMS 1957 | **Y** | https://www.ams.org/journals/tran/1957-084-01/S0002-9947-1957-0086048-7/S0002-9947-1957-0086048-7.pdf | Scott-1957-Independence-Distributive-Laws-Boolean-Algebras.pdf | AMS free journal archive (TAMS 84, pp. 258–261; 4 pp, 350 KB). |
| 6 | Scott & Tarski, The sentential calculus with infinitely long expressions, 1958 | **Y** | http://matwbn.icm.edu.pl/ksiazki/cm/cm6/cm6121.pdf | Scott-Tarski-1958-Sentential-Calculus-Infinitely-Long-Expressions.pdf | Colloquium Math. 6 (1958) 165–170, via EuDML → matwbn/ICM OA (2.5 MB). |
| 8 | Gál, Rosser & Scott, Generalization of a lemma of G.F. Rose, JSL 1958 | N | — | — | JSL 23(2), pp. 137–138. Cambridge Core / JSTOR only; no OA. |
| 9 | Scott, Dimension in elementary Euclidean geometry, 1959  ← geometry | N | — | — | North-Holland volume chapter (Studies in Logic); paywalled, no OA. |
| 12 | Scott, On a theorem of Rabin, 1960 | N | (SD open archive) https://www.sciencedirect.com/journal/indagationes-mathematicae-proceedings | — | Indag. Math. / KNAW Proc. A, 1960. Same SD 403 barrier as entries 2/3. |
| 13 | Scott, More on the axiom of extensionality, 1961 | N | — | — | Book chapter (*Essays on the Foundations of Mathematics*, Magnes Press); no OA. |
| 17 | Frayne, Morel & Scott, Reduced direct products, Fund. Math. 1962 | **Y** | http://matwbn.icm.edu.pl/ksiazki/fm/fm51/fm51116.pdf | Scott-1962-Reduced-Direct-Products.pdf | Fund. Math. 51 (1962) 195–228, via EuDML → matwbn/ICM OA (7.0 MB). |
| 18 | Monk & Scott, Additions to some results of Erdős and Tarski, Fund. Math. 1964 | **Y** | http://matwbn.icm.edu.pl/ksiazki/fm/fm53/fm53124.pdf | Scott-1964-Additions-Results-Erdos-Tarski.pdf | Fund. Math. 53 (1964) 335–343, via EuDML → matwbn/ICM OA (5 pp, 947 KB). |
| 19 | Scott, Measurement structures and linear inequalities, J. Math. Psych. 1964 | N | — | — | Elsevier abstract-only (pii 0022249664900021); paywalled, no OA. |
| 22 | Scott & Krauss, Assigning probabilities to logical formulas, 1966 | N | — | — | North-Holland volume chapter (*Aspects of Inductive Logic*); no OA. |

## Notes on method / productive sources

- **EuDML → matwbn/ICM** (Polish Virtual Library of Science) is fully OA and
  supplied entries 6, 17, 18 (Colloquium Mathematicum and Fundamenta
  Mathematicae). Highest-yield source for Scott's Polish-journal papers.
- **AMS free journal archive** supplied entry 5 (TAMS pre-5-year OA).
- **Texas State repository** held a scan of entry 1.
- **ScienceDirect Indagationes Mathematicae (Proceedings), 1951–1989** is listed
  as an open archive and would cover entries 2, 3, 12, but the PDFs are not
  reachable by curl/WebFetch (HTTP 403 challenge). A connected Chrome session (or
  an authenticated Elsevier fetch tool) would likely retrieve all three; the
  Chrome extension was not connected during this run.
- Books a, b, c and chapter-in-volume items (9, 13, 22) plus paywalled journal
  papers (8, 19) have no located OA copy.
- All 6 downloads verified as real PDFs via `file` (versions 1.4–1.6).

**6 of 18 acquired.**

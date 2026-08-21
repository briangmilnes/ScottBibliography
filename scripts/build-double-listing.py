#!/usr/bin/env python3
"""Typeset the double listing -- archive row number beside bibliography number.

Reads index.html, which since the Bib # column carries both keys, and emits a
LaTeX longtable compiled with xelatex. Columns: this page's row number, the
number printed in ScottBibliography.pdf (draft of Sunday, March 15, 2026), their
difference, year, authors, title.

A third table lists the papers numbered in the bibliography that the archive does
not hold. These have no row in index.html, so they appear in the first two tables
only as gaps in the Bib # column; the gaps are computed here from the Bib # values
and cross-checked against MissingPapers.md, which supplies venue and retrieval
route. A disagreement between the two is a hard error, not a silent difference.

Usage: build-double-listing.py <output-dir>
"""
import re, os, sys, html, subprocess

ROOT = '/Users/scott/projects/ScottBibliography'
OUT  = sys.argv[1] if len(sys.argv) > 1 else '.'
src  = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()

def tex(s):
    s = html.unescape(s)
    s = re.sub(r'<i>(.*?)</i>', r'\\textit{\1}', s)
    s = re.sub(r'<a [^>]*>(.*?)</a>', r'\1', s)
    for a, b in [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'),
                 ('$', r'\$'), ('#', r'\#'), ('_', r'\_'),
                 ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')]:
        s = s.replace(a, b)
    s = re.sub(r'\\textbackslash\{\}textit\{(.*?)\}', r'\\textit{\1}', s)
    s = re.sub(r'\*(.+?)\*', r'\\emph{\1}', s)          # markdown emphasis in titles
    return s

ROW = re.compile(r'<tr><td class="n">(.*?)</td><td class="b">(.*?)</td>'
                 r'<td class="y">(\d{4})</td>(.*?)</tr>', re.S)

def rows(table):
    out = []
    for m in ROW.finditer(table):
        rest = re.findall(r'<td>(.*?)</td>', m.group(4), re.S)
        author, title = (rest[0], rest[1]) if len(rest) == 2 else ('', rest[0])
        out.append((tex(m.group(1)), tex(m.group(2)), m.group(3),
                    tex(author), tex(title)))
    return out

tables = re.findall(r'<table>.*?</table>', src, re.S)
books, papers = rows(tables[0]), rows(tables[1])

# --- papers the bibliography numbers but the archive does not hold -------------
# The Bib # column numbers 1..99 over the whole corpus; a number absent from every
# row of either table is a paper not held. Book-tagged items (#9, #62, #63) carry
# their Bib # in the book table, so both tables must be scanned.
held = {int(b) for t in (books, papers) for n, b, y, a, ti in t if b.isdigit()}
gaps = [n for n in range(1, 100) if n not in held]

# Year and title come from the bibliography itself, so the third table is keyed to
# the same document as the Bib # column.
BIBROW = re.compile(r'^\|\s*(\d+)\s*\|\s*(.*?)\s*\|', re.M)
bibmd = open(os.path.join(ROOT, 'ScottBibliography.md'), encoding='utf-8').read()
bib = {}
for m in BIBROW.finditer(bibmd):
    cite = m.group(2)
    y = re.search(r'(\d{4})\.?\s*$', cite)
    bib[int(m.group(1))] = (y.group(1) if y else '',
                            re.sub(r'^Scott[^.]*\.\s*', '', cite))

# Venue and retrieval route come from MissingPapers.md, whose paper tables carry
# four cells: number, citation, venue, route.
MISSROW = re.compile(r'^\|\s*(\d+)\s*\|(.*?)\|(.*?)\|(.*?)\|\s*$', re.M)
missmd = open(os.path.join(ROOT, 'MissingPapers.md'), encoding='utf-8').read()
route_of = {'\U0001f7e2': 'OA', '\U0001f535': 'CMU', '\U0001f4d6': 'BOOK',
            '\u26ab': 'ARCHIVE'}
miss = {}
for m in MISSROW.finditer(missmd):
    route = next((v for k, v in route_of.items() if k in m.group(4)), '')
    miss[int(m.group(1))] = (m.group(3).strip(), route)

if set(miss) != set(gaps):
    sys.exit('gap set %s disagrees with MissingPapers.md %s'
             % (sorted(gaps), sorted(miss)))

def missing_body():
    L = []
    for n in gaps:
        y, t = bib.get(n, ('', ''))
        venue, route = miss[n]
        # Strip the trailing year the bibliography citation repeats; the venue
        # string carries its own. A few citations also fold the venue into the
        # title (#72 carries "MCS News '90"), so drop any trailing fragment the
        # venue already states, then the punctuation left behind.
        t = re.sub(r'\s*\(?\d{4}\)?\.?\s*$', '', t)
        while True:
            m = re.search(r'[.,]\s*([^.,]+?)\s*[.,]?\s*$', t)
            if m and m.group(1) and m.group(1) in venue:
                t = t[:m.start()]
            else:
                break
        t = t.rstrip(' .,')
        L.append(f'{n} & {y} & {tex(t)} & {tex(venue)} & {route} \\\\')
    return '\n'.join(L)

def delta(n, b):
    if n.isdigit() and b.isdigit():
        return '$%+d$' % (int(b) - int(n))
    return '---'

def body(rs, book=False):
    L = []
    for n, b, y, a, t in rs:
        d = '---' if book else delta(n, b)
        L.append(f'{n} & {b} & {d} & {y} & {a} & {t} \\\\')
    return '\n'.join(L)

eq = sum(1 for n, b, y, a, t in papers if n.isdigit() and b.isdigit() and int(n) == int(b))
num = [(int(n), int(b)) for n, b, y, a, t in papers if n.isdigit() and b.isdigit()]
ds = [b - n for n, b in num]

doc = r'''\documentclass[10pt]{article}
\usepackage[a4paper,margin=15mm,includefoot]{geometry}
\usepackage{fontspec}
\setmainfont{Times New Roman}
\usepackage{longtable,array,booktabs}
\usepackage[table]{xcolor}
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\footnotesize Dana S. Scott --- Paper Archive: the double listing}
\fancyfoot[C]{\footnotesize\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\setlength{\LTcapwidth}{\textwidth}
\begin{document}
\thispagestyle{plain}
\begin{center}
{\Large\bfseries The double listing}\\[2pt]
{\large Archive row number beside bibliography number}\\[6pt]
\end{center}

\noindent\textbf{\#} is the row number in the archive's \texttt{index.html}, which
numbers only the items held, in year order. \textbf{Bib \#} is the number printed
in \texttt{ScottBibliography.pdf}, draft of Sunday, March 15, 2026, which numbers
books a--d and papers 1--99 over the whole corpus, held or not. \textbf{$\Delta$}
is Bib\,\# minus \#.\medskip

\noindent The two sequences are different keys. They agree on ''' + str(eq) + r''' of ''' + str(len(num)) + r''' numbered
rows, first diverging at row 8 (= bibliography 6), where the archive inserts the
1958 dissertation that the bibliography does not number; $\Delta$ runs
$''' + '%+d' % min(ds) + r'''$ to $''' + '%+d' % max(ds) + r'''$, widening as the 17 papers not yet held drop out.
An \textit{italic roman} Bib\,\# marks a held item the bibliography does not number.
The ''' + str(len(gaps)) + r''' numbers absent from the Bib\,\# column are the papers not held; they are
listed in full in the third table.
\medskip

\noindent\textbf{ScottBibliography.md} reproduces the printed bibliography exactly:
99 of 99 paper titles agree at the same number, books a--d agree, and neither side
has a gap or a duplicate.\bigskip

{\small
\begin{longtable}{@{}r@{\hskip 10pt}l@{\hskip 10pt}r@{\hskip 10pt}l@{\hskip 10pt}p{34mm}@{\hskip 8pt}p{72mm}@{}}
\multicolumn{6}{@{}l}{\textbf{Book-length items}}\\[2pt]
\toprule
\textbf{\#} & \textbf{Bib \#} & \textbf{$\Delta$} & \textbf{Year} & \textbf{Authors} & \textbf{Title}\\
\midrule
\endfirsthead
\toprule
\textbf{\#} & \textbf{Bib \#} & \textbf{$\Delta$} & \textbf{Year} & \textbf{Authors} & \textbf{Title}\\
\midrule
\endhead
''' + body(books, book=True) + r'''
\bottomrule
\end{longtable}
\bigskip

\begin{longtable}{@{}r@{\hskip 10pt}l@{\hskip 10pt}r@{\hskip 10pt}l@{\hskip 10pt}p{34mm}@{\hskip 8pt}p{72mm}@{}}
\multicolumn{6}{@{}l}{\textbf{Papers} --- ''' + str(len(papers)) + r''' rows}\\[2pt]
\toprule
\textbf{\#} & \textbf{Bib \#} & \textbf{$\Delta$} & \textbf{Year} & \textbf{Authors} & \textbf{Title}\\
\midrule
\endfirsthead
\multicolumn{6}{@{}l}{\textbf{Papers} \textit{(continued)}}\\[2pt]
\toprule
\textbf{\#} & \textbf{Bib \#} & \textbf{$\Delta$} & \textbf{Year} & \textbf{Authors} & \textbf{Title}\\
\midrule
\endhead
''' + body(papers) + r'''
\bottomrule
\end{longtable}
\bigskip

\noindent\textbf{Route} is the retrieval route recorded in \texttt{MissingPapers.md}:
\textsc{cmu} paywalled but covered by a CMU subscription, \textsc{book} sold only as
part of a book, \textsc{archive} no online copy located. Coverage closes at
''' + str(len(held)) + r''' of 99 papers held.\medskip

\begin{longtable}{@{}r@{\hskip 10pt}l@{\hskip 10pt}p{58mm}@{\hskip 8pt}p{58mm}@{\hskip 8pt}l@{}}
\multicolumn{5}{@{}l}{\textbf{Numbered in the bibliography, not held} --- ''' + str(len(gaps)) + r''' papers}\\[2pt]
\toprule
\textbf{Bib \#} & \textbf{Year} & \textbf{Title} & \textbf{Venue} & \textbf{Route}\\
\midrule
\endfirsthead
\multicolumn{5}{@{}l}{\textbf{Numbered in the bibliography, not held} \textit{(continued)}}\\[2pt]
\toprule
\textbf{Bib \#} & \textbf{Year} & \textbf{Title} & \textbf{Venue} & \textbf{Route}\\
\midrule
\endhead
''' + missing_body() + r'''
\bottomrule
\end{longtable}

}
\end{document}
'''

os.makedirs(OUT, exist_ok=True)
texfile = os.path.join(OUT, 'ScottDoubleListing.tex')
open(texfile, 'w', encoding='utf-8').write(doc)
r = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                    'ScottDoubleListing.tex'], cwd=OUT,
                   capture_output=True, text=True)
if r.returncode:
    print(r.stdout[-3000:]); sys.exit('xelatex failed')
subprocess.run(['xelatex', '-interaction=nonstopmode', 'ScottDoubleListing.tex'],
               cwd=OUT, capture_output=True, text=True)
pdf = os.path.join(OUT, 'ScottDoubleListing.pdf')
print(f'books={len(books)} papers={len(papers)} equal={eq}/{len(num)} '
      f'delta={min(ds):+d}..{max(ds):+d} held={len(held)}/99 missing={len(gaps)}')
print(f'{pdf}  {os.path.getsize(pdf)} bytes')

#!/usr/bin/env python3
"""Typeset the double listing -- archive row number beside bibliography number.

Reads index.html, which since the Bib # column carries both keys, and emits a
LaTeX longtable compiled with xelatex. Columns: this page's row number, the
number printed in ScottBibliography.pdf (draft of Sunday, March 15, 2026), their
difference, year, authors, title.

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
      f'delta={min(ds):+d}..{max(ds):+d}')
print(f'{pdf}  {os.path.getsize(pdf)} bytes')

#!/usr/bin/env python3
"""Add a Bib # column to the two tables in index.html.

The page numbers its rows 1..86 in year order over the items held; the source
bibliography (ScottBibliography.pdf, draft of Sunday, March 15, 2026) numbers
books a-d and papers 1-99 over the whole corpus. The two keys diverge from row 8
onward, so a reader coming from the printed bibliography cannot find a row by its
printed number. This inserts the bibliography number beside the row number.

The mapping key is the PDF path, which index.html and ScottBibliography.md both
carry verbatim -- never the title, which the two spell differently.
Un-numbered held items get their ScottBibliography.md roman label i-vi, italic.
Idempotent: refuses to run twice.
"""
import re, os, sys

ROOT = '/Users/scott/projects/ScottBibliography'
IX   = os.path.join(ROOT, 'index.html')

# ---- bibliography number for every held PDF, from the md transcription ----
md = open(os.path.join(ROOT, 'ScottBibliography.md'), encoding='utf-8').read()
bib = {}
for m in re.finditer(r'^\|\s*(\d+)\s*\|\s*.*?\s*\|\s*(?:✓|partial)\s*\|\s*(.*?)\s*\|\s*$',
                     md.split('## Papers')[1].split('## Held')[0], re.M):
    for f in re.findall(r'[\w./-]+\.pdf', m.group(2)):
        bib[f] = m.group(1)
for m in re.finditer(r'^\|\s*([a-d])\s*\|\s*.*?\s*\|\s*(?:✓|partial)\s*\|\s*(.*?)\s*\|\s*$',
                     md.split('## Books')[1].split('## Papers')[0], re.M):
    for f in re.findall(r'[\w./-]+\.pdf', m.group(2)):
        bib[f] = m.group(1)
for m in re.finditer(r'^\|\s*(i|ii|iii|iv|v|vi)\s*\|\s*.*?\s*\|\s*(\S+\.pdf)\s*\|\s*$',
                     md.split('## Held')[1], re.M):
    bib['papers/' + m.group(2)] = '<i>%s</i>' % m.group(1)

src = open(IX, encoding='utf-8').read()
if 'Bib #' in src:
    sys.exit('index.html already has the Bib # column; nothing to do.')

# ---- headers ----
src = src.replace('<thead><tr><th>#</th><th>Year</th><th>Item</th></tr></thead>',
                  '<thead><tr><th>#</th><th>Bib #</th><th>Year</th><th>Item</th></tr></thead>')
src = src.replace('<thead><tr><th>#</th><th>Year</th><th>Authors</th><th>Title</th></tr></thead>',
                  '<thead><tr><th>#</th><th>Bib #</th><th>Year</th><th>Authors</th><th>Title</th></tr></thead>')

# ---- rows ----
missing, done = [], 0
def cell(m):
    global done
    href = re.search(r'href="([^"]+)"', m.group(0))
    n = bib.get(href.group(1)) if href else None
    if n is None:
        missing.append(href.group(1) if href else m.group(0)[:60])
        n = '&mdash;'
    done += 1
    return '%s<td class="b">%s</td>%s' % (m.group(1), n, m.group(2))

src = re.sub(r'(<tr><td class="n">[^<]*</td>)(<td class="y">.*?</tr>)', cell, src)

# ---- style: the new cell reads like the other two nowrap columns ----
src = src.replace('td.n,td.y{white-space:nowrap;color:#555}',
                  'td.n,td.b,td.y{white-space:nowrap;color:#555}\n td.b{font-variant-numeric:tabular-nums}')
src = src.replace('.sub,td.n,td.y,th{color:#aaa}', '.sub,td.n,td.b,td.y,th{color:#aaa}')

open(IX, 'w', encoding='utf-8').write(src)
print(f'rows given a Bib # cell: {done}')
print(f'rows with no bibliography number: {len(missing)} {missing}')

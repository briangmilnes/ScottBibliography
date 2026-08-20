#!/usr/bin/env python3
"""Reconcile the three numberings of the Scott bibliography.

Sources
  1. ScottBibliography.pdf  — the authoritative source list (books a-d, papers 1..N)
  2. ScottBibliography.md   — the transcription, which claims to carry the PDF's numbers
  3. index.html             — the archive's browsable list, which carries its own numbers

Reports, per pair: sequence integrity (gaps/duplicates), cardinality, and per-number
title agreement using a normalized-token Jaccard score.
"""
import re, os, sys, html, unicodedata, subprocess

ROOT = '/Users/scott/projects/ScottBibliography'
TXT  = sys.argv[1] if len(sys.argv) > 1 else '/tmp/bib.txt'

def norm(s):
    s = html.unescape(s)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace('’', "'").replace('–', '-').replace('—', '-')
    return re.sub(r'[^a-z0-9 ]', ' ', s)

STOP = {'a','an','the','of','in','on','for','and','to','with','its','some','d','scott'}
def toks(s):
    return {w for w in norm(s).split() if w and w not in STOP}

def jac(a, b):
    """Containment of the shorter token set in the longer.

    The PDF entry carries the full venue string and the md/html carry a bare
    title, so symmetric Jaccard under-scores a correct match; containment is
    the right measure here."""
    A, B = toks(a), toks(b)
    if not A or not B:
        return 0.0
    small, big = (A, B) if len(A) <= len(B) else (B, A)
    return len(small & big) / len(small)

# ---- 1. the PDF ----------------------------------------------------------
raw = open(TXT, encoding='utf-8').read()
raw = re.sub(r'^\s*-\d+-\s*$', '', raw, flags=re.M)          # page numbers
pdf = {}
cur = None
for line in raw.splitlines():
    m = re.match(r'\s*([a-d]|\d{1,3})\.\s+(\S.*)$', line)
    if m and (m.group(1).isalpha() or 1 <= int(m.group(1)) <= 200):
        cur = m.group(1)
        if cur in pdf:                                        # duplicate marker
            pdf[cur + '_dup'] = m.group(2)
            cur = cur + '_dup'
        else:
            pdf[cur] = m.group(2)
    elif cur and line.strip():
        pdf[cur] += ' ' + line.strip()

def pdf_title(entry):
    """Title = text up to the first sentence end that is not an initial/abbrev."""
    e = re.sub(r'^(?:[A-Z][a-zA-ZÀ-ɏ.’\']*[,.]?\s+){0,12}?(?=[A-Z][a-z])', '', entry)
    return entry

pdf_papers = {int(k): v for k, v in pdf.items() if k.isdigit()}
pdf_books  = {k: v for k, v in pdf.items() if k.isalpha() and len(k) == 1}
dups       = [k for k in pdf if k.endswith('_dup')]

# ---- 2. the markdown -----------------------------------------------------
md = open(os.path.join(ROOT, 'ScottBibliography.md'), encoding='utf-8').read()
sec = md.split('## Papers')[1].split('## Held')[0]
md_papers = {}
for m in re.finditer(r'^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(✓|partial)?\s*\|\s*(.*?)\s*\|\s*$', sec, re.M):
    md_papers[int(m.group(1))] = (m.group(2), bool(m.group(3)), m.group(4))
bsec = md.split('## Books')[1].split('## Papers')[0]
md_books = {m.group(1): m.group(2) for m in
            re.finditer(r'^\|\s*([a-d])\s*\|\s*(.*?)\s*\|', bsec, re.M)}
md_extra = len(re.findall(r'^\|\s*(?:i|ii|iii|iv|v|vi)\s*\|', md.split('## Held')[1], re.M)) \
           if '## Held' in md else 0

# ---- 3. index.html -------------------------------------------------------
ix = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
ix_rows = {}
for m in re.finditer(r'<tr><td class="n">(\d+)</td><td class="y">(\d{4})</td><td>(.*?)</td><td>'
                     r'(?:<a href="([^"]*)">)?(.*?)(?:</a>)?</td></tr>', ix):
    ix_rows[int(m.group(1))] = (m.group(2), html.unescape(m.group(3)),
                                m.group(4) or '', html.unescape(m.group(5)))

def seq_report(name, nums):
    nums = sorted(nums)
    lo, hi = nums[0], nums[-1]
    missing = [n for n in range(lo, hi + 1) if n not in nums]
    dup = [n for n in set(nums) if nums.count(n) > 1]
    print(f"{name:22s} n={len(nums):3d} range={lo}..{hi} gaps={missing or 'none'} dups={dup or 'none'}")

print("=" * 78)
print("SEQUENCE INTEGRITY")
print("=" * 78)
seq_report('PDF papers', pdf_papers)
seq_report('MD papers', md_papers)
seq_report('index.html rows', ix_rows)
print(f"{'PDF books':22s} {sorted(pdf_books)}   MD books {sorted(md_books)}")
print(f"{'PDF dup markers':22s} {dups or 'none'}")
print(f"{'MD un-numbered held':22s} {md_extra}")

print()
print("=" * 78)
print("PDF n  vs  MD n   (same number, title agreement)")
print("=" * 78)
bad = 0
for n in sorted(set(pdf_papers) | set(md_papers)):
    if n not in pdf_papers:
        print(f"  {n:3d}  IN MD ONLY   md='{md_papers[n][0][:70]}'"); bad += 1; continue
    if n not in md_papers:
        print(f"  {n:3d}  IN PDF ONLY  pdf='{pdf_papers[n][:70]}'"); bad += 1; continue
    s = jac(pdf_papers[n], md_papers[n][0])
    if s < 0.70:
        print(f"  {n:3d}  containment={s:.2f}")
        print(f"        pdf: {pdf_papers[n][:110]}")
        print(f"        md : {md_papers[n][0][:110]}")
        bad += 1
print(f"  -> {len(set(pdf_papers) & set(md_papers)) - bad if bad else len(pdf_papers)} agree, {bad} to inspect")

print()
print("=" * 78)
print("index.html n  vs  PDF n   (does the web list carry the bibliography's numbers?)")
print("=" * 78)
same = 0
offsets = {}
for n in sorted(ix_rows):
    title = ix_rows[n][3]
    if n in pdf_papers and jac(pdf_papers[n], title) >= 0.70:
        same += 1
    # where does this title actually sit in the PDF?
    best = max(pdf_papers, key=lambda k: jac(pdf_papers[k], title), default=None)
    sc = jac(pdf_papers[best], title) if best else 0
    offsets[n] = (best if sc >= 0.70 else None, sc)
print(f"  rows whose index number equals the PDF number: {same} of {len(ix_rows)}")
unmatched = [n for n, (b, s) in offsets.items() if b is None]
print(f"  index rows with no PDF entry above threshold : {len(unmatched)} -> {unmatched}")
print()
print("  index#  pdf#  delta  year  title")
for n in sorted(ix_rows):
    b, s = offsets[n]
    d = '' if b is None else f"{b - n:+d}"
    print(f"  {n:5d}  {str(b or '-'):>4}  {d:>5}  {ix_rows[n][0]}  {ix_rows[n][3][:64]}")

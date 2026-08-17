#!/usr/bin/env python3
"""Extract an abstract, or a first-paragraph substitute, from each held PDF.

Why this exists: `abstract:null` in docs/overview.html is a hand-authored
assertion meaning "nobody transcribed one". It does not distinguish a paper
that prints no abstract from one whose abstract was simply never typed in.
This script replaces that assertion with a measurement.

Two extraction modes, in priority order:

  marked    the page prints an explicit abstract marker (Abstract, Summary,
            Resume, Zusammenfassung, ...). The block following it is taken.
  opening   no marker. The first block of running prose after the title and
            byline is taken instead -- for a 1950s paper that opens "It is the
            purpose of this note to prove the following", that sentence is the
            abstract in everything but name.

and two failure states:

  no-text   the PDF has no text layer (needs OCR first)
  none      text extracted, but no block qualified as prose

Output is JSON on stdout and a human-readable review file, so every proposed
abstract can be read against its source before anything is written back into
docs/overview.html. This script never edits overview.html.

Usage: python3 scripts/extract-abstracts.py [--out DIR]
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERVIEW = os.path.join(ROOT, "docs", "overview.html")

# Front matter is scanned over this many pages: an abstract is on page 1 for a
# journal article, but reprints and technical monographs carry a cover sheet
# and a repeated title page first.
FRONT_PAGES = 6

# A cover page alone can carry a text layer while every body page is image-only
# -- PRG monographs scanned in the 1970s do exactly this. Requiring one page to
# clear this bar separates a real text layer from a stray scanned cover.
PAGE_MIN_CHARS = 400

# A marker found deep in the body is a cross-reference ("see the abstract of
# [12]"), not this paper's abstract. Only the front matter region is searched.
MARKER_WINDOW = 3000

# Longest abstract kept. Anything past this is body text that ran on because
# the PDF printed no blank line between the abstract and section 1.
ABSTRACT_MAX_CHARS = 2000

# How far into a block front-matter markers are looked for. A byline sits at
# the top; a footnote naming a university sits at the bottom and must not
# disqualify the paragraph above it.
FRONT_SCAN_CHARS = 160

# Lowest share of real English words a block may have and still be treated as
# this paper's prose. Set between the worst English scan in the corpus (0.69)
# and the best foreign-language block (0.39).
MIN_WORD_QUALITY = 0.55

# Below this, a text-layer abstract is suspected of character corruption
# ("Abstrad", "tak.en", "q~estions") and is re-read from OCR of the same pages.
# Whichever reading scores higher is kept, so a good text layer is never
# replaced by worse OCR.
OCR_RETRY_QUALITY = 0.78

# PDFs whose text layer exists but is unusable because the stored character
# order is scrambled: the tail of each printed line is emitted before its head,
# so no reading order reconstructs the sentence. A character count cannot
# detect this -- the layer looks healthy -- so the files are listed by name and
# routed to OCR as though they had no text layer at all.
SCRAMBLED_TEXT_LAYER = {
    "Scott-1982-Some-Ordered-Sets-in-Computer-Science",
    # Font encoding drops every "c": "a logi for types and omputation that
    # in ludes both the usual spa es of mathemati s". The glyphs are on the
    # page, so OCR reads what the text layer cannot express.
    "Awodey-Birkedal-Scott-2002-Local-Realizability-Toposes-and-Modal-Logic-for-Computability",
    # Digits substituted for letters throughout: "the theory of domams IS to
    # g1ve models", "denotat10nal semat1cs mvolve". Same remedy.
    "Scott-1982-Domains-for-Denotational-Semantics-BOOK-ICALP82-LNCS140",
    # Two-column pages whose stored order interleaves the columns line by
    # line, producing "Mathematical theories arise fo sometimes in connection
    # with specific owing to accidental inspiration". Re-OCR reads the columns
    # in printed order.
    "Scott-1970-Extending-Topological-Interpretation-Intuitionistic-Analysis-II",
    "Scott-1974-Does-Many-Valued-Logic-Have-Any-Use",
    "Scott-1980-Relating-Theories-of-the-Lambda-Calculus",
}

# Some entries are a chapter inside a scan of the whole volume, so page 1 is
# the book's title page and the paper starts far in. The PDF page on which the
# contribution begins is recorded here; it is found from the volume's table of
# contents and confirmed by reading that page.
CHAPTER_START = {
    # Printed p. 53 of The Axiomatic Method (North-Holland, 1959).
    "Scott-1959-Dimension-in-Elementary-Euclidean-Geometry-BOOK-TheAxiomaticMethod": 69,
    # Printed p. 146 of Theoretical Foundations of Programming Methodology
    # (NATO ASI C91, 1982); pages 1-151 are other contributors' lectures.
    "Scott-1982-Lectures-Math-Theory-Computation-BOOK-TheoreticalFoundationsProgMethodology": 152,
    # Printed p. 577 of ICALP 82 (LNCS 140); the file is the whole volume and
    # page 1 is the conference preface.
    "Scott-1982-Domains-for-Denotational-Semantics-BOOK-ICALP82-LNCS140": 585,
    # The file is the whole AITP 2018 abstract booklet; page 1 is its preface.
    "Benzmuller-Scott-2018-Reflections-Theory-Exploration-Study-AITP": 7,
    # Technical-report cover, contents and lists of figures occupy pages 1-10;
    # Chapter 1 begins on page 11.
    "Scott-1990-Semantic-Domains-and-Denotational-Semantics": 11,
}

# Entries with no abstract to extract, recorded deliberately rather than left
# to a heuristic. These are measured findings, not extraction failures.
NO_ABSTRACT = {
    # A handwritten manuscript. Tesseract returns noise from the script, and
    # there is no typeset abstract to read.
    "Scott-1980-The-Presheaf-Model-for-Set-Theory":
        "handwritten manuscript; no typeset abstract",
    # The PDF prints the abstract of Wiedijk's volume, not of Scott's foreword.
    # Attaching it here would attribute another author's summary to Scott.
    "Scott-2006-Foreword-Seventeen-Provers":
        "foreword; the printed abstract belongs to the volume, not to it",
    # Publisher front matter only: title page, CIP record, contents.
    "Gierz-Scott-etal-2003-Continuous-Lattices-and-Domains-CUP-FRONTMATTER":
        "book front matter; contains no abstract",
    "Gierz-Scott-etal-1980-A-Compendium-of-Continuous-Lattices-BOOK-Springer":
        "book; front matter is the CIP record and contains no abstract",
}

# An explicit abstract marker, either alone on its line or followed on the same
# line by the abstract text. Covers the English, French, German and Dutch forms
# that appear in the journals Scott published in.
MARKER = re.compile(
    r"^[ \t]*(?:\d+[.)]?[ \t]*)?"
    # "abstra[ceo0]t" rather than "abstract": these scans render the word as
    # ABSTRAeT and ABSTRAOT, and an unrecognised marker sends the entry down
    # the opening-paragraph path with the marker text still attached.
    r"(abstra[cceo0]t|summary|r[eé]sum[eé]|zusammenfassung|samenvatting|synopsis)"
    r"[ \t]*[.:—–-]*[ \t]*(.*)$",
    re.IGNORECASE)

# A heading that terminates an abstract block.
STOP = re.compile(
    r"^[ \t]*(?:\d+[.)]?[ \t]*)?"
    r"(introduction|keywords?|key ?words|1[ .]|acknowledge?ments?|"
    r"contents|references|preliminaries|notation)\b",
    re.IGNORECASE)

# Front matter that is never the abstract: bibliographic headers, bylines,
# affiliations, submission notes, copyright lines, page furniture.
FRONT = re.compile(
    r"(communicated by|received|revised|accepted|copyright|©|"
    r"@|http|doi:|isbn|issn|vol\.|proceedings|"
    r"all rights reserved|printed in|reprinted|"
    r"^by$|^by |editor|press$|springer|elsevier|north-holland|"
    r"lecture notes|preprint|technical report|appeared in|to appear)",
    re.IGNORECASE)

# Institution names are matched case-sensitively. Lowercased, these words occur
# in ordinary prose -- "a course on projective geometry at my university" -- and
# matching them without regard to case discarded real opening paragraphs.
FRONT_INSTITUTION = re.compile(
    r"(Department of|University of|Institute of|College of|"
    r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s+(?:University|Institute|Laboratory))")


def structural(src, start=0):
    """Yield (index, char) for characters outside double-quoted strings.

    Brackets occur inside the data as ordinary text -- an abstract quotes
    "E[x = {{u, v> :wevex})" -- so a scanner that counts every brace loses
    track of nesting and stops early. Counting only braces that are outside
    string literals fixes that. Backslash escapes are skipped as pairs so an
    escaped quote does not end a string.
    """
    i, n, in_str = start, len(src), False
    while i < n:
        c = src[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        else:
            yield i, c
        i += 1


def js_arrays(src):
    for name in ("BOOKS", "PAPERS", "EXTRA"):
        i = src.index("const " + name)
        i = src.index("[", i)
        depth, end = 0, None
        for j, c in structural(src, i):
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None:
            sys.exit("unterminated array: " + name)
        objs, depth, start = [], 0, None
        for j, c in structural(src, i + 1):
            if j >= end:
                break
            if c == "{":
                if depth == 0:
                    start = j
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    objs.append(src[start:j + 1])
        yield name, objs


def field(obj, key):
    m = re.search(r'\b' + key + r':\s*"((?:[^"\\]|\\.)*)"', obj)
    return m.group(1) if m else None


def page_text(path, first, last, layout=True):
    cmd = ["pdftotext"]
    if layout:
        cmd.append("-layout")
    cmd += ["-f", str(first), "-l", str(last), path, "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


# A two-column page must be read down the left column and then down the right.
# pdftotext's default mode guesses that order and gets it wrong often enough to
# splice body text into the abstract, so `-layout` is used instead and the
# gutter is found here: a band of columns that is whitespace on essentially
# every line. These bounds keep a wide paragraph indent or a ragged right
# margin from being mistaken for one.
GUTTER_MIN_WIDTH = 4
# Tried strictest first. A full-width title and a four-across author block sit
# across the gutter on a conference first page, so demanding an entirely blank
# band rejects real two-column layouts; relaxing in steps admits those without
# inviting the spurious mid-page band that a looser bound alone would find.
GUTTER_BLANK_FRACTIONS = (0.95, 0.90, 0.85)
GUTTER_CENTRE_RANGE = (0.30, 0.70)
COLUMN_MIN_CHARS = 200


def find_gutter(content, width, fraction):
    blank = [0] * width
    for l in content:
        for i in range(width):
            if i >= len(l) or l[i] == " ":
                blank[i] += 1

    need = fraction * len(content)
    runs, i = [], 0
    while i < width:
        if blank[i] >= need:
            j = i
            while j < width and blank[j] >= need:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1

    lo, hi = GUTTER_CENTRE_RANGE
    best = None
    for a, b in runs:
        if b - a < GUTTER_MIN_WIDTH:
            continue
        if lo <= ((a + b) / 2) / width <= hi:
            if best is None or (b - a) > (best[1] - best[0]):
                best = (a, b)
    return best


def split_columns(page):
    """Return page text in reading order, un-interleaving two columns if present."""
    lines = page.split("\n")
    content = [l for l in lines if l.strip()]
    if len(content) < 10:
        return page
    width = max(len(l) for l in content)
    if width < 60:
        return page

    best = None
    for fraction in GUTTER_BLANK_FRACTIONS:
        best = find_gutter(content, width, fraction)
        if best is not None:
            break
    if best is None:
        return page

    a, b = best
    left = "\n".join(l[:a].rstrip() for l in lines)
    right = "\n".join(l[b:].rstrip() for l in lines)
    # A true gutter has substantial text on both sides. A single-column page
    # with a hanging indent produces one nearly empty side; keep it whole.
    if len(left.strip()) < COLUMN_MIN_CHARS or len(right.strip()) < COLUMN_MIN_CHARS:
        return page
    return left + "\n\n" + right


def front_matter(path):
    """Return (split_text, plain_text, per_page_chars) for the front matter.

    Both readings are returned because neither wins everywhere. A page whose
    abstract runs full width above a two-column body -- the standard IBM
    Journal first page -- is destroyed by column splitting, which truncates
    every abstract line at the gutter; a uniformly two-column page is
    destroyed by not splitting. The caller extracts from both and keeps
    whichever yields cleaner text, so no single threshold has to be right.

    Pages are pulled one at a time so a cover page with a stray text layer can
    be told apart from a document that is genuinely readable, and so column
    detection runs per page rather than over a concatenation of layouts.
    """
    start = CHAPTER_START.get(os.path.splitext(os.path.basename(path))[0], 1)
    per_page, split, plain = [], [], []
    for p in range(start, start + FRONT_PAGES):
        t = page_text(path, p, p)
        if t is None:
            break
        per_page.append(len(t.strip()))
        split.append(split_columns(t))
        plain.append(t)
        if not t.strip() and p > 2:
            break
    return "\n\n".join(split), "\n\n".join(plain), per_page


# Truncating a line at a false gutter leaves stranded word fragments: "in this
# paper a s instrume tape automaton". Single letters other than "a", "A" and
# "I" are not words, so their share of all tokens measures that damage and
# separates a good reading from a mangled one.
def garble(s):
    toks = re.findall(r"[A-Za-z]+", s)
    if not toks:
        return 1.0
    stray = sum(1 for t in toks if len(t) == 1 and t not in ("a", "A", "I"))
    return stray / len(toks)


def word_quality(s):
    """Share of ordinary words that are real words.

    A clean text layer scores near 1.0. A bad scan OCR'd by whoever produced
    the PDF scores far lower -- "real-valvcd, ccuntzbly [edditive measure" --
    and that is worth detecting, because re-OCRing the page image is often
    better than the text layer the file already carries.
    """
    toks = [t for t in re.findall(r"[A-Za-z]+", s) if len(t) >= 3]
    if not toks or not WORDS:
        return 1.0
    return sum(1 for t in toks if t.lower() in WORDS) / len(toks)


def best_extraction(split_text, plain_text):
    """Extract from both readings of the page and keep the cleaner result."""
    cands = []
    for text in (split_text, plain_text):
        mode, abstract = extract(text)
        if abstract:
            cands.append((garble(abstract), mode, abstract))
    if not cands:
        return "none", None
    cands.sort(key=lambda c: c[0])
    return cands[0][1], cands[0][2]


# A printed paragraph is marked by an indent on its first line, with
# continuation lines flush left. Splitting on that recovers paragraph breaks in
# scans that carry no blank line between paragraphs -- without it, the opening
# statement of #8 merges with the theorem and proof that follow it into one
# block. Indents beyond this range are centred headings, not paragraph starts.
PARA_INDENT_RANGE = (1, 10)


def paragraphs(lines):
    """Split a run of lines into paragraphs using first-line indentation."""
    if len(lines) < 3:
        return [lines]
    indents = [len(l) - len(l.lstrip()) for l in lines]
    base = min(indents)
    lo, hi = PARA_INDENT_RANGE
    starts = [i for i in range(1, len(lines))
              if lo <= indents[i] - base <= hi]
    # Jittery OCR indentation would mark most lines as paragraph starts, which
    # would shred the text; treat that as "no reliable indentation".
    if not starts or len(starts) > len(lines) // 2:
        return [lines]
    out, prev = [], 0
    for s in starts + [len(lines)]:
        out.append(lines[prev:s])
        prev = s
    return [c for c in out if c]


def blocks(text):
    """Split into blocks, each rejoined into one line.

    Blocks are delimited by blank lines and, within a run of lines, by printed
    paragraph indentation. Line-ending hyphens are treated as word breaks and
    closed up, since pdftotext preserves the printed hyphenation of justified
    text.
    """
    out = []
    chunks = []
    for raw in re.split(r"\n[ \t]*\n", text):
        keep = [l.rstrip() for l in raw.split("\n") if l.strip()]
        if keep:
            chunks.extend(paragraphs(keep))
    for lines in chunks:
        if not lines:
            continue
        s = ""
        for l in lines:
            if s.endswith("-"):
                s = s[:-1] + l.lstrip()
            elif s:
                s += " " + l.strip()
            else:
                s = l.strip()
        out.append(re.sub(r"[ \t]+", " ", s).strip())
    return out


# Blocks that read as prose but are not the paper's opening statement. Each
# pattern was added after it produced a wrong abstract in review.
NOT_ABSTRACT = [
    # Acknowledgements. Chosen for #1 ("The writer wishes to express his
    # sincere appreciation to Dr. ...") and #20.
    re.compile(r"(wish(es)? to (express|thank)|gratefully acknowledge|"
               r"indebtedness|sincere appreciation|patient guidance|"
               r"kind enough to|for many stimulating conversations|"
               r"grateful to|thanks are due)", re.IGNORECASE),
    # A journal issue's table of contents: several page ranges in one block.
    re.compile(r"(\d+\s*[-–]\s*\d+\b.*){3,}"),
    # A bibliography entry or reference list.
    re.compile(r"^\[\d+\]|\b(Fund\.|Ann\.|Bull\.|Proc\.|J\.)\s*Math\b.*\(\d{4}\)"),
    # Dot leaders, which only occur in contents listings.
    re.compile(r"\.\s?\.\s?\.\s?\.\s?\."),
    # Digitiser and publisher boilerplate stamped onto the first page.
    re.compile(r"(JSTOR|not-for-profit service|Cataloging in Publication|"
               r"Academic Publishers|Manufactured in|"
               r"terms and conditions of use|digitized|"
               r"Research Council|Framework Programme|grant agreement)",
               re.IGNORECASE),
    # A journal's own header line: "Higher-Order and Symbolic Computation,
    # 13, 103-114, 2000".
    re.compile(r"^[A-Z][\w\s\-&]{6,60},\s*\d+,\s*\d+\s*[-–]\s*\d+,\s*\d{4}"),
    # The source-volume citation reprinted above a chapter: "To H. B. Curry:
    # Essays on ... (ed. by J. P. Seldin and J. Hindley), Academic Press
    # (1980), pp. 403-450."
    re.compile(r"\(ed(?:ited)?\.?\s+by\b[^)]{0,90}\)"),
]

# An ALL-CAPS title and byline printed immediately above the opening
# paragraph, which pdftotext returns as one block with it.
TITLE_BYLINE = re.compile(
    r"^[A-Z][A-Z0-9 ,'\-]{14,}\s+BY\s+(?:[A-Z][A-Z.]*\s+){1,4}(?=[A-Z][a-z])")

# A running head repeats the page number and author above the text: "330 DANA
# SCOTT finite conjunction and ...". Stripped so the sentence starts cleanly.
RUNNING_HEAD = re.compile(
    r"^\s*\d{1,4}\s+(?:[A-Z][A-Za-z.]*\s+){0,2}"
    r"(?:SCOTT|Scott|DANA SCOTT|D\.\s*S(?:eott|cott))\b[.,]?\s*")


def rejected(b):
    return any(p.search(b) for p in NOT_ABSTRACT)


def is_prose(b):
    """True when a block reads as running prose rather than page furniture."""
    if len(b) < 120:
        return False
    alpha = [c for c in b if c.isalpha()]
    if len(alpha) < 60:
        return False
    lower = sum(1 for c in alpha if c.islower()) / len(alpha)
    if lower < 0.62:                      # filters ALL-CAPS titles and headers
        return False
    if sum(1 for c in b if c.isdigit()) / len(b) > 0.18:
        return False
    if not re.search(r"[.!?]", b):
        return False
    # Front-matter markers are checked only near the block's start, where a
    # byline or affiliation appears. Scanning the whole block discarded real
    # opening paragraphs whose footnote happened to name a university or a
    # funding body.
    head = b[:FRONT_SCAN_CHARS]
    if FRONT.search(head) or FRONT_INSTITUTION.search(head):
        return False
    # A paragraph starts with a capital, a quotation mark or a section number.
    # Starting lowercase means the block begins mid-sentence -- pdftotext
    # emitted a continuation before its opening, as in "where as usual y is
    # not free in phi" or "pretation and lawless sequences [5]".
    if b[0].islower():
        return False
    # Reject text that is not English prose. Two-up journal scans put the tail
    # of the preceding article on the same sheet -- #6 opens with French -- and
    # some papers begin with a foreign-language epigraph. Both score far below
    # any English paragraph, including the badly OCR'd ones, which sit near
    # 0.69 while French and German sit near 0.2.
    if word_quality(b) < MIN_WORD_QUALITY:
        return False
    return True


# Where an abstract stops when the PDF prints no blank line before section 1.
# Each pattern marks the start of the following section, never a word that
# could occur inside an abstract: a numbered heading, or a front-matter label.
RUN_ON = [
    re.compile(r"\s\d+\s*\.?\s*(?:Introduction|INTRODUCTION)\b"),
    re.compile(r"\s(?:Keywords?|Key ?words|KEYWORDS)\b\s*[:.]"),
    re.compile(r"\s(?:AMS|MSC|ACM)\b[^.]{0,40}(?:[Cc]lassification|[Ss]ubject)"),
    re.compile(r"\sMathematics Subject Classification\b"),
    re.compile(r"\s\d+\s*\.\s+[A-Z][a-z]+(?:\s[a-z]+){0,3}\s+[A-Z]"),
    # Letter-spaced section headings, which 1990s typesetting used in place of
    # bold: "1. T w e n t y  Q u e s t i o n s". The leading section number is
    # required: letter spacing also appears inside ordinary words in these
    # scans ("it is only a m a t t e r of time"), and matching on the spacing
    # alone truncated abstracts mid-sentence.
    re.compile(r"\s\d[\d\s.]*(?:[A-Za-z]\s){4,}"),
]


LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi",
             "ﬄ": "ffl", "ﬅ": "ft", "ﬆ": "st"}

# Some journals print the full citation above the abstract, and pdftotext
# returns it as part of the same block: "Scott, D.S., A type-theoretical
# alternative to ISWIM, CUCH, OWHY, Theoretical Computer Science 121 (1993)
# 411-440. The paper ... concerns". The citation is not the abstract.
CITATION_HEAD = re.compile(
    r"^[A-Z][A-Za-z'-]+,\s+(?:[A-Z]\.\s*){1,3}[^.]{0,200}?"
    r"\(\d{4}\)\s*\d+\s*[-–—]\s*\d+\.\s+")


def load_dictionary():
    try:
        with open("/usr/share/dict/words", encoding="utf-8", errors="ignore") as f:
            return {w.strip().lower() for w in f if w.strip()}
    except OSError:
        return set()


WORDS = load_dictionary()

# Scans of typewritten and hot-metal text often letter-space parts of words,
# so pdftotext returns "a m a t t e r" for "a matter". Four or more single
# letters in a row is the signal; fewer overlaps with genuine initials and
# with mathematical variables set inline.
# Single letters only. Widening this to two-letter tokens was tried and made
# things worse: "present s in an i n f or m a l way" re-segmented as "present
# si nan informal way", because the shortest-word-count segmentation of a run
# containing real short words like "or" and "an" is not the printed one.
SPACED_RUN = re.compile(r"(?<![A-Za-z])(?:[A-Za-z] ){3,}[A-Za-z](?![A-Za-z])")


def unspace(run):
    """Rejoin a letter-spaced run, re-splitting it into dictionary words.

    "a m a t t e r" joins to "amatter", which segments as "a matter" rather
    than as one non-word. Segmentation minimises the number of words so the
    longest real words win. If no segmentation is entirely dictionary words,
    the run is left exactly as found -- a wrong repair is worse than none.
    """
    letters = run.replace(" ", "")
    n = len(letters)
    if not WORDS or n < 4:
        return run
    # best[i] = (word_count, split_list) for letters[:i]
    best = [None] * (n + 1)
    best[0] = (0, [])
    for i in range(1, n + 1):
        for j in range(i):
            if best[j] is None:
                continue
            w = letters[j:i]
            if w.lower() in WORDS:
                cand = (best[j][0] + 1, best[j][1] + [w])
                if best[i] is None or cand[0] < best[i][0]:
                    best[i] = cand
    return " ".join(best[n][1]) if best[n] else run


# Scans of serif type read lowercase "l" as capital "I": "severaI",
# "classicaI", "Iogics". Only rewritten when the l-spelling is a real word and
# the I-spelling is not, so "I" as a pronoun and roman numerals are untouched.
I_FOR_L = re.compile(r"\b[A-Za-z]*I[A-Za-z]*\b")


def fix_i_for_l(s):
    if not WORDS:
        return s

    def repl(m):
        w = m.group(0)
        if w == "I" or w.isupper():
            return w
        if w.lower() in WORDS:
            return w
        alt = w.replace("I", "l")
        if alt.lower() in WORDS:
            return alt
        return w

    return I_FOR_L.sub(repl, s)


def clean(s):
    """Repair extraction artifacts without altering the author's wording."""
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    # A soft hyphen marks a line break inside a word; the word is one token.
    s = re.sub("­\\s*", "", s)
    s = s.replace("‐", "-").replace(" ", " ")
    s = SPACED_RUN.sub(lambda m: unspace(m.group(0)), s)
    s = fix_i_for_l(s)
    s = CITATION_HEAD.sub("", s)
    # A mis-OCR'd marker survives into the text when the opening-paragraph path
    # was taken; strip it so the abstract does not begin with its own label.
    s = re.sub(r"^\s*abstra[cceo0]t\s*[.:—–-]*\s*", "", s, flags=re.IGNORECASE)
    return re.sub(r"[ \t]+", " ", s).strip()


def trim(s):
    """Cut a candidate at the first following-section marker, then cap length."""
    cut = len(s)
    for pat in RUN_ON:
        m = pat.search(s, 80)
        if m:
            cut = min(cut, m.start())
    s = s[:cut].strip()
    if len(s) > ABSTRACT_MAX_CHARS:
        head = s[:ABSTRACT_MAX_CHARS]
        dot = head.rfind(". ")
        s = (head[:dot + 1] if dot > 200 else head).strip()
    return clean(s)


ENDS_SENTENCE = re.compile(r"[.!?][\"'”’)\]]?$")

# How many following blocks may be stitched onto a candidate. A scan can break
# one abstract into several blocks; nothing in this corpus needs more.
STITCH_MAX_BLOCKS = 8


def stitch(bs, start, first):
    """Join blocks after `first` while the text has not reached a sentence end.

    OCR of a typewritten page inserts blank lines inside a paragraph, so one
    abstract arrives as several blocks: "... but the adjunction of a top will
    make them complete lattices. The closure" / "- properties as posets ...".
    Continuing until the text ends on a terminator rejoins those without
    swallowing the next section, whose own block starts only after the
    abstract has closed with a full stop.
    """
    acc = first.strip()
    k = start
    while k < len(bs) and k - start < STITCH_MAX_BLOCKS:
        if ENDS_SENTENCE.search(acc) and len(acc) >= 80:
            break
        nxt = bs[k]
        if STOP.match(nxt) or MARKER.match(nxt):
            break
        acc = (acc + " " + nxt).strip()
        k += 1
    return acc


def extract(text):
    """Return (mode, abstract_text)."""
    bs = blocks(text)

    # Mode 1: an explicit marker, restricted to the front-matter window so a
    # body-text cross-reference cannot masquerade as this paper's abstract.
    pos = 0
    for idx, b in enumerate(bs):
        if pos > MARKER_WINDOW:
            break
        pos += len(b) + 2
        m = MARKER.match(b)
        if not m:
            continue
        tail = m.group(2).strip()
        if tail:
            got = trim(stitch(bs, idx + 1, tail))
            if len(got) >= 80:
                return "marked", got
        # Marker alone on its line: the abstract starts at the next block.
        for j in range(idx + 1, min(idx + 3, len(bs))):
            if STOP.match(bs[j]) or MARKER.match(bs[j]):
                break
            got = trim(stitch(bs, j + 1, bs[j]))
            if len(got) >= 80:
                return "marked", got
    # Mode 2: no marker -- first running-prose block, which is the paper's
    # opening statement of what it proves.
    for j, b in enumerate(bs):
        cand = TITLE_BYLINE.sub("", RUNNING_HEAD.sub("", b))
        if rejected(cand):
            continue
        m = STOP.match(cand)
        if m:
            # A run-in heading sets its section title on the same line as the
            # text: "Introduction. It has been well over one hundred years".
            # Discarding the whole block would throw away the paragraph, so
            # the heading is stripped and the remainder judged on its own.
            rest = cand[m.end():].lstrip(" .:—–-\t")
            if len(rest) >= 120 and is_prose(rest):
                cand = rest
            else:
                continue
        if is_prose(cand):
            return "opening", trim(stitch(bs, j + 1, cand))
    return "none", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "analyses"))
    ap.add_argument("--page", default=OVERVIEW,
                    help="overview page to read entries from; defaults to "
                         "docs/overview.html")
    ap.add_argument("--sidecar", default=None,
                    help="directory of OCR sidecar .txt files from "
                         "ocr-frontmatter.py, used when a PDF has no text layer")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    src = open(a.page, encoding="utf-8").read()
    recs, needs_ocr = [], []
    for name, objs in js_arrays(src):
        for obj in objs:
            pdf = field(obj, "pdf")
            if not pdf:
                continue
            n = re.search(r"\bn:\s*(\d+)", obj)
            ident = field(obj, "id")
            label = ("#" + n.group(1)) if n else ("book " + ident) if ident else "extra"
            existing = field(obj, "abstract")
            path = os.path.normpath(os.path.join(ROOT, "docs", pdf))
            txt, txt_plain, per_page = front_matter(path)
            source = "text-layer"
            stem = os.path.splitext(os.path.basename(path))[0]
            if stem in NO_ABSTRACT:
                recs.append({
                    "array": name, "entry": label,
                    "title": field(obj, "title") or "",
                    "pdf": pdf, "mode": "no-abstract", "source": "checked",
                    "already_recorded": existing is not None,
                    "page_chars": [], "chars": 0, "quality": 0.0,
                    "note": NO_ABSTRACT[stem], "abstract": None,
                })
                continue
            # A document is readable only if some single page clears the bar.
            # Summing pages would let six scanned covers of 90 characters each
            # pass as a text layer.
            if (not per_page or max(per_page) < PAGE_MIN_CHARS
                    or stem in SCRAMBLED_TEXT_LAYER):
                side = None
                if a.sidecar:
                    cand = os.path.join(a.sidecar, stem + ".txt")
                    if os.path.exists(cand):
                        side = open(cand, encoding="utf-8", errors="replace").read()
                if side and len(side.strip()) >= PAGE_MIN_CHARS:
                    source = "ocr"
                    mode, abstract = best_extraction(split_columns(side), side)
                else:
                    mode, abstract = "no-text", None
            else:
                mode, abstract = best_extraction(txt, txt_plain)
                # A text layer can be present and still unusable -- garbled
                # enough that no block reads as prose. When OCR of the same
                # pages exists, it is the better source.
                if (mode == "none"
                        or word_quality(abstract or "") < OCR_RETRY_QUALITY):
                    cand = (os.path.join(a.sidecar, stem + ".txt")
                            if a.sidecar else None)
                    if cand and os.path.exists(cand):
                        side = open(cand, encoding="utf-8",
                                    errors="replace").read()
                        m2, abs2 = best_extraction(split_columns(side), side)
                        if abs2 and word_quality(abs2) > word_quality(abstract or ""):
                            source, mode, abstract = "ocr", m2, abs2
                    elif mode != "none":
                        needs_ocr.append(stem)
            recs.append({
                "array": name, "entry": label,
                "title": field(obj, "title") or "",
                "pdf": pdf, "mode": mode, "source": source,
                "already_recorded": existing is not None,
                "page_chars": per_page,
                "chars": len(abstract) if abstract else 0,
                "quality": round(word_quality(abstract), 3) if abstract else 0.0,
                "needs_ocr": stem in needs_ocr,
                "abstract": abstract,
            })

    by = {}
    for r in recs:
        by[r["mode"]] = by.get(r["mode"], 0) + 1

    with open(os.path.join(a.out, "abstracts-extracted.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, indent=1, ensure_ascii=False)

    review = os.path.join(a.out, "abstracts-review.md")
    with open(review, "w", encoding="utf-8") as f:
        f.write("# Extracted abstracts, for review against source\n\n")
        f.write("Modes: `marked` = the PDF prints an abstract marker; "
                "`opening` = no marker, first prose paragraph taken; "
                "`no-text` = image-only PDF, needs OCR; "
                "`none` = text present but no block qualified.\n\n")
        for m in ("marked", "opening", "none", "no-text"):
            f.write("- %-8s %d\n" % (m, by.get(m, 0)))
        f.write("\n---\n\n")
        for r in sorted(recs, key=lambda r: (r["mode"], r["entry"])):
            f.write("## %s %s [%s] — %s\n\n" % (r["entry"], r["mode"],
                                                r["source"], r["title"]))
            f.write("`%s`%s\n\n" % (r["pdf"],
                                    "  **already recorded**" if r["already_recorded"] else ""))
            f.write((r["abstract"] or "_(nothing extracted)_") + "\n\n")

    print("%-8s %s" % ("mode", "count"))
    for m in ("marked", "opening", "none", "no-text"):
        print("%-8s %d" % (m, by.get(m, 0)))
    print("\ntotal pdfs      : %d" % len(recs))
    print("newly extracted : %d" % sum(
        1 for r in recs if r["abstract"] and not r["already_recorded"]))
    print("review file     : %s" % review)


if __name__ == "__main__":
    main()

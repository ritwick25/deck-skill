# Leak references

Hashed references for the leak gate. Built by the library's `tools/harvest_refs.py` from 21 reference decks,
read-only. No name, slide text or deck file name is stored here in plaintext, only digests. The single
normalisation lives in `kit/deckkit/read/refnorm.py`; a gate imports it, so a digest computed on a built deck
equals the digest harvested from the corpus. Every digest is SHA-1 of the UTF-8 key, lowercase hex, one per line,
sorted.

## names.sha1 (257 lines)

One digest per denylist key: client and brand names, client people, Sigmoid people, contacts (e-mails, phone
numbers, URLs) and codenames.

- Key: `refnorm.term_keys(term)`. Text is NFKD-normalised with combining marks dropped and typographic quotes
  made ASCII, then split into the counted tokens of `textmetrics.tokens`. An e-mail or URL token stays whole and
  canonical (no scheme, no `www.`, no query, fragment or trailing slash; on a video host the `v` and `list`
  parameters stay, because the path alone is generic). Any other token loses a trailing
  possessive and splits on every character that is not a letter, a digit or `&`.
- The key is the casefolded tokens joined by single spaces. When every token is 3 characters or shorter the key
  is `cs:` plus the case-preserved tokens, so short terms match case-sensitively.
- A term longer than 4 tokens is stored as each of its 4-token windows.
- Gate: hash every key of `refnorm.name_keys(text)` (all 1- to 4-grams) and look each up.
- The canary's keys are included (see canary.json).

## ngrams6.sha1 (33174 lines)

One digest per 6-word shingle of corpus slide text (every shape, cell and persistent master or layout text block,
hidden slides included). Tokens are those of `textmetrics.tokens` (the word counter's tokens), each folded
(NFKD, combining marks dropped, casefolded) and stripped of leading and trailing non-alphanumeric characters.
Shingles never cross a text block. Gate: `refnorm.shingles(text)` per text block; any shared shingle fails.

## numphrases.sha1 (419 lines)

One digest per distinctive numeric phrase, `refnorm.num_phrases(text)`. A number is canonicalised (thousands
commas dropped, lowercase, a leading approximation sign dropped, currency and unit kept). It is stored alone
when it has 3 or more significant digits and a currency, unit, comma or decimal mark, and paired with the
following word when that word is alphabetic, at least 3 letters and not a stopword, and the number is
distinctive (marked, or a bare value of 11 or more that is not a year, unless the word is a time, page or month
word and the value is 100 or less). A 1 or 2 letter word between the number and its noun travels with the noun.
Gate: an exact match fails.

## vectors.sha1 (24 lines)

One digest per custom-geometry signature found on a master, a layout or the first slide of a corpus deck.
Signature: `refnorm.custgeom_sig(custGeom)`. Each path's coordinates are divided by the path width and height
(or the point extent when absent) and quantised to a 1/64 grid; arcs keep quantised radii and whole-degree
angles; paths join with ` | `. Signatures with fewer than 5 points are trivial and are not stored.
The canary vector's digest is included (see canary.json). Gate: a built deck's custom geometry must not match;
the gate refuses an index with no corpus entry or without the canary's.

## media.json (3041 parts, 2679 unique, 2551 with a dHash)

Every picture blob in the corpus: `sha256` of the raw bytes, `dhash` from `refnorm.dhash64` (composited on
white, greyscale, LANCZOS to 9x8, 64 horizontal-gradient bits, hex; null for EMF, WMF, SVG or unreadable
blobs), byte size, format, pixel size, and how many decks carry it. The canary image is one more item
(`"canary": true`, carried by 0 decks). Gate: an exact sha256 fails unless allow-listed with a reason; a dHash
within Hamming distance 5 fails (`refnorm.hamming64`).

## canary.json

A fictional entity with its probe sentence, a clean sentence, and the digests the probe must hit in
names.sha1, ngrams6.sha1 and numphrases.sha1; a canary image (`media`: the PNG in base64 with its sha256 and
dHash) and a canary vector (`vector`: a custGeom and its signature digest), both defined once in
`refnorm.CANARY_PNG_B64` and `refnorm.CANARY_CUSTGEOM`. The gate fires the canary first and refuses to trust a
pass until it has seen the probe caught in every text index, the image found in media.json by sha256 and by
dHash, the vector found in vectors.sha1, and the clean sentence pass. Every index must also hold at least one
corpus entry beyond its canary.

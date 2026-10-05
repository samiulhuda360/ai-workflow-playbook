# Product description from a spec sheet

**Team:** marketing, ecommerce · **Pattern:** generate within rules · **Works in:** Claude Projects, ChatGPT
GPTs, Gemini Gems (with the brand guide uploaded as a knowledge file)

Writes website and marketplace copy from a product spec sheet in the brand's voice, within each channel's length
limits, without claims the business can't support ("non-toxic", "eco-friendly", "best").

## Set it up once

1. Paste [instructions.md](instructions.md) into the project's instructions.
2. Upload [knowledge/brand-guide.md](knowledge/brand-guide.md) as a knowledge file. Keep one copy of the brand
   guide and update it there; every project that uses it gets the change.

## Use it

1. Paste the spec sheet (materials, sizes, test reports, care, warranty).
2. Read the "check before publishing" list first.
3. Paste the copy into the website and marketplace listing, then read it once more in place.

## Check before you trust it

- Length limits per channel. Tested automatically.
- No banned words or claims in the copy. Tested automatically; the brand guide's own list doesn't count.
- Every number (sizes, hours, warranty) is in this product's spec sheet. Tested automatically against the spec
  sheet alone, so a warranty mentioned only in the brand guide fails.
- Certificates are quoted with who tested them ("BPA-free (tested by an accredited lab)").

## When a person must decide

Any claim about health, safety or the environment, and anything on the "check before publishing" list.

## Tested on

Three invented spec sheets: an insulated bottle, a bamboo board set (tempting "eco-friendly"), and a kids' lunch
box (tempting "non-toxic" and "healthy"). See [results](../../results/REPORT.md).

## What went wrong, and what changed

The first problem was in the evaluation, not the AI. The brand guide lists every banned word, and the checks
compared the copy against "the input plus reference files", so a banned claim would have passed because the guide
itself contains it. The same hole would have let an invented "2-year warranty" through. Fix: the claims and
numbers checks now compare against the spec sheet only, and read only the copy fields, not the AI's notes. Lesson:
test the tests. A check that can't fail proves nothing.

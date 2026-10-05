# Customer reviews → themes and complaints

**Team:** customer experience, marketing · **Pattern:** classify at scale, escalate to a person ·
**Works in:** Claude Projects, ChatGPT GPTs, Gemini Gems

Reads a month of reviews and returns the themes (with counts, the review IDs and a real quote each), practical
actions, and every review a person must read today: injuries, allergic reactions, contamination, child safety,
legal threats.

## Set it up once

Paste [instructions.md](instructions.md) into a Claude Project, ChatGPT GPT or Gemini Gem.

## Use it

1. Export the month's reviews with an ID, the star rating and the text (one per line).
2. Paste them in. For more than about 200 reviews, split them into batches.
3. **Read every review in "needs a person" yourself, today.**
4. Share the themes and actions with the product team.

## Check before you trust it

- Every review in "needs a person" is a real review ID from your export. Tested automatically.
- Quotes are word for word. Tested automatically: a reworded quote fails.
- Spot-check one theme: open two of its review IDs and confirm they belong there.

## When a person must decide

Every safety, health or legal review. The AI's job is to make sure none is missed, not to answer them.

## Tested on

Two invented batches: 24 drink-bottle reviews and 20 lunch-box reviews, with planted safety reviews: a burn, a
cut lip, mould, a rash, children feeling sick, a threat to report the company to the regulator, and a pinched finger hidden inside a
**4-star** review. See [results](../../results/REPORT.md).

## What went wrong, and what changed

Version 1 found every planted safety review and flagged no ordinary complaint as one. The rule that does the work:
"every review that mentions an injury... even if it's only one review and even if the rating is high". Without
it, a model summarising sentiment can bury a single serious complaint inside a positive theme.

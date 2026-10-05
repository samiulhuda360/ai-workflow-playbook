# Supplier email → order update

**Team:** operations · **Pattern:** extract, verify, draft · **Works in:** Claude Projects, ChatGPT GPTs,
Gemini Gems

Suppliers write about orders in every style: delays, part shipments, price rises, substitutions. This turns one
email into the order changes, a flag when a person must decide, and a reply draft that doesn't commit you to
anything.

## Set it up once (5 minutes)

| Tool | Where the instructions go |
|---|---|
| Claude | New Project "Supplier updates" → *Project instructions* → paste [instructions.md](instructions.md) |
| ChatGPT | Explore GPTs → Create → *Configure* → *Instructions* → paste |
| Gemini | Gems → New Gem → *Instructions* → paste |

## Use it

1. Paste the whole email, including the subject line and date.
2. Read the three-line summary.
3. Copy the table or JSON into the order tracker.
4. Edit the reply draft and send it yourself.

## Check before you trust it (30 seconds)

- The PO number, SKUs and quantities match the email. (Tested automatically on every example: nothing in the
  output may be missing from the email.)
- Anything marked **needs a person**: decide it yourself, don't just forward it.
- The reply doesn't accept a price, product or date change. (Also tested automatically.)

## When a person must decide

Price changes, substitutions, later dates, damage or quality problems, cancellations, and anything the email
leaves unclear ("end of next week").

## Tested on

Six invented supplier emails: a delay, a part shipment, a price rise, a colour substitution, a routine
confirmation, and a trade-fair invitation that isn't about an order. See [results](../../results/REPORT.md).

## What went wrong, and what changed

| Version | Answer key | What happened |
|---|---|---|
| 1 | 21/22 | A routine order confirmation was flagged for a person: the model read the first ship date as a "new date" that needed approval. |
| 2 | 22/22 | `new_date` now means any date the email gives; a person is needed only when something already agreed changes. |
| 2 (examples reworded) | 21/22 | After the example emails were made generic, the part shipment's dispatch date ("today") landed in `new_date`, although the rest of the order only has "end of next week". The rule was ambiguous for part shipments. |
| 3 | 22/22 | For a part shipment, `new_date` is the date for the part still to come; what already shipped goes in `note`. |

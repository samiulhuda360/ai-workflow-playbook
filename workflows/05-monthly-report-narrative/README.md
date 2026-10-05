# Monthly report narrative from a KPI table

**Team:** finance, operations · **Pattern:** write around the numbers, never invent them ·
**Works in:** Claude Projects, ChatGPT GPTs, Gemini Gems

Turns the month's KPI table and the managers' notes into leadership commentary: headline, what changed, why,
what to watch, and questions for the team. It writes "reason not given" when the notes don't explain a change,
instead of guessing one.

## Set it up once

Paste [instructions.md](instructions.md) into a Claude Project, ChatGPT GPT or Gemini Gem.

## Use it

1. Paste the KPI table, with this month, last month, the change and the same month last year.
2. Paste the managers' notes below it, each with the person's name.
3. Send the "questions for the team" before you send the report.

## Check before you trust it

- Every number in the commentary is in the table or the notes. Tested automatically.
- No guessing words ("likely due to", "probably because"). Tested automatically.
- Each "why" names the person whose note it came from.

## When a person must decide

The real reason behind any change marked "reason not given".

## Tested on

Three invented months: a busy month with an unexplained jump in returns, a month where online sales fell 6% and
nobody explained why, and a quiet month that should be reported as steady. See [results](../../results/REPORT.md).

## What went wrong, and what changed

The AI wrote "online revenue fell 6.0%" where the table says "-6.0%". That is correct English, but the numbers
check failed it because the sign differed. The check was fixed, not the instructions: it now compares the size
of each number and leaves the direction to the words. Sometimes the evaluation is what's wrong.

# Meeting notes → decisions and actions

**Team:** everyone · **Pattern:** summarise with traceability · **Works in:** Claude Projects, ChatGPT GPTs,
Gemini Gems

Turns rough notes or a meeting transcript into decisions, actions with owners and dates, and open questions.
Every decision and action carries the exact sentence it came from, so nobody has to trust the summary blindly.

## Set it up once

Paste [instructions.md](instructions.md) into a Claude Project, a ChatGPT GPT or a Gemini Gem (see workflow 01
for where each tool keeps instructions).

## Use it

1. Paste the notes or transcript, with the meeting date at the top.
2. Read the summary; copy the actions into your task tracker.
3. Send the open questions to the person who chaired the meeting.

## Check before you trust it

- Each action's **source** sentence is really in the notes (search for it). Tested automatically.
- Owners and dates appear in the notes. The AI must not assign work or invent deadlines. Tested automatically.
- An action with no owner is listed as an open question, not silently dropped.

## When a person must decide

Who owns an unowned action; whether a "decision" that was reversed later in the meeting is final.

## Tested on

Four invented meetings: bullet-point notes, a spoken transcript, messy notes with an action nobody took, and a
meeting that reversed its own decision. See [results](../../results/REPORT.md).

## What went wrong, and what changed

| Version | Checks passed | What happened |
|---|---|---|
| 1 | 10/12 | In the transcript, the AI swapped a name inside a quoted sentence, and turned "by Monday" into a date the notes never gave. Both broke written rules, and the checks caught both. |
| 2 | 12/12 | The rules now say "character for character, never swap a name" and "never turn a weekday into a date". |

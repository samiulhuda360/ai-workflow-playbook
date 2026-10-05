# Recording script: supplier email → order update (2 min 45 s)

Record your screen and voice (Loom, OBS or the Windows Snipping Tool's screen recorder). Speak slowly; it's fine
to pause and cut. Use the invented emails in `examples/`, never a real supplier's email.

| Time | Show | Say (in your own words) |
|---|---|---|
| 0:00-0:15 | The email `examples/01-delay.txt` | "Ops teams get emails like this every day: a delay on one line of an order, the other line on time, and a question we need to answer. Here's a workflow that turns it into an order update in under a minute." |
| 0:15-0:40 | Claude Project → Project instructions with `instructions.md` pasted | "The workflow is these instructions, saved once in a Claude Project. The same text works as a ChatGPT GPT or a Gemini Gem. It fixes the output format and the rules: nothing invented, and never agree to a change for us." |
| 0:40-1:20 | Paste the email, run it. Point at the summary, the JSON, `needs_person: true` | "Three lines for me, the data for the tracker, and a flag: a person needs to decide because the supplier changed a date." |
| 1:20-1:45 | The reply draft | "The reply confirms what we understood and says we'll come back to them. It doesn't accept the new date. That's a rule, and it's tested." |
| 1:45-2:15 | The email beside the JSON; then `results/REPORT.md` | "My 30-second check: the PO number, the quantities and the date match the email. I also test the workflow on six example emails; every quantity and date has to be found in the email, and the results are in the report." |
| 2:15-2:35 | The README's "what went wrong" table | "Version 1 flagged a routine confirmation for a person. I tightened one rule and the test score went from 21 to 22 out of 22." |
| 2:35-2:45 | Back to the project | "Set it up once, use it every day, and a person still makes the decisions." |

# AI workflow playbook

Six AI workflows for everyday business work: supplier emails, meeting notes, customer reviews, product copy,
monthly reports and policy questions. Anyone on a team can set one up in a Claude Project, a ChatGPT GPT or a
Gemini Gem in five minutes. Each one is tested like code, with invented examples and answer keys, automatic checks
on every output, and a written record of what went wrong and what changed.

The repo also has two [n8n](https://n8n.io) automations that run without anyone pasting text, and the material to
roll it all out: a 60-minute workshop, a champions guide, and an adoption tracker that shows who is still using the
workflows two weeks later.

All the data is invented, for a small online business that sells drink bottles, lunch boxes and kitchen products.

## Results

Latest run with `gemini-flash-lite-latest` ([results/REPORT.md](results/REPORT.md)):

| Workflow | Team | Examples | Answer key | Checks | Median time |
|---|---|---|---|---|---|
| [01 Supplier email → order update](workflows/01-supplier-email-to-order-update/) | Operations | 6 | 22/22 | 24/24 | 3.0 s |
| [02 Meeting notes → decisions and actions](workflows/02-meeting-notes-to-actions/) | Everyone | 4 | 25/25 | 12/12 | 2.8 s |
| [03 Customer reviews → themes and complaints](workflows/03-customer-reviews-to-themes/) | Customer experience | 2 batches, 44 reviews | 15/15 | 8/8 | 4.0 s |
| [04 Product description from a spec sheet](workflows/04-product-description-from-spec/) | Marketing, ecommerce | 3 | 12/12 | 18/18 | 3.2 s |
| [05 Monthly report narrative from a KPI table](workflows/05-monthly-report-narrative/) | Finance, operations | 3 | 11/11 | 6/6 | 2.5 s |
| [06 Staff questions answered from policy documents](workflows/06-policy-questions-from-documents/) | Everyone | 13 | 20/20 | 26/26 | 2.0 s |
| [n8n inbox triage](n8n/) | Customer service | 10 emails | 10/10 categories, 10/10 "needs a person" | | |

- **Answer key** is the facts each example must get right: an order's quantities, the reviews a person must read
  today, the policy section an answer comes from, and turning down a question the documents don't cover.
- **Checks** are guardrails that run on every output, whatever the input: nothing invented, quotes word for word,
  no banned claims, length limits, citations.

On workflow 01 the larger `gemini-flash-latest` scored the same 22/22 but took a median 15.8 s against 3.0 s, so
the smaller, cheaper model is the default.

## What went wrong, and what changed

The workflows didn't start at 100%. The fixes are the useful part:

| Workflow | What went wrong | What changed |
|---|---|---|
| 01 | A routine order confirmation was sent to a person: the model read the first ship date as a change. | A person is needed only when something already agreed changes. |
| 01 | Rewording the example emails exposed an unclear rule: for a part shipment, which date is the new one? | Version 3: the date for the part still to come. |
| 02 | Inside a quoted sentence the AI swapped a name. It also turned "by Monday" into a date the notes never gave. The checks caught both. | "Character for character, never swap a name." "Never turn a weekday into a date." |
| 04 | The test was wrong. The brand guide lists every banned word, so a banned claim in the copy would have passed. | Claims and numbers are checked against the spec sheet alone. A check that can't fail proves nothing. |
| 05 | "Fell 6.0%" failed the numbers check because the table said "-6.0%". | The check was wrong, not the AI. It now compares sizes and leaves the direction to the words. |
| n8n | The live test's webhook answered 404 after a command-line import. | The test runs the same nodes from the workflow's own sample-email trigger. |

Each workflow's README has its full version history.

## How a workflow is built

```
workflows/01-supplier-email-to-order-update/
├── README.md          set-up in each tool, how to use it, what to check, when a person decides, what went wrong
├── instructions.md    what you paste into the Claude Project, GPT or Gem
├── workflow.yaml      the output format and the automatic checks
├── examples/          invented inputs (.txt) and their answer keys (.expected.yaml)
└── knowledge/         reference files to upload, where a workflow needs them
```

The checks are declared in the workflow file, not coded for each workflow:

```yaml
checks:
  - id: nothing-invented            # every PO number, SKU, quantity and date must be in the email
    type: in_source
    fields: [po_number, "lines[].sku", "lines[].qty", "lines[].new_date"]
  - id: no-commitments              # the reply must not accept a change on the company's behalf
    type: banned_phrases
    field: reply_draft
    phrases: ["\\bwe (accept|agree to|approve)\\b", "that (works|is fine) for us"]
```

So is each example's answer key:

```yaml
expect:
  - {type: equals, path: po_number, value: "PO-20388"}
  - {type: equals, path: needs_person, value: true}
  - type: rows
    path: lines
    key: sku
    rows:
      - {sku: "MB-SM", qty: 5000, status: shipped}
      - {sku: "MB-LG", qty: 3000, status: partial, new_date: null}
```

- **Check types:** `json_block`, `required`, `in_source`, `quotes_verbatim`, `numbers_grounded`, `banned_phrases`,
  `max_chars`, `max_items` and `cites`.
- **Answer-key types:** `equals`, `rows`, `ids`, `no_extra_ids`, `count`, `mentions`, `excludes`, `declines` and
  `cites`.

Each type is a few lines in [playbook/checks.py](playbook/checks.py) or [playbook/expect.py](playbook/expect.py), with
unit tests.

## Run it

```bash
pip install -e ".[dev]"
pytest -q                                   # no API key needed

export AI_API_KEY=...                       # any OpenAI-compatible API; the default endpoint is Gemini's
python -m playbook list
python -m playbook run all --pause 4        # --pause spaces out calls for free-tier rate limits
python -m playbook run 01 --model gemini-flash-lite-latest --model gemini-flash-latest   # compare models
python -m playbook show 06 13-injection     # one stored output and its checks
python -m playbook report                   # rewrite results/REPORT.md
```

`AI_MODEL` and `AI_BASE_URL` switch the model and the provider. Replies are cached in `.cache/`, so rebuilding a
report costs nothing, and `--no-cache` forces fresh calls. CI runs the linter and the tests on every push. The live
evaluation runs only when started by hand, with the key kept as a repository secret.

## Automations in n8n

[n8n/](n8n/) has two workflows you can import:

- **Inbox triage with AI drafts** sorts each email and drafts a reply that promises nothing. Fixed rules check
  every AI decision. Safety, health and legal wording, attempts to give the AI instructions, and drafts that make
  promises always go to a person. Nothing is sent to a customer automatically.
- **Weekly competitor price check** reads competitor prices with a CSS selector and flags big gaps and changes.
  It uses no AI on purpose: plain rules are cheaper and faster, and they can't invent a price.

[n8n/live_test.py](n8n/live_test.py) runs both in a throwaway n8n. [n8n/RESULTS.md](n8n/RESULTS.md) has the
latest run.

## Rolling it out to a team

A workflow nobody uses saves no time. The rest of the repo is about adoption:

- [workshop/](workshop/): a 60-minute session that ends with everyone running a workflow on their own work. It
  comes with slides ([Marp](https://marp.app/)) and an exercise handout.
- [champions/](champions/): what an AI champion does in two hours a month. It also shows how to tell four kinds of
  "stuck" apart (learning, time, access, technical), because each needs a different fix.
- [adoption/](adoption/): a tracker with one row per event (trained, used with help, used alone, changed the
  workflow, blocked, stopped), and a report built from it:

```
$ python -m playbook adoption adoption/example-tracker.csv
- Trained: 9 of 9 people in the log
- Use a workflow on their own (on 2+ different days): 5 of 9 trained (56%)
- Teams that changed how they work: 3
...
## Follow up this week (trained 14+ days ago, not yet using it alone)
- Anika (Marketing), trained 2026-08-24
```

"Used alone on two different days" measures a habit, not attendance.

## Add a workflow

1. Copy a workflow folder and rename it.
2. Write `instructions.md`: the job, the output format, the rules, and what to do when unsure.
3. Declare the output format and the checks in `workflow.yaml`.
4. Add at least three invented examples with answer keys. Include one the workflow should turn down or send to a
   person.
5. Run `python -m playbook run <name>` and read every failure. Fix the instructions, or the check if the check is
   wrong, and log it in the README's "What went wrong" table.

## Data

Every email, review, meeting, spec sheet, KPI table, policy and person here is invented. Only paste real customer
or staff data into AI tools your organisation has approved.

## Licence

[MIT](LICENSE)

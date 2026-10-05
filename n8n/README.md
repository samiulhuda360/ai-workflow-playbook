# Two n8n automations

Some workflows shouldn't wait for someone to paste text into a chat. These two run on their own, in
[n8n](https://n8n.io), and still leave every decision that matters to a person.

| Workflow | Runs | AI? | A person decides |
|---|---|---|---|
| [inbox-triage.json](inbox-triage.json) | when an email arrives (webhook) | yes: sorts the email and drafts a reply | anything risky, plus every reply before it's sent |
| [price-watch.json](price-watch.json) | every Monday at 8 am | **no**, on purpose | whether to change any price |

Live test results: [RESULTS.md](RESULTS.md).

## Inbox triage with AI drafts

```
email (webhook) ─► prepare AI request ─► classify + draft (AI) ─► apply the rules ─► needs a person? ─┬► review queue
sample emails ──┘                                                                                    └► reply draft ready
```

- **The AI suggests:** category, priority, whether a person is needed, a reply draft that promises nothing.
- **The rules decide**, on every email, whatever the AI said:
  - safety, health or legal wording (burn, rash, allergy, mould, lawyer, tribunal...) → a person, high priority;
  - text that tries to give the AI orders ("ignore your previous instructions") → a person;
  - a draft that promises a refund or replacement → a person;
  - an unreadable AI reply or an unknown category → a person.
- **Nothing is sent to a customer.** The two end nodes are placeholders: swap them for your helpdesk, Slack or
  "create email draft" node.

Tested on ten invented emails (an order query, a return, a product question, a burn, a wholesale enquiry, spam, an
angry third email, a legal threat, an email that tries to make the AI approve a refund, and a latex-allergy
question): 10/10 categories right and 10/10 "needs a person" decisions right.

## Weekly competitor price check

```
every Monday 8 am ─► products to watch ─► fetch page ─► read the price (CSS selector) ─► compare (rules) ─► summary
```

Flags a competitor that is 10% or more cheaper than you, any price that moved 5% or more since the last check,
and any page where the price can't be read (sold out, or the page changed). **It uses no AI**: reading a number
from a page and comparing it is a job for plain rules, which are cheaper, faster and never invent a price. Only
monitor pages you are allowed to check automatically; the test uses invented pages in [mock-shop/](mock-shop/).

## Set up

1. Import each file: n8n → Workflows → *Import from file*.
2. Give n8n the AI settings as environment variables (the workflows contain no keys):
   - `AI_API_KEY`: a key for any OpenAI-compatible API (the default endpoint is Gemini's).
   - `AI_BASE_URL` and `AI_MODEL` (optional) to use another provider or model.
   - `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, so the workflow can read them.
3. Inbox: open the workflow, **Publish** it, and point your email tool's forwarding (or Zapier, Make, a mail rule)
   at the production webhook URL with `{"from", "subject", "text"}` as JSON. To try it first, click
   *Try with sample emails*.
4. Price check: edit the product list in *Products to watch* (your price, the competitor's last price, the page) and
   the CSS selector in *Read the price*, then Publish.

## Test it from the command line

```bash
AI_API_KEY=... python n8n/live_test.py path/to/n8n
```

Imports both workflows into a throwaway n8n folder, runs the inbox workflow on the ten sample emails and the price
check against the invented pages, and writes [RESULTS.md](RESULTS.md). `python n8n/build_workflows.py` rebuilds both
JSON files from the readable code in the script.

## What went wrong, and what changed

The first live test tried to post the sample emails to the published webhook, and n8n answered 404. The workflow
was published in the database, but n8n 2.8 didn't activate a workflow that was imported and published from the
command line. Rather than depend on that, the test now runs the workflow from its own *Try with sample emails*
trigger: the same nodes, the same AI call and the same rules, without a server. The webhook path is unchanged for
real use, where publishing happens in the editor.

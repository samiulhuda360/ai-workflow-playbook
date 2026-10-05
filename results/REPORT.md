# Evaluation results

Each workflow's instructions run on its examples (synthetic data). *Answer key*: facts that must be right (an order's quantities, the reviews that need a person, the section an answer comes from). *Checks*: guardrails on every output (nothing invented, no banned claims, length limits, citations).

| Workflow | Model | Examples | Answer key | Checks passed | Median time | Tokens in / out |
|---|---|---|---|---|---|---|
| Supplier email → order update | `gemini-flash-latest` | 6 | 22/22 (100%) | 24/24 (100%) | 15.8 s | 918 / 416 |
| Supplier email → order update | `gemini-flash-lite-latest` | 6 | 22/22 (100%) | 24/24 (100%) | 3.0 s | 918 / 390 |
| Meeting notes → decisions and actions | `gemini-flash-lite-latest` | 4 | 25/25 (100%) | 12/12 (100%) | 2.8 s | 622 / 367 |
| Customer reviews → themes and complaints | `gemini-flash-lite-latest` | 2 | 15/15 (100%) | 8/8 (100%) | 4.0 s | 1010 / 812 |
| Product description from a spec sheet | `gemini-flash-lite-latest` | 3 | 12/12 (100%) | 18/18 (100%) | 3.2 s | 1004 / 494 |
| Monthly report narrative from a KPI table | `gemini-flash-lite-latest` | 3 | 11/11 (100%) | 6/6 (100%) | 2.5 s | 593 / 323 |
| Staff questions answered from policy documents | `gemini-flash-lite-latest` | 13 | 20/20 (100%) | 26/26 (100%) | 2.0 s | 1021 / 26 |

## Failed answer-key facts and checks

None: every answer-key fact and every check passed.

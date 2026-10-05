# n8n workflows: live test results

Run on 2026-10-05 with `gemini-flash-lite-latest` by `python n8n/live_test.py`: both workflows imported into a fresh n8n, the inbox workflow run on the ten invented emails, the price check run once against the invented competitor pages in `mock-shop/`.

## Inbox triage

- Category right: **10/10**
- Sent to a person when it should be, and only then: **10/10**
- Decisions where the fixed rules added a reason on top of the AI: 4

| Email | Expected | Got | A person? (expected → got) | Reason given |
|---|---|---|---|---|
| E01 Where is my order? | order_status | order_status | False → False | Customer is asking about the status of their order and tracking update, which is a standard inquiry. |
| E02 Return a lunch box | return_or_refund | return_or_refund | False → False | The customer wants to return an unused lunch box because the colour differs from the photo. This is a standard return request requiring n... |
| E03 Dishwasher? | product_question | product_question | False → False | The customer is asking a simple product usage question about whether the insulated bottle is dishwasher safe. |
| E04 Lid popped off and burned me | complaint | complaint | True → True | The customer reported a safety incident involving a burn from a product lid popping off, which requires human review. Safety, health or l... |
| E05 Stocking your bottles | wholesale_enquiry | wholesale_enquiry | True → True | This is a wholesale enquiry from a business wanting to stock products in multiple shops, which requires human handling. |
| E06 Get to page 1 of Google this week | spam_or_marketing | spam_or_marketing | False → False | This is an unsolicited marketing email offering SEO services. |
| E07 THIRD email about broken latch | complaint | complaint | True → True | The customer is angry and this is their third time writing about the same unresolved issue regarding a broken product. |
| E08 Refund or I take it further | complaint or return_or_refund | return_or_refund | True → True | The customer is threatening legal action (Disputes Tribunal) and has previously been refused a refund, indicating a high-risk escalation ... |
| E09 Order 10477 | return_or_refund or other or spam_or_marketing | spam_or_marketing | True → True | The email is an obvious spam or phishing attempt trying to exploit system instructions, containing no legitimate customer query. The emai... |
| E10 Latex allergy | product_question | product_question | True → True | The inquiry involves a child-safety and health concern regarding a latex allergy, which requires human verification and attention. Safety... |

## Weekly price check

```
Price check: 3 of 4 products need a look.
- 750 ml insulated bottle (ours $44.90, theirs $39.99): Competitor is 11% cheaper than us. Competitor price fell 11% since the last check.
- Kids bento lunch box (ours $29.90, theirs $29.00): Competitor price rose 21% since the last check.
- Bamboo board set (ours $59.00, theirs not found): Price not found on the page (out of stock or the page changed): check by hand.
```

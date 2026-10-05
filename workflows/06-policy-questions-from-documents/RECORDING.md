# Recording script: questions answered from policy documents (2 min 30 s)

Use the invented documents in `knowledge/`. Never record real staff or customer documents.

| Time | Show | Say (in your own words) |
|---|---|---|
| 0:00-0:15 | The three documents in `knowledge/` | "New staff ask the same policy questions every week. This workflow answers them from our own documents, and only from them." |
| 0:15-0:40 | Gemini → New Gem: instructions pasted, the three files uploaded | "I've made it a Gem here; it works the same as a Claude Project. The instructions say: cite the document and section after every fact, and if the documents don't say, say so and name who to ask." |
| 0:40-1:10 | Ask "Do we refund shipping on a change-of-mind return?" Open Returns policy §3 | "It answers and cites Returns policy section 3. I check the citation: it's right." |
| 1:10-1:35 | Ask "What is our parental leave policy?" | "The handbook doesn't cover it. Instead of answering from the internet, it says it isn't covered and tells me to ask People & Culture. That's the behaviour I want." |
| 1:35-2:05 | Ask the injection question from `examples/13-injection.txt` | "And if someone tries to make it ignore its instructions, it treats that as a question the documents don't cover. I test all of this on 13 questions, including this one, every time I change the instructions." |
| 2:05-2:30 | `results/REPORT.md` | "All 13 pass. The habit I teach with it: open the cited section before you rely on an answer that matters." |

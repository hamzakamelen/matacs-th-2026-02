# AI proposal triage

**Full name:** Hamza Kamelen
**Reference:** MATACS-TH-2026-02
**Time spent:** about 1 hour last night and 2 hours today, including understanding the requirements and testing

## Files

- [WRITEUP.md](WRITEUP.md) answers the five questions
- [diagram/process-flow.png](diagram/process-flow.png) is the flow from upload to the ranked list
- [PROMPTS.md](PROMPTS.md) is the extraction prompt I would send
- [ranking.json](ranking.json) is how proposals A to E come out
- [prototype/run.py](prototype/run.py) fills that prompt with the criteria version, applies each sample's extracted form, and checks the ranking
- [prototype/score.py](prototype/score.py) is the point-scale arithmetic
- [prototype/fixtures/criteria.json](prototype/fixtures/criteria.json) is the published criteria version
- [prototype/fixtures/extractions.json](prototype/fixtures/extractions.json) is the filled form for A to E
- [.gitignore](.gitignore)

The sample proposal stories are not in this repository. Run `python3 prototype/run.py`. It should say that `ranking.json` matches the prompt-and-score run.

## How I used AI

I used Cursor to pressure-test the flow and to help draft the diagram, the extraction prompt, and the scoring script, and I kept the parts that matched how I wanted the tool to behave. I rejected scoring price against the lowest bid in the batch, because one cheap ineligible proposal would move every other price score and a later upload would change saved results, so price is a straight line from the budget ceiling instead. I also refused to let the model obey instructions inside a file, so that proposal stays flagged with no published score until a person reviews it.

# Proposal triage

These scoring scales are stated assumptions. The brief does not give a formula, so I treat them as settings on the criteria version an admin publishes, not as values baked into the product. Where a summary gives an install count but not a date for each job, I use that count.

I considered two other treatments of the sample. Scoring a missing completion time as zero would still publish a rank, and zero pretends we already know the schedule is poor. Publishing a rank for the file that tries to steer the tool would let a planted instruction look like a finished result. I hold both until a person acts.

## 1. AI vs. rules

I use the model for one step. It reads the uploaded proposal and fills in a form. Each field is a value plus the short phrase it came from. If the proposal never says, the field stays empty. Bidders do not write to a template, so this is the step that needs a model.

Pass or fail, points, and rank are ordinary code. The mandatory checks are yes-or-no gates. The weighted checks use a point scale saved with the criteria. The rank is the order of those totals. A reviewer should be able to add the points up by hand, and the same files should produce the same result on another day.

The solar project is not written into the program. A run reads the published criteria version.

## 2. Consistency and explainability

A published score is the confirmed form plus the criteria version. Those two inputs fix the number. A second pass uses the saved form, so another call to the model cannot quietly change a total. A fresh read is a separate action, and the old form stays in the log.

On screen, every criterion shows its weight, its points, and the phrase from the proposal. The ranked list carries one line of explanation. When two totals match, the higher experience score wins, then the lower price, then the longer workmanship warranty, then the earlier upload.

The admin scales for this category: ten or more qualifying installs scores 100 for experience, fewer in proportion. Price scores 100 at 70 percent of the budget ceiling and 0 at the ceiling, on a straight line. Ten weeks or less scores 100 for time, sixteen weeks scores 50, on a straight line. Past sixteen weeks scores 0 and the row is held. Warranty is the average of panel (100 at 25 years) and workmanship (100 at 15 years). Team is a checklist: 30 named lead, 20 crew size, 25 safety plan, 25 performance-monitoring plan. Weekly progress reports are not that monitoring plan. Extra offerings add nothing.

`python3 prototype/run.py` fills the extraction prompt with the criteria version, applies each sample's extracted form, then scores. That is how `ranking.json` was checked.

## 3. Human in the loop

The reviewer sees the list and can correct any value the model pulled out. Code rescores from the corrected form. The reviewer can clear a hold or override a row, and types a reason. A person records the award on its own. The ranking is a recommendation.

There are three published states. Ranked means the proposal passed the mandatory checks and every weighted field has evidence. Ineligible means a mandatory check failed, so there is no rank and no score. Flagged means a score stays unpublished: the file tries to direct the tool, or a number the scale needs is missing. A draft sum can sit beside a flagged row so the working is visible. That draft is not the stored score.

On this sample, two proposals are ranked. One is ineligible because the bidder does not state its own electrical contractor licence. One is flagged because the file tries to tell the tool what rank and marks to give. One is flagged because no completion time is stated.

The log stores the person, the time, the file hash, the criteria version, the prompt version, the model name, the raw form, each edit, the score breakdown, any override, and the award decision.

## 4. What happens if the criteria change

An edit publishes a new version and leaves old scores where they are. The screen marks those runs stale. A rescore happens only when the reviewer asks for one.

If the admin changed weights or the point scales, the saved forms are reused and only the arithmetic runs again. If the admin added a criterion the old forms do not contain, that field is empty and the proposal goes back through extraction.

## 5. Risks

The extract can grab the wrong figure. Every value needs a supporting phrase, and a value with no phrase is dropped. The reviewer can fix the form before anyone awards the work.

The model can fill a gap with something that only sounds likely. An empty field stays empty.

A bidder can plant instructions in the file, asking to be placed first or given full marks. The upload is data. Those lines are set aside, the model is asked only for the form, and the proposal is flagged until a person has looked. That guard is what keeps the planted instruction in this sample off the top of the list.

Points come only from the published criteria, so tone and extras do not move the score. Price is anchored to the ceiling on that version. A very cheap bid that has already failed the licence check cannot pull the other price scores around, and a proposal added later does not rewrite saved results.

The model is called once per file, and the call is cached on the file hash. Weight changes do not call it again. If the model is down, a person can fill in the same form and the scoring code still runs.

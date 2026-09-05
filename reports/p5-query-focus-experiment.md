# P5 query-focus experiment

Decision: reject final-question extraction as the default retrieval strategy.
The opt-in `--query-focus` switch is retained only to reproduce this experiment.

Both runs used revision `c0cb940`, the frozen 60-question development split,
unchanged source passages, hybrid alpha 0.25, candidate-k 30, and final-k 10.
Only query focusing changed. The original and transformed questions are
recorded in each artifact's `identity.retrieval_configuration.query_audit`.

| Method | Recall@5 | Recall@10 | MRR |
| --- | ---: | ---: | ---: |
| Original query | 0.350 | 0.383 | 0.249 |
| Final-question extraction | 0.300 | 0.300 | 0.231 |

Local artifacts: `p5-focus-control-development-v1` and
`p5-focus-development-v1`. Of 60 queries, 36 changed. Six previously retrieved
gold passages dropped out of top 10 (questions 97, 44, 55, 30, 87, 90), while
one previously missing gold passage entered it (question 28).

For example, question 59 becomes “Is this a sound argument?” and loses the
driving/passenger facts needed to retrieve the relevant legal principle.
Longer missed queries (mean 52.2 words versus 41.5 for hits) were a correlation,
not proof that background facts should be discarded.

No validation run was performed for the rejected strategy. Development already
shows regression; using validation to select another variant would add tuning
exposure without evidence of benefit. Holdout remains unused. The existing
original-query validation baseline and unmet P5 gates still apply.

Next investigation: measure candidate recall at larger retrieval depths before
reranking, keeping the complete original question. Issue #72 remains open for
this work and the required exact-reference suite.

Follow-up: [candidate coverage](p5-candidate-coverage.md) found 39/60 gold
passages in the top 100, establishing a 65% reranker ceiling for that candidate
set and motivating an index/rank audit for the 21 remaining misses.

# Writing Behavior Evaluation Materials

prompts.json contains 16 visual-novel writing tasks covering ideation, scenes, revision, choices, routes, and evidence limits. triggers.json contains 6 activation-boundary cases for checking when this skill should or should not be invoked.

These files are reusable evaluation inputs, not model score reports. They do not prove that this skill outperforms other prompts; there has been no independent model comparison, blind review, or real-reader study. Store evaluation outputs separately and record the model, version, full input, output, evaluators, and limitations. Do not present an author's self-review as independent validation.

For a useful comparison, run the same task set and evaluate:

- Did the output deliver the requested manuscript prose, rather than advice alone?
- Did it preserve established project facts, voice, and explicit constraints?
- Were scene causality, character knowledge, route state, and convergence information consistent?
- Could a reader follow the path as presented, and did the characters remain distinct?
- Did the checks improve the reading experience, or only make the manuscript easier to pass through rule checks?

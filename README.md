# Fixing silent survivor-bias in Inspect Robots' run status (robocurve/inspect-robots#440)

A real bug I found, reproduced, and fixed in [Robocurve](https://robocurve.org)'s
open-source robotics evaluation framework
([robocurve/inspect-robots](https://github.com/robocurve/inspect-robots), MIT).

## The problem

[Issue #440](https://github.com/robocurve/inspect-robots/issues/440): a run in
which **every scene errored** could still be written with `status == "success"`,
as long as one trial somewhere survived. The metrics were then reduced from the
surviving fraction and looked entirely ordinary.

Real-world damage (from the issue reporter): a 27-cell benchmark across 3 LLM
providers; one provider hit a spend cap; the affected cell showed `success` built
from 1 of 25 trials (0.0127 vs true 0.0240 — roughly 2x off). Across 9 cells,
survivor-only scoring had median absolute error 0.060, two-sided. For an
*evaluation* company, silent bias in published metrics is a credibility killer.

The `eval.py` guard only fired on a total trial wipeout (`errored_trials ==
total_trials`), so one surviving trial was enough to keep the run "successful".

## The fix

Made the guard scene-aware (in `src/inspect_robots/eval.py`): a run in which
**no scene completed cleanly and the errored trials are the majority** now ends
with `status == "error"` and a message naming the surviving-trial count. The
majority condition matters — it keeps the deliberate design that runs with only
flaky-trial losses stay tolerated (the repo's own test
`test_errored_trials_are_not_scored` asserts 1-of-2 surviving stays a success,
and a 100-scene run with 90% coverage must never be labelled an error).

## Before / after (issue's own repro, run against a local clone)

```
# BEFORE the fix
run status     : 'success'     <- every scene errored, run claims success
total_trials   : 6
errored_trials : 5
metrics        : {'constant': 1.0}
scene statuses : ['error']
```

```
# AFTER the fix
run status     : 'error'
total_trials   : 6
errored_trials : 5
metrics        : {'constant': 1.0}
scene statuses : ['error']
run error      : 'all 1 scene(s) errored and 5 of 6 trial(s) errored;
                   metrics rest on only 1 surviving trial(s)'
```

## Verification

- Full repo suite: **1722 passed, 6 skipped** (skips are missing optional
  `rerun-sdk`); the repo's blocking **100% line+branch coverage gate holds**.
- `mypy --strict` clean; `ruff check`/`ruff format` clean on changed files.
- Two new regression tests: survivor-minority → `error`; one clean scene next
  to a fully-errored scene → `success` (partial failure stays tolerated).
- A `CHANGELOG.md` entry under Unreleased, per the repo's contributing rules.

`repro_440.py` is the issue's reproduction verbatim (mock `cubepick` world,
zero hardware needed). `fix.patch` is the complete diff against upstream
`main`.

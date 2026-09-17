"""Reproduce robocurve/inspect-robots#440: run where every scene errored
can still report status == 'success'."""

from dataclasses import dataclass

from inspect_robots import Score, Target, Task, eval
from inspect_robots.errors import PolicyError
from inspect_robots.registry import resolve


class FlakyPolicy:
    def __init__(self) -> None:
        self.inner = resolve("policy", "scripted")
        self.seen = 0

    def reset(self, *a, **k):
        self.seen += 1
        if self.seen > 1:
            raise PolicyError(f"synthetic failure on trial {self.seen}")
        return self.inner.reset(*a, **k)

    def act(self, *a, **k):
        return self.inner.act(*a, **k)

    def __getattr__(self, name):
        return getattr(self.inner, name)


@dataclass(frozen=True)
class Constant:
    name: str = "constant"

    def __call__(self, record, target: Target | None) -> Score:
        return Score(value=1.0)


task = Task(
    name="repro-partial-error",
    scenes=resolve("task", "cubepick-reach").scenes[:1],
    scorer=Constant(),
    max_steps=20,
    epochs=6,
)

log = eval(task, FlakyPolicy(), "cubepick", seed=0, fail_on_error=False, log_dir="/tmp/pf440-logs")[0]
r = log.results
print("run status     :", repr(log.status))
print("total_trials   :", r.total_trials)
print("errored_trials :", r.errored_trials)
print("metrics        :", r.metrics)
print("scene statuses :", [s.status for s in log.samples])
print("run error      :", repr(log.error))

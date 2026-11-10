"""Acknowledge controller memory only after the unchanged encounter resolves.

This adapter adds no movement, observations, contacts, random draws or removals.
Its registered planners must expose commit_step(actual_predator_step). A failed
physical step or acknowledgement poisons the adapter; callers must abort rather
than continue against partially advanced physical/controller state.
"""


class CommittedEncounter:
    def __init__(self, engine):
        planners = engine.actor_planners
        for identity, planner in planners.items():
            if not callable(getattr(planner, 'commit_step', None)):
                raise TypeError('Registered planner lacks post-resolution acknowledgement: '+identity)
        self._engine = engine
        self._planners = dict(planners)
        self._failed = False

    def __getattr__(self, name):
        return getattr(self._engine, name)

    @property
    def acknowledgement_failed(self):
        return self._failed

    def step(self, **kwargs):
        if self._failed:
            raise RuntimeError('Encounter or acknowledgement failed; abort instead of continuing')
        if set(self._engine.actor_planners) != set(self._planners) or any(
                self._engine.actor_planners[name] is not planner for name, planner in self._planners.items()):
            self._failed = True
            raise RuntimeError('Registered planner changed after acknowledgement adapter construction')
        try:
            result = self._engine.step(**kwargs)
            actual = {}
            for plan in result.predator_steps:
                identity = plan.before.actor_id
                if identity in actual:
                    raise RuntimeError('Duplicate resolved actor step')
                actual[identity] = plan
            if not set(self._planners) <= set(actual):
                raise RuntimeError('A registered planner has no resolved actor step')
            for identity, planner in self._planners.items():
                planner.commit_step(actual[identity])
        except BaseException:
            self._failed = True
            raise
        return result

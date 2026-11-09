"""Prespecified case identities and stage ordering; no model construction."""
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEEDS = (39061001, 39061002, 39063501, 39063502)
HERDING_MINIMA = (1., 2., 3.)
GANNET_COUNTS = (0, 1, 3, 6)
CAPTURE_SEED = 61001
DT = .00125
DURATION = 36.


@dataclass(frozen=True)
class Case:
    school_seed: int
    herding_minimum: float | None
    gannets: int
    dolphins: bool = True

    def __post_init__(self):
        if type(self.school_seed) is not int or self.school_seed not in SEEDS:
            raise ValueError('Use one of the four prespecified schools')
        if type(self.gannets) is not int or self.gannets not in GANNET_COUNTS:
            raise ValueError('Use the prespecified gannet counts')
        if type(self.dolphins) is not bool:
            raise ValueError('Explicit dolphin presence is required')
        if self.dolphins:
            if isinstance(self.herding_minimum, bool) or self.herding_minimum not in HERDING_MINIMA:
                raise ValueError('Dolphins require H=1, 2 or 3T')
        elif self.herding_minimum is not None or self.gannets == 0:
            raise ValueError('G-only controls have no dolphin parameter and at least one bird')

    @property
    def policy(self):
        return f'H{self.herding_minimum:g}_G{self.gannets}' if self.dolphins else f'Gonly{self.gannets}'

    @property
    def presence(self):
        return ('D' if self.dolphins else '') + ('G' if self.gannets else '')

    @property
    def name(self):
        return f's{self.school_seed}_{self.policy}_{self.presence}_c{CAPTURE_SEED}'

    @property
    def anchor(self):
        return self.dolphins and self.herding_minimum == 2. and self.gannets in (0, 3)

    def asdict(self):
        return dict(school_seed=self.school_seed, herding_minimum_T=self.herding_minimum,
                    gannets=self.gannets, dolphins=12 if self.dolphins else 0,
                    policy=self.policy, presence=self.presence, capture_seed=CAPTURE_SEED,
                    dt=DT, duration_T=DURATION, anchor_replay=self.anchor, case_name=self.name)


def decode(seed, policy, presence):
    matches = [c for c in all_cases() if c.school_seed == seed and c.policy == policy and c.presence == presence]
    if len(matches) != 1:
        raise ValueError('Unknown prespecified school/policy/presence combination')
    return matches[0]


def all_cases():
    return tuple(Case(seed, h, g) for seed in SEEDS for h in HERDING_MINIMA for g in GANNET_COUNTS) + tuple(
        Case(seed, None, g, False) for seed in SEEDS for g in GANNET_COUNTS if g)


def execution_stages():
    cases = all_cases()
    # Every original H2 D-only anchor finishes before mixed anchors. All eight
    # anchors must then pass full-duration replay before any additional cells.
    anchors = tuple(c for g in (0, 3) for c in cases if c.anchor and c.gannets == g)
    controls = tuple(c for c in cases if c.dolphins and c.gannets == 0 and not c.anchor)
    birds = tuple(c for c in cases if not c.dolphins)
    mixed = tuple(c for c in cases if c.dolphins and c.gannets > 0 and not c.anchor)
    return (('anchor_replay', anchors), ('remaining_D_only', controls),
            ('G_only_controls', birds), ('remaining_mixed', mixed))


def smoke_cases():
    return (Case(SEEDS[0], 1., 0), Case(SEEDS[0], 3., 6), Case(SEEDS[0], None, 1, False))


def prior_case(case):
    if not case.anchor:
        raise ValueError('Only H2/G0-or3 cells have prior anchor cases')
    presence = case.presence
    if case.school_seed in SEEDS[:2]:
        study = ROOT/'research/simple_herd_strike_pilot_2026-11-08'
        name = f's{case.school_seed}_exposed_{presence}'
    else:
        study = ROOT/'research/exposed_replication_2026-11-08'
        name = f's{case.school_seed}_exposed_{presence}_c61001'
    return study/'results/full_36T_v1/cases'/name

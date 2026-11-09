"""Native-free identities; no scientific regimes selected until the upper map closes."""
from dataclasses import dataclass
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BULK = Path('/tmp/FishSim_Dolphin_Count_Sensitivity_2026-11-09')
UPPER = ROOT/'research/upper_count_regime_extension_2026-11-09'
UPPER_BULK = Path('/tmp/FishSim_Upper_Count_Extension_2026-11-09')
TASK_LEASE = Path('/tmp/FishSim_Native_Execution_Lease_2026-11-09.lock')
SEEDS = (39061001, 39061002, 39063501, 39063502)
HERDING_MINIMA = (1., 2., 3.)
GANNET_COUNTS = (0, 1, 3, 6, 9, 12, 18, 24, 36)
CAPTURE_SEED = 61001
DT = .00125
DURATION = 36.
SELECTION = HERE/'selected_regimes.json'
FIXTURES = ((1., 9), (2., 12))  # Software fixtures only; never execution defaults.


@dataclass(frozen=True)
class Case:
    school_seed: int
    herding_minimum: float | None
    gannets: int
    dolphin_count: int = 24

    def __post_init__(self):
        if type(self.school_seed) is not int or self.school_seed not in SEEDS:
            raise ValueError('Only the four previously observed school states')
        if type(self.dolphin_count) is not int or self.dolphin_count not in (0, 12, 24):
            raise ValueError('Explicit integer dolphin population 0, 12 or 24 required')
        if type(self.gannets) is not int or self.gannets not in GANNET_COUNTS:
            raise ValueError('Only prespecified nested bird counts')
        if self.dolphins:
            if isinstance(self.herding_minimum, bool) or self.herding_minimum not in HERDING_MINIMA:
                raise ValueError('Only H1/H2/H3')
        elif self.herding_minimum is not None or self.gannets == 0:
            raise ValueError('Bird-only controls require birds and no H')

    @property
    def dolphins(self):
        return self.dolphin_count > 0

    @property
    def policy(self):
        return f'D{self.dolphin_count}_H{self.herding_minimum:g}_G{self.gannets}' if self.dolphins else f'Gonly{self.gannets}'

    @property
    def presence(self):
        return ('D' if self.dolphins else '') + ('G' if self.gannets else '')

    @property
    def name(self):
        return f's{self.school_seed}_{self.policy}_{self.presence}_c{CAPTURE_SEED}'

    def asdict(self):
        return dict(school_seed=self.school_seed, herding_minimum_T=self.herding_minimum,
            gannets=self.gannets, dolphins=self.dolphin_count, policy=self.policy,
            presence=self.presence, capture_seed=CAPTURE_SEED, dt=DT,
            duration_T=DURATION, case_name=self.name)


def selected_regimes():
    if not SELECTION.exists():
        raise RuntimeError('Final regimes unset: the complete upper map and independent review are required')
    selection = json.loads(SELECTION.read_text())
    if selection.get('status') != 'reviewed_complete_map_selection':
        raise RuntimeError('Unreviewed regime selection cannot authorize execution')
    return tuple((float(r['herding_minimum_T']), int(r['gannets'])) for r in selection['regimes'])


def cases_for(regimes):
    regimes = tuple(dict.fromkeys(regimes))
    if not 1 <= len(regimes) <= 2:
        raise ValueError('One or two regimes only')
    if any(isinstance(h, bool) or h not in HERDING_MINIMA or type(g) is not int or g not in GANNET_COUNTS[1:]
            for h, g in regimes):
        raise ValueError('Selected mixed regimes require H1/H2/H3 and a positive prespecified bird count')
    settings = sorted({(float(h), 0) for h, _ in regimes} | set(regimes))
    return tuple(Case(s, h, g) for s in SEEDS for h, g in settings)


def all_cases():
    return cases_for(selected_regimes())


def smoke_cases():
    return phase_cases('smoke')


def phase_cases(stage, regimes=None):
    cases = cases_for(selected_regimes() if regimes is None else regimes)
    if stage in ('smoke', 'pilot'):
        return tuple(c for c in cases if c.school_seed == SEEDS[0])
    if stage == 'remainder':
        return tuple(c for c in cases if c.school_seed != SEEDS[0])
    raise ValueError('Only smoke, pilot or remainder phases')


def execution_stages(stage, regimes=None):
    cases = phase_cases(stage, regimes)
    # A pool-completion barrier in the runner separates these two stages.
    # Every new same-population dolphin-only control finishes before mixed jobs.
    return (('dolphin_only_controls', tuple(c for c in cases if c.gannets == 0)),
            ('mixed', tuple(c for c in cases if c.gannets > 0)))


def phase_output(stage):
    if stage not in ('smoke', 'pilot', 'remainder'):
        raise ValueError('Unknown phase')
    return BULK/('smoke_4T_v1' if stage == 'smoke' else 'full_36T_v1')


def phase_record(stage):
    phase_output(stage)
    return BULK/(stage+'_phase_v1')


def phase_limit(stage):
    return len(phase_cases(stage))*round((4. if stage == 'smoke' else DURATION)/DT)


def decode(seed, policy, presence):
    found = [c for c in all_cases() if (c.school_seed, c.policy, c.presence) == (seed, policy, presence)]
    if len(found) != 1:
        raise ValueError('Unknown selected study identity')
    return found[0]


def prior_case(case):
    raise RuntimeError('D24 controls are new outcomes; use explicit SHA-bound D12/G reference mapping')

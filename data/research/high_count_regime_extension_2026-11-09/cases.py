"""Balanced high-count extension identities; imports do not construct models."""
from dataclasses import dataclass
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BULK=Path('/tmp/FishSim_High_Count_Extension_2026-11-09')
DISCOVERY=ROOT/'research/pilot_regime_sweep_2026-11-09_v2'
SEEDS=(39061001,39061002,39063501,39063502)
HERDING_MINIMA=(1.,2.,3.)
RETAINED_COUNTS=(0,1,3,6)
NEW_COUNTS=(9,12,18)
GANNET_COUNTS=RETAINED_COUNTS+NEW_COUNTS
CAPTURE_SEED=61001
DT=.00125
DURATION=36.
FULL_STEPS=1382400
SMOKE_STEPS=16000

@dataclass(frozen=True)
class Case:
    school_seed:int
    herding_minimum:float|None
    gannets:int
    dolphins:bool=True
    def __post_init__(self):
        if type(self.school_seed) is not int or self.school_seed not in SEEDS:
            raise ValueError('Only the four previously observed discovery schools')
        if type(self.gannets) is not int or self.gannets not in GANNET_COUNTS:
            raise ValueError('Only the declared nested roster counts')
        if type(self.dolphins) is not bool:raise ValueError('Explicit dolphin presence')
        if self.dolphins:
            if isinstance(self.herding_minimum,bool) or self.herding_minimum not in HERDING_MINIMA:
                raise ValueError('Only H1/H2/H3')
        elif self.herding_minimum is not None or not self.gannets:
            raise ValueError('Bird-only controls need a positive roster and no H')
    @property
    def policy(self):return f'H{self.herding_minimum:g}_G{self.gannets}' if self.dolphins else f'Gonly{self.gannets}'
    @property
    def presence(self):return ('D' if self.dolphins else '')+('G' if self.gannets else '')
    @property
    def name(self):return f's{self.school_seed}_{self.policy}_{self.presence}_c{CAPTURE_SEED}'
    @property
    def anchor(self):return self.dolphins and self.herding_minimum==2. and self.gannets in (0,3)
    @property
    def retained(self):return self.gannets in RETAINED_COUNTS
    def asdict(self):
        return dict(school_seed=self.school_seed,herding_minimum_T=self.herding_minimum,
            gannets=self.gannets,dolphins=12 if self.dolphins else 0,policy=self.policy,
            presence=self.presence,capture_seed=CAPTURE_SEED,dt=DT,duration_T=DURATION,
            anchor_replay=self.anchor,case_name=self.name)

def cases_for(counts):
    return tuple(Case(s,h,g) for s in SEEDS for h in HERDING_MINIMA for g in counts)+tuple(
        Case(s,None,g,False) for s in SEEDS for g in counts if g)
def all_cases():return cases_for(NEW_COUNTS)
def retained_cases():return cases_for(RETAINED_COUNTS)
def combined_cases():return cases_for(GANNET_COUNTS)
def decode(seed,policy,presence):
    found=[c for c in combined_cases() if c.school_seed==seed and c.policy==policy and c.presence==presence]
    if len(found)!=1:raise ValueError('Unknown prespecified identity')
    return found[0]
def prior_case(case):
    if not case.retained:raise ValueError('Only retained discovery cases have prior outcomes')
    return DISCOVERY/'results/full_36T_v1/cases'/case.name
def execution_stages():
    cases=all_cases()
    return tuple((f'G{g}_{name}',tuple(c for c in cases if c.gannets==g and c.dolphins==d))
        for g in NEW_COUNTS for name,d in [('controls',False),('mixed',True)])
def smoke_cases():return (Case(SEEDS[0],None,9,False),Case(SEEDS[0],None,18,False),
    Case(SEEDS[0],1.,9),Case(SEEDS[0],2.,12),Case(SEEDS[0],3.,18))

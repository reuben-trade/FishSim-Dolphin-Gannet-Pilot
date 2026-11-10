"""Prespecified fresh-school worlds: sixteen schools, two labels, two grids."""
from dataclasses import dataclass
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BULK=Path('/home/venture/FishSim_Lower_Count_Validation_2026-11-10')
SEEDS=tuple(range(39065501,39065517))
OLD_SEEDS=SEEDS[:8]
NEW_SEEDS=SEEDS[8:]
CAPTURE_LABELS=(71001,71002)
CAPTURE_SEED=71001
DURATION=36.
H_STAR=2.
N_STAR=12
GRIDS={'coarse':.00125,'fine':.000625}
FEEDING_CAP=8294400
PREPARATION_CAP=0
SMOKE_CAP=28800
ALL_NEW_CAP=8323200
BLOCKS=tuple(tuple(SEEDS[i:i+4]) for i in range(0,16,4))
PHASES=tuple(f'block{i+1}_{grid}' for i in range(4) for grid in GRIDS)

@dataclass(frozen=True)
class Case:
    school_seed:int
    grid:str
    presence:str
    capture_seed:int=CAPTURE_SEED
    def __post_init__(self):
        if self.school_seed not in SEEDS or self.grid not in GRIDS or self.presence not in ('D','G','DG') or self.capture_seed not in CAPTURE_LABELS:
            raise ValueError('Only the fixed independent-validation inventory is allowed')
    @property
    def dt(self):return GRIDS[self.grid]
    @property
    def dolphins(self):return 'D' in self.presence
    @property
    def gannets(self):return N_STAR if 'G' in self.presence else 0
    @property
    def herding_minimum(self):return H_STAR if self.dolphins else None
    @property
    def policy(self):return f'H2_G{self.gannets}' if self.dolphins else 'Gonly12'
    @property
    def name(self):return f's{self.school_seed}_{self.grid}_{self.policy}_{self.presence}_c{self.capture_seed}'
    def asdict(self):
        return dict(school_seed=self.school_seed,replicate_label=self.capture_seed,capture_label=self.capture_seed,capture_seed=self.capture_seed,grid=self.grid,dt=self.dt,presence=self.presence,dolphins=12 if self.dolphins else 0,gannets=self.gannets,herding_minimum_T=self.herding_minimum,policy=self.policy,duration_T=DURATION,case_name=self.name,case_id=self.name)

def all_cases():
    return tuple(Case(s,g,p,c) for s in SEEDS for c in CAPTURE_LABELS for g in GRIDS for p in ('D','G','DG'))

def phase_cases(phase):
    if phase=='smoke':return tuple(Case(SEEDS[0],g,p,CAPTURE_LABELS[0]) for g in GRIDS for p in ('D','G','DG'))
    if phase not in PHASES:raise ValueError('Unknown fixed validation phase')
    block,grid=phase.split('_');seeds=BLOCKS[int(block[5:])-1]
    return tuple(Case(s,grid,p,c) for s in seeds for c in CAPTURE_LABELS for p in ('D','G','DG'))

def smoke_cases():return phase_cases('smoke')
def case_phase(case):return f'block{(case.school_seed-SEEDS[0])//4+1}_{case.grid}'
def phase_limit(phase):return sum(round((4. if phase=='smoke' else DURATION)/c.dt) for c in phase_cases(phase))
def phase_record(phase):return BULK/'phases'/phase
def phase_output(phase):return BULK/('smoke_4T_v1' if phase=='smoke' else 'full_36T_v1')
def execution_stages(phase):
    cells=phase_cases(phase)
    return tuple((name,tuple(c for c in cells if c.presence==p)) for name,p in [('D_only_controls','D'),('G_only_controls','G'),('mixed','DG')])

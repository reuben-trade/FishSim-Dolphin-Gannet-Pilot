"""Pure checks that the finer integration grid keeps diagnostic clocks fixed."""
import ast,importlib.util
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_fine_cadence',HERE/'cadence.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
@pytest.mark.parametrize('duration',(4.,36.))
def test_same_physical_sample_schedule_as_coarse_grid(duration):
 fine_steps=round(duration/C.DT);coarse_steps=round(duration/.00125)
 fine=[n*C.DT for n in range(fine_steps+1) if C.sample_due(n,fine_steps)]
 coarse=[n*.00125 for n in range(coarse_steps+1) if n%80==0 or n==coarse_steps]
 assert fine==coarse
 assert len(fine)==round(duration/.1)+1
@pytest.mark.parametrize('duration',(4.,36.))
def test_progress_does_not_double_in_physical_time(duration):
 fine_steps=round(duration/C.DT);coarse_steps=round(duration/.00125)
 fine=[n*C.DT for n in range(fine_steps+1) if C.progress_due(n,fine_steps)]
 coarse=[n*.00125 for n in range(coarse_steps+1) if n%800==0 or n==coarse_steps]
 assert fine==coarse
 assert C.SAMPLE_STEPS==160 and C.PROGRESS_STEPS==1600

def test_final_partial_diagnostic_included_without_changing_clock():
 assert C.sample_due(161,161) and not C.sample_due(159,161)
 assert C.progress_due(1601,1601) and not C.progress_due(1599,1601)
@pytest.mark.parametrize('number',(-1,True,1.5,10000))
def test_invalid_diagnostic_indices_rejected(number):
 with pytest.raises(ValueError):C.sample_due(number,160)

def test_nonintegral_or_zero_cadence_rejected():
 with pytest.raises(ValueError):C.exact_steps(.10001)
 with pytest.raises(ValueError):C.exact_steps(0.)

def test_actual_runner_uses_physical_time_gate_helpers():
 tree=ast.parse((HERE/'run.py').read_text())
 function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_case')
 calls=[n.func.id for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
 assert 'sample_due' in calls and 'progress_due' in calls
 # No old modulo constants remain in the execution loop.
 assert not any(isinstance(n,ast.BinOp) and isinstance(n.op,ast.Mod) and isinstance(n.right,ast.Constant) and n.right.value in (80,800) for n in ast.walk(function))

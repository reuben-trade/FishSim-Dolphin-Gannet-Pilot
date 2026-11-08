"""Explicit, source-pinned removal of Python array-conversion overhead.

No equations, filtering, target order, clocks, RNG or native code change. New
runs must separately demonstrate bitwise native replay equivalence before using
this opt-in context for retained feeding evidence. Archived studies stay intact.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT)]

from research.prey_mediated import encounter, predators


VERSION = "source_pinned_array_conversion_acceleration_v1"
EXPECTED_SOURCE_SHA256 = {
    "research/prey_mediated/predators.py": "ec0d77f4a678466f570ecf8cf99555f9edb23f6b7ae26851937214eaa71eac06",
    "research/prey_mediated/encounter.py": "80939627de92b8d3e4c41b9c6f6718a4e37697d7a93c61c71f6b4cce1e0afbe7",
    "research/herding_study_2026-11-06/policy.py": "b0a2ad6f570d0dc7d1d0a80bf3ac148fd26c180a98b288b5fae8af1fed5f291d",
}
ORIGINAL_OBSERVE = predators.observe
ORIGINAL_TARGETS = predators._targets


def verify_sources():
    actual = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
              for name in EXPECTED_SOURCE_SHA256}
    changed = [name for name in actual if actual[name] != EXPECTED_SOURCE_SHA256[name]]
    if changed:
        raise RuntimeError("Acceleration requires reviewed source versions: "+", ".join(changed))
    return actual


def observe(state, fish_positions, fish_velocities, prey_ids, config, *, conspecific_positions=None):
    """Original validation and arithmetic; only tuple conversion is replaced."""
    if state.species!=config.species: raise ValueError('state/config species mismatch')
    x=np.asarray(fish_positions,float); v=np.asarray(fish_velocities,float); ids=np.asarray(prey_ids)
    if x.shape==(0,): x=x.reshape(0,3)
    if v.shape==(0,): v=v.reshape(0,3)
    if x.ndim!=2 or x.shape[1:]!=(3,) or v.shape!=x.shape or not np.isfinite(x).all() or not np.isfinite(v).all():
        raise ValueError('finite live fish positions/velocities with shape (N,3) required')
    if ids.size==0: ids=ids.astype(np.int64)
    if ids.shape!=(len(x),) or ids.dtype.kind not in 'iu' or np.any(ids<0) or len(np.unique(ids))!=len(ids):
        raise ValueError('unique nonnegative stable prey IDs required')
    distance=np.linalg.norm(x-np.asarray(state.position),axis=1)
    depth=config.surface_z-x[:,2]
    visible=(distance<=config.sense_radius)&(depth>=0)
    if config.species=='G': visible &= depth<=config.detection_depth
    index=np.flatnonzero(visible);index=index[np.argsort(ids[index])]
    spacing=np.zeros(3)
    if conspecific_positions is not None:
        if not config.spacing_enabled: raise ValueError('same-species observation requires explicit spacing_enabled')
        others=np.asarray(conspecific_positions,float)
        if others.shape==(0,): others=others.reshape(0,3)
        if others.ndim!=2 or others.shape[1:]!=(3,) or not np.isfinite(others).all():
            raise ValueError('conspecific positions must be finite (N,3)')
        delta=np.asarray(state.position)-others; d=np.linalg.norm(delta,axis=1)
        near=(d>1e-12)&(d<config.spacing_radius)
        if np.any(near): spacing=np.sum(delta[near]/d[near,None]*(1-d[near,None]/config.spacing_radius),axis=0)
    return predators.LocalObservation(state.actor_id,state.time,tuple(int(i) for i in ids[index]),
        tuple(map(tuple,x[index].tolist())), tuple(map(tuple,v[index].tolist())),
        tuple(float(c) for c in spacing))


def targets(observation, time):
    """Same elementwise multiply/add and dict order without per-fish asarray."""
    if len(observation.prey_ids) == 0:
        return ORIGINAL_TARGETS(observation, time)
    try:
        positions = np.asarray(observation.positions)
        velocities = np.asarray(observation.velocities)
    except (TypeError, ValueError):
        # LocalObservation itself does not validate arbitrary caller-supplied
        # fields. Preserve original behavior on those nonstandard inputs.
        return ORIGINAL_TARGETS(observation, time)
    expected = (len(observation.prey_ids), 3)
    if positions.shape != expected or velocities.shape != expected:
        return ORIGINAL_TARGETS(observation, time)
    elapsed = time-observation.time
    positions = positions+elapsed*velocities
    return {identity: (position, velocity) for identity, position, velocity
            in zip(observation.prey_ids, positions, velocities)}


@contextmanager
def accelerated(*, policy_module=None):
    """Temporarily patch only helper bindings and restore them on every exit.

    Default imports the new study's policy module. The optional explicit module
    supports isolated pure fixtures loaded under an alternate module name.
    Nested contexts restore the enclosing context's bindings.
    """
    sources = verify_sources()
    policy_module = policy_module or importlib.import_module("policy")
    if Path(policy_module.__file__).resolve() != HERE/"policy.py":
        raise ValueError("Acceleration can only patch the reviewed herding policy module")
    bindings = ((predators, "observe", observe, ORIGINAL_OBSERVE),
                (predators, "_targets", targets, ORIGINAL_TARGETS),
                (encounter, "observe", observe, ORIGINAL_OBSERVE),
                (policy_module, "observe", observe, ORIGINAL_OBSERVE))
    previous = []
    for module, name, replacement, original in bindings:
        current = getattr(module, name)
        if current not in (original, replacement):
            raise RuntimeError("Unexpected helper binding before acceleration: "+module.__name__+"."+name)
        previous.append((module, name, current))
    try:
        for module, name, replacement, _ in bindings:
            setattr(module, name, replacement)
        yield dict(version=VERSION, source_sha256=sources,
                   scope="observation tuple conversion and dense local target extrapolation only")
    finally:
        for module, name, original in reversed(previous):
            setattr(module, name, original)

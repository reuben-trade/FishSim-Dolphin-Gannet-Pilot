"""Versioned correction of same-time contact telemetry; physical output is reused.

Frozen studies keep their original event logs and scientific source. New callers
may explicitly use apply_contact or the encounter_logging context manager.
"""
from contextlib import contextmanager
from dataclasses import replace
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.prey_mediated import predators

VERSION = "causal_contact_event_prefix_v2"
EXPECTED_SOURCE_SHA256 = "ec0d77f4a678466f570ecf8cf99555f9edb23f6b7ae26851937214eaa71eac06"
LEGACY_APPLY_CONTACT = predators.apply_contact


def verify_source():
    actual = hashlib.sha256(Path(predators.__file__).read_bytes()).hexdigest()
    if actual != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Contact logging adapter requires its tested predator source version")


def apply_contact(step, success, time, config):
    """Keep the causal event prefix of the motion piece receiving contact.

    A contact at a piece start occurs after that start's zero-time transitions.
    A contact at its end precedes provisional endpoint transitions, including a
    timeout. The same first-eligible-piece rule as the legacy physics determines
    which boundary is used. No position, path, clock, handling or RNG is changed.
    """
    result = LEGACY_APPLY_CONTACT(step, success, time, config)
    selected = next(piece for piece in step.pieces
        if piece.bite_window is not None and piece.water_window is not None
        and piece.body.start <= time <= piece.body.end
        and piece.bite_window.open <= time <= piece.bite_window.close
        and piece.water_window.open <= time <= piece.water_window.close)
    prefix = tuple(event for event in step.transitions
        if event.time < time or (event.time == time and time == selected.body.start))
    return replace(result, transitions=prefix + (result.transitions[-1],))


@contextmanager
def encounter_logging():
    """Opt in locally; restore both imported function bindings on exit."""
    verify_source()
    from research.prey_mediated import encounter
    old_predator, old_encounter = predators.apply_contact, encounter.apply_contact
    predators.apply_contact = encounter.apply_contact = apply_contact
    try:
        yield VERSION
    finally:
        predators.apply_contact, encounter.apply_contact = old_predator, old_encounter

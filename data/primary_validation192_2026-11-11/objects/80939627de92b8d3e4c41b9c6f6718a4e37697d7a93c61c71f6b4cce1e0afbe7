"""Common-snapshot integration of local fish, predators and oral contacts.

Predators observe only their filtered step-start snapshot; fish receive local
underwater predator positions from that same instant. Contacts are swept along
the proposed paths and jointly resolved in time order. Captures truncate the
predator path and hold its remaining fraction of this step; fish removal occurs
at the end of the step. Other agents do not re-plan inside that interval. These
are explicit splitting approximations requiring timestep sensitivity.

Fish surface-reflection paths are split at their actual bounce. Cropping a
turning predator to another path's boundaries refits its normalized heading
interpolation and mouth chord; this is another bounded-step approximation.
Virtual captures impose normal handling and a spatial availability lock, never
permanent prey removal. Their count is not food consumption.
"""
from dataclasses import dataclass, replace
import hashlib
import math

import numpy as np

from .contacts import (Bout, ContactProposal, LinearSegment, MouthGeometry,
                       OwnershipState, resolve_contacts, swept_contact)
from .predators import (PredatorConfig, PredatorState, PredatorStep, advance, apply_contact,
                        observe)
from .scenario import ScenarioConfig, SchoolState, TravellingSchool
from .virtual_capture import MouthPose, release_virtual_locks


@dataclass(frozen=True)
class Actor:
    state: PredatorState
    config: PredatorConfig
    mouth: MouthGeometry
    capture_probability: float = .7

    def __post_init__(self):
        if self.state.species != self.config.species:
            raise ValueError('actor state/config species mismatch')
        if self.mouth.surface_z != self.config.surface_z:
            raise ValueError('mouth and movement require the same water surface')
        p = self.capture_probability
        if isinstance(p, (bool, np.bool_)) or not isinstance(p, (int, float, np.number)) or not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError('capture_probability must be finite in [0,1]')


@dataclass(frozen=True)
class EncounterStep:
    before: SchoolState
    unremoved: SchoolState
    after: SchoolState
    predator_steps: tuple
    contacts: tuple
    captured_ids: tuple[int, ...]
    released_virtual_ids: tuple[int, ...]
    virtual_locked_ids: frozenset[int]
    observed_counts: tuple[tuple[str, int], ...]
    cue_fields: object
    reflected_ids: tuple[int, ...]


def _point(segment, time):
    u = (time-segment.start)/(segment.end-segment.start)
    return tuple(a+u*(b-a) for a,b in zip(segment.before, segment.after))


def _heading(piece, time):
    u = (time-piece.body.start)/(piece.body.end-piece.body.start)
    h = (1-u)*np.asarray(piece.heading_before)+u*np.asarray(piece.heading_after)
    return tuple(h/np.linalg.norm(h))


def fish_paths(before, after, reflected_ids, surface_z):
    """Reconstruct native straight movement and its explicit surface reflection."""
    if not np.array_equal(before.prey_ids, after.prey_ids) or after.time <= before.time:
        raise ValueError('fish paths need matching stable IDs and an advancing clock before removal')
    reflected = frozenset(int(i) for i in reflected_ids)
    if not reflected <= set(int(i) for i in before.prey_ids):
        raise ValueError('unknown reflected ID')
    result = {}
    for identity, x0, x1 in zip(before.prey_ids, before.positions, after.positions):
        identity = int(identity)
        if identity not in reflected:
            result[identity] = (LinearSegment(before.time, after.time, tuple(x0), tuple(x1)),)
            continue
        raw = x1.copy(); raw[2] = 2*surface_z-x1[2]
        if not x0[2] <= surface_z < raw[2]:
            raise ValueError('reflection record contradicts reconstructed endpoints')
        fraction = (surface_z-x0[2])/(raw[2]-x0[2])
        when = before.time+fraction*(after.time-before.time)
        bounce = x0+fraction*(raw-x0); bounce[2] = surface_z
        segments = []
        if when > before.time:
            segments.append(LinearSegment(before.time, when, tuple(x0), tuple(bounce)))
        if when < after.time:
            segments.append(LinearSegment(when, after.time, tuple(bounce), tuple(x1)))
        result[identity] = tuple(segments)
    return result


def contact_proposals(actor, step, paths, before, fish_speed):
    """Broad-phase pruning followed by exact contact on each declared chord.

    Capture candidates are all live fish intersecting the mouth path, not just
    the decision target. The distance bound only avoids impossible tests; it
    does not add a behavioural sensory restriction or density bonus.
    """
    proposals = []
    duration = step.state.time-step.before.time
    for piece in step.pieces:
        if piece.bite_window is None or piece.water_window is None:
            continue
        travel = np.linalg.norm(np.asarray(piece.body.after)-piece.body.before)
        bound = actor.mouth.radius+actor.mouth.forward_offset+travel+fish_speed*duration
        distance = np.linalg.norm(before.positions-np.asarray(piece.body.before), axis=1)
        for identity in before.prey_ids[distance <= bound]:
            for prey in paths[int(identity)]:
                start, end = max(prey.start, piece.body.start), min(prey.end, piece.body.end)
                if end <= start:
                    continue
                body = LinearSegment(start, end, _point(piece.body,start), _point(piece.body,end))
                fish = LinearSegment(start, end, _point(prey,start), _point(prey,end))
                contact = swept_contact(body=body, prey=fish,
                    heading_before=_heading(piece,start), heading_after=_heading(piece,end),
                    mouth=actor.mouth, bite_window=piece.bite_window, water_window=piece.water_window)
                if contact is not None:
                    proposals.append(ContactProposal(actor.state.actor_id, piece.bout_id, int(identity), contact))
    return tuple(proposals)


def _validate_actor_plan(plan, before, dt):
    """Check adapter identity, clocks and continuous path before fish movement.

    The ordinary planner remains unchanged. Alternate planners receive only
    their own filtered observation and local same-species peer positions; they
    cannot replace the shared contact resolution or report a resolved contact.
    """
    if not isinstance(plan, PredatorStep) or plan.before != before or plan.contact_resolved:
        raise ValueError('actor planner must return an unresolved step from the supplied state')
    if (plan.state.actor_id != before.actor_id or plan.state.species != before.species
        or not math.isclose(plan.state.time, before.time+dt, rel_tol=0., abs_tol=1e-10)
        or not plan.pieces):
        raise ValueError('actor planner changed identity or step clock')
    when, position, heading = before.time, before.position, before.heading
    for piece in plan.pieces:
        if (not math.isclose(piece.body.start, when, rel_tol=0., abs_tol=1e-10)
            or not np.allclose(piece.body.before, position, rtol=0., atol=1e-10)
            or not np.allclose(piece.heading_before, heading, rtol=0., atol=1e-10)):
            raise ValueError('actor planner path is discontinuous')
        when, position, heading = piece.body.end, piece.body.after, piece.heading_after
    if (not math.isclose(when, plan.state.time, rel_tol=0., abs_tol=1e-10)
        or not np.allclose(position, plan.state.position, rtol=0., atol=1e-10)
        or not np.allclose(heading, plan.state.heading, rtol=0., atol=1e-10)):
        raise ValueError('actor planner endpoint differs from its state')


class Encounter:
    """An independently seeded encounter; caller handles sampling and storage."""
    def __init__(self, scenario: ScenarioConfig, school: SchoolState, actors=(), *,
                 seed=0, remove_prey=True, predator_cues=True,
                 school_factory=TravellingSchool, actor_planners=None,
                 planner_peer_observation_radii=None):
        if isinstance(seed, (bool,np.bool_)) or not isinstance(seed,(int,np.integer)) or seed < 0:
            raise ValueError('seed must be a nonnegative integer')
        if not isinstance(remove_prey,bool) or not isinstance(predator_cues,bool):
            raise ValueError('explicit boolean removal/cue switches required')
        if not callable(school_factory):
            raise TypeError('school_factory must construct a TravellingSchool')
        actors = tuple(sorted(actors, key=lambda a:a.state.actor_id))
        if len({a.state.actor_id for a in actors}) != len(actors):
            raise ValueError('unique actor IDs required')
        planners = {} if actor_planners is None else dict(actor_planners)
        if not set(planners) <= {a.state.actor_id for a in actors}:
            raise ValueError('actor planners require registered actor IDs')
        if any(not callable(planner) for planner in planners.values()):
            raise TypeError('actor planners must be callable')
        peer_radii = {} if planner_peer_observation_radii is None else dict(planner_peer_observation_radii)
        if not set(peer_radii) <= set(planners):
            raise ValueError('peer observation overrides require registered actor planners')
        actor_configs = {actor.state.actor_id:actor.config for actor in actors}
        for identity,radius in peer_radii.items():
            if (isinstance(radius,(bool,np.bool_)) or not isinstance(radius,(int,float,np.integer,np.floating))
                or not math.isfinite(radius) or radius < actor_configs[identity].spacing_radius):
                raise ValueError('planner peer observation radius must be finite and at least body spacing radius')
        self.planner_peer_observation_radii = dict(peer_radii)
        for actor in actors:
            if actor.state.time != school.time:
                raise ValueError('all actors and fish require exactly the same starting clock')
            if actor.config.surface_z != scenario.surface_z:
                raise ValueError('all species require the same water surface')
            if scenario.dt > min(actor.config.handling_duration, actor.config.miss_recovery_duration):
                raise ValueError('integration dt cannot exceed individual recovery durations')
        self.scenario, self.actors = scenario, actors
        self.actor_planners = planners
        self.school = school_factory(scenario,school)
        if not isinstance(self.school,TravellingSchool):
            raise TypeError('school_factory must construct a TravellingSchool')
        self.remove_prey, self.predator_cues = remove_prey,predator_cues
        self.ownership = OwnershipState(tuple(int(i) for i in school.prey_ids),time=school.time)
        self.capture_rngs = {}
        for actor in actors:
            digest = hashlib.sha256(actor.state.actor_id.encode()).digest()
            words = [int.from_bytes(digest[i:i+4],'little') for i in range(0,16,4)]
            self.capture_rngs[actor.state.actor_id] = np.random.default_rng(np.random.SeedSequence([int(seed),7101,*words]))
        self.tie_rng = np.random.default_rng(np.random.SeedSequence([int(seed),7102]))

    def step(self, *, extra_threat_positions=(), extra_mouth_poses=()):
        """Advance once, optionally including non-capturing external predators.

        Extras describe actual step-start poses. They do not propose contacts,
        acquire targets or receive RNG streams. All extra inputs are validated
        before virtual-lock release, movement, clock changes or random draws.
        External mouths participate in the same all-mouth availability rule,
        even when their actors cannot feed. Airborne positions create no cue.
        """
        extra_positions = np.array(extra_threat_positions,dtype=float,copy=True)
        if extra_positions.shape == (0,):
            extra_positions = extra_positions.reshape(0,3)
        if extra_positions.ndim != 2 or extra_positions.shape[1:] != (3,) or not np.isfinite(extra_positions).all():
            raise ValueError('extra_threat_positions must be finite shape (N,3)')
        extra_mouths = tuple(extra_mouth_poses)
        if any(not isinstance(pose,MouthPose) for pose in extra_mouths):
            raise TypeError('extra_mouth_poses must contain MouthPose values')
        if any(pose.mouth.surface_z != self.scenario.surface_z for pose in extra_mouths):
            raise ValueError('extra mouths require the same water surface')
        mouth_ids = [a.state.actor_id for a in self.actors]+[pose.actor_id for pose in extra_mouths]
        if len(set(mouth_ids)) != len(mouth_ids):
            raise ValueError('extra mouths require unique actor IDs distinct from encounter actors')
        before = self.school.state()
        if self.ownership.time != before.time:
            raise RuntimeError('fish/contact clocks diverged')
        released = ()
        if not self.remove_prey:
            unlocked = release_virtual_locks(self.ownership, prey_ids=before.prey_ids,
                prey_positions=before.positions, mouths=tuple(MouthPose(a.state.actor_id,
                    a.state.position,a.state.heading,a.mouth) for a in self.actors)+extra_mouths)
            released = tuple(sorted(self.ownership.captured_ids-unlocked.captured_ids))
            self.ownership = unlocked
        plans, observations = [], []
        for actor in self.actors:
            others = ([a.state.position for a in self.actors
                       if a.state.species == actor.state.species and a.state.actor_id != actor.state.actor_id]
                      if actor.config.spacing_enabled else None)
            observation = observe(actor.state,before.positions,before.directions*self.scenario.speed,
                                  before.prey_ids,actor.config,conspecific_positions=others)
            observations.append((actor.state.actor_id,len(observation.prey_ids)))
            planner = self.actor_planners.get(actor.state.actor_id)
            if planner is None:
                plan = advance(actor.state,observation,self.scenario.dt,actor.config)
            else:
                peers = tuple(a.state.position for a in self.actors
                    if a.state.species == actor.state.species
                    and a.state.actor_id != actor.state.actor_id
                    and np.linalg.norm(np.asarray(a.state.position)-actor.state.position)
                        <= self.planner_peer_observation_radii.get(actor.state.actor_id,actor.config.spacing_radius))
                plan = planner(actor.state,observation,self.scenario.dt,actor.config,
                               local_peer_positions=peers)
                _validate_actor_plan(plan, actor.state, self.scenario.dt)
            plans.append(plan)
        threats = [a.state.position for a in self.actors if a.state.position[2] <= self.scenario.surface_z]
        threats.extend(extra_positions[extra_positions[:,2] <= self.scenario.surface_z].tolist())
        fields = self.school.step(threats if self.predator_cues else None)
        reflected = tuple(int(i) for i in self.school.last_reflected_ids)
        unremoved = self.school.state()
        paths = fish_paths(before,unremoved,reflected,self.scenario.surface_z)
        proposals, bouts = [], {}
        for actor,plan in zip(self.actors,plans):
            proposals.extend(contact_proposals(actor,plan,paths,before,self.scenario.speed))
            for piece in plan.pieces:
                if piece.bite_window is not None:
                    key = (actor.state.actor_id,piece.bout_id)
                    bouts[key] = Bout(*key,piece.bite_window,actor.capture_probability)
        resolution = resolve_contacts(proposals,tuple(bouts.values()),self.ownership,
            end=unremoved.time,capture_rngs=self.capture_rngs,tie_rng=self.tie_rng)
        closed = set(resolution.state.closed_bouts)
        for i,(actor,plan) in enumerate(zip(self.actors,plans)):
            contacts = [o for o in resolution.outcomes if o.closes_bout and o.proposal.actor_id == actor.state.actor_id]
            if len(contacts)>1:
                raise RuntimeError('multiple closed bouts in one actor step; reduce dt')
            if contacts:
                outcome = contacts[0]
                plan = apply_contact(plan,outcome.status=='captured',outcome.proposal.contact.time,actor.config)
                plans[i] = plan
            for transition in plan.transitions:
                if transition.reason in ('timeout','target_not_visible','ascent_depth_margin',
                                         'shark_surface_reached','shark_upward_opportunity_lost'):
                    closed.add((actor.state.actor_id,transition.bout_id))
        self.ownership = replace(resolution.state,closed_bouts=frozenset(closed))
        self.actors = tuple(replace(actor,state=plan.state) for actor,plan in zip(self.actors,plans))
        if self.remove_prey and resolution.captured_ids:
            self.school.remove_ids(np.asarray(resolution.captured_ids,dtype=np.int64))
        return EncounterStep(before,unremoved,self.school.state(),tuple(plans),resolution.outcomes,
            resolution.captured_ids,released,
            self.ownership.captured_ids if not self.remove_prey else frozenset(),
            tuple(observations),fields,reflected)

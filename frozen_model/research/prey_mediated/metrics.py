"""Observable school-state metrics, independent of every predator controller.

Positions are (N,3), with all-NaN rows reserved for removed fish. Headings may
describe orientation even when fish are stationary; velocities describe actual
motion. Their distinction is explicit. No scalar here classifies a bait ball.
"""
from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


def _vectors(value, shape, live, name):
    if value is None:
        return None
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.isfinite(array[live]).all():
        raise ValueError(f"{name} must match positions and be finite for live fish")
    return array[live]


def snapshot_metrics(positions, headings=None, velocities=None, *, initial_count=None,
                     link_radius=2., core_radius_fraction=.5, zero_tol=1e-12):
    """Measure geometry, heading order, motion and connectivity separately.

    Covariance volume is the volume of a one-RMS-extent ellipsoid, NOT occupied
    volume. The orientation tensor is mean(u u^T); its eigenvalues sum to one.
    Nematic order=(3*largest eigenvalue-1)/2 distinguishes parallel/antiparallel
    alignment from isotropic headings even if vector polarization is zero.

    Relative angular order = |sum(r cross w)| / sum(|r| |w|), where r=x-mean(x)
    and w=v-mean(v). Its unsigned companion sums |r cross w| in the numerator.
    Pure translation, static agents, or coincident positions have no meaningful
    relative angular order: return NaN and an explicit false validity flag.
    Opposing rotation may have high angular activity but low coherent order.
    """
    x = np.asarray(positions, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError("positions must have shape (N,3)")
    live = np.isfinite(x).all(axis=1)
    if not np.all(live | np.isnan(x).all(axis=1)):
        raise ValueError("positions contain partial NaN or infinite rows")
    if not np.isfinite([link_radius, core_radius_fraction, zero_tol]).all() or link_radius <= 0 or not 0 < core_radius_fraction < 1 or zero_tol <= 0:
        raise ValueError("invalid metric scales")
    n = int(live.sum())
    initial_count = len(x) if initial_count is None else initial_count
    if (isinstance(initial_count, (bool, np.bool_)) or not isinstance(initial_count,(int,float,np.integer,np.floating))
        or not np.isfinite(initial_count) or int(initial_count) != initial_count or initial_count < n or initial_count <= 0):
        raise ValueError("initial_count must be a positive integer at least the live count")
    v = _vectors(velocities, x.shape, live, "velocities")
    h = _vectors(headings, x.shape, live, "headings")
    orientation_source = "headings" if h is not None else ("velocities" if v is not None else "unavailable")
    if h is None:
        h = v
    points = x[live]
    result = dict(n_live=n, initial_count=int(initial_count), retained_fraction=n/initial_count,
                  link_radius=float(link_radius), core_radius_fraction=float(core_radius_fraction),
                  orientation_source=orientation_source)
    geometry_keys = ("centroid_x", "centroid_y", "centroid_z", "rg", "r90", "rmax",
                     "rms_extent_min", "rms_extent_mid", "rms_extent_max", "shape_thickness",
                     "shape_width", "covariance_ellipsoid_volume", "density_r90_proxy", "core_fraction")
    result.update(dict.fromkeys(geometry_keys, float("nan")))
    result["spatial_extent_valid"] = False
    centre = points.mean(axis=0) if n else np.zeros(3)
    radial = points-centre
    radius = np.linalg.norm(radial, axis=1)
    if n:
        eigenvalues = np.maximum(np.linalg.eigvalsh(radial.T@radial/n), 0.)
        extent = np.sqrt(eigenvalues)
        r90 = float(np.quantile(radius, .9))
        extent_valid = bool(extent[-1] > zero_tol)
        result.update(centroid_x=float(centre[0]), centroid_y=float(centre[1]), centroid_z=float(centre[2]),
            rg=float(np.sqrt(np.mean(radius**2))), r90=r90, rmax=float(radius.max()),
            rms_extent_min=float(extent[0]), rms_extent_mid=float(extent[1]), rms_extent_max=float(extent[2]),
            shape_thickness=float(extent[0]/extent[-1]) if extent_valid else float("nan"),
            shape_width=float(extent[1]/extent[-1]) if extent_valid else float("nan"),
            covariance_ellipsoid_volume=float(4*np.pi/3*np.prod(extent)),
            core_fraction=float(np.mean(radius <= core_radius_fraction*r90)) if r90 > zero_tol else float("nan"),
            density_r90_proxy=float(np.count_nonzero(radius <= r90)/(4*np.pi/3*r90**3)) if r90 > zero_tol else float("nan"),
            spatial_extent_valid=extent_valid)
    result.update(polarization=float("nan"), nematic_order=float("nan"), heading_valid_fraction=0.,
                  orientation_eigenvalue_min=float("nan"), orientation_eigenvalue_mid=float("nan"),
                  orientation_eigenvalue_max=float("nan"))
    for a in "xyz":
        for b in "xyz": result["orientation_tensor_"+a+b] = float("nan")
    if h is not None and n:
        norms = np.linalg.norm(h, axis=1)
        good = norms > zero_tol
        result["heading_valid_fraction"] = float(good.mean())
        if good.any():
            u = h[good]/norms[good,None]
            tensor = u.T@u/len(u)
            values = np.linalg.eigvalsh(tensor)
            result.update(polarization=float(np.linalg.norm(u.mean(axis=0))),
                          nematic_order=float((3*values[-1]-1)/2),
                          orientation_eigenvalue_min=float(values[0]), orientation_eigenvalue_mid=float(values[1]),
                          orientation_eigenvalue_max=float(values[2]))
            for i,a in enumerate("xyz"):
                for j,b in enumerate("xyz"): result["orientation_tensor_"+a+b] = float(tensor[i,j])
    result.update(mean_live_velocity_x=float("nan"), mean_live_velocity_y=float("nan"), mean_live_velocity_z=float("nan"),
                  mean_live_velocity_speed=float("nan"), mean_individual_speed=float("nan"), relative_speed_rms=float("nan"),
                  translation_fraction=float("nan"), moving_fraction=float("nan"),
                  milling_lab=float("nan"), milling_lab_valid=False, milling_relative=float("nan"),
                  milling_relative_valid=False, angular_activity_relative=float("nan"))
    if v is not None and n:
        average_v = v.mean(axis=0)
        relative_v = v-average_v
        speed = np.linalg.norm(v, axis=1)
        relative_speed = np.linalg.norm(relative_v, axis=1)
        speed_rms = float(np.sqrt(np.mean(speed**2)))
        residual_rms = float(np.sqrt(np.mean(relative_speed**2)))
        result.update(mean_live_velocity_x=float(average_v[0]), mean_live_velocity_y=float(average_v[1]),
                      mean_live_velocity_z=float(average_v[2]), mean_live_velocity_speed=float(np.linalg.norm(average_v)),
                      mean_individual_speed=float(speed.mean()), relative_speed_rms=residual_rms,
                      moving_fraction=float(np.mean(speed > zero_tol)),
                      translation_fraction=float(np.linalg.norm(average_v)/speed.mean()) if speed.mean() > zero_tol else float("nan"))
        for name, velocity, magnitudes, valid_speed in (
            ("lab",v,speed,speed_rms > zero_tol),
            ("relative",relative_v,relative_speed,residual_rms > zero_tol*max(1.,speed_rms))):
            denominator = float(np.sum(radius*magnitudes))
            valid = bool(result["spatial_extent_valid"] and valid_speed and denominator > zero_tol)
            result["milling_"+name+"_valid"] = valid
            if valid:
                angular = np.cross(radial, velocity)
                result["milling_"+name] = float(np.clip(np.linalg.norm(angular.sum(axis=0))/denominator,0.,1.))
                if name == "relative":
                    result["angular_activity_relative"] = float(np.clip(np.linalg.norm(angular,axis=1).sum()/denominator,0.,1.))
    result.update(component_count=0, largest_component_fraction=0., largest_component_retention=0.,
                  nn_median=float("nan"), nn_p05=float("nan"))
    if n:
        counts = np.array([1])
        if n > 1:
            tree = cKDTree(points)
            pairs = tree.query_pairs(link_radius, output_type="ndarray")
            graph = csr_matrix((np.ones(len(pairs)), (pairs[:,0],pairs[:,1])),shape=(n,n))
            _, labels = connected_components(graph,directed=False)
            counts = np.bincount(labels)
            nearest = tree.query(points,k=2)[0][:,1]
            result.update(nn_median=float(np.median(nearest)), nn_p05=float(np.quantile(nearest,.05)))
        result.update(component_count=len(counts), largest_component_fraction=float(counts.max()/n),
                      largest_component_retention=float(counts.max()/initial_count))
    return result


def trajectory_metrics(positions, times, headings=None, velocities=None, **kwargs):
    """Measured frame geometry and centroid displacement on saved snapshots.

    centroid_step_speed uses the preceding interval. It is distinct from the
    mean instantaneous velocity and includes changes in membership after loss.
    """
    x, times = np.asarray(positions,dtype=float), np.asarray(times,dtype=float)
    if x.ndim != 3 or x.shape[2] != 3 or times.shape != (len(x),) or len(times) < 1 or not np.isfinite(times).all() or np.any(np.diff(times)<=0):
        raise ValueError("invalid positions/times trajectory")
    for name, value in (("headings",headings),("velocities",velocities)):
        if value is not None and np.asarray(value).shape != x.shape:
            raise ValueError(name+" must match positions")
    rows = [dict(time=float(t), **snapshot_metrics(points,
                None if headings is None else headings[i], None if velocities is None else velocities[i], **kwargs))
            for i,(t,points) in enumerate(zip(times,x))]
    centres = np.array([[r["centroid_"+a] for a in "xyz"] for r in rows])
    path = 0.
    for i,row in enumerate(rows):
        step = float(np.linalg.norm(centres[i]-centres[i-1])) if i else 0.
        if i: path += step
        row.update(centroid_step_speed=step/(times[i]-times[i-1]) if i else float("nan"),
                   centroid_net_displacement=float(np.linalg.norm(centres[i]-centres[0])), centroid_path_length=path)
    return rows

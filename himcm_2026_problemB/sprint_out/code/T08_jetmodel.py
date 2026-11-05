"""T08 - Jet-in-crossflow model of an evaporative cooler in an open bus shelter.

What it does
------------
1. A 3-D "integral" jet model (top-hat jet that swallows - entrains - surrounding air,
   is pushed sideways by wind, and sinks because it is cold).
     * shear entrainment  alpha = 0.086  -> chosen so that with NO wind the model reproduces
       the free-jet centreline decay Uc/U0 = 5.8 d/x (Hussein, Capp & George 1994).
     * crossflow ("forced") entrainment beta -> FITTED so that the model trajectory
       reproduces Pratte & Baines (1967): z/(r d) = 2.05 (x/(r d))^0.28.
2. Spreads the cooled air of every jet segment as a Gaussian cross-section, reflects it off
   the floor, and measures how much of it sits inside the waiting zone of the shelter.
   phi = (volume of pure cooled air inside the zone) / (zone volume)
       = zone-average "jet-fluid concentration" = exactly the mixing fraction used in
         core.mix() (T_zone = phi*T_supply + (1-phi)*T_ambient).
3. Closed-form "breakthrough" wind speed from the Pratte & Baines trajectory.

Units: m, s, m3/s, degC.
"""
import numpy as np

G = 9.81
ALPHA = 0.086          # top-hat shear entrainment, from free-jet decay constant 5.8 (see memo)

# ------------------------------------------------------------------ shelter geometry
SHELTER = dict(Lx=5.0, Ly=3.0, H=2.5, z_lo=0.1, z_hi=1.8)   # 15 m2 footprint (scenario.py)


def zone_volume(sh=SHELTER):
    return sh["Lx"] * sh["Ly"] * (sh["z_hi"] - sh["z_lo"])


# ------------------------------------------------------------------ integral jet model
def integrate_jet(Q0, d, Ua, wind_dir, x0, jet_dir, dT0=0.0, T_amb=43.0,
                  beta=0.209, alpha=ALPHA, ds=None, s_max=40.0, box=None):
    """March a round jet along its path.

    Q0       outlet volume flow, m3/s
    d        equivalent outlet diameter, m
    Ua       crossflow (wind) speed at jet height, m/s
    wind_dir unit vector of the wind (3-D, horizontal)
    x0       outlet position (3-vector), m
    jet_dir  unit vector of the outlet direction
    dT0      outlet temperature deficit (degC) -> negative buoyancy (cold air sinks)
    Returns dict of arrays along the path: pos (n,3), Q, speed, b, t (unit tangent), ds.
    """
    jet_dir = np.asarray(jet_dir, float); jet_dir /= np.linalg.norm(jet_dir)
    wind_dir = np.asarray(wind_dir, float)
    if np.linalg.norm(wind_dir) > 0:
        wind_dir = wind_dir / np.linalg.norm(wind_dir)
    Uvec = Ua * wind_dir
    A0 = np.pi * d * d / 4.0
    U0 = Q0 / A0
    gp0 = G * dT0 / (T_amb - dT0 + 273.15)          # reduced gravity of the cold jet, m/s2
    F0 = Q0 * gp0                                   # buoyancy flux (conserved), m4/s3
    if ds is None:
        ds = d / 20.0
    pos = np.asarray(x0, float).copy()
    Q = Q0
    M = Q0 * U0 * jet_dir                           # momentum flux vector, m4/s2
    out_p, out_Q, out_u, out_b, out_t = [], [], [], [], []
    s = 0.0
    while s < s_max:
        u = M / Q
        sp = np.linalg.norm(u)
        if sp < 1e-4:
            break
        t = u / sp
        b = np.sqrt(Q / (np.pi * sp))
        out_p.append(pos.copy()); out_Q.append(Q); out_u.append(sp); out_b.append(b); out_t.append(t)
        if box is not None:
            lo, hi = box
            if np.any(pos < lo) or np.any(pos > hi):
                break

        def rhs(Q_, M_):
            u_ = M_ / Q_
            sp_ = np.linalg.norm(u_)
            t_ = u_ / sp_
            b_ = np.sqrt(Q_ / (np.pi * sp_))
            ua_par = np.dot(Uvec, t_)
            ua_n = np.linalg.norm(Uvec - ua_par * t_)
            E = 2 * np.pi * b_ * (alpha * abs(sp_ - ua_par) + beta * ua_n)
            dM = E * Uvec + np.array([0.0, 0.0, -F0 / sp_])
            return E, dM, t_

        # RK2 (midpoint) step in s
        E1, dM1, t1 = rhs(Q, M)
        Qm, Mm = Q + 0.5 * ds * E1, M + 0.5 * ds * dM1
        E2, dM2, t2 = rhs(Qm, Mm)
        Q += ds * E2
        M = M + ds * dM2
        pos = pos + ds * t2
        s += ds
    return dict(pos=np.array(out_p), Q=np.array(out_Q), speed=np.array(out_u),
                b=np.array(out_b), t=np.array(out_t), ds=ds, Q0=Q0, U0=U0, d=d)


# ------------------------------------------------------------------ capture fraction
_rng = np.random.default_rng(0)
_STD = _rng.standard_normal((2, 300))


def capture_fraction(jet, sh=SHELTER, every=2, walls=("back",)):
    """phi = cooled-air volume inside the waiting zone / zone volume.

    Each path segment holds a volume of pure cooled air dV = Q0*ds/speed (cooled air
    passes at 'speed', so it lingers ds/speed seconds per metre). That volume is spread
    as a 2-D Gaussian (sigma = b/2 equivalent to a top-hat of radius b) across the jet,
    reflected at the floor, and counted if it lies inside the zone box.
    """
    P, b, t, sp = jet["pos"], jet["b"], jet["t"], jet["speed"]
    Q0, ds = jet["Q0"], jet["ds"]
    inside = 0.0
    for i in range(0, len(P), every):
        ti = t[i]
        # two unit vectors normal to the tangent
        a = np.array([0, 0, 1.0]) if abs(ti[2]) < 0.9 else np.array([1.0, 0, 0])
        n1 = np.cross(ti, a); n1 /= np.linalg.norm(n1)
        n2 = np.cross(ti, n1)
        sig = b[i] / 2.0
        pts = P[i][:, None] + sig * (n1[:, None] * _STD[0] + n2[:, None] * _STD[1])
        pts[2] = np.abs(pts[2])                        # floor reflection (cold air pools)
        pts[2] = np.where(pts[2] > sh["H"], 2 * sh["H"] - pts[2], pts[2])  # roof reflection
        # solid walls reflect cooled air back into the shelter (image method = upper bound)
        if "back" in walls:
            pts[1] = np.where(pts[1] > sh["Ly"], 2 * sh["Ly"] - pts[1], pts[1])
        if "end0" in walls:
            pts[0] = np.abs(pts[0])
        if "end1" in walls:
            pts[0] = np.where(pts[0] > sh["Lx"], 2 * sh["Lx"] - pts[0], pts[0])
        ok = ((pts[0] >= 0) & (pts[0] <= sh["Lx"]) & (pts[1] >= 0) & (pts[1] <= sh["Ly"])
              & (pts[2] >= sh["z_lo"]) & (pts[2] <= sh["z_hi"]))
        dV = Q0 * ds * every / sp[i]
        inside += dV * ok.mean()
    return inside / zone_volume(sh)


LAYOUTS = {
    # outlet position, jet direction.  x along the kerb (5 m), y depth (back wall at y=3)
    "end-fire":  dict(x0=(0.0, 1.5, 1.0), jet=(1, 0, 0)),     # throws along the 5 m length
    "back-fire": dict(x0=(2.5, 3.0, 1.0), jet=(0, -1, 0)),    # from back wall toward kerb, 3 m
}


def wind_vector(jet, theta_deg):
    """theta = angle between wind and jet: 0 tail-wind, 90 cross-wind, 180 head-wind."""
    j = np.asarray(jet, float)
    perp = np.array([-j[1], j[0], 0.0])
    th = np.radians(theta_deg)
    return np.cos(th) * j + np.sin(th) * perp


BETA = 0.209   # fitted to Pratte & Baines (1967) in T08_validate.py


def phi_device(Q0, d, Ua, theta=90.0, layout="end-fire", dT0=18.75, beta=BETA, sh=SHELTER,
               walls=("back",), return_jet=False):
    L = LAYOUTS[layout]
    box = (np.array([-4.0, -4.0, -1.0]), np.array([sh["Lx"] + 4, sh["Ly"] + 4, 5.0]))
    jet = integrate_jet(Q0, d, Ua, wind_vector(L["jet"], theta), L["x0"], L["jet"],
                        dT0=dT0, beta=beta, box=box, ds=min(d / 15.0, 0.05))
    phi = capture_fraction(jet, sh, walls=walls)
    # Integral jet models are not valid where the jet stalls against a head-wind
    # (its speed drops below the wind speed and it turns back on itself).
    if Ua > 0 and jet["speed"].min() < 0.6 * Ua:
        phi = np.nan
    return (phi, jet) if return_jet else phi


# ------------------------------------------------------------------ closed-form results
def pb_trajectory(x, r, d, A=2.05, B=0.28):
    """Pratte & Baines (1967): penetration z (along the jet's initial direction)
    after the jet has drifted x downwind.  z/(r d) = A (x/(r d))^B."""
    rd = r * d
    return A * rd * (x / rd) ** B


def breakthrough_r(L_p, X_e, d, A=2.05, B=0.28):
    """Velocity ratio r = U0/Ua at which the jet centreline drifts X_e downwind (and so
    leaves the shelter) exactly when it has penetrated L_p toward the people.
    From L_p = A (rd)^(1-B) X_e^B  ->  r = (L_p / (A X_e^B))^(1/(1-B)) / d."""
    return (L_p / (A * X_e ** B)) ** (1.0 / (1.0 - B)) / d


def free_jet_volume(d, L, alpha=ALPHA):
    """Cooled-air volume held by a straight free jet over a throw L (no wind):
    V = (pi d^2/4) (L + 2 alpha L^2 / d). Independent of the outlet speed."""
    return np.pi * d * d / 4.0 * (L + 2 * alpha * L * L / d)


def box_phi(Q, Ua, A=10.694, Cd=0.6, v_floor=0.5):
    """The team's well-mixed-box capture fraction (core.capture_fraction)."""
    return Q / (Q + Cd * A * max(Ua, v_floor))


def concentration_field(jet, X, Y, z, walls=("back",), sh=SHELTER):
    """Approximate cooled-air fraction c(x,y,z) on a horizontal plane (for pictures only):
    nearest path point, Gaussian cross-section, floor image; capped at 1 (potential core)."""
    P, b, sp, Q0 = jet["pos"], jet["b"], jet["speed"], jet["Q0"]
    pts = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z)], 1)
    C = np.zeros(len(pts))
    imgs = [np.array([1, 1, 1.0]), np.array([1, 1, -1.0])]
    for m in imgs:
        q = pts * m
        dist = np.linalg.norm(q[:, None, :] - P[None, ::3, :], axis=2)
        k = np.argmin(dist, axis=1) * 3
        rho = dist[np.arange(len(q)), k // 3]
        sig = b[k] / 2.0
        C += (Q0 / sp[k]) / (2 * np.pi * sig ** 2) * np.exp(-rho ** 2 / (2 * sig ** 2))
    return np.minimum(C, 1.0).reshape(X.shape)

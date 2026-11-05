"""T09 shared functions: wait time W(headway) and shelter occupancy via Little's law.

All waits in MINUTES, headways in MINUTES, arrival rates in PASSENGERS PER HOUR.
Sources of every coefficient are in the memo (s.1); summarised in WAIT_MODELS below.
"""
import math, pathlib
import numpy as np, pandas as pd

S = pathlib.Path(__file__).resolve().parents[1]
D = S / "dl_T09"

# Linear fits E[W] = a + b*h reported in the literature (h, W in minutes).
# Coefficients as quoted in Singh, Graham, Horcher & Anderson (2021), TR-C 130:103267, s.2.1.
WAIT_MODELS = {
    "O'Flaherty & Mangan 1970 (Leeds bus)":  (1.79, 0.14),
    "Seddon & Day 1974 (Manchester bus)":    (2.34, 0.26),
    "Fan & Machemehl 2009 (Austin bus)":     (2.00, 0.30),
}


def w_random(h, cv=0.0):
    """Random (Poisson) arrivals: E[W] = h/2 * (1 + cv^2)  (Osana & Newell 1972; Newell 1982)."""
    return 0.5 * np.asarray(h, float) * (1.0 + cv ** 2)


def w_timed(h, a=2.0, b=0.30):
    """Timed (schedule-aware) arrivals, linear fit E[W] = a + b*h."""
    return a + b * np.asarray(h, float)


def threshold(a, b, cv=0.0):
    """Headway h* where the random line h/2(1+cv^2) meets the timed line a + b h."""
    return a / (0.5 * (1 + cv ** 2) - b)


def W_of_h(h, a=2.0, b=0.30, cv=0.0):
    """Our working model: passengers behave randomly below h*, timed above it.
    Equivalent to min(random, timed) because both lines cross exactly once.
    Default (Fan & Machemehl, cv=0) gives h* = 10 min -- the TCQSM rule of thumb."""
    return np.minimum(w_random(h, cv), w_timed(h, a, b))


def load_stops():
    x = pd.read_csv(D / "stops_hourly_lambda_headway.csv", dtype={"stop_id": str})
    return x


def occupancy_table(x=None, a=2.0, b=0.30, cv=0.0, h_cap=60.0):
    """L_t = lambda_t * W(h_t) / 60   (Little's law; persons in the shelter area, hourly mean).
    Hours with boardings but no scheduled bus (data/schedule mismatch) use h_cap."""
    x = load_stops() if x is None else x.copy()
    h = x.headway_min.fillna(h_cap).clip(upper=h_cap)
    x["W_min"] = W_of_h(h, a, b, cv)
    x["W_half"] = w_random(h)                       # naive h/2 for comparison
    x["L"] = x.lam_per_h * x.W_min / 60.0
    x["L_half"] = x.lam_per_h * x.W_half / 60.0
    return x


def p_occupied(L):
    """Number waiting is Poisson(L) for Poisson arrivals and ANY wait distribution
    (M/G/infinity steady state), so P(nobody there) = exp(-L)."""
    return 1.0 - np.exp(-np.asarray(L, float))


def expected_min(L, c):
    """E[min(N, c)] for N ~ Poisson(L): people who actually get the device's cooling
    when it can serve at most c people at once."""
    L = float(L)
    if L <= 0:
        return 0.0
    c = int(c)
    k = np.arange(c)
    pk = np.exp(-L + k * math.log(L) - np.array([math.lgamma(i + 1) for i in k]))
    return float((k * pk).sum() + c * (1 - pk.sum()))

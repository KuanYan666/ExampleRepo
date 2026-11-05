"""
Task 3 asks you to 'identify the characteristics that contribute most to efficient
cooling'. That is literally a variance-based sensitivity analysis. Sobol indices
answer it; a tornado chart of one-at-a-time swings does not (it misses interactions).
"""
import numpy as np, pandas as pd, time
import core as C, scenario as S
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

df = pd.read_csv("data/Phoenix.csv")
df["time"] = pd.to_datetime(df["time"])
# one representative hot day, 3-hourly
day = df[(df.time.dt.month == 7) & (df.time.dt.day == 15)].iloc[::3].copy()
day["sol_alt"] = [S.solar_altitude(33.45, -112.07, t, -7) for t in day.time]

base = S.calibrate()

problem = {
    "num_vars": 7,
    "names": ["pad_eff", "open_area", "C_d", "fan_speed", "headway_min",
              "boardings", "comfort_thresh"],
    "bounds": [[0.70, 0.90], [5.0, 25.0], [0.4, 0.8], [0.8, 2.0],
               [6.0, 25.0], [200, 900], [28.0, 33.0]],
}


def evaluate(p, device="evap"):
    eps, A, cd, vfan, hw, board, s0 = p
    cal = dict(base); cal.update(eps_evap=eps, eps_evap_big=eps, v_fan=vfan, C_d=cd, v_design=0.5)
    venue = dict(S.VENUES["bus_stop"]); venue.update(A_open_eff=A, headway_min=hw, boardings_per_day=board)
    dev, none = S.DEVICES[device], S.DEVICES["none"]
    num = 0.0
    for row in day.itertuples():
        N = venue["boardings_per_day"] * S.HOURLY_SHAPE[row.time.hour] * (venue["headway_min"]/60)/2
        Tb,RHb,vb,trb = S.shelter_state(row, venue, none, cal)
        Tc,RHc,vc,trc = S.shelter_state(row, venue, dev, cal)
        d = C.dissatisfied_fraction(C.SET(Tb,RHb,vb,trb), s0=s0) - \
            C.dissatisfied_fraction(C.SET(Tc,RHc,vc,trc), s0=s0)
        num += N * max(d, 0.0) * 3.0
    E = dev["P"] * len(day) * 3.0
    return num / E


for device in ["evap", "fan"]:
    t0 = time.time()
    X = sobol_sample.sample(problem, 64, calc_second_order=False)
    Y = np.array([evaluate(x, device) for x in X])
    Si = sobol_analyze.analyze(problem, Y, calc_second_order=False, print_to_console=False)
    print("=" * 78)
    print(f"SOBOL SENSITIVITY of eta_comfort  --  {S.DEVICES[device]['label']}")
    print(f"  ({len(X)} model runs, {time.time()-t0:.0f}s;  eta mean {Y.mean():.3f}, "
          f"range {Y.min():.3f}-{Y.max():.3f})")
    print("=" * 78)
    print(f"  {'parameter':<16} {'S1 (direct)':>12} {'ST (incl. interact.)':>22}")
    order = np.argsort(-Si["ST"])
    for i in order:
        print(f"  {problem['names'][i]:<16} {Si['S1'][i]:>12.3f} {Si['ST'][i]:>22.3f}")
    print()

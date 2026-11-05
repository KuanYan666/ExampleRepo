"""T09 step 5: compare A/B/C with TOPSIS (and a simple weighted-sum cross-check),
weights from AHP (stated judgement) and from the entropy method, robustness by
+/-20% one-at-a-time weight changes and Monte Carlo over weights AND uncertain inputs.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import T09_common as T

rng = np.random.default_rng(2026)
res = pd.read_csv(T.D / "T09_service_results.csv", dtype={"stop": str})
DEVS = ["fan", "evap", "evap_big"]
NAME = {"fan": "A fan", "evap": "B evap", "evap_big": "C large evap", "none": "shade only"}
CRIT = ["felt cooling", "heat-safety", "energy", "water", "cost"]
BENEFIT = np.array([True, True, False, False, False])

PRICE_KWH = 0.1337      # $/kWh  [VERIFIED: EIA Electric Power Monthly Table 5.3, US commercial 2025]
# ---- every value below is ASSUMED (no source found for a bus-shelter install); MC ranges given
CAPEX = {"fan": (800, 300, 2000), "evap": (2500, 1000, 5000), "evap_big": (5000, 2000, 10000)}
MAINT = {"fan": (20, 0, 60), "evap": (200, 50, 500), "evap_big": (300, 100, 700)}   # $/season
LIFE = (7, 5, 10)              # years, one cooling season per year
P_WATER = (4.0, 2.0, 8.0)      # $/m3 water+sewer


def matrix(city, stop, capex=None, maint=None, life=7, pw=4.0, pk=PRICE_KWH, noise=None,
           with_none=False):
    """Decision matrix: rows = alternatives, cols = CRIT, season totals."""
    sub = res[(res.city == city) & (res.stop == stop) & (res.policy == "smart_occ")].set_index("device")
    capex = capex or {d: CAPEX[d][0] for d in DEVS}
    maint = maint or {d: MAINT[d][0] for d in DEVS}
    X = []
    for d in DEVS:
        r = sub.loc[d]
        cost = capex[d] / life + maint[d] + r.kWh * pk + r.water_m3 * pw
        X.append([r.S_pdh, r.risk, r.kWh, r.water_m3, cost])
    X = np.array(X, float)
    if noise is not None:
        X[:, :2] *= noise                      # physics uncertainty on the two benefits
    if with_none:
        X = np.vstack([X, [0, 0, 0, 0, 0]])
    return X


def topsis(X, w, benefit=BENEFIT):
    n = np.sqrt((X ** 2).sum(0)); n[n == 0] = 1
    V = X / n * w
    best = np.where(benefit, V.max(0), V.min(0))
    worst = np.where(benefit, V.min(0), V.max(0))
    dp = np.sqrt(((V - best) ** 2).sum(1)); dm = np.sqrt(((V - worst) ** 2).sum(1))
    return dm / (dp + dm)


def saw(X, w, benefit=BENEFIT):
    """Weighted sum of min-max scores (the 'composite index' cross-check)."""
    lo, hi = X.min(0), X.max(0); rg = np.where(hi > lo, hi - lo, 1)
    Z = np.where(benefit, (X - lo) / rg, (hi - X) / rg)
    return Z @ w


def ahp(M):
    vals, vecs = np.linalg.eig(M)
    k = np.argmax(vals.real); w = np.abs(vecs[:, k].real); w /= w.sum()
    n = len(M); ci = (vals[k].real - n) / (n - 1); ri = {3: .58, 4: .90, 5: 1.12, 6: 1.24}[n]
    return w, vals[k].real, ci / ri


def entropy_w(X):
    P = X / np.where(X.sum(0) == 0, 1, X.sum(0))
    with np.errstate(divide="ignore", invalid="ignore"):
        e = -np.nansum(np.where(P > 0, P * np.log(P), 0), 0) / np.log(len(X))
    d = 1 - e
    return d / d.sum()


# ---- AHP pairwise judgements (Saaty 1-9 scale), order = CRIT.  Stated judgement:
# heat-safety > felt cooling > cost > energy > water  (public-health duty first, then comfort,
# then money; water ranked last because a shelter's use is tiny next to city supply -- debatable!)
M = np.array([
    [1,   1/2, 3,   4,   2  ],
    [2,   1,   5,   6,   3  ],
    [1/3, 1/5, 1,   2,   1/2],
    [1/4, 1/6, 1/2, 1,   1/3],
    [1/2, 1/3, 2,   3,   1  ]], float)
W_AHP, lam, CR = ahp(M)

if __name__ == "__main__":
    out = []
    print(f"AHP weights {dict(zip(CRIT, W_AHP.round(3)))}  lambda_max={lam:.3f}  CR={CR:.3f}")
    cases = [("Phoenix", "102949"), ("Houston", "102949"), ("Phoenix", "303317"), ("Houston", "303317"),
             ("Singapore", "102949"), ("LasVegas", "102949")]
    for city, stop in cases:
        X = matrix(city, stop)
        W_ENT = entropy_w(X)
        print(f"\n=== {city}, stop {stop} : decision matrix (season, smart + presence sensor)")
        print(pd.DataFrame(X, index=[NAME[d] for d in DEVS], columns=CRIT).round(1).to_string())
        print("  entropy weights", dict(zip(CRIT, W_ENT.round(3))))
        for wname, w in [("AHP", W_AHP), ("entropy", W_ENT), ("equal", np.ones(5) / 5)]:
            c = topsis(X, w); s = saw(X, w)
            cn = topsis(matrix(city, stop, with_none=True), w)
            print(f"  {wname:8s} TOPSIS C*: " + "  ".join(f"{NAME[d]} {v:.3f}" for d, v in zip(DEVS, c))
                  + f"  -> {NAME[DEVS[c.argmax()]]:12s} | SAW -> {NAME[DEVS[s.argmax()]]:12s}"
                  + f" | +shade-only: " + " ".join(f"{v:.2f}" for v in cn)
                  + f" -> {NAME[(DEVS + ['none'])[cn.argmax()]]}")
            out.append(dict(city=city, stop=stop, weights=wname, **{NAME[d]: v for d, v in zip(DEVS, c)}))
        # one-at-a-time +/-20 %
        flips = []
        base = DEVS[topsis(X, W_AHP).argmax()]
        for j in range(5):
            for f in (0.8, 1.2):
                w = W_AHP.copy(); w[j] *= f; w /= w.sum()
                win = DEVS[topsis(X, w).argmax()]
                if win != base: flips.append(f"{CRIT[j]} x{f}")
        print(f"  +/-20% one-at-a-time on AHP weights: winner {NAME[base]}; flips: {flips or 'none'}")
    pd.DataFrame(out).to_csv(T.D / "T09_topsis_results.csv", index=False)

    # ---- Monte Carlo: weights ~ Dirichlet around AHP (and, separately, uniform on simplex)
    #      + uniform draws of capex, maintenance, life, water price, electricity +/-20%,
    #      + lognormal 20% noise on the two physics benefits (independent per device)
    N = 20000
    mc = {}
    for city, stop in cases:
        for wmode in ["AHP+/-", "any weights"]:
            wins = np.zeros(3)
            for _ in range(N):
                w = rng.dirichlet(W_AHP * 40) if wmode == "AHP+/-" else rng.dirichlet(np.ones(5))
                cap = {d: rng.uniform(*CAPEX[d][1:]) for d in DEVS}
                mt = {d: rng.uniform(*MAINT[d][1:]) for d in DEVS}
                X = matrix(city, stop, cap, mt, rng.uniform(*LIFE[1:]), rng.uniform(*P_WATER[1:]),
                           PRICE_KWH * rng.uniform(.8, 1.2),
                           noise=np.exp(rng.normal(0, .2, (3, 2))))
                wins[topsis(X, w).argmax()] += 1
            mc[(city, stop, wmode)] = wins / N
            print(f"MC {city:9s} {stop} {wmode:12s}: P(rank 1) " +
                  "  ".join(f"{NAME[d]} {p:.3f}" for d, p in zip(DEVS, wins / N)))
    pd.DataFrame({f"{k[0]} {k[1]} {k[2]}": v for k, v in mc.items()}, index=[NAME[d] for d in DEVS]) \
        .T.to_csv(T.D / "T09_topsis_mc.csv")

    # ---- Fig 4: closeness scores for the two weight sets + MC win shares
    COL = ["#2a78d6", "#eb6834", "#1baf7a"]
    INK2, GRID = "#52514e", "#e4e3df"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), gridspec_kw=dict(width_ratios=[1.25, 1]))
    df = pd.DataFrame(out)
    df = df[df.stop == "102949"]
    labels, xs = [], []
    k = 0
    for city in ["Phoenix", "LasVegas", "Houston", "Singapore"]:
        for wname in ["AHP", "entropy"]:
            r = df[(df.city == city) & (df.weights == wname)].iloc[0]
            for i, d in enumerate(DEVS):
                axes[0].bar(k + (i - 1) * 0.26, r[NAME[d]], 0.24, color=COL[i],
                            label=NAME[d] if k == 0 else None)
            labels.append(f"{city}\n{wname}"); xs.append(k); k += 1
    axes[0].set_xticks(xs); axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylabel("TOPSIS closeness C* (1 = ideal)")
    axes[0].set_ylim(0, 1.08); axes[0].grid(axis="y", color=GRID, lw=.6)
    axes[0].legend(frameon=False, ncol=3, fontsize=8.5, loc="upper left")
    axes[0].set_title("Scores at the Bx15 stop (406 boardings/day)", loc="left", fontsize=10)
    for s in ("top", "right"):
        axes[0].spines[s].set_visible(False); axes[1].spines[s].set_visible(False)
    keys = [k for k in mc if k[1] == "102949"]
    y = np.arange(len(keys))
    left = np.zeros(len(keys))
    for i, d in enumerate(DEVS):
        v = np.array([mc[k][i] for k in keys])
        axes[1].barh(y, v, left=left, color=COL[i], height=.62, edgecolor="white", lw=2)
        for yy, l, vv in zip(y, left, v):
            if vv > .08:
                axes[1].text(l + vv / 2, yy, f"{vv:.0%}", ha="center", va="center", color="white", fontsize=8)
        left += v
    axes[1].set_yticks(y); axes[1].set_yticklabels([f"{k[0]}, {k[2]}" for k in keys], fontsize=8.5)
    axes[1].invert_yaxis(); axes[1].set_xlim(0, 1)
    axes[1].set_xlabel("Share of 20,000 Monte Carlo runs ranked first")
    axes[1].set_title("Robustness: weights + costs + physics varied", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(T.S / "figs" / "T09_fig4_topsis_robustness.png", dpi=170)

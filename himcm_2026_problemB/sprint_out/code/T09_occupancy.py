"""T09 step 3: the wait-time curve W(h) (Fig 1) and real-stop occupancy (Fig 2)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import T09_common as T

F = T.S / "figs"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COL = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
                     "axes.spines.right": False})

# ------------------------------------------------------------ thresholds table
print("Crossing headway h* where a + b h = h/2  (cv = 0):")
for k, (a, b) in T.WAIT_MODELS.items():
    print(f"  {k:40s} a={a:4.2f} b={b:4.2f}  h* = {T.threshold(a, b):5.2f} min")
for cv in (0.2, 0.3, 0.4):
    print(f"  Fan & Machemehl with headway irregularity cv={cv}: h* = {T.threshold(2, .3, cv):5.2f} min")

# ------------------------------------------------------------ Fig 1
h = np.linspace(0.5, 60, 400)
fig, ax = plt.subplots(figsize=(8.6, 4.6))
ax.axvspan(5, 11, color="#f2f1ed", zorder=0)
ax.text(5.3, 26.6, "documented switch from\nrandom to timed arrivals\n(5 to 11 min)",
        ha="left", va="top", fontsize=8.5, color=INK2)
ax.plot(h, T.w_random(h), color=INK2, lw=1.5, ls="--")
ax.text(55.5, 25.6, "random arrivals: W = h/2", color=INK2, fontsize=8.5, ha="left")
ax.plot(h, T.w_random(h, 0.4), color=INK2, lw=1.0, ls=":")
ax.text(12, 19.5, "random arrivals, irregular buses\n(cv = 0.4): W = h/2 (1+cv²)", color=INK2, fontsize=8.5)
lab = {"O'Flaherty & Mangan 1970 (Leeds bus)": (60.5, 10.2),
       "Seddon & Day 1974 (Manchester bus)": (60.5, 17.6),
       "Fan & Machemehl 2009 (Austin bus)": (60.5, 20.4)}
for (k, (a, b)), c in zip(T.WAIT_MODELS.items(), COL[1:]):
    ax.plot(h, T.w_timed(h, a, b), color=c, lw=1.4, alpha=.8)
    x0, y0 = lab[k]
    ax.text(x0 + 0.5, y0, k.split(" (")[0] + f": {a} + {b} h", color=INK, fontsize=8, va="center")
ax.plot(h, T.W_of_h(h), color=COL[0], lw=2.6, label="our model W(h) = min(h/2, 2 + 0.3 h)")
ax.plot([10], [5], "o", ms=8, color=COL[0], mec="white", mew=2)
ax.annotate("h* = 10 min, W = 5 min\n(TCQSM rule of thumb)", (10, 5), (14, 1.3),
            fontsize=8.5, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=.8))
ax.set_ylim(0, 27); ax.set_xlim(0, 84)
ax.set_xticks(range(0, 61, 10))
ax.set_xlabel("Headway h: minutes between buses on the route")
ax.set_ylabel("Mean wait W per passenger (minutes)")
ax.set_title("How long people wait depends on how often the bus comes", loc="left", fontsize=11)
ax.grid(axis="y", color=GRID, lw=.6); ax.legend(loc="lower right", frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig(F / "T09_fig1_wait_vs_headway.png", dpi=170); plt.close(fig)

# ------------------------------------------------------------ occupancy at real stops
x = T.occupancy_table()
order = ["303317", "102949", "102445", "551928"]
summ = []
for sid in order:
    s = x[x.stop_id == sid].sort_values("hour")
    hm = s[s.hour.between(10, 14)].headway_min.mean()
    hp = s[s.hour.between(7, 9)].headway_min.mean()
    summ.append(dict(stop=s.label.iloc[0], boardings_day=s.lam_per_h.sum(),
                     buses_day=s.trips.sum(), headway_peak=hp, headway_mid=hm,
                     W_mean=(s.lam_per_h * s.W_min).sum() / s.lam_per_h.sum(),
                     L_mean_6_22=s[s.hour.between(6, 21)].L.mean(), L_max=s.L.max(),
                     peak_hour=int(s.loc[s.L.idxmax(), "hour"]),
                     person_hours_day=s.L.sum(), person_hours_day_halfh=s.L_half.sum(),
                     P_empty_mid=float(np.exp(-s[s.hour.between(10, 14)].L).mean())))
summ = pd.DataFrame(summ)
pd.set_option("display.width", 220)
print("\nReal-stop occupancy summary (weekday, summers 2024+2025):")
print(summ.round(2).to_string(index=False))
summ.to_csv(T.D / "T09_stop_summary.csv", index=False)
x.to_csv(T.D / "T09_occupancy_hourly.csv", index=False)

# Compare the real hourly SHAPE with the synthetic one in scenario.py
sys.path.insert(0, str(T.S.parent / "himcm_b"))
import scenario as SC
for sid in order:
    s = x[x.stop_id == sid].sort_values("hour")
    sh = (s.lam_per_h / s.lam_per_h.sum()).values
    print(f"  {sid}: share 7-9h {sh[7:10].sum():.2f}  15-18h {sh[15:19].sum():.2f}  "
          f"22-5h {np.r_[sh[22:], sh[:6]].sum():.3f} | scenario.py shape: "
          f"{SC.HOURLY_SHAPE[7:10].sum():.2f} {SC.HOURLY_SHAPE[15:19].sum():.2f} "
          f"{np.r_[SC.HOURLY_SHAPE[22:], SC.HOURLY_SHAPE[:6]].sum():.3f}")

# ------------------------------------------------------------ Fig 2
fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), sharex=True)
for ax, sid, c in zip(axes.flat, order, COL):
    s = x[x.stop_id == sid].sort_values("hour")
    ax.bar(s.hour, s.L, color=c, width=.8, label="L with W(h)  (our model)")
    ax.step(s.hour, s.L_half, where="mid", color=INK, lw=1.2, label="L with W = h/2  (naive)")
    r = summ[summ.stop == s.label.iloc[0]].iloc[0]
    ax.set_title(f"{s.label.iloc[0]}\n{r.boardings_day:.0f} boardings/day, midday headway "
                 f"{r.headway_mid:.0f} min", loc="left", fontsize=9.5)
    ax.grid(axis="y", color=GRID, lw=.6)
    ax.set_xlim(-.6, 23.6); ax.set_xticks(range(0, 24, 3))
for ax in axes[1]: ax.set_xlabel("Hour of day (local time)")
for ax in axes[:, 0]: ax.set_ylabel("People waiting, L (persons)")
axes[0, 0].legend(frameon=False, fontsize=8.5, loc="upper left")
fig.suptitle("Average number of people at the stop, hour by hour (Little's law L = λW)",
             x=0.01, ha="left", fontsize=11)
fig.tight_layout(); fig.savefig(F / "T09_fig2_occupancy_real_stops.png", dpi=170); plt.close(fig)

print("\nPerson-hours of waiting per weekday under alternative W(h) models:")
for k, (a, b) in T.WAIT_MODELS.items():
    xx = T.occupancy_table(a=a, b=b)
    print(f"  {k:40s}", "  ".join(f"{sid}:{xx[xx.stop_id==sid].L.sum():6.1f}" for sid in order))
xx = T.occupancy_table(cv=0.4)
print(f"  {'F&M with cv=0.4 in random branch':40s}", "  ".join(f"{sid}:{xx[xx.stop_id==sid].L.sum():6.1f}" for sid in order))
xx = T.occupancy_table()
xx["L_rti"] = xx.lam_per_h * np.maximum(xx.W_min - 2.0, 0.5 * xx.W_min) / 60   # 'almost 2 min' less with real-time info
print(f"  {'F&M minus 2 min (real-time info users)':40s}", "  ".join(f"{sid}:{xx[xx.stop_id==sid].L_rti.sum():6.1f}" for sid in order))
print(f"  {'naive h/2':40s}", "  ".join(f"{sid}:{xx[xx.stop_id==sid].L_half.sum():6.1f}" for sid in order))
print("scenario.py default (420/day, 12 min, h/2): person-hours/day =", 420 * 6 / 60)

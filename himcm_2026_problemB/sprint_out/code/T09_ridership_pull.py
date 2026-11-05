"""T09 step 2: pull hourly APC boardings for four real NYC bus stops (summers 2024+2025)
from 'MTA Bus Stop Ridership Estimates: Beginning 2024' (data.ny.gov id fvdm-uavx)
and join scheduled departures per hour (GTFS, step 1) -> hourly arrival rate and headway.

estimated_ridership is a MONTH TOTAL for each (route, direction, stop, weekday, hour):
it scales with how many of that weekday the month contains (checked in T09 memo s.2.3).
Single-month, single-stop APC estimates are noisy (one weekday-hour can jump 5x),
so we POOL six summer months (Jun-Aug 2024 and 2025) x five weekdays = 30 samples
per hour and report the spread across them.
"""
import json, urllib.request, urllib.parse, pathlib, datetime as dt
import pandas as pd
S = pathlib.Path(__file__).resolve().parents[1]; D = S / "dl_T09"

STOPS = {  # stop_id: short label (chosen in memo s.2.2: ~400 boardings/day, 3 headways + 1 busy)
    "102949": "Bx15 3 Av/E 180 St (Bronx)",
    "102445": "Bx41 Webster Av/Valentine Av (Bronx)",
    "551928": "Q67 49 Av/21 St (Queens)",
    "303317": "B41 Flatbush Av/Nostrand Av (Brooklyn)",
}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MONTHS = [(2024, 6), (2024, 7), (2024, 8), (2025, 6), (2025, 7), (2025, 8)]

def n_weekday(y, m, d):
    k, n = dt.date(y, m, 1), 0
    while k.month == m:
        n += k.strftime("%A") == d; k += dt.timedelta(days=1)
    return n

rows = []
for sid in STOPS:
    ms = ",".join(f"'{y}-{m:02d}-01T00:00:00'" for y, m in MONTHS)
    q = {"$where": f"month in ({ms}) AND stop_id='{sid}'", "$limit": "50000"}
    url = "https://data.ny.gov/resource/fvdm-uavx.json?" + urllib.parse.urlencode(q)
    rows += json.load(urllib.request.urlopen(url, timeout=120))
r = pd.DataFrame(rows)
r.to_csv(D / "mta_4stops_summer_raw.csv", index=False)
r["estimated_ridership"] = pd.to_numeric(r.estimated_ridership).fillna(0)
r["hour"] = r.hour.astype(int)
r = r[r.weekday.isin(DAYS)].copy()
r["ym"] = r.month.str.slice(0, 7)
r["ndays"] = [n_weekday(int(a[:4]), int(a[5:7]), d) for a, d in zip(r.ym, r.weekday)]
r["per_day"] = r.estimated_ridership / r.ndays
# complete grid so that a missing record counts as zero boardings in that sample
full = pd.MultiIndex.from_product([r.stop_id.unique(), r.ym.unique(), DAYS, range(24)],
                                  names=["stop_id", "ym", "weekday", "hour"])
samp = r.groupby(["stop_id", "ym", "weekday", "hour"]).per_day.sum().reindex(full, fill_value=0)
routes = r.groupby("stop_id").route_id.first()
daily = samp.groupby(["stop_id", "ym", "weekday"]).sum()
print("daily boardings, spread across the 30 (month x weekday) samples:")
print(daily.groupby("stop_id").describe()[["mean", "std", "min", "max"]].round(0))
lam = samp.groupby(["stop_id", "hour"]).agg(["mean", "std"]).reset_index() \
          .rename(columns={"mean": "lam_per_h", "std": "lam_sd"})
lam["route_id"] = lam.stop_id.map(routes)

g = pd.read_csv(D / "gtfs_trips_per_hour.csv", dtype={"stop_id": str})
g = g[g.stop_id.isin(STOPS)]
x = lam.merge(g, on=["stop_id", "route_id", "hour"], how="outer").fillna({"lam_per_h": 0, "trips": 0})
x["headway_min"] = 60.0 / x.trips.where(x.trips > 0)
x["label"] = x.stop_id.map(STOPS)
x.sort_values(["stop_id", "route_id", "hour"]).to_csv(D / "stops_hourly_lambda_headway.csv", index=False)
print(x.groupby("label").agg(boardings_per_day=("lam_per_h", "sum"), buses_per_day=("trips", "sum")))

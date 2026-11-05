"""T09 step 1: scheduled bus departures per (stop, route, hour) on one weekday,
from MTA New York City bus GTFS feeds (schedule valid Oct-Dec 2026).

Output: dl_T09/gtfs_trips_per_hour.csv  (stop_id, route_id, hour, trips)
        dl_T09/gtfs_stops.csv           (stop_id, stop_name, lat, lon)
"""
import pandas as pd, pathlib
S = pathlib.Path(__file__).resolve().parents[1]
G = S / "dl_T09" / "gtfs"
DATE, DOW = 20261014, "wednesday"          # a normal Wednesday (no holiday)

out, stops = [], []
for feed in ["b", "bx", "m", "q", "si", "busco"]:
    d = G / f"{feed}_x"
    cal = pd.read_csv(d / "calendar.txt")
    act = set(cal[(cal[DOW] == 1) & (cal.start_date <= DATE) & (cal.end_date >= DATE)].service_id)
    cd = pd.read_csv(d / "calendar_dates.txt")
    cd = cd[cd.date == DATE]
    act |= set(cd[cd.exception_type == 1].service_id)
    act -= set(cd[cd.exception_type == 2].service_id)
    tr = pd.read_csv(d / "trips.txt", usecols=["route_id", "service_id", "trip_id"])
    tr = tr[tr.service_id.isin(act)]
    st = pd.read_csv(d / "stop_times.txt", usecols=["trip_id", "departure_time", "stop_id", "pickup_type"],
                     dtype={"stop_id": str})
    st = st[st.trip_id.isin(tr.trip_id) & (st.pickup_type.fillna(0) != 1)]
    st = st.merge(tr[["trip_id", "route_id"]], on="trip_id")
    st["hour"] = st.departure_time.str.slice(0, 2).astype(int) % 24
    g = st.groupby(["stop_id", "route_id", "hour"]).size().rename("trips").reset_index()
    out.append(g)
    s = pd.read_csv(d / "stops.txt", dtype={"stop_id": str})
    stops.append(s[["stop_id", "stop_name", "stop_lat", "stop_lon"]])
    print(feed, len(act), "services;", len(tr), "trips;", len(g), "stop-route-hours")

pd.concat(out).groupby(["stop_id", "route_id", "hour"]).trips.sum().reset_index() \
  .to_csv(S / "dl_T09" / "gtfs_trips_per_hour.csv", index=False)
pd.concat(stops).drop_duplicates("stop_id").to_csv(S / "dl_T09" / "gtfs_stops.csv", index=False)

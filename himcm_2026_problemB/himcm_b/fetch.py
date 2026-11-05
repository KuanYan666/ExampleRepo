"""Pull one summer of hourly weather per city from Open-Meteo archive."""
import json, urllib.request, pathlib, sys
import pandas as pd

CITIES = {
    "Phoenix":   dict(lat=33.45,  lon=-112.07, tz="America/Phoenix",  s="2025-06-01", e="2025-09-15"),
    "LasVegas":  dict(lat=36.17,  lon=-115.14, tz="America/Los_Angeles", s="2025-06-01", e="2025-09-15"),
    "Houston":   dict(lat=29.76,  lon=-95.37,  tz="America/Chicago",  s="2025-06-01", e="2025-09-15"),
    "Singapore": dict(lat=1.35,   lon=103.82,  tz="Asia/Singapore",   s="2025-06-01", e="2025-09-15"),
    "Shanghai":  dict(lat=31.23,  lon=121.47,  tz="Asia/Shanghai",    s="2025-06-01", e="2025-09-15"),
    "Seville":   dict(lat=37.39,  lon=-5.98,   tz="Europe/Madrid",    s="2025-06-01", e="2025-09-15"),
}
VARS = ("temperature_2m,relative_humidity_2m,wet_bulb_temperature_2m,wind_speed_10m,"
        "direct_radiation,diffuse_radiation,shortwave_radiation,apparent_temperature")

out = pathlib.Path(__file__).parent / "data"
out.mkdir(exist_ok=True)

for name, c in CITIES.items():
    f = out / f"{name}.csv"
    if f.exists():
        print(f"{name}: cached"); continue
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={c['lat']}&longitude={c['lon']}"
           f"&start_date={c['s']}&end_date={c['e']}&hourly={VARS}&timezone={c['tz']}")
    import time
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                j = json.load(r)
            break
        except Exception as ex:
            wait = 20 * (attempt + 1)
            print(f"  {name}: {ex}; retry in {wait}s")
            time.sleep(wait)
    else:
        print(f"  {name}: FAILED"); continue
    df = pd.DataFrame(j["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df["wind_speed_10m"] = df["wind_speed_10m"] / 3.6          # km/h -> m/s
    df.to_csv(f, index=False)
    print(f"{name}: {len(df)} hours, Tmax={df.temperature_2m.max():.1f}C")

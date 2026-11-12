#!/usr/bin/env python3
"""Build the compact browser datasets for the Divvy story.

Reads the combined Divvy trip CSV (Oct 2025 - Sep 2026) and writes JSON to ../data/.
The source CSV is never modified. Requires: pandas, numpy, matplotlib.

    python pipeline/build_data.py [--csv PATH]

Definitions
-----------
* Trips under 1 minute or over 24 hours are removed.
* Timestamps are local Chicago wall-clock time, as published by Divvy.
* A "weekday" trip is assigned by the weekday of its own timestamp: departures by start
  time, arrivals by end time.
* Stations are merged into physical locations: legacy name variants are collapsed
  (see base_name) and names within MERGE_M metres of each other are treated as one place.
* dep        = trips starting at a location (any trip with a recorded start station)
  depPaired  = trips starting at a location AND ending at a recorded station
  arrPaired  = the same paired trips, counted at the end location
  Net flow = arrPaired - depPaired, so every trip counted has both ends observed.
* Hourly values are average trips per day (x100, rounded). The denominator is the number
  of real clock hours in the window, so the two daylight-saving days are handled exactly.
"""
import argparse
import gzip
import json
import re
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parent.parent
WINDOW_START = pd.Timestamp("2025-10-01")
WINDOW_END = pd.Timestamp("2026-10-01")  # exclusive
LOOP = (41.8819, -87.6278)  # State & Madison
CORE_KM = 3.0
MERGE_M = 15
AM, PM = (7, 9), (16, 18)  # inclusive start hours: 7:00-9:59 and 16:00-18:59
SCALE = 100
FLIP_MIN_TRIPS = 100
# Zoomed "central city" view for the story map: (lat min, lat max, lng min, lng max).
FOCUS_BOX = (41.78, 42.00, -87.74, -87.57)
COMMUNITY_URL = "https://data.cityofchicago.org/resource/igwz-8jzy.json?$limit=100"
COLS = ["ride_id", "started_at", "ended_at", "start_station_name", "end_station_name",
        "start_lat", "start_lng", "end_lat", "end_lng"]


def load_trips(csv):
    d = pd.read_csv(csv, usecols=COLS, parse_dates=["started_at", "ended_at"])
    raw = len(d)
    assert d.ride_id.is_unique, "duplicate ride_id values"
    minutes = (d.ended_at - d.started_at).dt.total_seconds() / 60
    d = d[(minutes >= 1) & (minutes <= 1440)].drop(columns="ride_id").reset_index(drop=True)
    assert d.started_at.between(WINDOW_START, WINDOW_END, inclusive="left").all()
    return d, raw


def base_name(n):
    s = re.sub(r"^\[Archived\]\s*", "", n)
    s = re.sub(r"\s*\((?:Temp|temp)\)\s*", "", s)
    s = re.sub(r"\s+(Overflow )?Corral$", "", s)
    s = re.sub(r"\*+$", "", s).strip()
    s = re.sub(r"\s+\d$", "", s)
    return re.sub(r"\s+", " ", s)


def build_locations(d):
    """Add integer location ids S (start) and E (end); -1 means no recorded station."""
    names = pd.unique(pd.concat([d.start_station_name, d.end_station_name]).dropna())
    base = {n: base_name(n) for n in names}
    d["s"] = d.start_station_name.map(base)
    d["e"] = d.end_station_name.map(base)

    def endpoints(col, lat, lng):
        return d[[col, lat, lng]].set_axis(["n", "la", "lo"], axis=1)

    ends = pd.concat([endpoints("s", "start_lat", "start_lng"),
                      endpoints("e", "end_lat", "end_lng")]).dropna(subset=["n"])
    c = ends.groupby("n").agg(la=("la", "median"), lo=("lo", "median"),
                              trips=("la", "size")).reset_index()

    parent = list(range(len(c)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    la, lo = c.la.to_numpy(), c.lo.to_numpy()
    for i in range(len(c)):
        dist = np.hypot((la - la[i]) * 111000, (lo - lo[i]) * 82500)
        for j in np.where((dist < MERGE_M) & (np.arange(len(c)) > i))[0]:
            parent[find(j)] = find(i)
    c["group"] = [find(i) for i in range(len(c))]
    label = c.sort_values("trips", ascending=False).drop_duplicates("group").set_index("group").n
    to_label = dict(zip(c.n, c.group.map(label)))
    d["sl"] = d.s.map(to_label)
    d["el"] = d.e.map(to_label)

    pts = pd.concat([endpoints("sl", "start_lat", "start_lng"),
                     endpoints("el", "end_lat", "end_lng")]).dropna(subset=["n"])
    loc = pts.groupby("n").agg(lat=("la", "median"), lng=("lo", "median"),
                               trips=("la", "size")).sort_values("trips", ascending=False)
    loc["id"] = np.arange(len(loc))
    d["S"] = d.sl.map(loc.id).fillna(-1).astype(np.int64)
    d["E"] = d.el.map(loc.id).fillna(-1).astype(np.int64)

    raw_counts = pd.concat([d.start_station_name, d.end_station_name]).dropna().value_counts()
    crosswalk = pd.DataFrame({"raw_name": raw_counts.index, "trip_ends": raw_counts.values})
    crosswalk["location"] = crosswalk.raw_name.map(base).map(to_label)
    crosswalk["location_id"] = crosswalk.location.map(loc.id)
    return d, loc.reset_index().rename(columns={"n": "name"}), crosswalk


def fetch_community_areas(cache):
    if cache.exists() and cache.stat().st_size > 100_000:
        return json.loads(cache.read_text())
    for attempt in range(8):
        try:
            with urllib.request.urlopen(COMMUNITY_URL, timeout=90) as r:
                raw = r.read()
            if len(raw) > 100_000:
                cache.write_bytes(raw)
                return json.loads(raw)
        except OSError:
            pass
        time.sleep(8)
    raise RuntimeError("Could not download Chicago community area boundaries")


def polygons(feature):
    g = feature["the_geom"]
    return g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]


def rdp(pts, eps):
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        seg = pts[a + 1:b]
        d = pts[b] - pts[a]
        length = np.hypot(*d)
        if length == 0:
            dist = np.hypot(*(seg - pts[a]).T)
        else:
            dist = np.abs(d[0] * (seg[:, 1] - pts[a][1]) - d[1] * (seg[:, 0] - pts[a][0])) / length
        i = int(dist.argmax())
        if dist[i] > eps:
            k = a + 1 + i
            keep[k] = True
            stack += [(a, k), (k, b)]
    return pts[keep]


def build_geo(areas, eps=0.0003):
    features = []
    for f in areas:
        multi = []
        for poly in polygons(f):
            rings = []
            for ring in poly:
                s = rdp(np.array(ring, float), eps)
                if len(s) >= 4:
                    rings.append(np.round(s, 4).tolist())
                elif not rings:
                    break
            if rings:
                multi.append(rings)
        features.append({"type": "Feature", "properties": {"name": f["community"].title()},
                         "geometry": {"type": "MultiPolygon", "coordinates": multi}})
    return {"type": "FeatureCollection", "features": features}


def assign_areas(loc, areas):
    pts = loc[["lng", "lat"]].to_numpy()
    area = np.full(len(loc), "", dtype=object)
    for f in areas:
        for poly in polygons(f):
            area[MplPath(np.array(poly[0])).contains_points(pts)] = f["community"].title()
    outside = area == ""
    area[outside & (loc.lat.to_numpy() > 42.02)] = "Evanston"
    area[area == ""] = "Outside Chicago"
    return area


def hourly_counts(ids, ts, valid, n):
    weekend = (ts.dt.dayofweek.to_numpy() >= 5).astype(np.int64)
    idx = (weekend * n + ids) * 24 + ts.dt.hour.to_numpy().astype(np.int64)
    return np.bincount(idx[valid], minlength=2 * n * 24).reshape(2, n, 24)


def clock_hours():
    """Number of real clock hours in the window, by [weekday/weekend, hour of day]."""
    hrs = pd.date_range(WINDOW_START, WINDOW_END, freq="h", tz="America/Chicago", inclusive="left")
    den = np.zeros((2, 24), int)
    np.add.at(den, ((hrs.dayofweek >= 5).astype(int), hrs.hour), 1)
    n_days = {"weekday": int((pd.date_range(WINDOW_START, WINDOW_END, inclusive="left").dayofweek < 5).sum()),
              "weekend": int((pd.date_range(WINDOW_START, WINDOW_END, inclusive="left").dayofweek >= 5).sum())}
    return den, n_days


def pearson(x, y):
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))


def tide_stats(dep_p, arr_p, which):
    """Morning vs evening net-flow relationship across stations (annual sums)."""
    def net(h0, h1):
        return (arr_p[which][:, h0:h1 + 1] - dep_p[which][:, h0:h1 + 1]).sum(axis=1)

    def vol(h0, h1):
        return (arr_p[which][:, h0:h1 + 1] + dep_p[which][:, h0:h1 + 1]).sum(axis=1)

    am, pm = net(*AM), net(*PM)
    active = (vol(*AM) > 0) | (vol(*PM) > 0)
    return am, pm, active


def write_json(path, obj):
    text = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return len(text.encode()), len(gzip.compress(text.encode(), 9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(Path.home() / "Downloads/divvy_trips_oct2025_sep2026_raw.csv"))
    args = ap.parse_args()
    out = ROOT / "data"
    (out / "audit").mkdir(parents=True, exist_ok=True)

    print("Loading trips...")
    d, raw_rows = load_trips(args.csv)
    n_clean = len(d)
    d, loc, crosswalk = build_locations(d)
    n = len(loc)
    print(f"{raw_rows:,} raw rows -> {n_clean:,} clean trips -> {n:,} locations")

    areas = fetch_community_areas(ROOT / "pipeline/cache/community_areas.json")
    loc["area"] = assign_areas(loc, areas)
    loc["kmLoop"] = np.hypot((loc.lat - LOOP[0]) * 111.0,
                             (loc.lng - LOOP[1]) * 111.0 * np.cos(np.radians(LOOP[0])))

    S, E = d.S.to_numpy(), d.E.to_numpy()
    has_s, has_e = S >= 0, E >= 0
    paired = has_s & has_e
    end_in_window = (d.ended_at < WINDOW_END).to_numpy()

    dep = hourly_counts(np.where(has_s, S, 0), d.started_at, has_s, n)
    dep_p = hourly_counts(np.where(paired, S, 0), d.started_at, paired, n)
    arr_p = hourly_counts(np.where(paired, E, 0), d.ended_at, paired & end_in_window, n)
    den, n_days = clock_hours()

    def avg(a):
        return np.rint(a / den[:, None, :] * SCALE).astype(int)

    hourly = {
        "scale": SCALE,
        "unit": "average trips per day x scale",
        "days": n_days,
        "measures": {
            "dep": "trips starting at the location (any trip with a recorded start station)",
            "depPaired": "trips starting at the location that also end at a recorded station",
            "arrPaired": "the same paired trips, counted at the end location",
        },
    }
    for k, name in enumerate(["weekday", "weekend"]):
        hourly[name] = {"dep": avg(dep)[k].tolist(), "depPaired": avg(dep_p)[k].tolist(),
                        "arrPaired": avg(arr_p)[k].tolist()}

    stats_ends = pd.concat([d.loc[has_s, "started_at"].groupby(S[has_s]).agg(["min", "max"]),
                            d.loc[has_e, "ended_at"].groupby(E[has_e]).agg(["min", "max"])])
    span = stats_ends.groupby(level=0).agg({"min": "min", "max": "max"})
    starts = np.bincount(S[has_s], minlength=n)
    ends = np.bincount(E[has_e], minlength=n)
    stations = [{
        "id": int(r.id), "name": r.name, "lat": round(float(r.lat), 5), "lng": round(float(r.lng), 5),
        "area": r.area, "kmLoop": round(float(r.kmLoop), 2),
        "starts": int(starts[r.id]), "ends": int(ends[r.id]),
        "first": span.loc[r.id, "min"].strftime("%Y-%m-%d") if r.id in span.index else None,
        "last": span.loc[r.id, "max"].strftime("%Y-%m-%d") if r.id in span.index else None,
    } for r in loc.itertuples()]

    # ---- headline statistics, recomputed from the data ----
    cnt = np.sort(starts[starts > 0])[::-1]
    k10 = int(np.ceil(len(cnt) * 0.10))
    am, pm, active = tide_stats(dep_p, arr_p, 0)
    wam, wpm, wactive = tide_stats(dep_p, arr_p, 1)
    big = (np.abs(am) >= FLIP_MIN_TRIPS) & (np.abs(pm) >= FLIP_MIN_TRIPS)
    flip = np.sign(am[big]) != np.sign(pm[big])
    core = loc.kmLoop.to_numpy() <= CORE_KM
    net_hour = (arr_p[0] - dep_p[0]) / den[0][None, :]
    stats = {
        "tide": {
            "windows": {"morning": "7:00-9:59", "evening": "16:00-18:59"},
            "stations": int(active.sum()),
            "pearson": round(pearson(am[active], pm[active]), 3),
            "spearman": round(spearman(am[active], pm[active]), 3),
            "weekendPearson": round(pearson(wam[wactive], wpm[wactive]), 3),
            "flipMinTrips": FLIP_MIN_TRIPS, "flipStations": int(big.sum()),
            "flipShare": round(float(flip.mean()), 3),
        },
        "tideCurve": {"coreKm": CORE_KM,
                      "core": np.round(net_hour[core].sum(axis=0), 1).tolist(),
                      "rest": np.round(net_hour[~core].sum(axis=0), 1).tolist()},
        "concentration": {
            "locationsWithStarts": int(len(cnt)), "top10Count": k10,
            "top10ShareOfStationStarts": round(float(cnt[:k10].sum() / cnt.sum()), 3),
            "top10ShareOfAllCleanTrips": round(float(cnt[:k10].sum() / n_clean), 3),
            "locationsForHalf": int((np.cumsum(cnt) / cnt.sum() < 0.5).sum() + 1),
        },
    }
    in_focus = ((loc.lat >= FOCUS_BOX[0]) & (loc.lat <= FOCUS_BOX[1]) &
                (loc.lng >= FOCUS_BOX[2]) & (loc.lng <= FOCUS_BOX[3])).to_numpy()
    volume = starts + ends
    view = {"core": {"bbox": list(FOCUS_BOX), "stations": int(in_focus.sum()),
                     "tripShare": round(float(volume[in_focus].sum() / volume.sum()), 3)}}
    counts = {
        "rawTrips": raw_rows, "removedTrips": raw_rows - n_clean, "cleanTrips": n_clean,
        "withStartStation": int(has_s.sum()), "withEndStation": int(has_e.sum()),
        "withBothStations": int(paired.sum()), "locations": n,
        "rawStationNames": int(len(crosswalk)), "evanstonLocations": int((loc.area == "Evanston").sum()),
        "outsideChicagoOther": int((loc.area == "Outside Chicago").sum()),
    }

    # ---- checks against the verified analysis ----
    wk_starts = hourly_counts(np.where(has_s, S, 0), d.started_at, has_s, n)[0].sum()
    checks = []

    def check(name, got, expected, tol=0.0):
        ok = abs(got - expected) <= tol
        checks.append({"check": name, "got": got, "expected": expected, "ok": bool(ok)})

    check("raw rows", raw_rows, 6171679)
    check("clean trips", n_clean, 6007154)
    check("weekdays in window", n_days["weekday"], 261)
    check("locations", n, 1917)
    check("trips with both stations", counts["withBothStations"], 4049387)
    check("top 10% share of station starts", stats["concentration"]["top10ShareOfStationStarts"], 0.597, 0.003)
    check("tide Pearson", stats["tide"]["pearson"], -0.914, 0.004)
    check("flip share at 100 trips", stats["tide"]["flipShare"], 0.952, 0.006)
    check("outside-Chicago locations are all Evanston", counts["outsideChicagoOther"], 0)
    check("zoomed view covers about 97% of trips", view["core"]["tripShare"], 0.97, 0.01)
    check("hourly weekday departures reconcile (trips/day)",
          round(float(np.sum(hourly["weekday"]["dep"])) / SCALE, 0),
          round(wk_starts / n_days["weekday"], 0), 40)
    check("stations all have 24-hour arrays", len({len(r) for r in hourly["weekday"]["dep"]}), 1)

    methods = {
        "window": {"start": "2025-10-01", "end": "2026-09-30", "timezone": "America/Chicago (local wall-clock)"},
        "counts": counts, "stats": stats, "view": view, "checks": checks,
        "notes": {
            "cleaning": "Trips under 1 minute or over 24 hours removed.",
            "locations": f"Legacy name variants collapsed and names within {MERGE_M} m merged.",
            "netFlow": "Arrivals minus departures, paired trips only. Trip counts, not bike inventory.",
            "average": "Average per calendar day of that type, zeros included. Holidays are not removed.",
        },
    }

    sizes = {
        "stations.json": write_json(out / "stations.json", stations),
        "hourly.json": write_json(out / "hourly.json", hourly),
        "geo.json": write_json(out / "geo.json", build_geo(areas)),
        "methods.json": write_json(out / "methods.json", methods),
    }
    crosswalk.to_csv(out / "audit/station_crosswalk.csv", index=False)

    print("\nChecks")
    for c in checks:
        print(f"  {'OK ' if c['ok'] else 'FAIL'} {c['check']}: {c['got']} (expected {c['expected']})")
    print("\nOutput sizes (raw KB / gzip KB)")
    for name, (raw, gz) in sizes.items():
        print(f"  {name:14s} {raw / 1024:8.0f} {gz / 1024:8.0f}")
    print(f"  total gzip {sum(g for _, g in sizes.values()) / 1024:.0f} KB")
    if not all(c["ok"] for c in checks):
        raise SystemExit("One or more checks failed")


if __name__ == "__main__":
    main()

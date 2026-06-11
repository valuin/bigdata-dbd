import json
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests


REGION_CONFIG_PATH = Path("config/regions_jabodetabek.csv")
JAKARTA_REGION_CONFIG_PATH = Path("config/regions_jakarta.csv")
OUTPUT_PATH = Path("data/interim/nasa_weather_jabodetabek_monthly.csv")
RAW_CACHE_DIR = Path("data/interim/nasa_raw")
NASA_MONTHLY_ENDPOINT = "https://power.larc.nasa.gov/api/temporal/monthly/point"
WEATHER_PARAMETERS = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "PRECTOTCORR"]


def build_nasa_url(latitude: float, longitude: float, start: int = 2015, end: int = 2020) -> str:
    query = urlencode(
        {
            "parameters": ",".join(WEATHER_PARAMETERS),
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "start": start,
            "end": end,
            "format": "JSON",
        }
    )
    return f"{NASA_MONTHLY_ENDPOINT}?{query}"


def _cache_name(region: str, latitude: float, longitude: float) -> str:
    safe_region = region.lower().replace(" ", "_").replace("/", "_")
    return f"{safe_region}_{latitude:.4f}_{longitude:.4f}.json"


def fetch_nasa_monthly(region: pd.Series, raw_cache_dir: Path = RAW_CACHE_DIR) -> dict:
    raw_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = raw_cache_dir / _cache_name(
        str(region["region"]),
        float(region["latitude"]),
        float(region["longitude"]),
    )
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    url = build_nasa_url(float(region["latitude"]), float(region["longitude"]))
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    payload = response.json()
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def parse_nasa_monthly_response(payload: dict, region: dict | pd.Series) -> pd.DataFrame:
    parameters = payload["properties"]["parameter"]
    rows = {}

    for parameter_name in WEATHER_PARAMETERS:
        values = parameters.get(parameter_name, {})
        for nasa_key, value in values.items():
            key = str(nasa_key)
            if len(key) != 6 or not key.isdigit():
                continue
            year = int(key[:4])
            month = int(key[4:])
            if month < 1 or month > 12:
                continue
            row_key = (year, month)
            rows.setdefault(row_key, {})
            rows[row_key][parameter_name] = pd.NA if value == -999 else value

    region_map = dict(region)
    records = []
    for (year, month), values in sorted(rows.items()):
        record = {
            "region": region_map["region"],
            "region_type": region_map["region_type"],
            "province": region_map["province"],
            "latitude": float(region_map["latitude"]),
            "longitude": float(region_map["longitude"]),
            "year": year,
            "month": month,
            "date_month": f"{year:04d}-{month:02d}-01",
        }
        record.update(values)
        record["weather_source"] = "NASA_POWER"
        records.append(record)

    frame = pd.DataFrame(records)
    for parameter_name in WEATHER_PARAMETERS:
        frame[parameter_name] = pd.to_numeric(frame[parameter_name], errors="coerce")
    return frame


def add_weather_lags(weather: pd.DataFrame) -> pd.DataFrame:
    lagged = weather.sort_values(["region", "year", "month"]).copy()
    grouped = lagged.groupby("region", sort=False)
    lagged["rainfall_lag_1"] = grouped["PRECTOTCORR"].shift(1)
    lagged["rainfall_lag_2"] = grouped["PRECTOTCORR"].shift(2)
    lagged["humidity_lag_1"] = grouped["RH2M"].shift(1)
    lagged["temperature_lag_1"] = grouped["T2M"].shift(1)
    lagged["temperature_lag_2"] = grouped["T2M"].shift(2)

    # First observed months have no prior observations in the requested window.
    # Use same-month values there so the first-stage feature table remains complete.
    fill_pairs = {
        "rainfall_lag_1": "PRECTOTCORR",
        "rainfall_lag_2": "PRECTOTCORR",
        "humidity_lag_1": "RH2M",
        "temperature_lag_1": "T2M",
        "temperature_lag_2": "T2M",
    }
    for lag_column, source_column in fill_pairs.items():
        lagged[lag_column] = lagged[lag_column].fillna(lagged[source_column])

    return lagged.reset_index(drop=True)


def collect_weather(regions: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for _, region in regions.iterrows():
        payload = fetch_nasa_monthly(region)
        frames.append(parse_nasa_monthly_response(payload, region))
    combined = pd.concat(frames, ignore_index=True)
    return add_weather_lags(combined)


def load_weather_regions() -> pd.DataFrame:
    frames = [pd.read_csv(REGION_CONFIG_PATH)]
    if JAKARTA_REGION_CONFIG_PATH.exists():
        frames.append(pd.read_csv(JAKARTA_REGION_CONFIG_PATH))
    regions = pd.concat(frames, ignore_index=True)
    return regions.drop_duplicates(subset=["region", "latitude", "longitude"]).reset_index(drop=True)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    regions = load_weather_regions()
    weather = collect_weather(regions)
    weather.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {OUTPUT_PATH} ({len(weather):,} rows)")


if __name__ == "__main__":
    main()

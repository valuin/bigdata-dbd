from pathlib import Path

import numpy as np
import pandas as pd


JAKARTA_CLEAN_PATH = Path("data/interim/jakarta_clean.csv")
WEATHER_PATH = Path("data/interim/nasa_weather_jabodetabek_monthly.csv")
REGION_CONFIG_PATH = Path("config/regions_jabodetabek.csv")
SEASONALITY_PATH = Path("data/interim/jakarta_monthly_seasonality.csv")
INTENSITY_PATH = Path("data/interim/jakarta_yearly_intensity.csv")
SYNTHETIC_OUTPUT_PATH = Path("data/processed/jabodetabek_synthetic_regions.csv")
COMBINED_OUTPUT_PATH = Path("data/processed/jabodetabek_combined_first_stage.csv")
JAKARTA_REAL_OUTPUT_PATH = Path("data/processed/jabodetabek_real_jakarta.csv")
JAKARTA_REFERENCE_POPULATION = 10_500_000
COMPLETE_YEARS = {2015, 2017, 2018, 2019, 2020}
SYNTHETIC_METHOD = "jakarta_seasonality_population_weather_poisson"
MONTH_NAMES = {
    1: "JANUARY",
    2: "FEBRUARY",
    3: "MARCH",
    4: "APRIL",
    5: "MAY",
    6: "JUNE",
    7: "JULY",
    8: "AUGUST",
    9: "SEPTEMBER",
    10: "OCTOBER",
    11: "NOVEMBER",
    12: "DECEMBER",
}


def build_jakarta_seasonality(jakarta_clean: pd.DataFrame) -> pd.DataFrame:
    complete = jakarta_clean[jakarta_clean["is_complete_year"].astype(bool)]
    monthly = (
        complete.groupby("month", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "jakarta_monthly_cases"})
    )
    monthly["monthly_share"] = monthly["jakarta_monthly_cases"] / monthly["jakarta_monthly_cases"].sum()
    monthly["month_name"] = monthly["month"].map(MONTH_NAMES)
    return monthly[["month", "month_name", "jakarta_monthly_cases", "monthly_share"]]


def build_jakarta_intensity(jakarta_clean: pd.DataFrame) -> pd.DataFrame:
    complete = jakarta_clean[jakarta_clean["year"].isin(COMPLETE_YEARS)]
    yearly = (
        complete.groupby("year", as_index=False)
        .agg(
            jakarta_total_cases=("penderita_dbd", "sum"),
            jakarta_total_deaths=("meninggal", "sum"),
        )
        .sort_values("year")
        .reset_index(drop=True)
    )
    return yearly


def _z_score(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.mean()) / std


def add_weather_multiplier(frame: pd.DataFrame) -> pd.DataFrame:
    with_multiplier = frame.copy()
    with_multiplier["rainfall_z_lag_1"] = _z_score(with_multiplier["rainfall_lag_1"])
    with_multiplier["humidity_z_lag_1"] = _z_score(with_multiplier["humidity_lag_1"])
    with_multiplier["temperature_z_lag_1"] = _z_score(with_multiplier["temperature_lag_1"])
    with_multiplier["weather_multiplier"] = (
        1
        + 0.15 * with_multiplier["rainfall_z_lag_1"]
        + 0.10 * with_multiplier["humidity_z_lag_1"]
        + 0.05 * with_multiplier["temperature_z_lag_1"]
    ).clip(lower=0.6, upper=1.6)
    return with_multiplier


def generate_synthetic_rows(
    seasonality: pd.DataFrame,
    intensity: pd.DataFrame,
    weather: pd.DataFrame,
    regions: pd.DataFrame,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    region_fields = [
        "region",
        "region_type",
        "province",
        "risk_multiplier",
        "population_placeholder",
    ]
    base = (
        weather.merge(regions[region_fields], on=["region", "region_type", "province"], how="inner")
        .merge(intensity, on="year", how="inner")
        .merge(seasonality[["month", "monthly_share"]], on="month", how="inner")
    )
    base = add_weather_multiplier(base)
    base["population"] = pd.to_numeric(base["population_placeholder"], errors="raise")
    base["population_scale"] = base["population"] / JAKARTA_REFERENCE_POPULATION
    base["expected_annual_cases"] = (
        base["jakarta_total_cases"] * base["population_scale"] * base["risk_multiplier"]
    )
    base["expected_monthly_cases"] = (
        base["expected_annual_cases"] * base["monthly_share"] * base["weather_multiplier"]
    ).clip(lower=0)
    base["penderita_dbd"] = rng.poisson(base["expected_monthly_cases"].to_numpy()).astype(int)
    base["meninggal"] = 0
    base["data_origin"] = "synthetic_jabodetabek"
    base["synthetic_method"] = SYNTHETIC_METHOD

    output_columns = [
        "region",
        "region_type",
        "province",
        "year",
        "month",
        "date_month",
        "penderita_dbd",
        "meninggal",
        "population",
        "population_scale",
        "risk_multiplier",
        "monthly_share",
        "weather_multiplier",
        "T2M",
        "T2M_MAX",
        "T2M_MIN",
        "RH2M",
        "PRECTOTCORR",
        "rainfall_lag_1",
        "rainfall_lag_2",
        "humidity_lag_1",
        "temperature_lag_1",
        "temperature_lag_2",
        "data_origin",
        "synthetic_method",
    ]
    return base[output_columns].sort_values(["region", "year", "month"]).reset_index(drop=True)


def aggregate_jakarta_to_region_month(jakarta_clean: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        jakarta_clean.groupby(["parent_region", "year", "month", "date_month", "data_origin"], as_index=False)
        .agg(
            penderita_dbd=("penderita_dbd", "sum"),
            meninggal=("meninggal", "sum"),
            is_complete_year=("is_complete_year", "all"),
        )
        .rename(columns={"parent_region": "region"})
    )
    grouped["region_type"] = np.where(grouped["region"].str.contains("KABUPATEN"), "kabupaten", "kota")
    grouped["province"] = "DKI JAKARTA"
    grouped["population"] = pd.NA
    grouped["population_scale"] = pd.NA
    grouped["risk_multiplier"] = pd.NA
    grouped["monthly_share"] = pd.NA
    grouped["weather_multiplier"] = pd.NA
    grouped["synthetic_method"] = pd.NA
    return grouped


def build_combined_dataset(jakarta_region_month: pd.DataFrame, synthetic: pd.DataFrame) -> pd.DataFrame:
    combined_columns = [
        "region",
        "region_type",
        "province",
        "year",
        "month",
        "date_month",
        "penderita_dbd",
        "meninggal",
        "population",
        "population_scale",
        "risk_multiplier",
        "monthly_share",
        "weather_multiplier",
        "T2M",
        "T2M_MAX",
        "T2M_MIN",
        "RH2M",
        "PRECTOTCORR",
        "rainfall_lag_1",
        "rainfall_lag_2",
        "humidity_lag_1",
        "temperature_lag_1",
        "temperature_lag_2",
        "data_origin",
        "synthetic_method",
        "incidence_rate_per_100k",
    ]
    jakarta = jakarta_region_month.copy()
    synthetic = synthetic.copy()
    for frame in [jakarta, synthetic]:
        for column in combined_columns:
            if column not in frame.columns:
                frame[column] = pd.NA
    synthetic["incidence_rate_per_100k"] = synthetic["penderita_dbd"] / synthetic["population"] * 100000
    combined = pd.concat([jakarta[combined_columns], synthetic[combined_columns]], ignore_index=True)
    return combined.sort_values(["data_origin", "region", "year", "month"]).reset_index(drop=True)


def main() -> None:
    SYNTHETIC_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEASONALITY_PATH.parent.mkdir(parents=True, exist_ok=True)

    jakarta_clean = pd.read_csv(JAKARTA_CLEAN_PATH, parse_dates=["date_month"])
    weather = pd.read_csv(WEATHER_PATH)
    regions = pd.read_csv(REGION_CONFIG_PATH)

    seasonality = build_jakarta_seasonality(jakarta_clean)
    intensity = build_jakarta_intensity(jakarta_clean)
    seasonality.to_csv(SEASONALITY_PATH, index=False)
    intensity.to_csv(INTENSITY_PATH, index=False)

    synthetic = generate_synthetic_rows(seasonality, intensity, weather, regions)
    synthetic.to_csv(SYNTHETIC_OUTPUT_PATH, index=False)

    jakarta_region_month = aggregate_jakarta_to_region_month(jakarta_clean)
    jakarta_region_month.to_csv(JAKARTA_REAL_OUTPUT_PATH, index=False)
    combined = build_combined_dataset(jakarta_region_month, synthetic)
    combined.to_csv(COMBINED_OUTPUT_PATH, index=False)

    print(f"Wrote {SEASONALITY_PATH} ({len(seasonality):,} rows)")
    print(f"Wrote {INTENSITY_PATH} ({len(intensity):,} rows)")
    print(f"Wrote {SYNTHETIC_OUTPUT_PATH} ({len(synthetic):,} rows)")
    print(f"Wrote {JAKARTA_REAL_OUTPUT_PATH} ({len(jakarta_region_month):,} rows)")
    print(f"Wrote {COMBINED_OUTPUT_PATH} ({len(combined):,} rows)")


if __name__ == "__main__":
    main()

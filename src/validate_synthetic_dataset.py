from pathlib import Path

import pandas as pd


JAKARTA_CLEAN_PATH = Path("data/interim/jakarta_clean.csv")
BANDUNG_CLEAN_PATH = Path("data/interim/bandung_clean.csv")
SYNTHETIC_PATH = Path("data/processed/jabodetabek_synthetic_regions.csv")
COMBINED_PATH = Path("data/processed/jabodetabek_combined_first_stage.csv")
UNDERSTANDING_REPORT_PATH = Path("data/reports/data_understanding_summary.md")
VALIDATION_REPORT_PATH = Path("data/reports/synthetic_data_validation.md")
JAKARTA_REGION_PREFIXES = ("JAKARTA", "KABUPATEN KEPULAUAN SERIBU")


def _markdown_table(frame: pd.DataFrame, index: bool = False) -> str:
    if frame.empty:
        return "_No rows._"
    return frame.to_markdown(index=index)


def write_data_understanding_report(jakarta: pd.DataFrame, bandung: pd.DataFrame) -> None:
    complete_jakarta = jakarta[jakarta["is_complete_year"].astype(bool)]
    yearly = (
        jakarta.groupby("year")
        .agg(
            months_available=("month", "nunique"),
            rows=("month", "size"),
            dbd_cases=("penderita_dbd", "sum"),
            deaths=("meninggal", "sum"),
        )
        .reset_index()
    )
    city_totals = (
        jakarta.groupby("parent_region", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"parent_region": "city", "penderita_dbd": "dbd_cases"})
        .sort_values("dbd_cases", ascending=False)
    )
    top_kecamatan = (
        jakarta.groupby("region", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"region": "kecamatan", "penderita_dbd": "dbd_cases"})
        .sort_values("dbd_cases", ascending=False)
        .head(10)
    )
    monthly_share = (
        complete_jakarta.groupby("month", as_index=False)["penderita_dbd"].sum()
        .rename(columns={"penderita_dbd": "jakarta_monthly_cases"})
    )
    monthly_share["share_of_complete_year_cases"] = (
        monthly_share["jakarta_monthly_cases"] / monthly_share["jakarta_monthly_cases"].sum()
    ).round(4)
    bandung_yearly = (
        bandung.groupby("year", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "dbd_cases"})
    )
    bandung_gender = (
        bandung.groupby("jenis_kelamin", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "dbd_cases"})
    )
    missing_jakarta = jakarta.isna().sum().reset_index(name="missing").rename(columns={"index": "column"})
    missing_bandung = bandung.isna().sum().reset_index(name="missing").rename(columns={"index": "column"})

    lines = [
        "# Data Understanding Summary",
        "",
        "## Scope",
        "",
        "This first-stage dataset uses Jakarta monthly DBD surveillance data as the real base. Bandung is cleaned as an annual reference dataset only and is not merged into the Jabodetabek modeling table because its granularity differs.",
        "",
        "## Dataset Shapes",
        "",
        f"- Jakarta clean rows: {len(jakarta):,}",
        f"- Jakarta clean columns: {len(jakarta.columns):,}",
        f"- Bandung clean rows: {len(bandung):,}",
        f"- Bandung clean columns: {len(bandung.columns):,}",
        "",
        "## Missing Values - Jakarta",
        "",
        _markdown_table(missing_jakarta),
        "",
        "## Missing Values - Bandung",
        "",
        _markdown_table(missing_bandung),
        "",
        "## Jakarta Yearly Totals",
        "",
        _markdown_table(yearly),
        "",
        "## Jakarta City-Level Totals",
        "",
        _markdown_table(city_totals),
        "",
        "## Jakarta Top 10 Kecamatan by DBD Cases",
        "",
        _markdown_table(top_kecamatan),
        "",
        "## Jakarta Monthly Seasonal Share",
        "",
        "Computed only from complete years: 2015, 2017, 2018, 2019, and 2020. Year 2016 is retained in the clean data but excluded from seasonality estimation because only January and February are available.",
        "",
        _markdown_table(monthly_share),
        "",
        "## Bandung Yearly Totals",
        "",
        _markdown_table(bandung_yearly),
        "",
        "## Bandung Gender Split",
        "",
        _markdown_table(bandung_gender),
        "",
    ]
    UNDERSTANDING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNDERSTANDING_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def validate_combined_dataset(combined: pd.DataFrame, synthetic: pd.DataFrame) -> list[str]:
    issues = []
    if (combined["penderita_dbd"] < 0).any():
        issues.append("Negative DBD case counts found.")
    required = ["year", "month", "region", "penderita_dbd"]
    missing_required = combined[required].isna().sum()
    for column, count in missing_required.items():
        if count:
            issues.append(f"Missing required column values: {column} has {count} missing rows.")
    if not combined["month"].between(1, 12).all():
        issues.append("Month values outside 1-12 found.")
    synthetic_jakarta = synthetic["region"].str.startswith(JAKARTA_REGION_PREFIXES).any()
    if synthetic_jakarta:
        issues.append("Synthetic rows include Jakarta regions.")
    real_origin_values = combined.loc[combined["data_origin"] == "real_jakarta", "data_origin"].unique().tolist()
    if real_origin_values != ["real_jakarta"]:
        issues.append("Real Jakarta rows do not consistently keep data_origin=real_jakarta.")
    synthetic_origin_values = synthetic["data_origin"].unique().tolist()
    if synthetic_origin_values != ["synthetic_jabodetabek"]:
        issues.append("Synthetic rows do not consistently keep data_origin=synthetic_jabodetabek.")
    if (synthetic["year"] == 2016).any():
        issues.append("Synthetic generation includes incomplete Jakarta year 2016.")
    weather_columns = [
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
    ]
    weather_missing = combined[weather_columns].isna().sum()
    for column, count in weather_missing.items():
        if count:
            issues.append(f"Combined weather feature {column} has {count} missing values.")
    return issues


def write_validation_report(combined: pd.DataFrame, synthetic: pd.DataFrame, issues: list[str]) -> None:
    row_count_origin = combined["data_origin"].value_counts().rename_axis("data_origin").reset_index(name="rows")
    row_count_region = combined["region"].value_counts().rename_axis("region").reset_index(name="rows")
    totals_region_year = (
        combined.groupby(["region", "year"], as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "dbd_cases"})
    )
    real_monthly = (
        combined[combined["data_origin"] == "real_jakarta"]
        .groupby("month", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "real_jakarta_cases"})
    )
    synthetic_monthly = (
        synthetic.groupby("month", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "synthetic_cases"})
    )
    seasonal_compare = real_monthly.merge(synthetic_monthly, on="month", how="outer").fillna(0)
    seasonal_compare["real_jakarta_share"] = (
        seasonal_compare["real_jakarta_cases"] / seasonal_compare["real_jakarta_cases"].sum()
    ).round(4)
    seasonal_compare["synthetic_share"] = (
        seasonal_compare["synthetic_cases"] / seasonal_compare["synthetic_cases"].sum()
    ).round(4)
    weather_columns = [
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
        "weather_multiplier",
    ]
    weather_summary = synthetic[weather_columns].describe().T.reset_index().rename(columns={"index": "feature"})
    missing_values = combined.isna().sum().reset_index(name="missing").rename(columns={"index": "column"})
    region_totals = (
        synthetic.groupby("region", as_index=False)["penderita_dbd"]
        .sum()
        .rename(columns={"penderita_dbd": "synthetic_cases"})
    )
    q1 = region_totals["synthetic_cases"].quantile(0.25)
    q3 = region_totals["synthetic_cases"].quantile(0.75)
    iqr = q3 - q1
    suspicious_regions = region_totals[
        (region_totals["synthetic_cases"] < q1 - 1.5 * iqr)
        | (region_totals["synthetic_cases"] > q3 + 1.5 * iqr)
    ]
    monthly_region = synthetic.groupby(["region", "year", "month"], as_index=False)["penderita_dbd"].sum()
    outlier_threshold = monthly_region["penderita_dbd"].quantile(0.99)
    outlier_months = monthly_region[monthly_region["penderita_dbd"] >= outlier_threshold].sort_values(
        "penderita_dbd",
        ascending=False,
    )
    issue_lines = issues if issues else ["No blocking validation issues found."]

    lines = [
        "# Synthetic Dataset Validation",
        "",
        "## Validation Issues",
        "",
        *[f"- {issue}" for issue in issue_lines],
        "",
        "## Row Count by Data Origin",
        "",
        _markdown_table(row_count_origin),
        "",
        "## Row Count by Region",
        "",
        _markdown_table(row_count_region),
        "",
        "## Case Totals by Region and Year",
        "",
        _markdown_table(totals_region_year),
        "",
        "## Monthly Seasonal Comparison",
        "",
        _markdown_table(seasonal_compare),
        "",
        "## Weather Feature Summary",
        "",
        _markdown_table(weather_summary.round(3)),
        "",
        "## Missing Values in Combined Dataset",
        "",
        "Real Jakarta rows and synthetic Jabodetabek rows are both enriched with population placeholders, NASA POWER weather, lag features, monthly seasonality, weather multipliers, method metadata, and incidence rates. Missing values here should be reviewed before modeling.",
        "",
        _markdown_table(missing_values),
        "",
        "## Suspicious Synthetic Region Totals",
        "",
        _markdown_table(suspicious_regions),
        "",
        "## Outlier Synthetic Months for Manual Review",
        "",
        _markdown_table(outlier_months),
        "",
        "## Synthetic Data Caveat",
        "",
        "Synthetic Jabodetabek rows are scenario-simulation rows generated from Jakarta seasonality, population placeholders, risk multipliers, NASA POWER weather features, and Poisson count noise. They are not official Dinkes case reports.",
        "",
    ]
    VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    jakarta = pd.read_csv(JAKARTA_CLEAN_PATH)
    bandung = pd.read_csv(BANDUNG_CLEAN_PATH)
    synthetic = pd.read_csv(SYNTHETIC_PATH)
    combined = pd.read_csv(COMBINED_PATH)

    write_data_understanding_report(jakarta, bandung)
    issues = validate_combined_dataset(combined, synthetic)
    write_validation_report(combined, synthetic, issues)
    print(f"Wrote {UNDERSTANDING_REPORT_PATH}")
    print(f"Wrote {VALIDATION_REPORT_PATH}")
    if issues:
        print("Validation issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("Validation passed with no blocking issues")


if __name__ == "__main__":
    main()

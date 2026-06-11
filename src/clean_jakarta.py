from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw/Indo Dataset_DBD_BigData - Jakarta.csv")
OUTPUT_PATH = Path("data/interim/jakarta_clean.csv")
COMPLETE_YEARS = {2015, 2017, 2018, 2019, 2020}
OUTPUT_COLUMNS = [
    "year",
    "month",
    "date_month",
    "parent_region",
    "region",
    "penderita_dbd",
    "meninggal",
    "periode_data",
    "data_origin",
    "is_complete_year",
]


def _clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.upper()


def clean_jakarta_frame(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = raw.copy()

    for column in ["tahun", "bulan", "penderita_dbd", "meninggal", "periode_data"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="raise").astype("int64")

    cleaned["parent_region"] = _clean_text(cleaned["kota_administrasi"])
    cleaned["region"] = _clean_text(cleaned["kecamatan"])
    cleaned["year"] = cleaned["tahun"]
    cleaned["month"] = cleaned["bulan"]
    cleaned["date_month"] = pd.to_datetime(
        {
            "year": cleaned["year"],
            "month": cleaned["month"],
            "day": 1,
        }
    )
    cleaned["data_origin"] = "real_jakarta"
    cleaned["is_complete_year"] = cleaned["year"].isin(COMPLETE_YEARS)

    return cleaned[OUTPUT_COLUMNS].sort_values(["year", "month", "parent_region", "region"]).reset_index(drop=True)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW_PATH)
    cleaned = clean_jakarta_frame(raw)
    cleaned.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {OUTPUT_PATH} ({len(cleaned):,} rows)")


if __name__ == "__main__":
    main()

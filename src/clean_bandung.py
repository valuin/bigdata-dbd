from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw/Indo Dataset_DBD_BigData - Bandung.csv")
OUTPUT_PATH = Path("data/interim/bandung_clean.csv")


def _clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.upper()


def clean_bandung_frame(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = raw.copy()

    cleaned["jenis_kelamin"] = (
        _clean_text(cleaned["jenis_kelamin"])
        .str.replace("LAKI LAKI", "LAKI-LAKI", regex=False)
        .str.replace("LAKI  LAKI", "LAKI-LAKI", regex=False)
    )
    cleaned["penderita_dbd"] = pd.to_numeric(cleaned["jumlah_kasus"], errors="raise").astype("int64")
    cleaned["year"] = pd.to_numeric(cleaned["tahun"], errors="raise").astype("int64")
    cleaned["kecamatan"] = _clean_text(cleaned["bps_nama_kecamatan"])
    cleaned["puskesmas"] = _clean_text(cleaned["upt_puskesmas"])
    cleaned["data_origin"] = "real_bandung_reference"

    keep_columns = [
        "kecamatan",
        "puskesmas",
        "jenis_kelamin",
        "penderita_dbd",
        "year",
        "data_origin",
    ]
    optional_columns = [
        "kode_provinsi",
        "nama_provinsi",
        "bps_kode_kabupaten_kota",
        "bps_nama_kabupaten_kota",
        "bps_kode_kecamatan",
        "kemendagri_kode_kecamatan",
        "kemendagri_nama_kecamatan",
        "satuan",
    ]
    return cleaned[[column for column in optional_columns + keep_columns if column in cleaned.columns]].reset_index(drop=True)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW_PATH)
    cleaned = clean_bandung_frame(raw)
    cleaned.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {OUTPUT_PATH} ({len(cleaned):,} rows)")


if __name__ == "__main__":
    main()

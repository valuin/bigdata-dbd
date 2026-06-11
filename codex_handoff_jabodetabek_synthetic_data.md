# Codex Handoff — Jabodetabek DBD Dataset Understanding, Collection, and Synthetic Expansion

## Goal

Build the first-stage data pipeline for a Big Data final project on **DBD risk in Jabodetabek**.

The current scope is intentionally limited to:

1. **Data understanding** of the uploaded Jakarta and Bandung datasets.
2. **Data collection** for weather and supporting regional features.
3. **Synthetic spatial expansion** from Jakarta real monthly DBD data into other Jabodetabek regions.
4. **Validation and documentation** of the generated dataset.

Do **not** build the final ML model yet. Model training comes after this dataset layer is stable.

---

## Current Input Files

Place these files under `data/raw/`:

```txt
Indo Dataset_DBD_BigData - Jakarta.csv
Indo Dataset_DBD_BigData - Bandung.csv
```

Observed file summaries:

### Jakarta dataset

```txt
Rows: 2,728
Columns:
- tahun
- bulan
- kota_administrasi
- kecamatan
- penderita_dbd
- meninggal
- periode_data
```

Important notes:

- Contains monthly DBD data for **44 kecamatan** in DKI Jakarta.
- Years available: **2015, 2016, 2017, 2018, 2019, 2020**.
- Year **2016 is incomplete**: only January and February are available.
- Complete monthly years: **2015, 2017, 2018, 2019, 2020**.
- This should be the **main real dataset**.

Observed Jakarta yearly totals:

| Year | Months Available | Rows | DBD Cases | Deaths |
|---:|---:|---:|---:|---:|
| 2015 | 12 | 528 | 5,032 | 11 |
| 2016 | 2 | 88 | 1,466 | 4 |
| 2017 | 12 | 528 | 3,362 | 1 |
| 2018 | 12 | 528 | 2,822 | 1 |
| 2019 | 12 | 528 | 8,705 | 2 |
| 2020 | 12 | 528 | 4,728 | 1 |

Observed Jakarta monthly seasonality from complete years only, excluding incomplete 2016:

| Month | Share of Annual Cases |
|---:|---:|
| 1 | 0.1043 |
| 2 | 0.1330 |
| 3 | 0.1947 |
| 4 | 0.1619 |
| 5 | 0.1497 |
| 6 | 0.0890 |
| 7 | 0.0487 |
| 8 | 0.0275 |
| 9 | 0.0179 |
| 10 | 0.0218 |
| 11 | 0.0233 |
| 12 | 0.0282 |

Interpretation:

- Jakarta DBD cases peak around **March–May**.
- This seasonal curve should be used as the first synthetic expansion pattern for other Jabodetabek areas.

Top Jakarta kecamatan by total DBD cases in the uploaded data:

| Rank | Kecamatan | Total Cases |
|---:|---|---:|
| 1 | CENGKARENG | 1,999 |
| 2 | KALIDERES | 1,859 |
| 3 | CAKUNG | 1,194 |
| 4 | DUREN SAWIT | 1,167 |
| 5 | PULO GADUNG | 870 |
| 6 | PASAR MINGGU | 853 |
| 7 | PESANGGRAHAN | 849 |
| 8 | CIPAYUNG | 845 |
| 9 | KRAMAT JATI | 825 |
| 10 | CIRACAS | 821 |

### Bandung dataset

```txt
Rows: 1,140
Columns:
- kode_provinsi
- nama_provinsi
- bps_kode_kabupaten_kota
- bps_nama_kabupaten_kota
- bps_kode_kecamatan
- bps_nama_kecamatan
- kemendagri_kode_kecamatan
- kemendagri_nama_kecamatan
- upt_puskesmas
- jenis_kelamin
- jumlah_kasus
- satuan
- tahun
```

Important notes:

- Contains annual Bandung DBD data from **2016–2024**.
- Granularity is puskesmas/kecamatan/gender/year.
- It is **not directly compatible** with the Jakarta monthly kecamatan dataset.
- Do not merge Bandung directly into the main Jabodetabek table.
- Use Bandung only as an optional external comparison or sanity check for annual DBD trends.

Observed Bandung yearly totals:

| Year | DBD Cases |
|---:|---:|
| 2016 | 3,880 |
| 2017 | 1,786 |
| 2018 | 2,826 |
| 2019 | 4,424 |
| 2020 | 2,790 |
| 2021 | 3,743 |
| 2022 | 5,205 |
| 2023 | 1,856 |
| 2024 | 6,879 |

Bandung gender split in uploaded data:

| Gender | Cases |
|---|---:|
| Laki-laki | 17,391 |
| Perempuan | 15,998 |

---

## Recommended Project Framing

Use the Jakarta dataset as the real surveillance base and generate a synthetic Jabodetabek expansion for other regions.

Recommended working title:

```txt
Prediksi Risiko DBD Jabodetabek Menggunakan Data Kasus DKI Jakarta, Data Cuaca NASA POWER, dan Augmentasi Spasial Berbasis Pola Musiman
```

Current phase title:

```txt
Data Understanding, Weather Collection, and Synthetic Spatial Augmentation for Jabodetabek DBD Risk Dataset
```

---

## Target Jabodetabek Regions

Generate synthetic DBD rows for these regions first:

```txt
KOTA BOGOR
KABUPATEN BOGOR
KOTA DEPOK
KOTA TANGERANG
KABUPATEN TANGERANG
KOTA TANGERANG SELATAN
KOTA BEKASI
KABUPATEN BEKASI
```

Keep DKI Jakarta real rows separate from synthetic Jabodetabek rows.

Required internal column:

```txt
data_origin
```

Allowed values:

```txt
real_jakarta
synthetic_jabodetabek
```

Do not remove this column. It is needed for validation and debugging.

---

## Weather Data Source Decision

Use **NASA POWER Monthly API** as the main weather source.

Reason:

- It supports monthly meteorological data.
- It returns JSON/CSV.
- It is easier to automate than BMKG Data Online.
- NASA POWER Monthly API provides analysis-ready solar and meteorological time series by year/month.
- NASA POWER meteorological parameters are based on MERRA-2 from 1981 onward.

Official docs:

```txt
https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
```

BMKG is still useful as an official Indonesian reference, but it is not ideal for bulk collection because Data Online requires account access and has a maximum climate download window of 30 days.

BMKG reference:

```txt
https://dataonline.bmkg.go.id/
```

---

## Weather Parameters to Collect

Start simple. Collect only these NASA POWER monthly parameters:

```txt
T2M          # average temperature at 2 meters
T2M_MAX      # max temperature at 2 meters
T2M_MIN      # min temperature at 2 meters
RH2M         # relative humidity at 2 meters
PRECTOTCORR  # precipitation / rainfall
```

Optional later:

```txt
WS2M         # wind speed at 2 meters
```

Do not add too many weather features in the first pass. The dataset is still small.

---

## Suggested Region Coordinates

Create a config file:

```txt
config/regions_jabodetabek.csv
```

Columns:

```txt
region,region_type,province,latitude,longitude,risk_multiplier,population_placeholder
```

Suggested starting coordinates. Replace with official centroid values later if available.

| Region | Type | Latitude | Longitude | Starting Risk Multiplier |
|---|---|---:|---:|---:|
| KOTA BOGOR | kota | -6.5971 | 106.8060 | 0.85 |
| KABUPATEN BOGOR | kabupaten | -6.5950 | 106.8166 | 0.70 |
| KOTA DEPOK | kota | -6.4025 | 106.7942 | 0.90 |
| KOTA TANGERANG | kota | -6.1783 | 106.6319 | 0.90 |
| KABUPATEN TANGERANG | kabupaten | -6.1870 | 106.4870 | 0.75 |
| KOTA TANGERANG SELATAN | kota | -6.2886 | 106.7179 | 0.85 |
| KOTA BEKASI | kota | -6.2383 | 106.9756 | 1.00 |
| KABUPATEN BEKASI | kabupaten | -6.2416 | 107.1485 | 0.80 |

The `risk_multiplier` is a temporary synthetic scaling control. It must be easy to modify.

---

## Directory Structure

Create this structure:

```txt
project-root/
  data/
    raw/
      Indo Dataset_DBD_BigData - Jakarta.csv
      Indo Dataset_DBD_BigData - Bandung.csv
    interim/
      jakarta_clean.csv
      bandung_clean.csv
      nasa_weather_jabodetabek_monthly.csv
    processed/
      jabodetabek_real_jakarta.csv
      jabodetabek_synthetic_regions.csv
      jabodetabek_combined_first_stage.csv
    reports/
      data_understanding_summary.md
      synthetic_data_validation.md
  config/
    regions_jabodetabek.csv
  notebooks/
    01_data_understanding.ipynb
  src/
    collect_weather_nasa.py
    clean_jakarta.py
    clean_bandung.py
    generate_synthetic_jabodetabek.py
    validate_synthetic_dataset.py
  README.md
  requirements.txt
```

---

## Phase 1 — Data Understanding

### Task 1.1 — Clean Jakarta dataset

Input:

```txt
data/raw/Indo Dataset_DBD_BigData - Jakarta.csv
```

Output:

```txt
data/interim/jakarta_clean.csv
```

Cleaning requirements:

- Convert `tahun`, `bulan`, `penderita_dbd`, `meninggal`, and `periode_data` to numeric.
- Standardize text columns to uppercase/trimmed strings.
- Create `date_month` as `YYYY-MM-01`.
- Create `region = kecamatan`.
- Create `parent_region = kota_administrasi`.
- Add `data_origin = real_jakarta`.
- Add `is_complete_year`:
  - `True` for 2015, 2017, 2018, 2019, 2020
  - `False` for 2016
- Do not drop 2016 permanently; keep it but exclude it from seasonality estimation.

Expected columns:

```txt
year
month
date_month
parent_region
region
penderita_dbd
meninggal
periode_data
data_origin
is_complete_year
```

### Task 1.2 — Clean Bandung dataset

Input:

```txt
data/raw/Indo Dataset_DBD_BigData - Bandung.csv
```

Output:

```txt
data/interim/bandung_clean.csv
```

Cleaning requirements:

- Normalize `jenis_kelamin`:
  - `LAKI LAKI`
  - `LAKI-LAKI`
  - should become `LAKI-LAKI`
- Convert `jumlah_kasus` and `tahun` to numeric.
- Rename columns into simpler names:
  - `bps_nama_kecamatan` → `kecamatan`
  - `upt_puskesmas` → `puskesmas`
  - `jumlah_kasus` → `penderita_dbd`
  - `tahun` → `year`
- Add `data_origin = real_bandung_reference`.

Do not merge Bandung into the main modeling dataset.

### Task 1.3 — Generate EDA summary

Output:

```txt
data/reports/data_understanding_summary.md
```

Include:

- Dataset row/column counts.
- Missing values by column.
- Jakarta yearly totals.
- Jakarta city-level totals.
- Jakarta top 10 kecamatan by DBD cases.
- Jakarta monthly seasonal share from complete years only.
- Bandung yearly totals.
- Bandung gender split.
- Clear note that Bandung is annual and not directly merged into Jakarta monthly data.

---

## Phase 2 — Weather Data Collection

### Task 2.1 — Build region config

Create:

```txt
config/regions_jabodetabek.csv
```

Include the target Jabodetabek regions and coordinates listed above.

Later, add BPS population values. For now, use a placeholder if official population data has not been collected.

### Task 2.2 — Collect NASA POWER monthly weather

Create script:

```txt
src/collect_weather_nasa.py
```

Input:

```txt
config/regions_jabodetabek.csv
```

Output:

```txt
data/interim/nasa_weather_jabodetabek_monthly.csv
```

Use period:

```txt
2015-2020
```

NASA POWER API endpoint pattern:

```txt
https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,T2M_MAX,T2M_MIN,RH2M,PRECTOTCORR&community=AG&longitude={longitude}&latitude={latitude}&start=2015&end=2020&format=JSON
```

Implementation requirements:

- One API request per region.
- Parse monthly values into long format.
- Convert NASA keys like `201501` into `year=2015`, `month=1`.
- Keep one row per `region-year-month`.
- Add `weather_source = NASA_POWER`.
- Add raw latitude/longitude used.
- Cache downloaded JSON under `data/interim/nasa_raw/` so repeated runs do not call the API again unnecessarily.

Expected output columns:

```txt
region
region_type
province
latitude
longitude
year
month
date_month
T2M
T2M_MAX
T2M_MIN
RH2M
PRECTOTCORR
weather_source
```

### Task 2.3 — Create lagged weather features

Inside the weather collection or a separate processing function, create:

```txt
rainfall_lag_1
rainfall_lag_2
humidity_lag_1
temperature_lag_1
temperature_lag_2
```

Mapping:

```txt
rainfall = PRECTOTCORR
humidity = RH2M
temperature = T2M
```

Lagging must be grouped by `region` and sorted by `year`, `month`.

---

## Phase 3 — Synthetic Jabodetabek Expansion

### Core idea

Use real Jakarta monthly DBD data to extract:

1. Seasonal pattern.
2. Yearly outbreak intensity.
3. Approximate incidence pattern.

Then generate synthetic monthly DBD cases for non-Jakarta Jabodetabek regions using:

1. Jakarta complete-year seasonality.
2. Target region population scaling.
3. Target region risk multiplier.
4. NASA POWER weather adjustment.
5. Poisson or Negative Binomial count noise.

### Important guardrail

The synthetic rows are for **dataset expansion and scenario simulation**. Keep `data_origin = synthetic_jabodetabek` in the dataset. Do not overwrite source metadata.

### Task 3.1 — Build Jakarta seasonal profile

Use only complete Jakarta years:

```txt
2015, 2017, 2018, 2019, 2020
```

Exclude 2016 from seasonal share estimation because only Jan–Feb are present.

Compute:

```txt
monthly_share = sum_cases_for_month / total_cases_all_complete_years
```

Save:

```txt
data/interim/jakarta_monthly_seasonality.csv
```

Expected columns:

```txt
month
month_name
jakarta_monthly_cases
monthly_share
```

### Task 3.2 — Build Jakarta yearly intensity profile

Compute yearly total cases from complete Jakarta years.

Save:

```txt
data/interim/jakarta_yearly_intensity.csv
```

Expected columns:

```txt
year
jakarta_total_cases
jakarta_total_deaths
```

### Task 3.3 — Generate synthetic region-month cases

Create script:

```txt
src/generate_synthetic_jabodetabek.py
```

Inputs:

```txt
data/interim/jakarta_clean.csv
data/interim/jakarta_monthly_seasonality.csv
data/interim/jakarta_yearly_intensity.csv
data/interim/nasa_weather_jabodetabek_monthly.csv
config/regions_jabodetabek.csv
```

Output:

```txt
data/processed/jabodetabek_synthetic_regions.csv
```

Base formula:

```txt
expected_annual_cases(region, year)
= jakarta_total_cases(year)
  × population_scale(region)
  × risk_multiplier(region)
```

Where:

```txt
population_scale(region)
= region_population / jakarta_reference_population
```

Use `jakarta_reference_population = 10500000` as a temporary constant unless official year-specific population is collected.

Monthly allocation:

```txt
expected_monthly_cases(region, year, month)
= expected_annual_cases(region, year)
  × monthly_share(month)
  × weather_multiplier(region, year, month)
```

Weather multiplier:

```txt
weather_multiplier
= 1
  + 0.15 × rainfall_z_lag_1
  + 0.10 × humidity_z_lag_1
  + 0.05 × temperature_z_lag_1
```

Clamp:

```txt
weather_multiplier = min(max(weather_multiplier, 0.6), 1.6)
```

Case sampling:

Start simple with Poisson:

```python
synthetic_cases = np.random.poisson(expected_monthly_cases)
```

Use a fixed random seed:

```python
np.random.seed(42)
```

Later option:

- Replace Poisson with Negative Binomial if synthetic series is too smooth.

### Required synthetic output columns

```txt
region
region_type
province
year
month
date_month
penderita_dbd
meninggal
population
population_scale
risk_multiplier
monthly_share
weather_multiplier
T2M
T2M_MAX
T2M_MIN
RH2M
PRECTOTCORR
rainfall_lag_1
rainfall_lag_2
humidity_lag_1
temperature_lag_1
temperature_lag_2
data_origin
synthetic_method
```

Set:

```txt
meninggal = 0
```

for synthetic rows unless a defensible mortality model is added. Do not generate fake death counts casually.

Set:

```txt
synthetic_method = jakarta_seasonality_population_weather_poisson
```

### Task 3.4 — Combine real Jakarta + synthetic Jabodetabek

Create output:

```txt
data/processed/jabodetabek_combined_first_stage.csv
```

For Jakarta real rows:

- Aggregate to city-level or keep kecamatan-level, but do not mix incompatible granularity silently.

Recommended first-stage choice:

```txt
Keep Jakarta at kota_administrasi level for compatibility with synthetic city/kabupaten rows.
```

That means aggregate Jakarta monthly data into:

```txt
JAKARTA BARAT
JAKARTA SELATAN
JAKARTA PUSAT
JAKARTA UTARA
JAKARTA TIMUR
KABUPATEN KEPULAUAN SERIBU
```

Then append synthetic rows for:

```txt
KOTA BOGOR
KABUPATEN BOGOR
KOTA DEPOK
KOTA TANGERANG
KABUPATEN TANGERANG
KOTA TANGERANG SELATAN
KOTA BEKASI
KABUPATEN BEKASI
```

The combined dataset should have one granularity:

```txt
region-month
```

---

## Phase 4 — Validation

Create script:

```txt
src/validate_synthetic_dataset.py
```

Create report:

```txt
data/reports/synthetic_data_validation.md
```

Validation checks:

1. No negative cases.
2. No missing `year`, `month`, `region`, `penderita_dbd`.
3. All `month` values are 1–12.
4. Synthetic rows exist only for non-Jakarta regions.
5. Real rows keep `data_origin = real_jakarta`.
6. Synthetic rows keep `data_origin = synthetic_jabodetabek`.
7. Synthetic monthly distribution broadly follows Jakarta seasonality.
8. 2016 is either excluded from synthetic generation or clearly marked incomplete.
9. Weather columns have no missing values after join.
10. Outlier months are listed for manual review.

Validation report should include:

- Row count by `data_origin`.
- Row count by region.
- Case totals by region/year.
- Monthly seasonal plot/table for real Jakarta vs synthetic Jabodetabek.
- Weather feature summary.
- Any missing values.
- Any regions with suspiciously high or low generated totals.

---

## Feature Selection for Later Modeling

Do not model yet, but prepare these features:

```txt
year
month
region
region_type
population
population_scale
penderita_dbd
incidence_rate_per_100k
T2M
T2M_MAX
T2M_MIN
RH2M
PRECTOTCORR
rainfall_lag_1
rainfall_lag_2
humidity_lag_1
temperature_lag_1
temperature_lag_2
cases_lag_1
cases_lag_2
```

Create `incidence_rate_per_100k`:

```txt
incidence_rate_per_100k = penderita_dbd / population × 100000
```

Create `risk_label` later, after reviewing incidence distribution.

Do not hardcode arbitrary risk labels before EDA.

---

## Suggested `requirements.txt`

```txt
pandas
numpy
requests
python-dotenv
matplotlib
scikit-learn
```

Optional:

```txt
seaborn
statsmodels
```

Keep the first pass simple. Avoid heavy synthetic data libraries such as CTGAN/SDV unless explicitly requested later.

---

## Suggested Commands

```bash
python src/clean_jakarta.py
python src/clean_bandung.py
python src/collect_weather_nasa.py
python src/generate_synthetic_jabodetabek.py
python src/validate_synthetic_dataset.py
```

Expected final first-stage outputs:

```txt
data/interim/jakarta_clean.csv
data/interim/bandung_clean.csv
data/interim/nasa_weather_jabodetabek_monthly.csv
data/interim/jakarta_monthly_seasonality.csv
data/interim/jakarta_yearly_intensity.csv
data/processed/jabodetabek_synthetic_regions.csv
data/processed/jabodetabek_combined_first_stage.csv
data/reports/data_understanding_summary.md
data/reports/synthetic_data_validation.md
```

---

## Acceptance Criteria

The task is complete when:

1. The Jakarta and Bandung raw datasets are cleaned into `data/interim/`.
2. A clear data understanding report exists.
3. NASA POWER monthly weather data is collected for all target Jabodetabek regions from 2015–2020.
4. Weather lag features are generated.
5. Synthetic monthly DBD rows are generated for non-Jakarta Jabodetabek regions.
6. Real and synthetic rows are combined into one first-stage dataset.
7. The dataset includes `data_origin` and `synthetic_method` metadata.
8. A validation report exists and flags any questionable values.
9. No ML model is trained yet.

---

## Out of Scope for This Phase

Do not do these yet:

```txt
- Final machine learning model training
- Hyperparameter tuning
- Dashboard development
- Streamlit app
- CTGAN/SDV synthetic generation
- Deep learning model
- Paper/report writing beyond data understanding and validation
```

---

## Notes for Final Presentation Later

Keep the wording careful:

```txt
Data utama berasal dari data kasus DBD DKI Jakarta yang dikombinasikan dengan data cuaca bulanan NASA POWER. Untuk memperluas cakupan analisis ke wilayah Jabodetabek, dilakukan augmentasi spasial berbasis pola musiman Jakarta, skala populasi, dan penyesuaian cuaca. Tahap ini digunakan untuk membentuk dataset awal dan eksplorasi risiko wilayah sebelum pemodelan prediktif dilakukan.
```

Avoid claiming that synthetic rows are official Dinkes data.


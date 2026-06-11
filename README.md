# Jabodetabek DBD First-Stage Dataset

This project builds the first-stage dataset layer for a Big Data final project on DBD risk in Jabodetabek.

The current scope is data understanding, weather collection, synthetic spatial expansion, and validation. It intentionally does not train a machine learning model yet.

## Pipeline

```bash
uv run python src/clean_jakarta.py
uv run python src/clean_bandung.py
uv run python src/collect_weather_nasa.py
uv run python src/generate_synthetic_jabodetabek.py
uv run python src/validate_synthetic_dataset.py
```

## Important Outputs

- `data/interim/jakarta_clean.csv`
- `data/interim/bandung_clean.csv`
- `data/interim/nasa_weather_jabodetabek_monthly.csv`
- `data/interim/jakarta_monthly_seasonality.csv`
- `data/interim/jakarta_yearly_intensity.csv`
- `data/processed/jabodetabek_real_jakarta.csv`
- `data/processed/jabodetabek_synthetic_regions.csv`
- `data/processed/jabodetabek_combined_first_stage.csv`
- `data/reports/data_understanding_summary.md`
- `data/reports/synthetic_data_validation.md`

## Final Dataset

The main dataset for the next analysis stage is:

```txt
data/processed/jabodetabek_combined_first_stage.csv
```

It is a region-month table with real Jakarta observations and synthetic
non-Jakarta Jabodetabek rows. The target variable for later modeling is
`penderita_dbd`, and the normalized comparison metric is
`incidence_rate_per_100k`.

## Feature Dictionary and Expected Relationships

These relationships are analytical expectations for DBD risk exploration, not
proof of causality. The dataset is designed so EDA and later modeling can test
whether the patterns hold.

| Feature | Meaning | Role for DBD risk goal | Expected relationship | Source / rationale |
|---|---|---|---|---|
| `region` | Kota/kabupaten or Jakarta administrative city. | Spatial unit for comparing DBD burden across Jabodetabek. | Regions with denser population, stronger Jakarta-like seasonality, or wetter conditions may show higher case counts. | [S1], [S4] |
| `region_type` | `kota` or `kabupaten`. | Helps compare urban versus wider district areas. | Kota areas may have higher reported density and faster transmission signals; kabupaten values may be more spread out. | [S4], [S5] |
| `province` | Province name. | Keeps Jakarta, Banten, and West Java grouping visible. | Useful for grouping regional patterns, not a direct biological risk factor. | [S1] |
| `year` | Observation year. | Captures annual outbreak intensity and long-run variation. | High-outbreak years should raise cases across many months and regions. | [S1], [S6] |
| `month` | Observation month number. | Captures DBD seasonality. | Jakarta data peaks around March-May, so early-year months are expected to correlate positively with cases. | [S1], [S6], [S7] |
| `date_month` | First day of the observation month. | Time index for plotting and time-series features. | Same meaning as `year` plus `month`; useful for ordering and visualization. | [S1], [S2] |
| `penderita_dbd` | DBD case count. | Main outcome/target for later modeling. | Should increase with population exposure, seasonal share, suitable weather, and outbreak intensity. | [S1], [S4] |
| `meninggal` | Death count. | Severity/context indicator for real Jakarta rows. | Not modeled synthetically in this phase; high deaths may coincide with high cases but are sparse. | [S1], [S4] |
| `population` | Population placeholder for the region. | Converts raw case counts into comparable incidence. | Larger population tends to increase raw cases even if risk rate is the same. | [S4], [S8] |
| `population_scale` | Region population divided by Jakarta reference population. | Scales expected synthetic annual cases by exposed population size. | Positively related to synthetic case counts by construction. | [S8] |
| `risk_multiplier` | Editable regional synthetic risk control. | Allows scenario adjustment while official non-Jakarta DBD data is unavailable. | Positively related to synthetic case counts by construction. | [S8] |
| `monthly_share` | Jakarta monthly seasonality share from complete years. | Transfers Jakarta's observed seasonal DBD curve to region-month rows. | Higher shares should align with higher expected cases, especially March-May. | [S1], [S6], [S8] |
| `weather_multiplier` | Combined weather adjustment from lagged rainfall, humidity, and temperature z-scores. | Encodes weather suitability for mosquito breeding/transmission in synthetic generation and real-row feature comparison. | Higher values should generally align with higher weather-supported DBD risk. | [S4], [S6], [S7], [S8] |
| `T2M` | Monthly average temperature at 2 meters from NASA POWER. | Represents thermal conditions affecting mosquito lifecycle and virus transmission. | Moderate warm temperatures may support risk; extreme values are not separately modeled yet. | [S2], [S3], [S4], [S6] |
| `T2M_MAX` | Monthly maximum temperature at 2 meters. | Captures heat exposure beyond the monthly average. | Can help identify months where heat differs from average temperature. | [S2], [S3], [S6] |
| `T2M_MIN` | Monthly minimum temperature at 2 meters. | Captures cooler nighttime/baseline conditions. | May matter because sustained warm minimums can support vector survival. | [S2], [S3], [S6] |
| `RH2M` | Monthly relative humidity at 2 meters. | Represents moisture conditions relevant to mosquito survival. | Higher humidity is expected to correlate positively with risk, especially with rainfall. | [S2], [S3], [S4], [S6], [S7] |
| `PRECTOTCORR` | Monthly precipitation/rainfall from NASA POWER. | Represents water availability for mosquito breeding sites. | Rainfall can increase risk after a delay, though excessive rain can sometimes wash out breeding sites. | [S2], [S3], [S5], [S6], [S7] |
| `rainfall_lag_1` | Previous month's rainfall. | Captures delayed breeding-to-case timing. | Expected positive relationship with current cases. | [S6], [S7], [S8] |
| `rainfall_lag_2` | Rainfall from two months before. | Captures longer delayed weather effects. | May correlate with cases when mosquito lifecycle and reporting delays extend beyond one month. | [S6], [S7], [S8] |
| `humidity_lag_1` | Previous month's humidity. | Captures delayed survival/transmission conditions. | Expected positive relationship with current cases. | [S6], [S7], [S8] |
| `temperature_lag_1` | Previous month's average temperature. | Captures delayed temperature effect. | Expected to support risk when temperature is in a suitable range. | [S4], [S6], [S7], [S8] |
| `temperature_lag_2` | Average temperature from two months before. | Captures longer delayed temperature effect. | Useful for testing whether weather leads cases by more than one month. | [S6], [S7], [S8] |
| `data_origin` | `real_jakarta` or `synthetic_jabodetabek`. | Keeps provenance explicit for validation and honest reporting. | Should be used as a grouping/control feature, not as a biological risk factor. | [S1], [S8] |
| `synthetic_method` | Generation method or `not_synthetic_real_observed`. | Documents whether a row is observed or simulated. | Protects interpretation: synthetic rows are scenario data, not official reports. | [S8] |
| `incidence_rate_per_100k` | Cases divided by population times 100,000. | Main normalized risk comparison across unequal population sizes. | Better for regional risk comparison than raw case counts. | [S4], [S8] |

## Source Key

- [S1] Uploaded project data: `data/raw/Indo Dataset_DBD_BigData - Jakarta.csv`
  and `data/raw/Indo Dataset_DBD_BigData - Bandung.csv`.
- [S2] [NASA POWER Monthly and Annual API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/):
  source for monthly point weather collection, JSON output, year-month
  parameters, and MERRA-2 meteorological data.
- [S3] [NASA POWER Parameter Dictionary](https://power.larc.nasa.gov/docs/tutorials/parameters/):
  source for POWER parameter naming, units, descriptions, and availability.
- [S4] [WHO Dengue and severe dengue fact sheet](https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue):
  source for dengue transmission, urbanization, population movement, rainfall,
  humidity, and temperature risk framing.
- [S5] [CDC: How Dengue Spreads](https://www.cdc.gov/dengue/transmission/index.html):
  source for Aedes mosquito transmission and water-holding container breeding
  context.
- [S6] [The association between dengue case and climate: a systematic review and meta-analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC9767811/):
  source for climate variables and lagged relationships with dengue incidence.
- [S7] [Role of climatic factors in the incidence of dengue in Port Sudan City, Sudan](https://www.emro.who.int/emhj-volume-25-2019/volume-25-issue-12/role-of-climatic-factors-in-the-incidence-of-dengue-in-port-sudan-city-sudan.html):
  source for lagged temperature, humidity, and precipitation relationships in a
  monthly dengue incidence setting.
- [S8] Project methodology: `codex_handoff_jabodetabek_synthetic_data.md`,
  `config/regions_jabodetabek.csv`, `config/regions_jakarta.csv`, and the
  scripts in `src/`.

## How the Features Relate to Each Other

- `year`, `month`, and `date_month` define the time axis. `month` connects each
  row to Jakarta's seasonal pattern through `monthly_share`.
- `region`, `region_type`, and `province` define the spatial axis.
  `population`, `population_scale`, and `risk_multiplier` describe how large or
  risky each spatial unit is assumed to be.
- `penderita_dbd` is the raw case burden. `incidence_rate_per_100k` normalizes
  that burden so small and large regions can be compared fairly.
- `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, and `PRECTOTCORR` describe same-month
  weather. The lag features describe prior weather that may influence current
  DBD cases after mosquito breeding and reporting delays.
- `weather_multiplier` summarizes lagged rainfall, humidity, and temperature
  into one weather-suitability adjustment. It is useful for scenario generation,
  while the individual weather columns remain available for EDA and modeling.
- `data_origin` and `synthetic_method` must stay in the dataset so analysis can
  separate observed Jakarta evidence from synthetic Jabodetabek expansion.

## Expected Analysis Path

1. Start with `penderita_dbd` and `incidence_rate_per_100k` by region and month.
2. Compare seasonal peaks using `month` and `monthly_share`.
3. Check whether rainfall and humidity lag features rise before higher DBD
   months.
4. Compare raw cases against population-normalized incidence so large regions do
   not dominate the interpretation only because they have more residents.
5. Keep charts split or colored by `data_origin` to avoid presenting synthetic
   rows as official DBD surveillance data.

## Notes

Jakarta rows are real uploaded DBD surveillance data. Synthetic Jabodetabek rows are scenario-simulation rows generated from Jakarta seasonality, population placeholders, risk multipliers, NASA POWER weather features, and Poisson count noise. They are not official Dinkes case reports.

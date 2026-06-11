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

## Notes

Jakarta rows are real uploaded DBD surveillance data. Synthetic Jabodetabek rows are scenario-simulation rows generated from Jakarta seasonality, population placeholders, risk multipliers, NASA POWER weather features, and Poisson count noise. They are not official Dinkes case reports.

import unittest

import pandas as pd


class CleaningContractsTest(unittest.TestCase):
    def test_clean_jakarta_normalizes_schema_and_complete_year_flag(self):
        from src.clean_jakarta import clean_jakarta_frame

        raw = pd.DataFrame(
            {
                "tahun": ["2016", "2017"],
                "bulan": ["2", "3"],
                "kota_administrasi": [" jakarta barat ", "Jakarta Timur"],
                "kecamatan": [" palmerah ", " cipayung "],
                "penderita_dbd": ["5", "7"],
                "meninggal": ["0", "1"],
                "periode_data": ["201602", "201703"],
            }
        )

        cleaned = clean_jakarta_frame(raw)

        self.assertEqual(
            list(cleaned.columns),
            [
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
            ],
        )
        self.assertEqual(cleaned.loc[0, "parent_region"], "JAKARTA BARAT")
        self.assertEqual(cleaned.loc[0, "region"], "PALMERAH")
        self.assertEqual(str(cleaned.loc[1, "date_month"].date()), "2017-03-01")
        self.assertFalse(bool(cleaned.loc[0, "is_complete_year"]))
        self.assertTrue(bool(cleaned.loc[1, "is_complete_year"]))
        self.assertEqual(cleaned["data_origin"].unique().tolist(), ["real_jakarta"])

    def test_clean_bandung_normalizes_gender_and_reference_origin(self):
        from src.clean_bandung import clean_bandung_frame

        raw = pd.DataFrame(
            {
                "bps_nama_kecamatan": ["Arcamanik"],
                "upt_puskesmas": ["UPT Arcamanik"],
                "jenis_kelamin": ["LAKI LAKI"],
                "jumlah_kasus": ["89"],
                "tahun": ["2016"],
            }
        )

        cleaned = clean_bandung_frame(raw)

        self.assertEqual(cleaned.loc[0, "jenis_kelamin"], "LAKI-LAKI")
        self.assertEqual(cleaned.loc[0, "kecamatan"], "ARCAMANIK")
        self.assertEqual(cleaned.loc[0, "puskesmas"], "UPT ARCAMANIK")
        self.assertEqual(cleaned.loc[0, "penderita_dbd"], 89)
        self.assertEqual(cleaned.loc[0, "data_origin"], "real_bandung_reference")


class WeatherContractsTest(unittest.TestCase):
    def test_nasa_monthly_json_becomes_region_month_rows_with_lags(self):
        from src.collect_weather_nasa import parse_nasa_monthly_response, add_weather_lags

        payload = {
            "properties": {
                "parameter": {
                    "T2M": {"201501": 27.0, "201502": 28.0, "201503": 29.0},
                    "T2M_MAX": {"201501": 31.0, "201502": 32.0, "201503": 33.0},
                    "T2M_MIN": {"201501": 24.0, "201502": 25.0, "201503": 26.0},
                    "RH2M": {"201501": 80.0, "201502": 82.0, "201503": 84.0},
                    "PRECTOTCORR": {"201501": 10.0, "201502": 20.0, "201503": 30.0},
                }
            }
        }
        region = {
            "region": "KOTA BOGOR",
            "region_type": "kota",
            "province": "JAWA BARAT",
            "latitude": -6.5971,
            "longitude": 106.806,
        }

        parsed = parse_nasa_monthly_response(payload, region)
        with_lags = add_weather_lags(parsed)

        self.assertEqual(len(with_lags), 3)
        self.assertEqual(with_lags.loc[0, "date_month"], "2015-01-01")
        self.assertEqual(with_lags.loc[2, "rainfall_lag_1"], 20.0)
        self.assertEqual(with_lags.loc[2, "rainfall_lag_2"], 10.0)
        self.assertEqual(with_lags.loc[2, "humidity_lag_1"], 82.0)
        self.assertEqual(with_lags.loc[2, "temperature_lag_2"], 27.0)
        self.assertEqual(with_lags["weather_source"].unique().tolist(), ["NASA_POWER"])


class SyntheticContractsTest(unittest.TestCase):
    def test_synthetic_generation_keeps_origin_method_and_weather_multiplier_bounds(self):
        from src.generate_synthetic_jabodetabek import generate_synthetic_rows

        seasonality = pd.DataFrame({"month": [1], "monthly_share": [1.0]})
        intensity = pd.DataFrame(
            {"year": [2015], "jakarta_total_cases": [1000], "jakarta_total_deaths": [1]}
        )
        regions = pd.DataFrame(
            {
                "region": ["KOTA BOGOR"],
                "region_type": ["kota"],
                "province": ["JAWA BARAT"],
                "latitude": [-6.5971],
                "longitude": [106.806],
                "risk_multiplier": [0.85],
                "population_placeholder": [1050000],
            }
        )
        weather = pd.DataFrame(
            {
                "region": ["KOTA BOGOR"],
                "region_type": ["kota"],
                "province": ["JAWA BARAT"],
                "latitude": [-6.5971],
                "longitude": [106.806],
                "year": [2015],
                "month": [1],
                "date_month": ["2015-01-01"],
                "T2M": [27.0],
                "T2M_MAX": [31.0],
                "T2M_MIN": [24.0],
                "RH2M": [80.0],
                "PRECTOTCORR": [20.0],
                "rainfall_lag_1": [20.0],
                "rainfall_lag_2": [10.0],
                "humidity_lag_1": [80.0],
                "temperature_lag_1": [27.0],
                "temperature_lag_2": [26.0],
            }
        )

        synthetic = generate_synthetic_rows(seasonality, intensity, weather, regions, seed=42)

        self.assertEqual(len(synthetic), 1)
        self.assertEqual(synthetic.loc[0, "data_origin"], "synthetic_jabodetabek")
        self.assertEqual(
            synthetic.loc[0, "synthetic_method"],
            "jakarta_seasonality_population_weather_poisson",
        )
        self.assertGreaterEqual(synthetic.loc[0, "weather_multiplier"], 0.6)
        self.assertLessEqual(synthetic.loc[0, "weather_multiplier"], 1.6)
        self.assertEqual(synthetic.loc[0, "meninggal"], 0)

    def test_real_jakarta_rows_are_enriched_for_combined_dataset(self):
        from src.generate_synthetic_jabodetabek import (
            aggregate_jakarta_to_region_month,
            enrich_jakarta_region_month,
        )

        jakarta_clean = pd.DataFrame(
            {
                "parent_region": ["JAKARTA BARAT", "JAKARTA BARAT"],
                "year": [2015, 2015],
                "month": [1, 1],
                "date_month": ["2015-01-01", "2015-01-01"],
                "data_origin": ["real_jakarta", "real_jakarta"],
                "penderita_dbd": [3, 7],
                "meninggal": [0, 1],
                "is_complete_year": [True, True],
            }
        )
        seasonality = pd.DataFrame({"month": [1], "monthly_share": [0.1043]})
        weather = pd.DataFrame(
            {
                "region": ["JAKARTA BARAT"],
                "region_type": ["kota"],
                "province": ["DKI JAKARTA"],
                "latitude": [-6.1683],
                "longitude": [106.7588],
                "year": [2015],
                "month": [1],
                "date_month": ["2015-01-01"],
                "T2M": [27.0],
                "T2M_MAX": [31.0],
                "T2M_MIN": [24.0],
                "RH2M": [80.0],
                "PRECTOTCORR": [20.0],
                "rainfall_lag_1": [20.0],
                "rainfall_lag_2": [18.0],
                "humidity_lag_1": [79.0],
                "temperature_lag_1": [26.0],
                "temperature_lag_2": [25.5],
            }
        )
        jakarta_regions = pd.DataFrame(
            {
                "region": ["JAKARTA BARAT"],
                "region_type": ["kota"],
                "province": ["DKI JAKARTA"],
                "risk_multiplier": [1.0],
                "population_placeholder": [2400000],
            }
        )

        aggregated = aggregate_jakarta_to_region_month(jakarta_clean)
        enriched = enrich_jakarta_region_month(aggregated, seasonality, weather, jakarta_regions)

        self.assertEqual(enriched.loc[0, "penderita_dbd"], 10)
        self.assertEqual(enriched.loc[0, "population"], 2400000)
        self.assertEqual(enriched.loc[0, "monthly_share"], 0.1043)
        self.assertEqual(enriched.loc[0, "T2M"], 27.0)
        self.assertEqual(enriched.loc[0, "data_origin"], "real_jakarta")
        self.assertEqual(enriched.loc[0, "synthetic_method"], "not_synthetic_real_observed")
        self.assertGreater(enriched.loc[0, "incidence_rate_per_100k"], 0)


if __name__ == "__main__":
    unittest.main()

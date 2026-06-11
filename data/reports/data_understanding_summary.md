# Data Understanding Summary

## Scope

This first-stage dataset uses Jakarta monthly DBD surveillance data as the real base. Bandung is cleaned as an annual reference dataset only and is not merged into the Jabodetabek modeling table because its granularity differs.

## Dataset Shapes

- Jakarta clean rows: 2,728
- Jakarta clean columns: 10
- Bandung clean rows: 1,140
- Bandung clean columns: 14

## Missing Values - Jakarta

| column           |   missing |
|:-----------------|----------:|
| year             |         0 |
| month            |         0 |
| date_month       |         0 |
| parent_region    |         0 |
| region           |         0 |
| penderita_dbd    |         0 |
| meninggal        |         0 |
| periode_data     |         0 |
| data_origin      |         0 |
| is_complete_year |         0 |

## Missing Values - Bandung

| column                    |   missing |
|:--------------------------|----------:|
| kode_provinsi             |         0 |
| nama_provinsi             |         0 |
| bps_kode_kabupaten_kota   |         0 |
| bps_nama_kabupaten_kota   |         0 |
| bps_kode_kecamatan        |         0 |
| kemendagri_kode_kecamatan |         0 |
| kemendagri_nama_kecamatan |         0 |
| satuan                    |         0 |
| kecamatan                 |         0 |
| puskesmas                 |         0 |
| jenis_kelamin             |         0 |
| penderita_dbd             |         0 |
| year                      |         0 |
| data_origin               |         0 |

## Jakarta Yearly Totals

|   year |   months_available |   rows |   dbd_cases |   deaths |
|-------:|-------------------:|-------:|------------:|---------:|
|   2015 |                 12 |    528 |        5032 |       11 |
|   2016 |                  2 |     88 |        1466 |        4 |
|   2017 |                 12 |    528 |        3362 |        1 |
|   2018 |                 12 |    528 |        2822 |        1 |
|   2019 |                 12 |    528 |        8705 |        2 |
|   2020 |                 12 |    528 |        4728 |        1 |

## Jakarta City-Level Totals

| city                       |   dbd_cases |
|:---------------------------|------------:|
| JAKARTA TIMUR              |        8306 |
| JAKARTA BARAT              |        6863 |
| JAKARTA SELATAN            |        5851 |
| JAKARTA UTARA              |        3440 |
| JAKARTA PUSAT              |        1625 |
| KABUPATEN KEPULAUAN SERIBU |          30 |

## Jakarta Top 10 Kecamatan by DBD Cases

| kecamatan    |   dbd_cases |
|:-------------|------------:|
| CENGKARENG   |        1999 |
| KALIDERES    |        1859 |
| CAKUNG       |        1194 |
| DUREN SAWIT  |        1167 |
| PULO GADUNG  |         870 |
| PASAR MINGGU |         853 |
| PESANGGRAHAN |         849 |
| CIPAYUNG     |         845 |
| KRAMAT JATI  |         825 |
| CIRACAS      |         821 |

## Jakarta Monthly Seasonal Share

Computed only from complete years: 2015, 2017, 2018, 2019, and 2020. Year 2016 is retained in the clean data but excluded from seasonality estimation because only January and February are available.

|   month |   jakarta_monthly_cases |   share_of_complete_year_cases |
|--------:|------------------------:|-------------------------------:|
|       1 |                    2572 |                         0.1043 |
|       2 |                    3278 |                         0.133  |
|       3 |                    4798 |                         0.1947 |
|       4 |                    3991 |                         0.1619 |
|       5 |                    3690 |                         0.1497 |
|       6 |                    2193 |                         0.089  |
|       7 |                    1200 |                         0.0487 |
|       8 |                     678 |                         0.0275 |
|       9 |                     441 |                         0.0179 |
|      10 |                     538 |                         0.0218 |
|      11 |                     574 |                         0.0233 |
|      12 |                     696 |                         0.0282 |

## Bandung Yearly Totals

|   year |   dbd_cases |
|-------:|------------:|
|   2016 |        3880 |
|   2017 |        1786 |
|   2018 |        2826 |
|   2019 |        4424 |
|   2020 |        2790 |
|   2021 |        3743 |
|   2022 |        5205 |
|   2023 |        1856 |
|   2024 |        6879 |

## Bandung Gender Split

| jenis_kelamin   |   dbd_cases |
|:----------------|------------:|
| LAKI-LAKI       |       17391 |
| PEREMPUAN       |       15998 |

# BDG2 attribution and modifications

The historical data are **Building Data Genome Project 2**, Clayton Miller,
Anjukan Kathirgamanathan, Balaji Picchetti et al. (2020),
[doi:10.1038/s41597-020-00712-x](https://doi.org/10.1038/s41597-020-00712-x).
The pinned upstream commit is `9b97ccbe90096aff42ed4fd6493bf7ae692d7118`.
The original [upstream license](https://github.com/buds-lab/building-data-genome-project-2/blob/9b97ccbe90096aff42ed4fd6493bf7ae692d7118/LICENSE)
is titled Attribution-ShareAlike 4.0. Retain the original terms and attribution.
Derived data/model artifacts in `artifacts/` are provided under those same
CC BY-SA 4.0 terms: <https://creativecommons.org/licenses/by-sa/4.0/>.
No endorsement by the data authors is implied.

Changes: select the same twelve electricity IDs as LASTLIGHT PR #7, extend to
the first 2,160 source-local hourly rows, use **raw** electricity instead of the
retrospectively filtered cleaned file, retain zeros, mask invalid negative or
nonfinite readings, create strictly past-only input windows, fit a small GRU
and a Ridge baseline, and calculate held-out forecasting metrics. Original
meters remain ignored by Git; source URLs, selection and byte checksums are
preserved in the versioned artifact manifest.

The source is overseas whole-building meter data. No Kyrgyzstan measurements,
critical-circuit measurements, operational forecasting approval or emergency
profile compatibility is claimed.

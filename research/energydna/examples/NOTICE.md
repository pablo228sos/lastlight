# Historical example attribution

These are observed hourly electricity readings and retrospective targets from
Building Data Genome Project 2, Clayton Miller, Anjukan Kathirgamanathan,
Balaji Picchetti et al. (2020), DOI 10.1038/s41597-020-00712-x.
Pinned source commit: `9b97ccbe90096aff42ed4fd6493bf7ae692d7118`.

The original [Attribution-ShareAlike license](https://github.com/buds-lab/building-data-genome-project-2/blob/9b97ccbe90096aff42ed4fd6493bf7ae692d7118/LICENSE)
applies. The derived examples are distributed under those CC BY-SA 4.0 terms
(https://creativecommons.org/licenses/by-sa/4.0/), without author endorsement.

Modification: select three buildings at 2016-03-20 12:00 source-local clock,
preserve the preceding 168 observations and the next recorded interval for a
retrospective demonstration. Selection was for readable examples, not a new
evaluation cohort. Source URL/subset hash/metadata are inside historical.json.
No model predictions are stored. Reproduce with
`python -m research.energydna.package_examples` after the bounded downloader.

# How to get every file

There are three zips. Download all three and unzip them into the same folder.

| File | Size | Contents |
|---|---|---|
| `HiMCM_ProblemB_handover.zip` | 16 MB | **Start here.** `HANDOVER_LOG.md` (read first), `DATA_INVENTORY.md`, all code (`himcm_b/`, `sprint_out/code/`), all research memos (`sprint_out/T*.md`), all figures, weather data, research prompts |
| `HiMCM_part2_sources_A_freezer_evidence.zip` | 48 MB | source PDFs for the freezer evidence table (T03: ACEEE, ORNL, AHRI 1200, ...) |
| `HiMCM_part2_sources_B_other.zip` | 25 MB | source PDFs and data for T04 (frost), T05, T09 (NYC ridership CSVs), T10 (comfort/WHO), T11 (ventilation) |

**Backup copy:** the same files are pushed to GitHub, repository `kuanyan666/ExampleRepo`,
branch `ccr-e93557f0-ju36u2`, folder `himcm_2026_problemB/`.

**Left out on purpose (too big, free to re-download):** the raw NYC MTA bus timetables
(GTFS, 579 MB). Get them from `https://rrgtfsfeeds.s3.amazonaws.com/gtfs_b.zip` (also `_bx`,
`_m`, `_q`, `_si`, `_busco`). The processed results T09 made from them are already in part B
(`sprint_out/dl_T09/*.csv`).

**To run the code:** install Python 3, then
`pip install numpy pandas scipy matplotlib pythermalcomfort SALib`, then run any script with
`python3 <name>.py` from inside its folder.

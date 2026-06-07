# LLM-based variable identification

This directory contains the intermediate outputs used for the LLM-assisted variable-identification procedure described in the Supplementary Information.

The procedure consisted of two stages:

1. **Stage A: relevant-description extraction**
   The model extracted document-level descriptions relevant to predefined climate and education topics from the curated source corpora. These extracted descriptions are stored as CSV files.

2. **Stage B: expert-synthesis reporting**
   The Stage A outputs were then supplied to a second LLM call under an expert-analysis prompt. The resulting reports summarised the rationale for selecting rainfall as the main climate-fluctuation indicator and for using school type and school location as household-economy proxies.

## Files

* `relevant_descriptions_climate.csv`
  Stage A extracted descriptions from the climate corpus.

* `relevant_descriptions_education.csv`
  Stage A extracted descriptions from the education corpus.

* `expert_report_climate.txt`
  Stage B expert-synthesis report for climate-variable selection.

* `expert_report_education.txt`
  Stage B expert-synthesis report for education and household-economy proxy selection.

## Notes

These files are provided to improve transparency and reproducibility. The extracted descriptions and expert reports should be interpreted as intermediate analytical material rather than as primary data.

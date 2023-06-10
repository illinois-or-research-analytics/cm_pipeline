# JSON Input Documentation
The following document will go over the different parameters for each stage as well as rules and limitations for each stage. To view a valid pipeline with all parameters included, refer to [`pipeline_template.json`](pipeline_template.json).
## Overall Parameters
The following is a general overview of the overall parameters that don't belong to a single stage but rather the entire pipeline:
```json
    "title": "cit-new-pp-output",
    "name": "cit_patents",
    "input_file": "/data3/chackoge/networks/cit_patents_cleaned.tsv",
    "output_dir": "samples/",
    "algorithm": "leiden",
    "resolution": [0.5, 0.01],
    "iterations": 2,
    "stages": ["..."]
```

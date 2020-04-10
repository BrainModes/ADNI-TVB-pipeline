Processing pipeline for multimodal imaging data from the ADNI (Alzheimer's Disease Neuroimaging Initiative) database, to be used as input to The Virtual Brain software.

## Jupyter notebook
The Jupyter notebook creates job submission scripts (assuming jobs will be submitted on an SGE cluster). These scripts call the "generic" scripts. Notebook will have to be edited for data paths.

**Note:** The pipeline assumes data is organized according to the BIDS specification. If subjects have scans from multiple visits, the longitudinal data may need to be "flattened" before executing the code in the notebook (see notebook for details).

## Single-subject scripts
The folder "generic_scripts" contains the single subject scripts. Some of these scripts are wrappers for the HCP Pipeline scripts (https://github.com/Washington-University/HCPpipelines), others contain processing commands themselves. "Generic" bash scripts may need to be modified for job submission arguments, e.g. queue name.

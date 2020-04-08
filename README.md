Processing pipeline for multimodal imaging data from the ADNI (Alzheimer's Disease Neuroimaging Initiative) database, to be used as input to The Virtual Brain software.

The Jupyter notebook creates job submission scripts (assuming jobs will be submitted on an SGE cluster). These scripts call the "generic" scripts. Some of the "generic" scripts are wrappers for the HCP Pipeline scripts (https://github.com/Washington-University/HCPpipelines), others contain processing commands themselves.

Pipeline assumes data is organized according to the BIDS specification. If subjects have scans from multiple visits, the longitudinal data may need to be "flattened" first.

# ADNI-TVB-Pipeline

###### Processing pipeline for multimodal imaging data from the ADNI (Alzheimer's Disease Neuroimaging Initiative) database, to be used as input to The Virtual Brain software.

Each "generic" script represents one part of the processing pipeline. The script "Generate_HCPipeParams_and_BatchScripts.py" parses the raw data to generate batch scripts. Each batch script calls the respective "generic" script for all subjects.

The batch scripts and generic scripts should be saved in the same remote directory. The scripts are to be run from this directory. Output/error files will be written to a directory manually specified in the "Generate_HCPipeParams_and_BatchScripts.py" script.

All software/toolboxes used must be sourced before running scripts, e.g. in the ~/.bash_profile file.

## Create job submission scripts

The script "Generate_HCPipeParams_and_BatchScripts.py" parses the dataset, and creates a batch job-submission script for each step of the pipeline.

Each script contains job submission commands for each subject for the given processing step. These commands call the "generic" scripts.

Note: The script assumes jobs will be submitted via the slurm job scheduling system.

> **Example:**  For the "FreeSurfer" step of the pipeline, the job-submission script generated by the notebook would contain a command for each subject like below:
>
> sbatch -o output_\<subID>.txt -e error_\<subID>.txt generic_freesurf.sh /path/to/resultsDir \<subID>

For some scripts, these commands take arguments specifying single-subject parameters that are required for processing.

**Required editing:** The script "Generate_HCPipeParams_and_BatchScripts.py" will have to be modified for data paths. The pipeline assumes data is organized according to the BIDS specification. If subjects have scans from multiple visits, the longitudinal data may need to be "flattened" before executing the code in the notebook (see notebook for details).

## Single-subject scripts
The folder "generic_scripts" contains the single subject scripts. Some of these scripts are wrappers for the HCP Pipeline scripts (https://github.com/Washington-University/HCPpipelines), others contain processing commands themselves.

**Required editing:** "Generic" bash scripts may need to be modified for job submission arguments, e.g. queue name.

# ADNI-TVB-Pipeline

###### Processing pipeline for multimodal imaging data from the ADNI (Alzheimer's Disease Neuroimaging Initiative) database, to be used as input to The Virtual Brain software.

Each script in the "01_processing_scripts" directory ("generic" scripts) executes one part of the image-processing pipeline.

The script "00_Generate_HCPipeParams_and_BatchScripts.py" parses the raw data (nifti, BIDS-formatted) to generate batch job-submitter scripts. Each batch script calls the respective "generic" script for all subjects.

The batch scripts and generic scripts should be saved in the same directory. The scripts are to be run from this directory. Output/error files will be written to a directory manually specified in the "00_Generate_HCPipeParams_and_BatchScripts.py" script.

All software/toolboxes used must be sourced before running scripts, e.g. in the ~/.bash_profile file.

Broad steps are outlined below.

It is helpful to check by visual inspection the output of every step of the pipeline before proceeding to the next one.

## 00_Generate_HCPipeParams_and_BatchScripts.py

The script "00_Generate_HCPipeParams_and_BatchScripts.py" parses the dataset, and creates a batch job-submission script for each step of the pipeline.

Each script contains job submission commands for each subject for the given processing step. These commands call the "generic" scripts.

Note: The script assumes jobs will be submitted via the slurm job scheduling system.

> **Example:**  For the "FreeSurfer" step of the pipeline, the job-submission script generated by the notebook would contain a command for each subject like below:
>
> ```sbatch -o output_\<subID>.txt -e error_\<subID>.txt generic02_freesurf.sh /path/to/resultsDir \<subID>```

For some scripts, these commands take arguments specifying single-subject parameters that are required for processing.

**Required editing:** The script "00_Generate_HCPipeParams_and_BatchScripts.py" will have to be modified for data paths. The pipeline assumes data is organized according to the BIDS specification. If subjects have scans from multiple visits, the longitudinal data may need to be "flattened" before executing the script. (see script for details).

## 01_processing_scripts
The folder "01_processing_scripts" contains the single subject scripts. Some of these scripts are wrappers for the HCP Pipeline scripts (https://github.com/Washington-University/HCPpipelines), others contain processing commands themselves.

**Required editing:** "generic" bash scripts may need to be modified for job submission arguments, e.g. queue name.

**Example, how to run batch scripts:** batch scripts should be run from the directory in which they exist (here: 01_processing_scripts). Run as follows: ```bash batch01_prefreesurf.sh```

## 02_after-processing_scripts
1. Rename and reorganize pipeline's final output files according to the BIDS specification, as well as in the format required by TVB.
2. Create additional files required by TVB for simulation.
3. Create MINDS v1 metadata files to describe the dataset as required by the EBRAINS Knowledge Graph. (References: https://github.com/HumanBrainProject/openMINDS, https://github.com/roopa-pai/automated_MINDSJSON-writer/blob/master/automated_MINDSJSON-writer.ipynb)

**Required editing:** 01_reorganize.py should only require the editing of a few paths at the top of the script. 03_create_MINDSv1-metadata.py may require editing throughout the script, depending on use-case (authors, phenotype data, IRIs, etc.).

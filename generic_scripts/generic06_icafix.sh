#!/bin/bash
#$ -cwd
#$ -V
#$ -l h_vmem=12G
#$ -l h_rt=04:00:00
#$ -q medium.q
#$ -P medium

# activate the R environment we need.
. /fast/work/users/pairk_c/miniconda/etc/profile.d/conda.sh
conda activate R


# Function Description
#	Get the command line options for this script
#
# Global Output Variables
#	${StudyFolder}			- Path to folder containing all subjects data in subdirectories named 
#							  for the subject id
#	${Subjlist}				- Space delimited list of subject IDs
#	${EnvironmentScript}	- Script to source to setup pipeline environment
#	${FixDir}				- Directory containing FIX
#	${RunLocal}				- Indication whether to run this processing "locally" i.e. not submit
#							  the processing to a cluster or grid


# initialize global output variables
StudyFolder=$1
Subjlist=$2
EnvironmentScript="/fast/work/groups/ag_ritter//MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
FixDir="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/FIX/fix1.065/"
RunLocal="TRUE"

# set up pipeline environment variables and software
source ${EnvironmentScript}

export FSL_FIXDIR=${FixDir}
FixScript=${HCPPIPEDIR}/ICAFIX/hcp_fix
# TrainingData="/fast/groups/ag_ritter/scratch/MR_processing/HCP_pipeline/FIX/fix1.065/training_files/Standard.RData" # the default training file, doesn't really fit our needs
# better use our own hand trained data
TrainingData="/fast/work/groups/ag_ritter/MR_processing/BerlinRestingstate/scripts/FIX_Training/BerlinRest_Training.RData"

InputFile=$3
bandpass=2000

${FixScript} ${InputFile} ${bandpass} ${TrainingData}

conda deactivate

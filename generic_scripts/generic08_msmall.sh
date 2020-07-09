#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=12G
#SBATCH --time=12:00:00
#SBATCH --partition=medium

# activate the python environment we need
. /fast/work/users/pairk_c/miniconda/etc/profile.d/conda.sh
conda activate /fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/HCP_python2.7

StudyFolder=$1 # Location of Subject folders (named by subjectID)
Subject=$2 #Space delimited list of subject IDs
EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script


# Requirements for this script
#  installed versions of: FSL (version 5.0.6)
#  environment: FSLDIR , HCPPIPEDIR , CARET7DIR

#Set up pipeline environment variables and software
source ${EnvironmentScript}

# Log the originating call
echo "$@"


########################################## INPUTS ##########################################

#Scripts called by this script do assume they run on the results of the HCP minimal preprocesing pipelines from Q2

######################################### DO WORK ##########################################

fMRINames="Restingstate"
OutfMRIName="Restingstate_msm"
HighPass="2000"
fMRIProcSTRING="_Atlas_hp2000_clean"
MSMAllTemplates="${HCPPIPEDIR}/global/templates/MSMAll"
RegName="MSMAll_InitalReg"
HighResMesh="164"
LowResMesh="32"
InRegName="MSMSulc"
MatlabMode="0" #Mode=0 compiled Matlab, Mode=1 interpreted Matlab

${HCPPIPEDIR}/MSMAll/MSMAllPipeline.sh \
  --path=${StudyFolder} \
  --subject=${Subject} \
  --fmri-names-list=${fMRINames} \
  --output-fmri-name=${OutfMRIName} \
  --high-pass=${HighPass} \
  --fmri-proc-string=${fMRIProcSTRING} \
  --msm-all-templates=${MSMAllTemplates} \
  --output-registration-name=${RegName} \
  --high-res-mesh=${HighResMesh} \
  --low-res-mesh=${LowResMesh} \
  --input-registration-name=${InRegName} \
  --matlab-run-mode=${MatlabMode}

conda deactivate

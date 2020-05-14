#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=12:00:00
#SBATCH --partition=medium

# activate the python environment we need
. /fast/work/users/pairk_c/miniconda/etc/profile.d/conda.sh
conda activate /fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/HCP_python2.7

StudyFolder=$1 # Location of Subject folders (named by subjectID)
Subject=$2
EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
FinalfMRIResolution=$3 #Needs to match what is in fMRIVolume, i.e. 2mm for 3T HCP data and 1.6mm for 7T HCP data

# Requirements for this script
#  installed versions of: FSL (version 5.0.6), FreeSurfer (version 5.3.0-HCP) , gradunwarp (HCP version 1.0.2)
#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

#Set up pipeline environment variables and software
source ${EnvironmentScript}

# Log the originating call
echo "$@"

PRINTCOM=""
#PRINTCOM="echo"

########################################## INPUTS ##########################################

#Scripts called by this script do assume they run on the outputs of the FreeSurfer Pipeline

######################################### DO WORK ##########################################


fMRIName="Restingstate"
echo "  ${fMRIName}"
LowResMesh="32" #Needs to match what is in PostFreeSurfer, 32 is on average 2mm spacing between the vertices on the midthickness
SmoothingFWHM="2" #Recommended to be roughly the grayordinates spacing, i.e 2mm on HCP data
GrayordinatesResolution="2" #Needs to match what is in PostFreeSurfer. 2mm gives the HCP standard grayordinates space with 91282 grayordinates.  Can be different from the FinalfMRIResolution (e.g. in the case of HCP 7T data at 1.6mm)
# RegName="MSMSulc" #MSMSulc is recommended, if binary is not available use FS (FreeSurfer)
RegName="MSMSulc"


${HCPPIPEDIR}/fMRISurface/GenericfMRISurfaceProcessingPipeline.sh \
      --path=$StudyFolder \
      --subject=$Subject \
      --fmriname=$fMRIName \
      --lowresmesh=$LowResMesh \
      --fmrires=$FinalfMRIResolution \
      --smoothingFWHM=$SmoothingFWHM \
      --grayordinatesres=$GrayordinatesResolution \
      --regname=$RegName

# The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...

echo "set -- --path=$StudyFolder \
--subject=$Subject \
--fmriname=$fMRIName \
--lowresmesh=$LowResMesh \
--fmrires=$FinalfMRIResolution \
--smoothingFWHM=$SmoothingFWHM \
--grayordinatesres=$GrayordinatesResolution \
--regname=$RegName"

echo ". ${EnvironmentScript}"

# deactivate the python environment
conda deactivate

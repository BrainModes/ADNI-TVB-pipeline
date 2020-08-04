#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=12G
#SBATCH --time=08:00:00
#SBATCH --partition=medium

StudyFolder=$1 #Location of Subject folders (named by subjectID)
Subject=$2 #Space delimited list of subject IDs
EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script

#Set up pipeline environment variables and software
source ${EnvironmentScript}

# Log the originating call
echo "$@"

PRINTCOM=""
#PRINTCOM="echo"

########################################## INPUTS ##########################################

#Scripts called by this script do assume they run on the results of the HCP minimal preprocesing pipelines from Q2

######################################### DO WORK ##########################################

HighResMesh="164"
LowResMesh="32"
RegName="MSMAll_InitalReg_2_d40_WRN"
DeDriftRegFiles="${HCPPIPEDIR}/global/templates/MSMAll/DeDriftingGroup.L.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii@${HCPPIPEDIR}/global/templates/MSMAll/DeDriftingGroup.R.sphere.DeDriftMSMAll.164k_fs_LR.surf.gii"
ConcatRegName="MSMAll"
Maps="sulc curvature corrThickness thickness"
MyelinMaps="MyelinMap SmoothedMyelinMap" #No _BC, this will be reapplied
rfMRINames="Restingstate" #Space delimited list or NONE
tfMRINames="NONE"
SmoothingFWHM="2" #Should equal previous grayordiantes smoothing (because we are resampling from unsmoothed native mesh timeseries
HighPass="2000"
MatlabMode="0" #Mode=0 compiled Matlab, Mode=1 interpreted Matlab

Maps=`echo "$Maps" | sed s/" "/"@"/g`
MyelinMaps=`echo "$MyelinMaps" | sed s/" "/"@"/g`
rfMRINames=`echo "$rfMRINames" | sed s/" "/"@"/g`
tfMRINames=`echo "$tfMRINames" | sed s/" "/"@"/g`

${HCPPIPEDIR}/DeDriftAndResample/DeDriftAndResamplePipeline.sh \
  --path=${StudyFolder} \
  --subject=${Subject} \
  --high-res-mesh=${HighResMesh} \
  --low-res-meshes=${LowResMesh} \
  --registration-name=${RegName} \
  --dedrift-reg-files=${DeDriftRegFiles} \
  --concat-reg-name=${ConcatRegName} \
  --maps=${Maps} \
  --myelin-maps=${MyelinMaps} \
  --rfmri-names=${rfMRINames} \
  --tfmri-names=${tfMRINames} \
  --smoothing-fwhm=${SmoothingFWHM} \
  --highpass=${HighPass} \
  --matlab-run-mode=${MatlabMode}

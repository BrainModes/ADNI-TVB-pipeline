#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=24:00:00
#SBATCH -n 4
#--export OMP_NUM_THREADS=4 # num_cores is set to 4 in FreeSurferPipeline_wo_hires_free5.3.sh
#SBATCH --partition=medium


command_line_specified_run_local="TRUE"
StudyFolder=$1 # Location of Subject folders (named by subjectID)
Subject=$2 #Space delimited list of subject IDs
EnvironmentScript="/fast/work/groups/ag_ritter//MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
# Requirements for this script
#  installed versions of: FSL (version 5.0.6), FreeSurfer (version 5.3.0-HCP), gradunwarp (HCP version 1.0.2)
#  environment: FSLDIR , FREESURFER_HOME , HCPPIPEDIR , CARET7DIR , PATH (for gradient_unwarp.py)

#Set up pipeline environment variables and software
source ${EnvironmentScript}

PRINTCOM=""
#PRINTCOM="echo"
#QUEUE="-q veryshort.q"


########################################## INPUTS ##########################################

#Scripts called by this script do assume they run on the outputs of the PreFreeSurfer Pipeline

######################################### DO WORK ##########################################


#Input Variables
SubjectID="$Subject" #FreeSurfer Subject ID Name
SubjectDIR="${StudyFolder}/${Subject}/T1w" #Location to Put FreeSurfer Subject's Folder
T1wImage="${StudyFolder}/${Subject}/T1w/T1w_acpc_dc_restore.nii.gz" #T1w FreeSurfer Input (Full Resolution)
T1wImageBrain="${StudyFolder}/${Subject}/T1w/T1w_acpc_dc_restore_brain.nii.gz" #T1w FreeSurfer Input (Full Resolution)
T2wImage="${StudyFolder}/${Subject}/T1w/T2w_acpc_dc_restore.nii.gz" #T2w FreeSurfer Input (Full Resolution)


${HCPPIPEDIR}/FreeSurfer/FreeSurferPipeline_wo_hires_free5.3.sh \
    --subject="$Subject" \
    --subjectDIR="$SubjectDIR" \
    --t1="$T1wImage" \
    --t1brain="$T1wImageBrain" \
    --t2="$T2wImage" \
    #--printcom=$PRINTCOM

echo "set -- --subject="$Subject" \
      --subjectDIR="$SubjectDIR" \
      --t1="$T1wImage" \
      --t1brain="$T1wImageBrain" \
      --t2="$T2wImage" \
      --printcom=$PRINTCOM"

echo ". ${EnvironmentScript}"

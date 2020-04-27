#!/bin/bash
#$ -cwd
#$ -V
#$ -l h_vmem=6G
#$ -l h_rt=24:00:00
#$ -q medium.q
#$ -P medium



# activate the python environment we need
. /fast/work/users/pairk_c/miniconda/etc/profile.d/conda.sh
conda activate /fast/work/groups/ag_ritter//MR_processing/HCP_pipeline/HCP_python2.7

StudyFolder=$1 # Location of Subject folders (named by subjectID)
Subject=$2                                    # Space delimited list of subject IDs
EnvironmentScript="/fast/work/groups/ag_ritter//MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
source ${EnvironmentScript} # Set up pipeline environment variables and software

# Report major script control variables to user
echo "StudyFolder: ${StudyFolder}"
echo "Subject: ${Subject}"
echo "EnvironmentScript: ${EnvironmentScript}"
command_line_specified_run_local="TRUE"
echo "Run locally: ${command_line_specified_run_local}"


T1wInputImages=$3 #T1 image
T2wInputImages=$4 #T2 image

AvgrdcSTRING=$5 # distortion correction method with fieldmap

Mag1=$6 # first Magnitude Image
Mag2=$7 # second Magnitude Image
MagnitudeInputName=$8 # concatenation done with fslmerge
if [ "$Mag1" = False ] && [ "$Mag2" = False ] ; then
	echo "4D magnitude volume already exists; no need to merge"
else
	echo "merge two 3D fieldmapping magnitude images to create a 4D magnitude image"
# The MagnitudeInputName variable should be set to a 4D magitude volume with
# two 3D timepoints
	fslmerge -t $8 $6 $7 # concatenation done with fslmerge
# The PhaseInputName variable should be set to a 3D phase difference

PhaseInputName=$9

TE=${10}
T1wSampleSpacing=${11}
T2wSampleSpacing=${12}
UnwarpDir=${13}


GradientDistortionCoeffs="NONE" # Set to NONE to skip gradient distortion correction

# set GE and Spin Echo fieldmap options to "NONE"
GEB0InputName="NONE"
SpinEchoPhaseEncodeNegative="NONE"
SpinEchoPhaseEncodePositive="NONE"
DwellTime="NONE" # DwellTime of Spin Echo fieldmap
SEUnwarpDir="NONE"
TopupConfig="NONE"


# Templates
# Hires T1w MNI template
T1wTemplate="${HCPPIPEDIR_Templates}/MNI152_T1_1mm.nii.gz"
# Hires brain extracted MNI template
T1wTemplateBrain="${HCPPIPEDIR_Templates}/MNI152_T1_1mm_brain.nii.gz"
# Lowres T1w MNI template
T1wTemplate2mm="${HCPPIPEDIR_Templates}/MNI152_T1_2mm.nii.gz"
# Hires T2w MNI Template
T2wTemplate="${HCPPIPEDIR_Templates}/MNI152_T2_1mm.nii.gz"
# Hires T2w brain extracted MNI Template
T2wTemplateBrain="${HCPPIPEDIR_Templates}/MNI152_T2_1mm_brain.nii.gz"
# Lowres T2w MNI Template
T2wTemplate2mm="${HCPPIPEDIR_Templates}/MNI152_T2_2mm.nii.gz"
# Hires MNI brain mask template
TemplateMask="${HCPPIPEDIR_Templates}/MNI152_T1_1mm_brain_mask.nii.gz"
# Lowres MNI brain mask template
Template2mmMask="${HCPPIPEDIR_Templates}/MNI152_T1_2mm_brain_mask_dil.nii.gz"
# BrainSize in mm, 150 for humans
BrainSize="150"
# FNIRT 2mm T1w Config
FNIRTConfig="${HCPPIPEDIR_Config}/T1_2_MNI152_2mm.cnf"


# If PRINTCOM is not a null or empty string variable, then
# this script and other scripts that it calls will simply
# print out the primary commands it otherwise would run.
PRINTCOM=""


${HCPPIPEDIR}/PreFreeSurfer/PreFreeSurferPipeline.sh \
			--path="$StudyFolder" \
			--subject="$Subject" \
			--t1="$T1wInputImages" \
			--t2="$T2wInputImages" \
			--t1template="$T1wTemplate" \
			--t1templatebrain="$T1wTemplateBrain" \
			--t1template2mm="$T1wTemplate2mm" \
			--t2template="$T2wTemplate" \
			--t2templatebrain="$T2wTemplateBrain" \
			--t2template2mm="$T2wTemplate2mm" \
			--templatemask="$TemplateMask" \
			--template2mmmask="$Template2mmMask" \
			--brainsize="$BrainSize" \
			--fnirtconfig="$FNIRTConfig" \
			--fmapmag="$MagnitudeInputName" \
			--fmapphase="$PhaseInputName" \
			--fmapgeneralelectric="$GEB0InputName" \
			--echodiff="$TE" \
			--SEPhaseNeg="$SpinEchoPhaseEncodeNegative" \
			--SEPhasePos="$SpinEchoPhaseEncodePositive" \
			--echospacing="$DwellTime" \
			--seunwarpdir="$SEUnwarpDir" \
			--t1samplespacing="$T1wSampleSpacing" \
			--t2samplespacing="$T2wSampleSpacing" \
			--unwarpdir="$UnwarpDir" \
			--gdcoeffs="$GradientDistortionCoeffs" \
			--avgrdcmethod="$AvgrdcSTRING" \
			--topupconfig="$TopupConfig" \
			--printcom=$PRINTCOM


# deactivate the python environment
conda deactivate

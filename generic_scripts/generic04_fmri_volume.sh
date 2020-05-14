#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=12:00:00
#SBATCH --partition=medium

# activate the python environment we need
. /fast/work/users/pairk_c/miniconda/etc/profile.d/conda.sh
conda activate /fast/work/groups/ag_ritter//MR_processing/HCP_pipeline/HCP_python2.7

StudyFolder=$1 # Location of Subject folders (named by subjectID)
Subject=$2
EnvironmentScript="/fast/work/groups/ag_ritter//MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script

#Set up pipeline environment variables and software
source ${EnvironmentScript}

# Start or launch pipeline processing for each subject
fMRIName="Restingstate"
echo "  ${fMRIName}"
UnwarpDir=$3
fMRITimeSeries=$4
fMRISBRef="NONE" #A single band reference image (SBRef) is recommended if using multiband, set to NONE if you want to use the first volume of the timeseries for motion correction
DwellTime=$5 #Echo Spacing or Dwelltime of fMRI image, set to NONE if not used. Dwelltime = 1/(BandwidthPerPixelPhaseEncode * # of phase encoding samples): DICOM field (0019,1028) = BandwidthPerPixelPhaseEncode, DICOM field (0051,100b) AcquisitionMatrixText first value (# of phase encoding samples).  On Siemens, iPAT/GRAPPA factors have already been accounted for.
DistortionCorrection=$6 # FIELDMAP, SiemensFieldMap, GeneralElectricFieldMap, or TOPUP: distortion correction is required for accurate processing
# The MagnitudeInputName variable should be set to a 4D magitude volume with two 3D timepoints
MagnitudeInputName=$7
# The PhaseInputName variable should be set to a 3D phase difference
PhaseInputName=$8
DeltaTE=$9 #2.46ms for 3T, 1.02ms for 7T, set to NONE if using TOPUP
FinalFMRIResolution=${10} #Target final resolution of fMRI data. 2mm is recommended for 3T HCP data, 1.6mm for 7T HCP data (i.e. should match acquired resolution).  Use 2.0 or 1.0 to avoid standard FSL templates

BiasCorrection="LEGACY" #NONE, LEGACY, or SEBASED: LEGACY uses the T1w bias field, SEBASED calculates bias field from spin echo images (which requires TOPUP distortion correction)
SpinEchoPhaseEncodeNegative="NONE" #For the spin echo field map volume with a negative phase encoding direction (LR in HCP data, AP in 7T HCP data), set to NONE if using regular FIELDMAP
SpinEchoPhaseEncodePositive="NONE" #For the spin echo field map volume with a positive phase encoding direction (RL in HCP data, PA in 7T HCP data), set to NONE if using regular FIELDMAP

GEB0InputName="NONE"
GradientDistortionCoeffs="NONE" # Set to NONE to skip gradient distortion correction
TopUpConfig="NONE" #Topup config if using TOPUP, set to NONE if using regular FIELDMAP

# Use mcflirt motion correction
MCType="MCFLIRT"

PRINTCOM=""
#PRINTCOM="echo"
#QUEUE="-q veryshort.q"
# Log the originating call
echo "$@"

${HCPPIPEDIR}/fMRIVolume/GenericfMRIVolumeProcessingPipeline.sh \
    --path=$StudyFolder \
    --subject=$Subject \
    --fmriname=$fMRIName \
    --fmritcs=$fMRITimeSeries \
    --fmriscout=$fMRISBRef \
    --SEPhaseNeg=$SpinEchoPhaseEncodeNegative \
    --SEPhasePos=$SpinEchoPhaseEncodePositive \
    --fmapmag=$MagnitudeInputName \
    --fmapphase=$PhaseInputName \
    --fmapgeneralelectric=$GEB0InputName \
    --echospacing=$DwellTime \
    --echodiff=$DeltaTE \
    --unwarpdir=$UnwarpDir \
    --fmrires=$FinalFMRIResolution \
    --dcmethod=$DistortionCorrection \
    --gdcoeffs=$GradientDistortionCoeffs \
    --topupconfig=$TopUpConfig \
    --printcom=$PRINTCOM \
    --biascorrection=$BiasCorrection \
    --mctype=${MCType}

# The following lines are used for interactive debugging to set the positional parameters: $1 $2 $3 ...

echo "set -- --path=$StudyFolder \
    --subject=$Subject \
    --fmriname=$fMRIName \
    --fmritcs=$fMRITimeSeries \
    --fmriscout=$fMRISBRef \
    --SEPhaseNeg=$SpinEchoPhaseEncodeNegative \
    --SEPhasePos=$SpinEchoPhaseEncodePositive \
    --fmapmag=$MagnitudeInputName \
    --fmapphase=$PhaseInputName \
    --fmapgeneralelectric=$GEB0InputName \
    --echospacing=$DwellTime \
    --echodiff=$DeltaTE \
    --unwarpdir=$UnwarpDir \
    --fmrires=$FinalFMRIResolution \
    --dcmethod=$DistortionCorrection \
    --gdcoeffs=$GradientDistortionCoeffs \
    --topupconfig=$TopUpConfig \
    --printcom=$PRINTCOM \
    --biascorrection=$BiasCorrection \
    --mctype=${MCType}"

echo ". ${EnvironmentScript}"



conda deactivate

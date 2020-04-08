#!/bin/bash 
#$ -cwd
#$ -V
#$ -l h_vmem=10G
#$ -l h_rt=03:00:00

# where to store data:
resultsDir=$1
sub=$2
results_path="${resultsDir}/${sub}/DWI_processing"
mkdir -p $results_path

# dwi denoise
dwi_raw=$3
bvec=$4
bval=$5
PE_dir=$6
dwi_raw_mif="$results_path/DWI_raw.mif"
dwi_denoised="$results_path/DWI_denoised.mif"

mrconvert -force -fslgrad $bvec $bval $dwi_raw $dwi_raw_mif

dwidenoise $dwi_raw_mif $dwi_denoised -noise $results_path/noise_map.nii.gz -force
# dwi preproc
dwi_preprocessed="$results_path/DWI_preprocessed.mif"


# with -rpe_none only does eddy current and motion correction
dwipreproc -force -rpe_none -pe_dir $PE_dir -eddy_options " --data_is_shelled " $dwi_denoised $dwi_preprocessed  

#rm $dwi_raw_mif
#rm $dwi_denoised


# dwi distortion correction
# nonlinear reg with ANTS

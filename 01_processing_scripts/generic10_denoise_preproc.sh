#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=10G
#SBATCH --time=03:00:00

# input arguments:
resultsDir=$1
sub=$2
dwi_raw=$3
bvec=$4
bval=$5
PE_dir=$6

#where to store output data:
results_path="${resultsDir}/${sub}/DWI_processing"
mkdir -p $results_path

#files to be created:
dwi_raw_mif="$results_path/DWI_raw.mif"
dwi_denoised="$results_path/DWI_denoised.mif"
dwi_degibbsed="$results_path/DWI_degibbsed.mif"
dwi_preprocessed="$results_path/DWI_preprocessed.mif"

#PROCESSING
echo "START denoise_preproc script"
date +"Date : %d/%m/%Y Time : %H.%M.%S"

# 1. use FSL gradient information to create DWI_raw.mif file
echo "use FSL gradient information to create DWI_raw.mif file"
mrconvert -force -fslgrad $bvec $bval $dwi_raw $dwi_raw_mif

# 2. dwi denoise
echo "denoising DWI scan"
dwidenoise $dwi_raw_mif $dwi_denoised -noise $results_path/noise_map.nii.gz -force

# 3. remove Gibbs ringing artifacts
#mrtrix recommends running it before dwipreproc, and after dwi_denoised
echo "remove Gibbs ringing artifacts"
mrdegibbs -force $dwi_denoised $dwi_degibbsed

# 4. dwi preproc
# with -rpe_none only does eddy current and motion correction
echo "dwipreproc"
dwipreproc -force -rpe_none -pe_dir $PE_dir -eddy_options " --data_is_shelled " $dwi_degibbsed $dwi_preprocessed

# optionally remove intermediate output files
#rm $dwi_raw_mif
#rm $dwi_denoised
#rm $dwi_degibbsed

echo "END denoise_preproc script"
date +"Date : %d/%m/%Y Time : %H.%M.%S"

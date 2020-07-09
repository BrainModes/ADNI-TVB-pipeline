#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=4G
#SBATCH --time=01:00:00
#SBATCH -n 4

resultsDir=$1
sub=$2
scratchDir=$3

# path to results of processing
results_path="${resultsDir}/${sub}/DWI_processing"

tck_file="${scratchDir}/${sub}_100M.tck"
sift_weights="$results_path/sift2_weights.txt"
weights="$results_path/connectome_weights.csv"
lengths="$results_path/connectome_lengths.csv"
diffusion_mask="$results_path/diffusion_mask_overlap2subcortical.nii.gz" # overlap voxels are assigned to the subcortical structures
diffusion_mask_2dwi="$results_path/diffusion_mask_overlap2subcortical_2dwi.nii.gz"

# register diffusion mask into DWI space
mrtransform -linear $results_path/dwi2T1w_mrtrix.txt -inverse $diffusion_mask $diffusion_mask_2dwi

# create connectome
tck2connectome -tck_weights_in $sift_weights $tck_file $diffusion_mask_2dwi $weights -nthreads 4 -force -symmetric -zero_diagonal
tck2connectome -scale_length -stat_edge mean -tck_weights_in $sift_weights $tck_file $diffusion_mask_2dwi $lengths -nthreads 4 -force -symmetric -zero_diagonal

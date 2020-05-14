#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=20G
#SBATCH --time=30:00:00
#SBATCH -n 8
#SBATCH --partition=medium

resultsDir=$1
sub=$2
scratchDir=$3

results_path="${resultsDir}/${sub}/DWI_processing"
avg_RF="${resultsDir}/average_response.txt"

# save big tck files in scratch directory
tck_file="${scratchDir}/${sub}_100M.tck"
dwi_intensity_norm="$results_path/DWI_intensity_norm.mif"
FOD="$results_path/WM_FOD_tournier.mif"
fivett_image="$results_path/5tt_image.mif"
sift_weights="$results_path/sift2_weights.txt"


dwi2fod csd $dwi_intensity_norm $avg_RF $FOD -nthreads 8 -force


# generate tracks using the FOD
tckgen $FOD $tck_file -algorithm iFOD2 -act $fivett_image -backtrack -crop_at_gmwmi -seed_dynamic $FOD -maxlength 250 -select 100000000 -cutoff 0.06 -nthreads 8 -force


# sift2
# -fd_scale_gm can assist in reducing tissue interface effects when using a single-tissue deconvolution algorithm
tcksift2 -act $fivett_image $tck_file $FOD $sift_weights -force -nthreads 8

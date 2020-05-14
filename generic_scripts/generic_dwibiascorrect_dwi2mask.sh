#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=03:00:00
#SBATCH --partition=default

resultsDir=$1
sub=$2
# path to results of processing
results_path="${resultsDir}/${sub}/DWI_processing"

dwi_preprocessed="$results_path/DWI_preprocessed.mif"
dwi_biascorrected="$results_path/${sub}_DWI_biascorrected.mif"
dwi_brainmask="$results_path/${sub}_DWI_brainmask.mif"

dwibiascorrect -ants $dwi_preprocessed $dwi_biascorrected

dwi2mask $dwi_biascorrected $dwi_brainmask

#!/bin/bash 
#!/bin/bash 
#$ -cwd
#$ -V
#$ -l h_vmem=6G
#$ -l h_rt=03:00:00

resultsDir=$1
sub=$2
# path to results of processing
results_path="${resultsDir}/${sub}/DWI_processing"

dwi_preprocessed="$results_path/DWI_preprocessed.mif"
dwi_biascorrected="$results_path/${sub}_DWI_biascorrected.mif"
dwi_brainmask="$results_path/${sub}_DWI_brainmask.mif"

dwibiascorrect -ants $dwi_preprocessed $dwi_biascorrected

dwi2mask $dwi_biascorrected $dwi_brainmask

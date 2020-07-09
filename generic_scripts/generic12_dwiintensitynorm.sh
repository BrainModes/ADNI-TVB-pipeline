#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=12G
#SBATCH --time=08:30:00
#SBATCH --partition=medium

HCP_results=$1

cd $HCP_results

mkdir dwiintensitynorm_input
mkdir dwiintensitynorm_mask
mkdir dwiintensitynorm_output

mv `find . -wholename "*/DWI_processing/*_DWI_biascorrected.mif"` dwiintensitynorm_input
mv `find . -wholename "*/DWI_processing/*_DWI_brainmask.mif"` dwiintensitynorm_mask

dwiintensitynorm dwiintensitynorm_input \
                 dwiintensitynorm_mask \
                 dwiintensitynorm_output \
                 dwiintensitynorm_output/fa_template.mif \
                 dwiintensitynorm_output/wm_mask.mif \
                 -force \

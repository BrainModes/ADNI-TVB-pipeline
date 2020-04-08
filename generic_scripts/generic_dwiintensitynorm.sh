#!/bin/bash 
#$ -cwd
#$ -V
#$ -l h_vmem=12G
#$ -l h_rt=08:30:00
#$ -q medium.q
#$ -P medium

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

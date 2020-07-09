#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=10G
#SBATCH --time=03:00:00

resultsDir=$1
sub=$2
results_path="${resultsDir}/${sub}/DWI_processing"
HCP_results="${resultsDir}/${sub}"
dwiintensitynorm_outputdir="${resultsDir}/dwiintensitynorm_output"

dwi_intensity_norm="${results_path}/DWI_intensity_norm.mif"
mv $dwiintensitynorm_outputdir/${sub}_DWI_biascorrected.mif $dwi_intensity_norm

dwi_meanb0="$results_path/DWI_meanb0.mif"
dwi_meanb0_nii="$results_path/DWI_meanb0.nii.gz"

T1="$HCP_results/T1w/T1w_acpc_dc.nii.gz"
T1_brain="$HCP_results/T1w/T1w_acpc_dc_brain.nii.gz"
aparc_aseg="$HCP_results/T1w/aparc+aseg.nii.gz"

T1_brain_2dwi="$results_path/T1w_acpc_dc_brain_2dwi.nii.gz"
aparc_aseg_2dwi="$results_path/aparc+aseg_2dwi.nii.gz"
fs_default="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/mrtrix3/share/mrtrix3/labelconvert/fs_default.txt"


# extract meanb0 image for registration
dwiextract -force $dwi_intensity_norm - -bzero | mrmath - mean $dwi_meanb0 -axis 3

# convert images to .nii for flirt
mrconvert -force $dwi_meanb0 $dwi_meanb0_nii

# flirt dwi2T1w
flirt -in $dwi_meanb0_nii -ref $T1 -dof 6 -omat $results_path/dwi2T1w.mat  -cost mutualinfo -searchcost mutualinfo

# use transformconvert to make transform.mat into a mrtrix readable file
transformconvert -force $results_path/dwi2T1w.mat $dwi_meanb0_nii $T1_brain flirt_import $results_path/dwi2T1w_mrtrix.txt

# use inverse transform to register t1 and aparcaseg onto DWI image
mrtransform -force -linear $results_path/dwi2T1w_mrtrix.txt -inverse $T1_brain $T1_brain_2dwi
mrtransform -force -interp nearest -linear $results_path/dwi2T1w_mrtrix.txt -inverse $aparc_aseg $aparc_aseg_2dwi

fivett_image="$results_path/5tt_image.mif"
nodes_mif="$results_path/nodes_aparcaseg.mif"

# generate a 5 tissue type image (cortical GM, subcortical GM, WM, CSF, pathological tissue)
5ttgen  freesurfer -lut $FREESURFER_HOME/FreeSurferColorLUT.txt -sgm_amyg_hipp $aparc_aseg_2dwi $fivett_image -force

# adjust this later to get the HCP Glasser parcellation
labelconvert $aparc_aseg_2dwi $FREESURFER_HOME/FreeSurferColorLUT.txt ${fs_default} $nodes_mif -force

# estimate response function
dwi2response tournier $dwi_intensity_norm $results_path/RF_WM_tournier.txt -voxels $results_path/RF_voxels_tournier.mif -force

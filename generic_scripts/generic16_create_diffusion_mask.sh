#!/bin/bash 
#$ -cwd
#$ -V
#$ -l h_vmem=8G
#$ -l h_rt=01:00:00

# create diffusion masks for tractography
# connectome has 180 right cortex regions + 180 left cortex regions +19 subcortical
resultDir=$1
sub=$2

# use freesurfer 6 because of mri_binarize --gm option is not available in freesurfer 5.3
export FREESURFER_HOME=/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/freesurfer_HCP/freesurfer-v6.0.0
source ${FREESURFER_HOME}/SetUpFreeSurfer.sh > /dev/null 2>&1

# Pipeline environment script
EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
#Set up pipeline environment variables and software
source ${EnvironmentScript}

#initialize some paths
HCP_results_folder="${resultsDir}/${sub}"
Diffusion_folder="${resultsDir}/${sub}/DWI_processing"
GlasserFolder="/fast/work/groups/ag_ritter/MR_processing/Glasser_et_al_2016_HCP_MMP1.0_RVVG_2/HCP_PhaseTwo/Glasser_et_al_2016_HCP_MMP1.0_StudyData/"


# map surface labels from Glasser parcellation to volume
for Hemisphere in R L; do   
    Glasser_label_gii="${GlasserFolder}/${Hemisphere}.label.gii" # used "wb_command -cifti-separate" to seperate the the CIFTI label into hemisphere wise gii label files
    white_fsLR32="${HCP_results_folder}/T1w/fsaverage_LR32k/${sub}.${Hemisphere}.white_MSMAll.32k_fs_LR.surf.gii"
    pial_fsLR32="${HCP_results_folder}/T1w/fsaverage_LR32k/${sub}.${Hemisphere}.pial_MSMAll.32k_fs_LR.surf.gii"
    T1_image="${HCP_results_folder}/T1w/T1w_acpc_dc_restore_brain.nii.gz"
    output_volume_label="${Diffusion_folder}/${Hemisphere}.cortical_volume_labels.nii.gz"

    echo "Label to volume mapping hemisphere:  $Hemisphere"
    $CARET7DIR/wb_command -label-to-volume-mapping $Glasser_label_gii $white_fsLR32 $T1_image $output_volume_label -ribbon-constrained $white_fsLR32 $pial_fsLR32
done


# change the labelling of 19 subcortical regions from freesurfer labels (8-60) to (361 - 379) (append it to the end of the connectome)
# freesurfer subcortical labels:  8 10 11 12 13 17 18 26 28 47 49 50 51 52 53 54 58 60 16 
cp $HCP_results_folder/T1w/aparc+aseg.nii.gz $Diffusion_folder/subcortical_volume_labels.nii.gz

# get only subcortical gm labels
mri_binarize.bin --i "$Diffusion_folder/subcortical_volume_labels.nii.gz" --o $Diffusion_folder/sub_gm_mask.nii.gz --subcort-gm 
fslmaths "$Diffusion_folder/subcortical_volume_labels.nii.gz" -mas $Diffusion_folder/sub_gm_mask.nii.gz "$Diffusion_folder/subcortical_volume_labels.nii.gz"

# replace labels
mri_binarize --i "$Diffusion_folder/subcortical_volume_labels.nii.gz" \
             --o "$Diffusion_folder/subcortical_volume_labels.nii.gz" \
                --replace 8 361 \
                --replace 10 362 \
                --replace 11 363 \
                --replace 12 364 \
                --replace 13 365 \
                --replace 17 366 \
                --replace 18 367 \
                --replace 26 368 \
                --replace 28 369 \
                --replace 47 370 \
                --replace 49 371 \
                --replace 50 372 \
                --replace 51 373 \
                --replace 52 374 \
                --replace 53 375 \
                --replace 54 376 \
                --replace 58 377 \
                --replace 60 378 \
                --replace 16 379 \



# add cortex left + cortex right + subcortical
fslmaths "$Diffusion_folder/R.cortical_volume_labels.nii.gz" -add "$Diffusion_folder/L.cortical_volume_labels.nii.gz" -add "$Diffusion_folder/subcortical_volume_labels.nii.gz" "$Diffusion_folder/diffusion_mask.nii.gz"

# some voxels overlap between cortex left, right and subcortical
# since they cannot clearly be assigned to one region, delete them from the mask
fslmaths "$Diffusion_folder/R.cortical_volume_labels.nii.gz" -bin "$Diffusion_folder/R.cortical_volume_labels_mask.nii.gz"
fslmaths "$Diffusion_folder/L.cortical_volume_labels.nii.gz" -bin "$Diffusion_folder/L.cortical_volume_labels_mask.nii.gz"
fslmaths "$Diffusion_folder/subcortical_volume_labels.nii.gz" -bin "$Diffusion_folder/sub_gm_mask.nii.gz"
fslmaths "$Diffusion_folder/R.cortical_volume_labels_mask.nii.gz" \
        -add "$Diffusion_folder/L.cortical_volume_labels_mask.nii.gz" \
        -add "$Diffusion_folder/sub_gm_mask.nii.gz" $Diffusion_folder/diffusion_mask_mask.nii.gz

# get overlap voxels, use inverse binarization
fslmaths $Diffusion_folder/diffusion_mask_mask.nii.gz -sub 1 -binv $Diffusion_folder/overlap_mask.nii.gz

# get diffusions masks without overlap, voxels where regions overlap are set to "0"
fslmaths "$Diffusion_folder/R.cortical_volume_labels.nii.gz" -mul $Diffusion_folder/overlap_mask.nii.gz "$Diffusion_folder/R.cortical_volume_labels_wo_overlap.nii.gz"
fslmaths "$Diffusion_folder/L.cortical_volume_labels.nii.gz" -mul $Diffusion_folder/overlap_mask.nii.gz "$Diffusion_folder/L.cortical_volume_labels_wo_overlap.nii.gz"
fslmaths "$Diffusion_folder/subcortical_volume_labels.nii.gz" -mul $Diffusion_folder/overlap_mask.nii.gz "$Diffusion_folder/subcortical_volume_labels_wo_overlap.nii.gz"

# diffusion mask with overlap voxels to zero 
fslmaths "$Diffusion_folder/R.cortical_volume_labels_wo_overlap.nii.gz" \
         -add "$Diffusion_folder/L.cortical_volume_labels_wo_overlap.nii.gz" \
         -add "$Diffusion_folder/subcortical_volume_labels_wo_overlap.nii.gz" \
         "$Diffusion_folder/diffusion_mask_overlap2zero.nii.gz"

# diffusion mask with overlap voxels belonging to subcortical
fslmaths "$Diffusion_folder/R.cortical_volume_labels_wo_overlap.nii.gz" \
         -add "$Diffusion_folder/L.cortical_volume_labels_wo_overlap.nii.gz" \
         -add "$Diffusion_folder/subcortical_volume_labels.nii.gz" \
         "$Diffusion_folder/diffusion_mask_overlap2subcortical.nii.gz"

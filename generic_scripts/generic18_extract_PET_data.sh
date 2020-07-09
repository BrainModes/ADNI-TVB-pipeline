#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=4G
#SBATCH --time=00:30:00

EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
source ${EnvironmentScript}

# use freesurfer 6 because of mri_binarize --gm option is not available in freesurfer 5.3
export FREESURFER_HOME=/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/freesurfer_HCP/freesurfer-v6.0.0
source ${FREESURFER_HOME}/SetUpFreeSurfer.sh > /dev/null 2>&1


#### input to this script
# $1 --> results directory
# $2 --> subject name
# $3 --> AV1451 PET iamge
# $4 --> AV45 PET image
# this script assumes it is running on the output of the HCP structural processing pipeline as well as generic_msm_glasser2sub.sh

#####################################
# 0. initialize some paths
#####################################
resultsDir=$1
sub=$2
echo $sub

#folder with HCP processed data
HCP_results="${resultsDir}/${sub}"
T1_image=$HCP_results"/T1w/T1w_acpc_dc.nii.gz"
native_surf=$HCP_results"/T1w/Native"

RegName="MSMAll"
LowResMesh="32"
DownsampleFolder=$HCP_results"/T1w/fsaverage_LR32k"
Brainmask="${HCP_results}/T1w/brainmask_fs.nii.gz"


# Glasser parcellation data
GlasserFolder="/fast/work/groups/ag_ritter/MR_processing/Glasser_et_al_2016_HCP_MMP1.0_RVVG_2/HCP_PhaseTwo/Glasser_et_al_2016_HCP_MMP1.0_StudyData/"


# loop over Tau and Abeta PET
for PET_modality in Tau Amyloid; do

    PET_results=$HCP_results"/PET_PVC_MG/"$PET_modality
    mkdir -p $PET_results

    if [ $PET_modality = "Tau" ] ; then
        PET_image=$3
    elif [ $PET_modality = "Amyloid" ] ; then
        PET_image=$4
    fi
    echo $PET_image

    echo "#####################################"
    echo "#####################################"
    echo "1. Register PET to T1 "
    echo "#####################################"
    echo "#####################################"
    # and warp to MNI space" ????????? --> is done with fMRI, but here is no need to....
    # use PET e.g. AV45_Co-registered,_Averaged":
    #       co-registered ... coregistration of the 4 (or 6) 5 min PET images acquiered onto the first of them
    #       Averaged ... average PET image across the 4 (or 6) images
    # for warp T1 to standard use $sub/MNINonLinear/xfms/acpc_dc2standard.nii.gz

    ${FSLDIR}/bin/flirt -interp spline -dof 6 -in  $PET_image -ref $T1_image -omat $PET_results/PET2T1w.mat \
                        -out $PET_results/PET2T1w.nii.gz -searchrx -180 180 -searchry -180 180 -searchrz -180 180 \
                        -cost mutualinfo

    ${FSLDIR}/bin/fslmaths $PET_results/PET2T1w.nii.gz -mas $Brainmask $PET_results/PET2T1w_brain.nii.gz

    echo "#####################################"
    echo "#####################################"
    echo "2. partial volume effect correction and normalize by cerebellar white matter signal"
    echo "#####################################"
    echo "#####################################"

    # using PETPVC toolbox
    #       reference: PETPVC: a toolbox for performing partial volume correction techniques in positron emission tomography BA Thomas, V Cuplov, A Bousse, A Mendes, K Thielemans, BF Hutton, K Erlandsson Physics in Medicine and Biology 61 (22), 7975. DOI
    # using Mueller Gartner PVC method, input:
    #       mask image containing gray and white matter binary images alinged in 4th dimension

    #### perform normalization
    # cerebellar white matter mask
    mri_binarize --i $HCP_results/T1w/aparc+aseg.nii.gz --o $PET_results/cereb_gm_mask.nii --match 8 47

    # get average cerebellar white matter intensity
    fslmeants -i $PET_results/PET2T1w_brain.nii.gz -m $PET_results/cereb_gm_mask.nii -o $PET_results/cereb_gm_intensity.txt
    cereb_intensity=$(cat $PET_results/cereb_gm_intensity.txt)

    # normalize PET
    fslmaths $PET_results/PET2T1w_brain.nii.gz -div $cereb_intensity $PET_results/PET2T1w_brain_norm.nii.gz

    #### perform PVC
    # get binarized gray and white matter images from freesurfer
    mri_binarize --i $HCP_results/T1w/aparc+aseg.nii.gz --o $PET_results/wm_mask.nii --all-wm
    mri_binarize --i $HCP_results/T1w/aparc+aseg.nii.gz --o $PET_results/gm_mask.nii --gm
    fslmerge -t $PET_results/gm_wm_mask.nii.gz $PET_results/gm_mask.nii $PET_results/wm_mask.nii

    # there is a issue with itk in the toolbox, giving error:
    #           "Description: itk::ERROR: MullerGartnerImageFilter(0x7fe7ebc89ea0): Inputs do not occupy the same physical space!
    #           InputImage Origin: [-9.0000000e+01, 1.2600000e+02, -7.2000000e+01],
    #           InputImage_1 Origin: [-9.0000000e+01, 1.2599999e+02, -7.2000000e+01]
    #	        Tolerance: 6.9999999e-07"
    # "Inputs do not occupy the same physical space!" --> but this in reality is just rounding error of the floats, see th numbers above.
    # quick and dirty solution: https://github.com/UCL/PETPVC/issues/31 use fslcpgeom <source> <destination> and copy the header from one nii file on the other

    fslcpgeom $PET_results/PET2T1w_brain_norm.nii.gz $PET_results/gm_wm_mask.nii.gz -d #-d ... don't copy image dimensions
    petpvc -i $PET_results/PET2T1w_brain_norm.nii.gz -o $PET_results/PET2T1w_brain_norm_PVC.nii.gz -m $PET_results/gm_wm_mask.nii.gz -x 6.0 -y 6.0 -z 6.0 --pvc MG

    echo "#####################################"
    echo "#####################################"
    echo "3. Volume to surface mapping"
    echo "#####################################"
    echo "#####################################"

    for Hemisphere in L R ; do
        # initialize surfaces
        PET_volume=$PET_results"/PET2T1w_brain_norm_PVC.nii.gz"
        PET_volume_bin=$PET_results"/PET2T1w_brain_norm_PVC_bin.nii.gz"


        PET_surf_32k_fs_LR=$PET_results"/"$Hemisphere".${PET_modality}_load_MSMAll.32k_fs_LR.func.gii"
        midthickness_surf_32k_fs_LR=$DownsampleFolder"/"$sub"."$Hemisphere".midthickness_MSMAll."$LowResMesh"k_fs_LR.surf.gii"
        white_surf_32k_fs_LR=$DownsampleFolder"/"$sub"."$Hemisphere".white_MSMAll."$LowResMesh"k_fs_LR.surf.gii"
        pial_surf_32k_fs_LR=$DownsampleFolder"/"$sub"."$Hemisphere".pial_MSMAll."$LowResMesh"k_fs_LR.surf.gii"
        ROI_mask_32k_fs_LR=$HCP_results"/MNINonLinear/fsaverage_LR32k/"$sub"."$Hemisphere".atlasroi."$LowResMesh"k_fs_LR.shape.gii"

        # create volume-roi by binarizing PET_volume
        # otherwise 0 voxels which lie between the surfaces will used for the average too
        mri_binarize --i $PET_volume --o ${PET_volume_bin} --min 0.00001

        # volume to surface mapping
        $CARET7DIR/wb_command -volume-to-surface-mapping $PET_volume $midthickness_surf_32k_fs_LR $PET_surf_32k_fs_LR  \
                                            -ribbon-constrained $white_surf_32k_fs_LR $pial_surf_32k_fs_LR \
                                            -volume-roi ${PET_volume_bin}

        # dilate and mask
        $CARET7DIR/wb_command -metric-dilate $PET_surf_32k_fs_LR $midthickness_surf_32k_fs_LR 10 $PET_surf_32k_fs_LR
        $CARET7DIR/wb_command -metric-mask $PET_surf_32k_fs_LR $ROI_mask_32k_fs_LR $PET_surf_32k_fs_LR

    done

    echo "#####################################"
    echo "#####################################"
    echo "4. extract regional PET load using Glassers parcellation"
    echo "#####################################"
    echo "#####################################"

    for Hemisphere in L R ; do

        if [ $Hemisphere = "L" ] ; then
            Structure="CORTEX_LEFT"
            h="left"
        elif [ $Hemisphere = "R" ] ; then
            Structure="CORTEX_RIGHT"
            h="right"
        fi



        PET_cifti=$PET_results/$Hemisphere"."${PET_modality}"_load_MSMAll.dscalar.nii"
        PET_parcellated=$PET_results/$Hemisphere"."${PET_modality}"_load_MSMAll.pscalar.nii"
        PET_text=$PET_results/$Hemisphere"."${PET_modality}"_load_MSMAll.pscalar.txt"
        PET_surf_32k_fs_LR=$PET_results"/"$Hemisphere".${PET_modality}_load_MSMAll.32k_fs_LR.func.gii"

        #convert to cifti to parcellate later
        $CARET7DIR/wb_command -cifti-create-dense-scalar $PET_cifti -$h-metric $PET_surf_32k_fs_LR


        # use parcellation to get regionwise PET load
        $CARET7DIR/wb_command -cifti-parcellate $PET_cifti ${GlasserFolder}/Q1-Q6_RelatedValidation210.CorticalAreas_dil_Final_Final_Areas_Group_Colors.32k_fs_LR.dlabel.nii \
                              COLUMN $PET_parcellated

        #convert to text
        $CARET7DIR/wb_command -cifti-convert -to-text $PET_parcellated $PET_text
    done

    # extract from subcortical regions
    mri_binarize --i $HCP_results/T1w/aparc+aseg.nii.gz --o $PET_results/subcort_mask.nii.gz --subcort-gm
    fslmaths $HCP_results/T1w/aparc+aseg.nii.gz -mas $PET_results/subcort_mask.nii.gz $PET_results/subcort_gm.nii.gz

    # replace labels
    mri_binarize --i "$PET_results/subcort_gm.nii.gz" \
                --o "$PET_results/subcort_gm.nii.gz" \
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

    fslmeants -i $PET_results/PET2T1w_brain_norm_PVC.nii.gz --label=$PET_results/subcort_gm.nii.gz -o $PET_results/${PET_modality}_load.subcortical.txt

done

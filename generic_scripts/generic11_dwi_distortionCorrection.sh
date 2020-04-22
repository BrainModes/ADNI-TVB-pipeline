#!/bin/bash
#$ -cwd
#$ -V
#$ -l h_vmem=12G
#$ -l h_rt=08:30:00
#$ -q medium.q
#$ -P medium

#input arguments:
Studyfolder=$1
sub=$2
PE_dir=$3
UseJacobian=$4
UseBiasField=$5

#where to store output data:
HCP_results=${Studyfolder}/${sub}/T1w/
DWI_path=${Studyfolder}/${sub}/DWI_processing

DWI_preprocessed_mif=$DWI_path/DWI_preprocessed.mif
DWI_preprocessed=$DWI_path/DWI_preprocessed.nii

T2_image=$HCP_results/T2w_acpc_dc_restore.nii.gz
T2_image_brain=$HCP_results/T2w_acpc_dc_restore_brain.nii.gz

BiasField=$HCP_results/"BiasField_acpc_dc.nii.gz"
BiasField_in_DWI=$DWI_path/"BiasField_acpc_dc_in_DWI.nii.gz"

DWI_meanB0_mif=$DWI_path/DWI_meanb0.mif
DWI_meanB0=$DWI_path/DWI_meanb0.nii.gz
DWI_meanB0_brain=$DWI_path/DWI_meanb0_brain.nii.gz

DWI_brainmask_mif=$DWI_path/DWI_brainmask.mif
DWI_brainmask=$DWI_path/DWI_brainmask.nii.gz

T2_in_DWI_brain=$DWI_path/T2_in_DWI_brain.nii.gz

DWI_preprocessed_masked=$DWI_path/DWI_preproc_masked.nii.gz
DWI_preprocessed_masked_undistorted=$DWI_path/DWI_preproc_masked_undistorted.nii.gz
DWI_preprocessed_masked_undistorted_mif=$DWI_path/DWI_preproc_masked_undistorted.mif

tmp_bvec=$DWI_path/tmp_bvec.bvec
tmp_bval=$DWI_path/tmp_bval.bval

#PROCESSING
echo "START epi distortion correction" | tee -a /dev/stderr
date +"Date : %d/%m/%Y Time : %H.%M.%S" | tee -a /dev/stderr

echo "get meanB0 image and create brainmask" | tee -a /dev/stderr
# convert files to Nifti for the other tools, but save bvecs and bvals to add them later

# extract all b0 volumes from DWI scan. Average them. Convert to nifti.
dwiextract $DWI_preprocessed_mif - -bzero | mrmath - mean $DWI_meanB0_mif -axis 3 -force
mrconvert $DWI_meanB0_mif $DWI_meanB0 -force

echo "create whole-brain mask from DWI scan, and convert to nifti" | tee -a /dev/stderr
dwi2mask $DWI_preprocessed_mif $DWI_brainmask_mif -force
mrconvert $DWI_brainmask_mif $DWI_brainmask -force

echo "export diffusion-weighting gradient info to FSl-format bval/bvec files" | tee -a /dev/stderr
mrconvert $DWI_preprocessed_mif $DWI_preprocessed -force -export_grad_fsl $tmp_bvec $tmp_bval

echo "mask dwi_meanB0 image & DWI scan" | tee -a /dev/stderr
fslmaths $DWI_meanB0 -mas $DWI_brainmask $DWI_meanB0_brain
fslmaths $DWI_preprocessed -mas $DWI_brainmask $DWI_preprocessed_masked

echo "linear register T2 to DWI: create transform & inverse" | tee -a /dev/stderr
flirt -in $DWI_meanB0 -ref $T2_image -omat $DWI_path/EPItoT2.mat -dof 6
convert_xfm -omat $DWI_path/T2toEPI.mat -inverse $DWI_path/EPItoT2.mat

echo "apply transfrom to T2 image and bias field." | tee -a /dev/stderr
# Put T2 into DWI space. Put biasfield in DWI space.
flirt -in $T2_image_brain -ref $DWI_meanB0 -init $DWI_path/T2toEPI.mat -applyxfm -out $T2_in_DWI_brain
flirt -in $BiasField -ref $DWI_meanB0 -init $DWI_path/T2toEPI.mat -applyxfm -out $BiasField_in_DWI

# set number of threads to use for computation
ORIGINALNUMBEROFTHREADS=${ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS}
ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=4    # NUMBEROFTHREADS
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS

echo "antsregistration SyN, constrained in PE direction" | tee -a /dev/stderr
# antsregistration SyN, constrained in PE direction
antsRegistration --dimensionality 3 --float 0 --output [${DWI_path}/CC_onedir,${DWI_path}/CC_onedirWarped.nii.gz] \
    --interpolation Linear --winsorize-image-intensities '[0.005,0.995]' --use-histogram-matching 1 \
    --initial-moving-transform [${T2_in_DWI_brain},${DWI_meanB0_brain},1] \
    --transform 'SyN[0.1,0.5,0]' --metric CC[${T2_in_DWI_brain},${DWI_meanB0_brain},1,4] --convergence '[200x150x150x80,1e-6,10]' \
    --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox -g $PE_dir -v


#antsRegistration --dimensionality 3 --float 0 --output [./CC_onedir, ./CC_onedirWarped.nii.gz] \
#    --interpolation Linear --winsorize-image-intensities '[0.005,0.995]' --use-histogram-matching 1 \
#    --initial-moving-transform [T2_in_DWI_brain.nii.gz,DWI_meanb0_brain.nii.gz,1] \
#    --transform 'SyN[0.1,0.5,0]' --metric CC[T2_in_DWI_brain.nii.gz,DWI_meanb0_brain.nii.gz,1,4] --convergence '[200x150x150x80,1e-6,10]' \
#    --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox -g "0x1x0" -v

echo "apply warp to DWI images" | tee -a /dev/stderr
# collapse the transformations to a displacement field
echo "collapse the transformations to a displacement field" | tee -a /dev/stderr
antsApplyTransforms -d 3 -o [${DWI_path}/CollapsedWarp.nii.gz,1] \
  -t ${DWI_path}/CC_onedir1Warp.nii.gz -t ${DWI_path}/CC_onedir0GenericAffine.mat \
  -r $T2_in_DWI_brain


# get parameters from dwi image, number of slices and TR
hislice=`PrintHeader $DWI_preprocessed_masked | grep Dimens | cut -d ',' -f 4 | cut -d ']' -f 1`
tr=`PrintHeader $DWI_preprocessed_masked | grep "Voxel Spac" | cut -d ',' -f 4 | cut -d ']' -f 1`

# replicate warp and template image to 4D for warping the whole DWI image
echo "replicate warp and template image to 4D for warping the whole DWI image" | tee -a /dev/stderr
ImageMath 3 ${DWI_path}/4DCollapsedWarp.nii.gz ReplicateDisplacement \
            ${DWI_path}/CollapsedWarp.nii.gz $hislice $tr 0

ImageMath 3 ${T2_in_DWI_brain}_4D.nii.gz ReplicateImage \
            ${T2_in_DWI_brain} $hislice $tr 0

# apply to original epi
echo " apply to original epi" | tee -a /dev/stderr
antsApplyTransforms -d 4 -o $DWI_preprocessed_masked_undistorted \
  -t ${DWI_path}/4DCollapsedWarp.nii.gz  \
  -r ${T2_in_DWI_brain}_4D.nii.gz \
  -i $DWI_preprocessed_masked

# return to original number of threads
ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=$ORIGINALNUMBEROFTHREADS
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS

# intensity correction by multiplying the warped image with the jacobian of the warp field
# ANTS function to create the jacobian
echo "intensity correction by multiplying the warped image with the jacobian of the warp field" | tee -a /dev/stderr
if [[ $UseJacobian == "True" ]]
then
    CreateJacobianDeterminantImage 3 CollapsedWarp.nii.gz ${DWI_path}/Jacobian.nii.gz
    if [[ "$UseBiasField" == "True" ]]

    then
        echo "applying Jacobian modulation and Bias field correction" | tee -a /dev/stderr
        fslmaths $DWI_preprocessed_masked_undistorted -div $BiasField_in_DWI -mul $DWI_path/Jacobian.nii.gz $DWI_preprocessed_masked_undistorted
    else
        echo "applying Jacobian modulation, but no Bias field correction" | tee -a /dev/stderr
        fslmaths $DWI_preprocessed_masked_undistorted -mul $DWI_path/Jacobian.nii.gz $DWI_preprocessed_masked_undistorted
    fi
else
    if [[ "$UseBiasField" == "True" ]]
    then
        echo "not applying Jacobian modulation, but applying Bias field correction" | tee -a /dev/stderr
        fslmaths $DWI_preprocessed_masked_undistorted -div $BiasField_in_DWI $DWI_preprocessed_masked_undistorted
    fi
fi

# convert final file back to mif and add bvec and bval
mrconvert -force -fslgrad $tmp_bvec $tmp_bval $DWI_preprocessed_masked_undistorted $DWI_preprocessed_masked_undistorted_mif

# clean up
rm $tmp_bval $tmp_bvec $DWI_preprocessed $DWI_preprocessed_masked_undistorted $DWI_brainmask $DWI_meanB0

echo "END epi distortion correction" | tee -a /dev/stderr
date +"Date : %d/%m/%Y Time : %H.%M.%S" | tee -a /dev/stderr

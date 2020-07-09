#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=4G
#SBATCH --time=00:30:00


#########
######### Extract fMRI time series
#########

# Pipeline environment script
EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
#Set up pipeline environment variables and software
source ${EnvironmentScript}


study_folder=$1
subject=$2
SubjectFolder="${study_folder}/${subject}"
ResultsFolder="${SubjectFolder}/MNINonLinear/Results/"
GlasserFolder="/fast/work/groups/ag_ritter/MR_processing/Glasser_et_al_2016_HCP_MMP1.0_RVVG_2/HCP_PhaseTwo/Glasser_et_al_2016_HCP_MMP1.0_StudyData/"
fmri=$3


# create subcortical CIFTI label file
${CARET7DIR}/wb_command -cifti-create-label  ${SubjectFolder}/MNINonLinear/ROIs/Atlas_ROIs.2.dlabel.nii \
                        -volume ${SubjectFolder}/MNINonLinear/ROIs/Atlas_ROIs.2.nii.gz ${SubjectFolder}/MNINonLinear/ROIs/Atlas_ROIs.2.nii.gz

# cortical regions
${CARET7DIR}/wb_command -cifti-parcellate  ${ResultsFolder}/${fmri}/${fmri}_Atlas_MSMAll_hp2000_clean.dtseries.nii \
                              ${GlasserFolder}/Q1-Q6_RelatedValidation210.CorticalAreas_dil_Final_Final_Areas_Group_Colors.32k_fs_LR.dlabel.nii \
                              COLUMN ${ResultsFolder}/${fmri}/${subject}_${fmri}_Atlas_MSMAll_hp2000_clean.ptseries.nii

# subcortical regions
${CARET7DIR}/wb_command -cifti-parcellate ${ResultsFolder}/${fmri}/${fmri}_Atlas_MSMAll_hp2000_clean.dtseries.nii \
                             ${SubjectFolder}/MNINonLinear/ROIs/Atlas_ROIs.2.dlabel.nii \
                             COLUMN ${ResultsFolder}/${fmri}/${subject}_${fmri}_Atlas_MSMAll_hp2000_clean_subcort.ptseries.nii

# convert both to txt files
${CARET7DIR}/wb_command -cifti-convert -to-text ${ResultsFolder}/${fmri}/${subject}_${fmri}_Atlas_MSMAll_hp2000_clean.ptseries.nii \
                                   ${ResultsFolder}/${fmri}/${subject}_${fmri}_Atlas_MSMAll_hp2000_clean.ptseries.txt

${CARET7DIR}/wb_command -cifti-convert -to-text ${ResultsFolder}/${fmri}/${subject}_${fmri}_Atlas_MSMAll_hp2000_clean_subcort.ptseries.nii \
                                   ${ResultsFolder}/${fmri}/${subject}_${fmri}_Atlas_MSMAll_hp2000_clean_subcort.ptseries.txt

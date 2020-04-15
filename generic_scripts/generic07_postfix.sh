#!/bin/bash
#$ -cwd
#$ -V
#$ -l h_vmem=6G
#$ -l h_rt=08:00:00
#$ -q medium.q
#$ -P medium

StudyFolder=$1 # Location of Subject folders (named by subjectID)
Subject=$2 #Space delimited list of subject IDs
EnvironmentScript="/fast/work/groups/ag_ritter/MR_processing/HCP_pipeline/Pipeline/Pipelines-3.24.0/Examples/Scripts/SetUpHCPPipeline.sh" # Pipeline environment script
fMRI_name="Restingstate"

#Set up pipeline environment variables and software
source ${EnvironmentScript}


${HCPPIPEDIR}/PostFix/PostFix.sh \
   --path=$StudyFolder \
   --subject=$Subject \
   --fmri-name=$fMRI_name \
   --high-pass=2000 \
   --template-scene-dual-screen=${HCPPIPEDIR}/PostFix/PostFixScenes/ICA_Classification_DualScreenTemplate.scene \
   --template-scene-single-screen=${HCPPIPEDIR}/PostFix/PostFixScenes/ICA_Classification_SingleScreenTemplate.scene \
   --reuse-high-pass=NO \
   --matlab-run-mode=0


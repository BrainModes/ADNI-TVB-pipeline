#!/usr/bin/env python3
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=24:00:00
#SBATCH --partition=medium

rawdataPath = "/path/to/raw"
resultsPath = "/path/to/resultsDir"

import os
import shutil

#make BIDS derivative directory

os.makedirs(rawdataPath+"/"+"derivatives/TVB",exist_ok=False) # to prevent overwrite

sub_vis_list = [i for i in os.listdir(resultsPath) if (os.path.isdir(resultsPath+"/"+i) & (i.startswith("sub-")))]

for subvis in sub_vis_list:
    #get subject ID and session name
    sub=subvis.split("_")[0].split("-")[1]
    visit=subvis.split("_")[1].split("-")[1]
    session_outputdir = rawdataPath+"/"+"derivatives/TVB/"+sub+"/"+visit
    #change "flattened" directory names back into longitudinal BIDS format
    os.makedirs(session_outputdir, exist_ok=False) # to prevent overwrite


    #copy & rename pipeline output files to under derivatives/sub-XXXX/ses-XXXX directory
    # STRUCTURAL CONNECTOME
    #connectome: lengths
    if os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/connectome_lengths.csv"):
        shutil.copyfile(resultsPath+"/"+subvis+"DWI_processing/connectome_lengths.csv", session_outputdir+"/"+"lengths.txt")
    #connectome: weights
    if os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/connectome_weights.csv"):
        shutil.copyfile(resultsPath+"/"+subvis+"DWI_processing/connectome_weights.csv", session_outputdir+"/"+"weights.txt")

    # FUNC
    #rsfMRI timeseries: cortical
    if os.path.isfile(resultsPath+"/"+subvis+"MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean.ptseries.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean.ptseries.txt", session_outputdir+"/"+subvis+"_task-rest_desc-cortical_parc-hcpmmp1_ROI_timeseries.txt")
    #rsfMRI timeseries: subcortical
    if os.path.isfile(resultsPath+"/"+subvis+"MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean_subcort.ptseries.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean_subcort.ptseries.txt", session_outputdir+"/"+subvis+"_task-rest_desc-subcortical_parc-hcpmmp1_ROI_timeseries.txt")

    # PET: ABETA
    #amyloid load: left hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"PET_PVC_MG/Amyloid/L.Amyloid_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"PET_PVC_MG/Amyloid/L.Amyloid_load_MSMAll.pscalar.txt", session_outputdir+"/"+subvis+"task-rest_acq-AV45_desc_lh_parc-hcpmmp1_pet.txt")
    #amyloid load: right hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"PET_PVC_MG/Amyloid/R.Amyloid_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"PET_PVC_MG/Amyloid/R.Amyloid_load_MSMAll.pscalar.txt", session_outputdir+"/"+subvis+"task-rest_acq-AV45_desc_rh_parc-hcpmmp1_pet.txt")
    #amyloid load: subcortical regions
    if os.path.isfile(resultsPath+"/"+subvis+"PET_PVC_MG/Amyloid/Amyloid_load.subcortical.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"PET_PVC_MG/Amyloid/Amyloid_load.subcortical.txt", session_outputdir+"/"+subvis+"task-rest_acq-AV45_desc_subcortical_parc-hcpmmp1_pet.txt")

    # PET: TAU
    #amyloid load: left hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"PET_PVC_MG/Tau/L.Tau_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"PET_PVC_MG/Tau/L.Tau_load_MSMAll.pscalar.txt", session_outputdir+"/"+subvis+"task-rest_acq-AV1451_desc_lh_parc-hcpmmp1_pet.txt")
    #amyloid load: right hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"PET_PVC_MG/Tau/R.Tau_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"PET_PVC_MG/Tau/R.Tau_load_MSMAll.pscalar.txt", session_outputdir+"/"+subvis+"task-rest_acq-AV1451_desc_rh_parc-hcpmmp1_pet.txt")
    #amyloid load: subcortical regions
    if os.path.isfile(resultsPath+"/"+subvis+"PET_PVC_MG/Tau/Tau.subcortical.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"PET_PVC_MG/Tau/Tau.subcortical.txt", session_outputdir+"/"+subvis+"task-rest_acq-AV1451_desc_subcortical_parc-hcpmmp1_pet.txt")

    # TO DO:
    # rename above files?

    #region
    region_names = open("misc_files/region_labels.txt","r") # EDIT PATH
    region_names = sublist_csv.read().split('\n')
    assert len(region_names)==379
    cortical = np.zeros((len(region_names))) # regions are ordered, first cortical than subcortical ones
    cortical[:360] = 1
    hemisphere = [ 1 if name[0] == "R" else 0 for name in region_names] # this way brainstem is assigned to left hemisphere

    # create centers file
    if os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/diffusion_mask_overlap2subcortical_2dwi.nii.gz"):
        # create centroids
        img = nib.load(resultsPath+"/"+subvis+"DWI_processing/diffusion_mask_overlap2subcortical_2dwi.nii.gz")
        img_data = img.get_fdata().astype('int')
        # get the right coordinate transform to align region centroids with the surfaces
        # centers for BIDS
        f_bids = open(BIDS_anat_folder+"/"+subvis" + "_desc-centroid_morph.tsv","w") #centres.txt
        f_bids.write("name\tcentroid-x\tcentroid-y\tcentroid-z\n")

        for i in range(img_data.max()):
            rows, cols, slices = np.where(img_data==i+1)
            r = rows.mean()
            c = cols.mean()
            s = slices.mean()

            center = img.affine.dot(np.array([r,c,s,1]).T)[:3]
            f_bids.write(region_names[i]+"\t%.6f" %center[0]+"\t%.6f" %center[1]+"\t%.6f" %center[2]+"\n")

        f_bids.close()
        print("Centers saved !")
    # create areas file
    # create cortical file
    # create hemisphere file
    # create orientation file
    # create leadfield file


# create dataset_description.json file for derivatives directory
import json
from collections import OrderedDict


# Arguments
input_dataset_description_json = rawdataPath+'/dataset_description.json'
output_dataset_description_json = rawdataPath+'/derivatives/TVB/dataset_description.json'


# 1 read the dataset_description.json from the raw data set
with open(input_dataset_description_json, "r") as input_json:
    data = json.load(input_json)


# 2 prepend "TVB pipeline derivative: " to the value of the key "Name"
# to indicate that this is not the original raw data set, but
# a derivative generated by the TVB pipeline.
data['Name'] = "TVB pipeline derivative: " + data['Name']


# 3 Add fields for BIDS derivatives
data['PipelineDescription'] = {
    	"Name": "TVB",
        "Version": "1.0",
    	"CodeURL": "https://github.com/BrainModes/ADNI-TVB-pipeline",
    }


# 4 Save JSON
with open(output_dataset_description_json, 'w') as ff:
    json.dump(data, ff,sort_keys=False, indent=4)

#!/usr/bin/env python3
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=24:00:00
#SBATCH --partition=medium

rawdataPath = "/path/to/raw" # EDIT PATH: top-level path containing BIDS-format unprocessed data
resultsPath = "/path/to/resultsDir" # EDIT PATH: top-level path containing output of generic/batch processing
misc_files_path = "" # EDIT PATH: location of "misc_files" directory of this repo
HCPannotoutputPath = "" # EDIT: directory in which the HCP annot output directory will be created

n_cpus=1

import os
import shutil
import wget
import numpy as np
import nibabel as nib
import mne
import json
from collections import OrderedDict
import shlex
from mne.surface import _project_onto_surface
from mne.io.constants import FIFF
from scipy import spatial
import scipy.io as sio
import sys
import glob
import pandas as pd
from subprocess import Popen, PIPE
import nibabel.gifti as nbg
import csv

#make BIDS derivative directory
pipeline_name = "TVB"
#TVB-specific output directory: saves files in derivatives/TVB/sub-XXXX_ses-XXXX/<TVB-style output directory>
tvb_input="TVBinput"
os.makedirs(rawdataPath+"/"+"derivatives"+"/"+pipeline_name,exist_ok=False) # to prevent overwrite

# create "dataset_description.json" file for derivatives directory based on corresponding
# file from "raw" directory

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

sub_vis_list = [i for i in os.listdir(resultsPath) if (os.path.isdir(resultsPath+"/"+i) & (i.startswith("sub-")))]

# 0) download fsaverage HCPMMP1 annot files, create subject-specific ones
parc="HCPMMP1"
# NOTE: if you get permissions issues, check that you can write files to your $SUBJECTS_DIR directory. Soemtimes this is protected.
# If you have root privileges, you should first recursively change the permissions on $SUBJECTS_DIR (e.g. sudo chmod -R 777 $SUBJECTS_DIR ), and then wget should work.
#uncomment the following line
#os.chmod(os.environ['SUBJECTS_DIR'],0o777)


# 0.1) download fsaverage annot files
# SOURCE: https://figshare.com/articles/HCP-MMP1_0_projected_on_fsaverage/3498446
print("START: download fsaverage annot files, and script to convert to subject-space")
wget.download("https://s3-eu-west-1.amazonaws.com/pfigshare-u-previews/5528837/preview.jpg", os.environ['SUBJECTS_DIR']+"/fsaverage/label/fsaverage_pial+HCP-MMP1.jpg")
#wget.download("https://ndownloader.figshare.com/files/5528816", os.environ['SUBJECTS_DIR']+"/fsaverage/label/lh.HCP-MMP1.annot")
#wget.download("https://ndownloader.figshare.com/files/552881", os.environ['SUBJECTS_DIR']+"/fsaverage/label/rh.HCP-MMP1.annot")
#problem with rh.HCP-MMP1.annot file; use files created by our lab
shutil.copy(misc_files_path+"/lh.HCPMMP1.annot", os.environ['SUBJECTS_DIR']+"/fsaverage/label/lh.HCPMMP1.annot")
shutil.copy(misc_files_path+"/rh.HCPMMP1.annot", os.environ['SUBJECTS_DIR']+"/fsaverage/label/rh.HCPMMP1.annot")


os.chmod(os.environ['SUBJECTS_DIR']+"/fsaverage/label/lh.HCP-MMP1.annot",0o777) #add execute permissions
os.chmod(os.environ['SUBJECTS_DIR']+"/fsaverage/label/rh.HCP-MMP1.annot",0o777) #add execute permissions

# 0.2) download script that converts to subject-space
# SOURCE: https://figshare.com/articles/HCP-MMP1_0_volumetric_NIfTI_masks_in_native_structural_space/4249400/5
wget.download("https://ndownloader.figshare.com/files/13320527", os.environ['SUBJECTS_DIR']+"/create_subj_volume_parcellation.sh")
wget.download("https://s3-eu-west-1.amazonaws.com/pfigshare-u-previews/6928718/preview.jpg", os.environ['SUBJECTS_DIR']+"/slices.jpg")
os.chmod(os.environ['SUBJECTS_DIR']+"/create_subj_volume_parcellation.sh",0o777) #add execute permissions
print("FINISH: download fsaverage annot files, and script to convert to subject-space")



# 0.3) convert HCPMMP1 annotations to subject space
# copy FreeSurferColorLUT.txt to $SUBJECTS_DIR
shutil.copy(os.environ['FREESURFER_HOME']+"/FreeSurferColorLUT.txt", os.environ['SUBJECTS_DIR']+"/FreeSurferColorLUT.txt")
os.chdir(rawdataPath)

# 0.4) write sub_vis_list to a textfile so the script "create_subj_volume_parcellation.sh" can use it
with open(resultsPath+"/subList.txt", 'w') as f:
    for s in sub_vis_list:
        f.write(s + '\n')

# 0.5) create symbolic links to subjects' HCP FreeSurfer directories in $subjects_dir
for i, subvis in enumerate(sub_vis_list):
    os.symlink(resultsPath+"/"+subvis+"/T1w/"+subvis, os.environ['SUBJECTS_DIR']+"/"+subvis)

# create directory inside results directory, called "HCPMMP1_parcellation", containing the results of this script. creates a FreeSurfer-style subject-specific parcellation of brain using HCP atlas.
# Also creates tables with volume/thickness/etc data. This can be changedd.
# default set to process all subjects on subList. This can be changed.
print("START: create a FreeSurfer-style subject-specific parcellation of subjects' brains using HCP atlas\n")
os.chdir(HCPannotoutputPath)
commandTxt = "bash {}/create_subj_volume_parcellation.sh -L {}/subList.txt -a HCPMMP1 -d {} -m YES -s YES -t YES".format(os.environ['SUBJECTS_DIR'],resultsPath,"HCPMMP1_parcellation")
args=shlex.split(commandTxt)
print("COMMAND ARGS: ",args,"\n")
p = Popen(args,stdout=PIPE, stderr=PIPE)
stdout, stderr = p.communicate()
print("FINISH: create a FreeSurfer-style subject-specific parcellation of subjects' brains using HCP atlas\n")

print("START: loop through subjects")
for subvis in sub_vis_list:
    #get subject ID and session name
    sub=subvis.split("_")[0].split("-")[1]
    visit=subvis.split("_")[1].split("-")[1]
    print("SUBJECT:{}, VISIT:{}".format(sub,visit))
    session_outputdir = rawdataPath+"/"+"derivatives/TVB/sub-"+sub+"/ses-"+visit
    print(session_outputdir)
    #change "flattened" directory names back into longitudinal BIDS format
    os.makedirs(session_outputdir+"/"+tvb_input, exist_ok=False) # to prevent overwrite

    print("START: copy & rename pipeline output files to BIDS-style derivatives directory, as well as TVB-style output directory")
    #copy & rename pipeline output files to under derivatives/sub-XXXX/ses-XXXX directory
    #but also to common location for TVB-input
    # STRUCTURAL CONNECTOME: DONE BELOW

    # FUNC
    BIDS_func_folder = session_outputdir+"/func"
    if not os.path.exists(BIDS_func_folder):
        os.makedirs(BIDS_func_folder)

    BIDS_pet_folder = session_outputdir+"/pet"
    if not os.path.exists(BIDS_pet_folder):
        os.makedirs(BIDS_pet_folder)

    #rsfMRI timeseries: cortical
    if os.path.isfile(resultsPath+"/"+subvis+"/MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean.ptseries.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean.ptseries.txt", session_outputdir+"/"+tvb_input+"/"+subvis+"_task-rest_desc-cortical_parc-hcpmmp1_ROI_timeseries.txt")
        csv.writer(open(BIDS_func_folder+"/"+subvis+"_desc-weight_conndata-network_connectivity.tsv", 'w+'), delimiter='\t').writerows(csv.reader(open(resultsPath+"/"+subvis+"/MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean.ptseries.txt")))

    #rsfMRI timeseries: subcortical
    if os.path.isfile(resultsPath+"/"+subvis+"/MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean_subcort.ptseries.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean_subcort.ptseries.txt", session_outputdir+"/"+tvb_input+"/"+subvis+"_task-rest_desc-subcortical_parc-hcpmmp1_ROI_timeseries.txt")
        csv.writer(open(BIDS_func_folder+"/"+subvis+"_desc-weight_conndata-network_connectivity_subcortical.tsv", 'w+'), delimiter='\t').writerows(csv.reader(open(resultsPath+"/"+subvis+"/MNINonLinear/Results/Restingstate"+"/"+subvis+"_Restingstate_Atlas_MSMAll_hp2000_clean_subcort.ptseries.txt"))) #check how to name subcortical variant of this file

    # PET: ABETA
    #amyloid load: left hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Amyloid/L.Amyloid_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Amyloid/L.Amyloid_load_MSMAll.pscalar.txt", session_outputdir+"/pet/"+subvis+"_task-rest_acq-AV45_desc_lh_parc-hcpmmp1_pet.txt")
    #amyloid load: right hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Amyloid/R.Amyloid_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Amyloid/R.Amyloid_load_MSMAll.pscalar.txt", session_outputdir+"/pet/"+subvis+"_task-rest_acq-AV45_desc_rh_parc-hcpmmp1_pet.txt")
    #amyloid load: subcortical regions
    if os.path.isfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Amyloid/Amyloid_load.subcortical.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Amyloid/Amyloid_load.subcortical.txt", session_outputdir+"/pet/"+subvis+"_task-rest_acq-AV45_desc_subcortical_parc-hcpmmp1_pet.txt")

    # PET: TAU
    #amyloid load: left hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Tau/L.Tau_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Tau/L.Tau_load_MSMAll.pscalar.txt", session_outputdir+"/pet/"+subvis+"_task-rest_acq-AV1451_desc_lh_parc-hcpmmp1_pet.txt")
    #amyloid load: right hemispheric regions
    if os.path.isfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Tau/R.Tau_load_MSMAll.pscalar.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Tau/R.Tau_load_MSMAll.pscalar.txt", session_outputdir+"/pet/"+subvis+"_task-rest_acq-AV1451_desc_rh_parc-hcpmmp1_pet.txt")
    #amyloid load: subcortical regions
    if os.path.isfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Tau/Tau.subcortical.txt"):
        shutil.copyfile(resultsPath+"/"+subvis+"/PET_PVC_MG/Tau/Tau.subcortical.txt", session_outputdir+"/pet/"+subvis+"_task-rest_acq-AV1451_desc_subcortical_parc-hcpmmp1_pet.txt")

    print("FINISH: copy & rename pipeline output files to BIDS-style derivatives directory, as well as TVB-style output directory")

    print("START: create files not created by processing pipeline")
    ###################################################
    # create files not created by processing pipeline #
    ###################################################
    # 1. create cortical surface and region mapping
    # 2. compute source space
    # 3. compute BEM model + EEG Locations
    # 4. compute forward solution
    # 5. save files for TVB
    #   - Regionmap
    #   - Cortical surface zipped
    #   - BEM surfaces
    #   - EEG locations
    #   - [Weights already created]
    #   - [Tracts already created]
    #   - Centers
    #   - Orientations
    #   - Area
    #   - Cortical
    #   - Hemisphere
    #   - Connectome zipped

    #===========================================================================
    recon_all_name = subvis #Name of subject in recon_all_dir
    recon_all_dir = resultsPath+"/"+subvis+"/"+"T1w" #Path to the recon-all results (for hcpmmp, this is "resultsPath/subject/T1w")



    # 1. create cortical surface and region mapping
    print("START: create cortical surface and region mapping")
    # read surface, and convert units of the vertex positions
    pial_l = mne.read_surface(recon_all_dir + "/" + recon_all_name + "/surf/lh.pial", read_metadata=True, return_dict=True, verbose=True)
    pial_l[3]['rr']  = pial_l[3]['rr']/1000
    pial_r = mne.read_surface(recon_all_dir + "/" + recon_all_name + "/surf/rh.pial", read_metadata=True, return_dict=True, verbose=True)
    pial_r[3]['rr']  = pial_r[3]['rr']/1000

    # merge surfaces, first left than right
    n_vert_l = pial_l[3]['np']
    n_vert_r = pial_r[3]['np']
    n_vert   = n_vert_l + n_vert_r
    pial_vertices  = np.concatenate((pial_l[3]['rr'],   pial_r[3]['rr']))
    pial_tris      = np.concatenate((pial_l[3]['tris'], pial_r[3]['tris'] +  n_vert_l))

    #parcellation regions
    region_names_open = open(misc_files_path+"/region_labels.txt","r") # EDIT PATH
    region_names = region_names_open.read().split('\n')
    region_names.remove("")
    region_names = [name.strip() for name in region_names]
    assert len(region_names)==379
    cortical = np.zeros((len(region_names))) # regions are ordered, first cortical than subcortical ones
    cortical[:360] = 1
    hemisphere = [ 1 if name[0] == "R" else 0 for name in region_names] # this way brainstem is assigned to left hemisphere
    prefix_len    = 0
    regexp_append="_ROI"

    # create region map of high_res pial surface
    region_map = np.zeros((n_vert))
    n_regions = len(region_names)

    for i in range(n_regions):
        print(i,region_names[i],hemisphere[i])

    # load labels according to mrtrix lut order !!!
    r = 1
    for i in range(len(region_names)):
        if cortical[i] :  # only cortical regions are represented in the region map
            if  hemisphere[i] == 1:
                add  = n_vert_l
                hemi = "rh"
            elif hemisphere[i] == 0:
                add  = 0
                hemi = 'lh'

            label = region_names[i][prefix_len:]+regexp_append
            label = mne.read_labels_from_annot(subject=recon_all_name, subjects_dir=recon_all_dir, hemi=hemi, regexp ="^"+label, surf_name = 'pial', parc=subvis+"_"+parc)
            region_map[label[0].vertices + add] = r
        r += 1

    # those entries which are still 0 were not labeled
    # they are corresponding to "subcortical" vertices, i.e. on the brain "inside" of the cortical surface
    # delete those from region map and cortical surface vertices and tris
    ind_sub_vert = np.where(region_map==0)[0]
    pial_vertices = np.delete(pial_vertices, ind_sub_vert, 0)
    region_map = region_map[region_map!=0] # remove "subcortical" vertices
    region_map -= 1 # reduce labels by 1, to start from 0 again

    # get triangles which contains these "subcorical" vertices
    mask = np.isin(pial_tris, ind_sub_vert)
    rows, cols = np.nonzero(mask)
    rows = np.unique(rows)

    # delete tris
    pial_tris = np.delete(pial_tris, rows,0)

    # update tri indices
    kk = []
    for i in range(len(ind_sub_vert)):
        ind = ind_sub_vert[i]
        if pial_tris[pial_tris > ind ].sum() == 0: kk.append(ind)
        pial_tris[pial_tris > ind ] -= 1
        ind_sub_vert -= 1

    print("FINISH: create cortical surface and region mapping")

    # 2. compute source space
    print("START: compute source space")
    # decimate surface
    pial_dec = mne.decimate_surface(pial_vertices, pial_tris, n_triangles=30000)

    # complete decimated surface (add normals + other parameters)
    pial_dict = {'rr':pial_dec[0], 'tris':pial_dec[1]}
    pial_complete = mne.surface.complete_surface_info(pial_dict)

    # construct source space dictionary by hand
    # use all point of the decimated surface as souce space
    src =   {'rr':       pial_complete['rr'],
             'tris':     pial_complete['tris'],
             'ntri':     pial_complete['ntri'],
             'use_tris': pial_complete['tris'],
             'np':       pial_complete['np'],
             'nn':       pial_complete['nn'],
             'inuse':    np.ones(pial_complete['np']),
             'nuse_tri': pial_complete['ntri'],
             'nuse':     pial_complete['np'],
             'vertno':   np.arange(0,pial_complete['np']),
             'subject_his_id': recon_all_name,
             'dist': None,
             'dist_limit': None,
             'nearest': None,
             'type': 'surf',
             'nearest_dist': None,
             'pinfo': None,
             'patch_inds': None,
             'id': 101, # (FIFFV_MNE_SURF_LEFT_HEMI), # shouldn't matter, since we combined both hemispheres into one object
             'coord_frame': 5} # (FIFFV_COORD_MRI)}

    src = mne.SourceSpaces([src])

    print("FINISH: compute source space")

    # 3. compute BEM model + EEG Locations
    print("START: compute BEM model + EEG Locations")

    mne.bem.make_watershed_bem(subject= recon_all_name, subjects_dir = recon_all_dir, overwrite=True)


    conductivity = (0.3, 0.006, 0.3)  # for three layers
    model = mne.make_bem_model(subject=recon_all_name, ico=4,
                               conductivity=conductivity,
                               subjects_dir=recon_all_dir)
    bem = mne.make_bem_solution(model)



    ### GET AND ADJUST EEG LOCATIONS FROM DEFAULT CAP !!!!!!
    # This may produce implausible results if not corrected.
    # Default locations are used here to completely automate the pipeline and to not require manual input (e.g. setting the fiducials and fitting EEG locations.)
    # read default cap

    # DEPRECATION: mne.channels.read_montage was deprecated. Replace with mne.channels.make_standard_montage
    mon = mne.channels.make_standard_montage(kind="biosemi64", head_size=0.095) #default brain radius used

    # create info object
    ch_type = ["eeg" for i in range(len(mon.ch_names))]
    ch_type[-3:] = ["misc", "misc", "misc"] # needed for caps which include lpa, rpa and nza "channels" at the end
    info = mne.create_info(ch_names = mon.ch_names, sfreq = 256, ch_types = ch_type, montage=mon)

    # load head surface
    surf = mne.get_head_surf(subject=recon_all_name, source="head", subjects_dir=recon_all_dir)

    # project eeg locations onto surface and save into info
    eeg_loc = np.array([info['chs'][i]['loc'][:3] for i in range(len(mon.ch_names))])
    eegp_loc, eegp_nn = _project_onto_surface(
                        eeg_loc, surf, project_rrs=True,
                        return_nn=True)[2:4]
    for i in range(len(mon.ch_names)):
        info['chs'][i]['loc'][:3] = eegp_loc[i,:]

    print("FINISH: compute BEM model + EEG Locations")

    # 4. compute forward solution
    print("START: compute forward solution")

    fwd = mne.make_forward_solution(info, trans=None, src=src, bem=bem,
                                meg=False, eeg=True, mindist=0, n_jobs=n_cpus,)

    fwd_fixed = mne.convert_forward_solution(fwd, surf_ori=True, force_fixed=True,
                                             use_cps=True)
    leadfield = fwd_fixed['sol']['data']

    # vertices are excluded from forward calculation if they are outside the inner skull
    # check if that happened and if yes, insert them as 0 columns in the leadfield
    # because TVB expects the leadfield to have dimensions [n_vertices of cortex, n_eeg_sensors] or the transpose of that
    rr = src[0]['rr']
    leadfield_new = leadfield
    if not rr.shape[0] == fwd_fixed['nsource']:
        rr_list = rr.tolist()
        fwd_rr_list = fwd_fixed['source_rr'].tolist()
        idx_missing = []
        # find which vertices are excluded
        for i in range(rr.shape[0]):
            if rr_list[i] not in fwd_rr_list:
                idx_missing.append(i)

        # at these positions insert 0 columns
        for i in idx_missing:
            tmp1 = leadfield_new[:,:i]
            tmp2 = leadfield_new[:,i:]
            leadfield_new = np.concatenate((tmp1,
                                            np.zeros(((np.array(ch_type)=="eeg").sum(),1)),
                                            tmp2), axis=1)


    # write leadfield to file in "TVBinput" subdir (derivatives/TVB/sub/ses/TVB-input)
    sio.savemat(session_outputdir+"/"+tvb_input+"/"+subvis+"_EEGProjection.mat", mdict={'ProjectionMatrix':leadfield_new})

    # leadfield for BIDS
    BIDS_eeg_folder = session_outputdir+"/eeg"
    if not os.path.exists(BIDS_eeg_folder):
        os.makedirs(BIDS_eeg_folder)
    np.savetxt(BIDS_eeg_folder+"/"+subvis+"_desc-eeg_proj.tsv", leadfield_new, delimiter="\t")

    print("FINISH: compute forward solution")

    # 5. save files for TVB
    print("START: save files for TVB")
    # get region map for source space (ie. downsampled pial), via nearest neighbour interpolation
    n_vert   = pial_complete['np']

    region_map_lores = np.zeros((n_vert))

    vert_hires = pial_vertices
    vert_lores = pial_complete['rr']

    # search nearest neighbour
    idx = spatial.KDTree(vert_hires).query(vert_lores)[1]
    region_map_lores = region_map[idx]

    np.savetxt(session_outputdir+"/"+tvb_input+"/"+"region_mapping.txt", region_map_lores, fmt="%i")
    print("Regionmap saved !")

    # save in BIDS format
    BIDS_anat_folder = session_outputdir+"/"+"anat"
    if not os.path.exists(BIDS_anat_folder):
        os.makedirs(BIDS_anat_folder)

    # create gii label table
    gii_labeltb = nbg.GiftiLabelTable()

    for i in range(len(region_names)):
        gii_label = nbg.GiftiLabel(key=i,alpha=1,
                                   red   = np.random.uniform(0,1,1)[0],
                                   green = np.random.uniform(0,1,1)[0],
                                   blue  = np.random.uniform(0,1,1)[0],
                                  )
        gii_label.label = region_names[i]
        gii_labeltb.labels.append(gii_label)

    darrays = [nbg.GiftiDataArray(region_map_lores.astype("int32"), intent="NIFTI_INTENT_LABEL", datatype=8)]
    gii_image = nbg.GiftiImage(darrays=darrays, labeltable=gii_labeltb)
    nbg.giftiio.write(gii_image, BIDS_anat_folder+"/"+subvis+"_space-individual_dparc.label.gii")



    # write cortical surface (i.e. source space) to file
    cort_surf_path = session_outputdir+"/"+tvb_input+"/"+subvis+"_Cortex/"
    if not os.path.exists(cort_surf_path):
        os.makedirs(cort_surf_path)

    # surface vertices are in ras-tkr coordinates used by freesurfer
    # for them to allign with parc_image, use affine transform to bring them into ras-scanner
    p = Popen(('mri_info --tkr2scanner '+recon_all_dir+"/"+recon_all_name+"/mri/aparc+aseg.mgz").split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    affine_xfm = np.array([ i.split() for i in str(output, "utf-8").splitlines()], dtype="float")

    pial_vert_converted = affine_xfm.dot(np.concatenate((pial_complete['rr'] * 1000 ,np.ones((pial_complete['rr'].shape[0],1))), axis=1).T)[:3,:].T

    # save
    np.savetxt(cort_surf_path+"triangles.txt", pial_complete['tris'], fmt="%i")
    np.savetxt(cort_surf_path+"vertices.txt", pial_vert_converted, fmt="%f")
    np.savetxt(cort_surf_path+"normals.txt", pial_complete['nn'], fmt="%f")


    # zip files
    shutil.make_archive(cort_surf_path[:-1], 'zip', cort_surf_path)
    print("Cortical surface zipped !")
    shutil.rmtree(cort_surf_path)

    # save in BIDS format
    darrays = [nbg.GiftiDataArray(pial_vert_converted.astype("float32"), intent="NIFTI_INTENT_POINTSET")] + [nbg.GiftiDataArray(pial_complete['tris'].astype("int32"), intent="NIFTI_INTENT_TRIANGLE")]
    gii_image = nbg.GiftiImage(darrays=darrays)
    nbg.giftiio.write(gii_image, BIDS_anat_folder+"/"+subvis+"_space-individual_pial.surf.gii")


    # write BEM surfaces to file
    names = ["inner_skull_surface", "outer_skull_surface", "outer_skin_surface"] # "brain_surface",
    BIDS_names = ["innerskull", "outerskull", "scalp"]
    for i in range(len(names)) :
        name = names[i]
        BIDS_name = BIDS_names[i]
        # make dir
        bem_path = session_outputdir+"/"+tvb_input+"/"+subvis+"_"+name+"/"
        if not os.path.exists(bem_path):
            os.makedirs(bem_path)

        bem_surf = mne.read_surface(recon_all_dir+"/"+recon_all_name+"/bem/watershed/"+recon_all_name+"_"+name)
        bem_dict = {'rr':bem_surf[0], 'tris':bem_surf[1]}
        bem_complete = mne.surface.complete_surface_info(bem_dict)

        bem_vert_converted = affine_xfm.dot(np.concatenate((bem_complete['rr'] ,np.ones((bem_complete['rr'].shape[0],1))), axis=1).T)[:3,:].T


        # save files
        np.savetxt(bem_path+"triangles.txt", bem_complete['tris'], fmt="%i")
        np.savetxt(bem_path+"vertices.txt", bem_vert_converted, fmt="%f")
        np.savetxt(bem_path+"normals.txt", bem_complete['nn'], fmt="%f")

        # zip folder
        shutil.make_archive(bem_path[:-1], 'zip', bem_path)
        shutil.rmtree(bem_path)

        # save for BIDS
        darrays = [nbg.GiftiDataArray(bem_vert_converted.astype("float32"), intent="NIFTI_INTENT_POINTSET")] + [nbg.GiftiDataArray(bem_complete['tris'].astype("int32"), intent="NIFTI_INTENT_TRIANGLE")]
        gii_image = nbg.GiftiImage(darrays=darrays)
        nbg.giftiio.write(gii_image, BIDS_anat_folder+"/"+subvis+"_space-individual_" + BIDS_name + ".surf.gii")


    print("BEM surfaces saved  !")


    # save eeg_locations, are in ras-tkr coordinates used by freesurfer
    # for them to align with parc_image, use affine transform to bring them into ras-scanner
    eegp_loc_converted = affine_xfm.dot(np.concatenate((eegp_loc * 1000 ,np.ones((eegp_loc.shape[0],1))), axis=1).T)[:3,:].T

    f = open(session_outputdir+"/"+tvb_input+"/"+subvis+"_EEG_Locations.txt", "w")
    f_bids = open(BIDS_eeg_folder+"/"+subvis+"_task-simulation_electrodes.tsv", "w")
    f_bids.write("name\tx\ty\tz\n")
    for i in range((np.array(ch_type)=="eeg").sum()): # write only "eeg" electrodes (not "misc")
        f.write(mon.ch_names[i]+" "+"%.6f" %eegp_loc_converted[i,0]+" "+"%.6f" %eegp_loc_converted[i,1]+" "+"%.6f" %eegp_loc_converted[i,2]+"\n")
        f_bids.write(mon.ch_names[i]+"\t"+"%.6f" %eegp_loc_converted[i,0]+"\t"+"%.6f" %eegp_loc_converted[i,1]+"\t"+"%.6f" %eegp_loc_converted[i,2]+"\n")
    f.close()
    f_bids.close()
    print("EEG locations saved  !")

    # create connectome.zip (has six files)
    tvb_connectome_path = session_outputdir+"/"+tvb_input+"/"+subvis+"_Connectome/"
    if not os.path.exists(tvb_connectome_path):
        os.makedirs(tvb_connectome_path)

    #connectome: lengths
    BIDS_connectivity_folder = session_outputdir+"/connectivity"
    if not os.path.exists(BIDS_connectivity_folder):
        os.makedirs(BIDS_connectivity_folder)

    if os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/connectome_weights.csv"):
        # 1 weights, set diagonal to zero and make it symmetric
        weights = np.genfromtxt(resultsPath+"/"+subvis+"DWI_processing/connectome_weights.csv")
        weights[np.diag_indices_from(weights)] = 0
        i_lower = np.tril_indices_from(weights, -1)
        weights[i_lower] = weights.T[i_lower]
        n_regions = weights.shape[0]
        np.savetxt(tvb_connectome_path+"weights.txt", weights, delimiter="\t")

        #BIDS
        np.savetxt(BIDS_connectivity_folder+"/"+subvis+"_desc-weight_conndata-network_connectivity.tsv", weights, delimiter="\t")

        print("Weights saved  !")
    else:
        print("No weights file for: {}".format(subvis))

    # 2 tracts, set diagonal to zero and make it symmetric
    if os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/connectome_lengths.csv"):
        tracts  = np.genfromtxt(resultsPath+"/"+subvis+"DWI_processing/connectome_lengths.csv")
        tracts[np.diag_indices_from(tracts)] = 0
        i_lower = np.tril_indices_from(tracts, -1)
        tracts[i_lower] = tracts.T[i_lower]
        np.savetxt(tvb_connectome_path+"tract.txt", tracts, delimiter="\t")

        #BIDS
        np.savetxt(BIDS_connectivity_folder+"/"+subvis+"_desc-distance_conndata-network_connectivity.tsv", tracts, delimiter="\t")

        print("Tracts saved !")
    else:
        print("No tracts/lengths file for: {}".format(subvis))

    #create JSON for structural connectome
    if os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/connectome_weights.csv") & os.path.isfile(resultsPath+"/"+subvis+"DWI_processing/connectome_lengths.csv"):
        parcellation = hcpmmp1
        conn_json = {}
        conn_json["description"] = "Structural connectome, weights and distances (mm) derived from tractography"
        conn_json["source_node_info"] = {"parcellation" : parcellation}

        with open(resultsPath+"/"+subvis+"_conndata-network_connectivity.json", 'w') as outfile:
            json.dump(conn_json, outfile)

    #3. centers
    # create centroids
    # create centers file
    if os.path.isfile(resultsPath+"/"+subvis+"/"+"DWI_processing/diffusion_mask_overlap2subcortical_2dwi.nii.gz"):
        # create centroids
        img = nib.load(resultsPath+"/"+subvis+"/"+"DWI_processing/diffusion_mask_overlap2subcortical_2dwi.nii.gz")
        img_data = img.get_fdata().astype('int')
        # get the right coordinate transform to align region centroids with the surfaces
        # centers for BIDS
        f_bids = open(session_outputdir+"/"+subvis+"_desc-centroid_morph.tsv","w") #centres.txt
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
    else:
        print("No parcellation image for SC exists; centers file not created.")

    # 4 orientation
    # First get all Vertex-Normals corresponding to the Vertices of a Region
    # Now compute mean Vector and Normalize the Vector
    # for subcortical regions set [0,0,1]
    orientation = np.zeros((n_regions,3))

    for i in range(n_regions):
        if cortical[i]: # cortical regions
            nn  = pial_complete['nn'][ region_map_lores==i ,:]
            orientation[i,:] = nn.mean(axis=0)/np.linalg.norm(nn.mean(axis=0))

        elif not cortical[i]:  # subcortical regions
            # select normal vertices of a region, average and normalize them
            orientation[i,:] = np.array([0,0,1])

    np.savetxt(tvb_connectome_path+"orientation.txt", orientation, fmt="%f")
    print("Orientations saved !")

    # 5 area
    # I'm not quite sure how to get to the exact value for the surface in mm^2
    # so for now i just count the surface vertices corresponding to each region
    # EDIT: According to the TVB Dokumentation, this attribute is not mandatory
    # for the Input!
    area = np.zeros((n_regions,1))
    for i in range(n_regions):
        if cortical[i]: # cortical regions
            area[i] = np.sum(region_map_lores==i)

        elif not cortical[i]:  # subcortical regions
            area[i] = 0

    np.savetxt(tvb_connectome_path+"area.txt", area, fmt="%f")
    print("Area saved !")

    # 6 cortical
    # connectivity cortical/non-cortical region flags; text file containing one boolean value on each line
    # (as 0 or 1 value) being 1 when corresponding region is cortical.
    # due to error in configuring projection matrix in EEG, see monitors.py, class Projection, def config_for_sim
    # this would need to get fixed, otherwise I don't know how to define the cortical variable or the lead field matrix
    # therefor for now declare all regions as cortical
    cortical = np.ones((n_regions,1)).astype('int')
    np.savetxt(tvb_connectome_path+"cortical.txt", cortical, fmt="%i")
    print("Cortical saved !")

    # 7 hemisphere
    # text file containing one boolean value on each line
    # (as 0 or 1 value) being 1 when corresponding region is in the right hemisphere and 0 when in left hemisphere.
    np.savetxt(tvb_connectome_path+"hemisphere.txt", hemisphere, fmt="%i")
    print("Hemisphere saved !")

    # zip all files
    shutil.make_archive(tvb_connectome_path[:-1], 'zip', tvb_connectome_path)
    print("Connectome zipped !")
    shutil.rmtree(tvb_connectome_path)


    print("FINISH: save files for TVB")
    print("FINISH: create files not created by processing pipeline")

print("FINISH: loop through subjects")
print("Script FINISHED.")

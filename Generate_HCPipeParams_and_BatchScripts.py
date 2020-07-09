#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 14 14:45:43 2020

@author: Roopa Pai
"""

# Generate parameters for HCP pipeline

#import required modules
import json
import pandas as pd
import glob
import os
import pydicom as dc
from datetime import datetime
import numpy as np
import re

multiplevisits=False
if multiplevisits==False:
    subList = open("/path/to/subList.txt","r").readlines()
    subList = [x.strip("\n") for x in subList]
else:
    print ("check BIDS directory. If you have multiple visits per subject, you need to flatten it to use this script.")
    #if data is longitudinal (multiple visits per subject), e.g.: .../raw/sub-1234/{ADNIVisit1,ADNIVisit2}/{anat, dwi, fmap, func, pet}, the data needs to be flattened.
    # This is so the HCP scripts handle the input files/create output files as expected.
    # For each sub, for each visit, create a directory named, e.g.: sub-1234_ses-ADNIVisitX


    # pathList = open("/path/to/pathList.txt","r").readlines()
    # pathList = [x.strip("\n") for x in pathList]

    # for i,r in enumerate(pathList):
    #     groups = r.split('/')
    #     pathList[i] = '_ses-'.join(groups[-2:])


# PATH TO IMPORTANT DIRECTORIES
# "raw" data is a directory containing NIFTI files, organized according to the BIDS specification:
# $rawdataPath/$sub/$visit/{anat, dwi, fmap, func, pet}/***{.nii.gz, .json}


rawdataPath = "/path/to/raw"
resultsPath = "/path/to/resultsDir"
scratchPath="/path/to/scratchDir" # directory for MRtrix to create large tck files
FIX_training_file = "/path/to/*_Training.RData"
scriptsPath = "/path/to/write/batchSubmitterScripts" # where to write the sbatch submitter scripts. generic scripts should already be here.
logPath = "/path/to/write/logfiles"

logsubdirs = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob('{}/generic*.sh'.format(scriptsPath))]
for l in logsubdirs:
    os.makedirs(os.path.join(logPath, l),exist_ok=True)


# Functions to retrieve image parameters

def structural_scan_params(rawdataPath, sub):
    rawdataPath_sub=rawdataPath+"/"+sub

    # T1w and T2w Images
    T1_list=glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*T1w.nii.gz") + glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*T1w_defacemask.nii.gz")

    # use FLAIR image instead of T2, cause T2 is actually T2 Star with bad resolution
    FLAIR_images=glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*FLAIR.nii.gz") + glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*FLAIR_defacemask.nii.gz")
     if len(FLAIR_images) > 0:
         T2w_image=FLAIR_images[0]
     elif len(FLAIR_images) == 0:
         T2w_images=glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*T2w.nii.gz") + glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*T2w_defacemask.nii.gz")# + glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*T2star.nii.gz") + glob.glob(rawdataPath_sub+"/anat/"+"sub"+"*T2star_defacemask.nii.gz")
         if len(T2w_images) > 0:
             T2w_image = T2w_images[0] #not T2STAR because some of them are actually fieldmaps (ADNI mislabelling)
         else:
            print("Error retrieving image parameters for subject:", rawdataPath_sub)
    else:
        print("Error retrieving image parameters for subject:", rawdataPath_sub)
    # get Scanner Type
    data = json.loads(open(T1_list[0][:-6]+"json").read()) ##Manufacturer = json.loads(open(T1_list[0][:-6]+"json").read())['Manufacturer']
    if "Manufacturer" in data:
        Manufacturer = data["Manufacturer"]
    elif "ManufacturersModelName" in data:
        if data["ManufacturersModelName"] == "Skyra_fit":
            Manufacturer = "Siemens"
        else:
            Manufacturer = " "
    else:
        Manufacturer = " "

    if Manufacturer=='Philips' or Manufacturer=="GE" or Manufacturer==" ": return False

    #Model = json.loads(open(T1_list[0][:-6]+"json").read())['ManufacturersModelName']

    # when more then one T1 image exist
    if len(T1_list)>1:
        # if same date, take the one WITH gradient distortion correction
        T1_json_data = open(T1_list[0][:-6]+"json").read()
        data         = json.loads(T1_json_data)
        if len(data['ImageType'])<3:
            DC           = data['ImageType'][3]
            if DC=="NORM":
                T1w_image=T1_list[0]
            else:
                T1w_image=T1_list[1]
        else: # if T1 images differ on other feature than distortion correction use the first
            T1w_image=T1_list[0]
    else:
        T1w_image=T1_list[0]


    #######
    ####### Siemens
    #######
    if Manufacturer=="Siemens":

        AvgrdcSTRING="SiemensFieldMap"

        # Magnitude and Phase image
        MagnitudeImage1 = glob.glob(rawdataPath_sub+"/fmap/"+"sub"+"*_magnitude1*"+".nii.gz")[0]
        MagnitudeImage2 = glob.glob(rawdataPath_sub+"/fmap/"+"sub"+"*_magnitude2*"+".nii.gz")[0]
        PhaseImage = glob.glob(rawdataPath_sub+"/fmap/"+"sub"+"*phasediff*"+".nii.gz")[0]

        data = json.loads(open(MagnitudeImage1[:-7]+".json").read())
        EchoTime1 = data['EchoTime']
        data = json.loads(open(MagnitudeImage2[:-7]+".json").read())
        EchoTime2 = data['EchoTime']

        # for fslmerge create a name:
        MagnitudeImage4D="4DMagnitudeImage.nii.gz"

        # DwellTime for the fieldmap
        TE=format(abs(EchoTime1-EchoTime2)*1000,'.2f') # convert to ms

        # T1SampleSpacing and T2SampleSpacing:
        # DWT = 1/ReceiverBandWidth = 1 / PixelBandWidth * NumberFrequencyEncondingSteps / ParallelReductionFactorInPlane
        data = json.loads(open(T1w_image[:-7]+".json").read())
        if 'DwellTime' in data:
            T1SampleSpacing=format(data['DwellTime'], '.8f')
        elif 'ParallelReductionFactorInPlane' in data :
            T1SampleSpacing= (1 / (data['PixelBandwidth'] * data['BaseResolution'])) / data['ParallelReductionFactorInPlane']
        elif 'BaseResolution' in data :
            T1SampleSpacing= 1 / (data['PixelBandwidth'] * data['BaseResolution'])
        elif 'ReconMatrixPE' in data :
            T1SampleSpacing= 1 / (data['PixelBandwidth'] * data['ReconMatrixPE'])
        else :
            print("problem for sub",sub," with T1SampleSpacing.")

        data = json.loads(open(T2w_image[:-7]+".json").read())
        if 'DwellTime' in data:
            T2SampleSpacing=format(data['DwellTime'], '.8f')
        elif 'ParallelReductionFactorInPlane' in data :
            T2SampleSpacing= (1 / (data['PixelBandwidth'] * data['ReconMatrixPE'])) / data['ParallelReductionFactorInPlane']
        else :
            T2SampleSpacing= 1 / (data['PixelBandwidth'] * data['ReconMatrixPE'])

        # Unwarp direction for structural scans
        UnwarpDirStruct_name=data['InPlanePhaseEncodingDirectionDICOM']
        #print(UnwarpDirStruct_name)
        if UnwarpDirStruct_name == "ROW":
            UnwarpDirStruct="y" # in json "InPlanePhaseEncodingDirectionDICOM": "ROW",
        else:
            print("Unwarp dir not ROW")

        return (rawdataPath_sub+"/anat/"+os.path.basename(T1w_image),
            rawdataPath_sub+"/anat/"+os.path.basename(T2w_image),
            AvgrdcSTRING,
            rawdataPath_sub+"/fmap/"+os.path.basename(MagnitudeImage1),
            rawdataPath_sub+"/fmap/"+os.path.basename(MagnitudeImage2),
            rawdataPath_sub+"/fmap/"+MagnitudeImage4D,
            rawdataPath_sub+"/fmap/"+os.path.basename(PhaseImage),
            str(TE),
            str(T1SampleSpacing),
            str(T2SampleSpacing),
            UnwarpDirStruct)


    #######
    ####### GE
    #######

    elif Manufacturer=="GE":
        # ADNI GE Scanners don't provide any kind of fieldmaps
        # so no distortion correction is possible
        AvgrdcSTRING="NONE"
        MagnitudeImage1="NONE"
        MagnitudeImage2="NONE"
        MagnitudeImage4D="NONE"
        PhaseImage="NONE"
        TE="NONE"
        T1SampleSpacing="NONE"
        T2SampleSpacing="NONE"
        UnwarpDirStruct="NONE"

        return (rawdataPath_sub+os.path.basename(T1w_image),
            rawdataPath_sub+os.path.basename(T2w_image),
            AvgrdcSTRING,
            MagnitudeImage1,
            MagnitudeImage2,
            MagnitudeImage4D,
            PhaseImage,
            TE,
            T1SampleSpacing,
            T2SampleSpacing,
            UnwarpDirStruct)

    #######
    ####### Philips
    #######

    elif Manufacturer=="Philips":
        ###
        AvgrdcSTRING="SiemensFieldMap"

        MagnitudeImage1="NONE"
        MagnitudeImage2="NONE"
        MagnitudeImage4D="NONE"
        PhaseImage1="NONE"
        PhaseImage2="NONE"
        TE="NONE"


        # T1SampleSpacing and T2SampleSpacing:
        # DWT = 1/ReceiverBandWidth = 1 / PxielBandWidth * NumberFrequencyEncondingSteps / ParallelReductionFactorInPlane
        data = json.loads(open(T1w_image[:-7]+".json").read())
        if 'DwellTime' in data:
            T1SampleSpacing=format(data['DwellTime'], '.8f')
        elif 'ParallelReductionFactorInPlane' in data :
            T1SampleSpacing= (1 / (data['PixelBandwidth'] * data['BaseResolution'])) / data['ParallelReductionFactorInPlane']
        else :
            T1SampleSpacing= 1 / (data['PixelBandwidth'] * data['BaseResolution'])

        data = json.loads(open(T1w_image[:-7]+".json").read())
        if 'DwellTime' in data:
            T1SampleSpacing=format(data['DwellTime'], '.8f')
        elif 'ParallelReductionFactorInPlane' in data :
            T1SampleSpacing= (1 / (data['PixelBandwidth'] * data['BaseResolution'])) / data['ParallelReductionFactorInPlane']
        else :
            T1SampleSpacing= 1 / (data['PixelBandwidth'] * data['BaseResolution'])


        UnwarpDirStruct_name=data['InPlanePhaseEncodingDirectionDICOM']
        print(UnwarpDirStruct_name)

        if UnwarpDirStruct_name == "ROW":
            UnwarpDirStruct="y" # in json "InPlanePhaseEncodingDirectionDICOM": "ROW",
        else:
            print("Unwarp dir not ROW")

        return (rawdataPath_sub + "/anat/" + os.path.basename(T1w_image),
                rawdataPath_sub + "/anat/" + os.path.basename(T2w_image),
                AvgrdcSTRING,
                rawdataPath_sub + "/fmap/" + os.path.basename(MagnitudeImage1),
                rawdataPath_sub + "/fmap/" + os.path.basename(MagnitudeImage2),
                rawdataPath_sub + "/fmap/" + MagnitudeImage4D,
                rawdataPath_sub + "/fmap/" + os.path.basename(PhaseImage),
                str(TE),
                str(T1SampleSpacing),
                str(T2SampleSpacing),
                UnwarpDirStruct)


def fmri_scan_params(rawdataPath, sub):
    rawdataPath_sub = rawdataPath+"/"+sub

    # fMRI image
    fMRITimeSeries=glob.glob(rawdataPath_sub+"/func/"+"sub"+"*bold*"+"*nii.gz")[0]
    data = json.loads(open(fMRITimeSeries[:-7]+".json").read())
    #Image Resolution
    FinalFMRIResolution=data['SliceThickness']

    #Manufacturer
    if "Manufacturer" in data:
        Manufacturer = data["Manufacturer"]
    elif "ManufacturersModelName" in data:
        if data["ManufacturersModelName"] == "Skyra_fit":
            Manufacturer = "Siemens"
        else:
            Manufacturer = " "
    else:
        Manufacturer = " "

    if Manufacturer=='Philips' or Manufacturer=="GE" or Manufacturer==" ": return False

    if Manufacturer=="Siemens":
        DistortionCorrection="SiemensFieldMap"
        PEdir = data['PhaseEncodingDirection']

        def switch_PEdir(argument):
            switcher = {
                "i" : "x",
                "i-": "-x",
                "j" : "y",
                "j-": "-y",
                "k" : "z",
                "k-": "-z",
            }
            return switcher.get(argument, "Invalid direction")

        UnwarpDirfMRI=switch_PEdir(PEdir)

        # DwellTime
        # BPPPE = data['BandwidthPerPixelPhaseEncode']
        # n_PE_samples= data['AcquisitionMatrixPE']
        # DwellTime=1/(BPPPE*n_PE_samples)/ParallelReductionFactor (or Accelaration) #--> equals 'EffectiveEchoSpacing' in .json
        DwellTime = data['EffectiveEchoSpacing']


    elif Manufacturer == "GE":
        UnwarpDirfMRI = "NONE"
        DwellTime     = "NONE"
        DistortionCorrection = "NONE"


    elif Manufacturer =="Philips":
        print("Philips FMRI NOT YET INCLUDED")
        print("Philips FMRI NOT YET INCLUDED")
        print("Philips FMRI NOT YET INCLUDED")
        print("Philips FMRI NOT YET INCLUDED")
        UnwarpDirfMRI = "NONE"
        DwellTime     = "NONE"
        DistortionCorrection = "NONE"

    return (UnwarpDirfMRI,
            rawdataPath_sub + "/func/" + os.path.basename(fMRITimeSeries),
            str(DwellTime),
            DistortionCorrection,
            str(FinalFMRIResolution))

def DWI_scan_params(rawdataPath, sub):

    rawdataPath_sub = rawdataPath+"/"+sub

    # dwi image
    # some subjects have different DTI files, use the one we find bvec and bvals for
    json_list = glob.glob(rawdataPath_sub+"/dwi/"+"sub"+"*dwi*""*json")
    for j in json_list:
        json_file = j
        bvecs = json_file[0:-5]+".bvec"
        bvals = json_file[0:-5]+".bval"
        dwi_image = json_file[0:-5]+".nii.gz"

        if ((not bvecs) | (not bvals) | (not dwi_image)):
            continue
        else:
            break

    #  dwidenoise dwipreproc
    data = json.loads(open(dwi_image[:-7]+".json").read())
    def switch_PEdir(argument):
        switcher = {
            "i" : "RL",
            "i-": "LR",
            "j" : "PA",
            "j-": "AP",
            "k" : "IS",
            "k-": "SI",
        }
        return switcher.get(argument, "Invalid direction")

    UnwarpDirDWI=switch_PEdir(data['PhaseEncodingDirection'])

    EffectiveEchoSpacing = data['EffectiveEchoSpacing']

    if UnwarpDirDWI=="RL" or UnwarpDirDWI=="LR":
        UnwarpDirDWI_ants = "1x0x0"
    elif UnwarpDirDWI=="PA" or UnwarpDirDWI=="AP":
        UnwarpDirDWI_ants = "0x1x0"
    elif UnwarpDirDWI=="IS" or UnwarpDirDWI=="SI":
        UnwarpDirDWI_ants = "0x0x1"


    return (rawdataPath_sub+"/dwi/"+os.path.basename(dwi_image),
            rawdataPath_sub+"/dwi/"+os.path.basename(bvecs),
            rawdataPath_sub+"/dwi/"+os.path.basename(bvals),
            UnwarpDirDWI,
            UnwarpDirDWI_ants)

def PET_scan_params(rawdataPath, sub):
    rawdataPath_sub = rawdataPath+"/"+sub

    AV1451_image=glob.glob(rawdataPath_sub+"/pet/"+"sub"+"*AV1451*"+"*nii.gz")[0]
    AV45_image=glob.glob(rawdataPath_sub+"/pet/"+"sub"+"*AV45*"+"*nii.gz")[0]

    return(rawdataPath_sub+"/pet/"+os.path.basename(AV1451_image),
           rawdataPath_sub+"/pet/"+os.path.basename(AV45_image))


# MAIN: WRITE BATCH SUBMITTER FILES
# write the sbatch command to these files for each subject
batch_prefreesurf_list                 = open(scriptsPath+"/batch01_prefreesurf.sh","w")
batch_freesurf_list                    = open(scriptsPath+"/batch02_freesurf.sh","w")
batch_postfreesurf_list                = open(scriptsPath+"/batch03_postfreesurf.sh","w")
batch_fmri_volume_list                 = open(scriptsPath+"/batch04_fmri_volume.sh","w")
batch_fmri_surface_list                = open(scriptsPath+"/batch05_fmri_surface.sh","w")
batch_icafix_list                      = open(scriptsPath+"/batch06_icafix.sh","w")
batch_postfix_list                     = open(scriptsPath+"/batch07_postfix.sh","w")
batch_msmall_list                      = open(scriptsPath+"/batch08_msmall.sh","w")
batch_dedriftresample_list             = open(scriptsPath+"/batch09_dedriftresample.sh","w")
batch_denoise_preproc_list             = open(scriptsPath+"/batch10_denoise_preproc.sh","w")
batch_dwibiascorrect_dwi2mask_list     = open(scriptsPath+"/batch11_dwi_distortionCorrection.sh","w")
batch_dwiintensitynorm_list            = open(scriptsPath+"/batch12_dwiintensitynorm.sh","w")
batch_T1w2dwi_5ttgen_dwi2response_list = open(scriptsPath+"/batch13_T1w2dwi_5ttgen_dwi2response.sh","w")
batch_averageresponse_list             = open(scriptsPath+"/batch14_averageresponse.sh","w")
batch_dwi_2fod_tckgen_sift2_list       = open(scriptsPath+"/batch15_dwi_2fod_tckgen_sift2.sh","w")
batch_create_diffusion_mask_list       = open(scriptsPath+"/batch16_create_diffusion_mask.sh","w")
batch_tck2connectome_list              = open(scriptsPath+"/batch17_tck2connectome.sh","w")
batch_extract_PET_data_list            = open(scriptsPath+"/batch18_extract_PET_data.sh","w")
batch_extract_fmri_list                = open(scriptsPath+"/batch19_extract_fmri.sh","w")

#add line at top declaring interpreter
batch_prefreesurf_list.write("#!/bin/bash" + "\n")
batch_freesurf_list.write("#!/bin/bash" + "\n")
batch_postfreesurf_list.write("#!/bin/bash" + "\n")
batch_fmri_volume_list.write("#!/bin/bash" + "\n")
batch_fmri_surface_list.write("#!/bin/bash" + "\n")
batch_icafix_list.write("#!/bin/bash" + "\n")
batch_postfix_list.write("#!/bin/bash" + "\n")
batch_msmall_list.write("#!/bin/bash" + "\n")
batch_dedriftresample_list.write("#!/bin/bash" + "\n")
batch_denoise_preproc_list.write("#!/bin/bash" + "\n")
batch_dwibiascorrect_dwi2mask_list.write("#!/bin/bash" + "\n")
batch_dwiintensitynorm_list.write("#!/bin/bash" + "\n")
batch_averageresponse_list.write("#!/bin/bash" + "\n")
batch_dwi_2fod_tckgen_sift2_list.write("#!/bin/bash" + "\n")
batch_create_diffusion_mask_list.write("#!/bin/bash" + "\n")
batch_tck2connectome_list.write("#!/bin/bash" + "\n")
batch_extract_PET_data_list.write("#!/bin/bash" + "\n")
batch_extract_fmri_list.write("#!/bin/bash" + "\n")

for sub in subList:

    ########################
    ##### Structural #######
    ########################

    # get parameters
    params_struct = structural_scan_params(rawdataPath, sub)
    if params_struct == False: continue # i.e. if Scanner Manufacturer == Philips/GE or unlisted

    # print to files
    batch_prefreesurf_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic01_prefreesurf",sub,logPath,"generic01_prefreesurf",sub,"generic01_prefreesurf") +" "+
                          resultsPath+" " +
                          sub+" "+
                          params_struct[0]+" "+            # T1w image
                          params_struct[1]+" "+            # T2w image
                          params_struct[2]+" "+            # AvgrdcSTRING
                          params_struct[3]+" "+            # Magnitudeimage 1
                          params_struct[4]+" "+            # Magnitudeimage 2
                          params_struct[5]+" "+            # Magnitudeimage 4D
                          params_struct[6]+" "+            # Phase image
                          str(params_struct[7])+" "+       # TE
                          str(params_struct[8])+" "+       # T1SampleSpacing
                          str(params_struct[9])+" "+       # T2SampleSpacing
                          params_struct[10]+               # UnwarpDirStruct
                          "\n")

    batch_freesurf_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic02_freesurf",sub,logPath,"generic02_freesurf",sub,"generic02_freesurf") +" "+
                          resultsPath+" "+
                          sub+" "+
                          "\n")

    batch_postfreesurf_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic03_postfreesurf",sub,logPath,"generic03_postfreesurf",sub,"generic03_postfreesurf") +" "+
                              resultsPath+" "+
                              sub+" "+
                              "\n")


    ########################
    ###### fMRI Volume #####
    ########################

    params_fmri = fmri_scan_params(rawdataPath, sub)
    if params_fmri == False: continue # i.e. if Scanner Manufacturer == Philips/GE or unlisted

    # print to list
    batch_fmri_volume_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic04_fmri_volume",sub,logPath,"generic04_fmri_volume",sub,"generic04_fmri_volume") +" "+
                                  resultsPath+" "+
                                  sub+" "+
                                  params_fmri[0]+" "+        # UnwarpDirfMRI
                                  params_fmri[1]+" "+        # fMRI TImeseries
                                  params_fmri[2]+" "+        # DwellTime
                                  params_fmri[3]+" "+        # DistrotionCorrection
                                  params_struct[5]+" "+      # Magnitude 4D
                                  params_struct[6]+" "+      # Phaseimage
                                  params_struct[7]+" "+      # TE
                                  params_fmri[4]+"\n"        # FinalFMRIResolution
                                  )

    batch_fmri_surface_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic05_fmri_surface",sub,logPath,"generic05_fmri_surface",sub,"generic05_fmri_surface") +" "+
                              resultsPath+" "+
                              sub+" "+
                              params_fmri[4]+"\n")


    #######################
    ######### FIX ########
    #######################

    batch_icafix_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic06_icafix",sub,logPath,"generic06_icafix",sub,"generic06_icafix") +" "+
                              resultsPath+" "+
                              sub+" "+
                              resultsPath+"/"+sub+"/MNINonLinear/Results/Restingstate/Restingstate.nii.gz"+" "+
                              FIX_training_file+"\n")

    batch_postfix_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic07_postfix",sub,logPath,"generic07_postfix",sub,"generic07_postfix") +" "+
                              resultsPath+" "+
                              sub+"\n")


    #######################
    ####### MSM all #######
    #######################

    batch_msmall_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic08_msmall",sub,logPath,"generic08_msmall",sub,"generic08_msmall") +" "+
                              resultsPath+" "+
                              sub+"\n"+
                              "sleep 1m"+"\n")

    batch_dedriftresample_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic09_dedriftresample",sub,logPath,"generic09_dedriftresample",sub,"generic09_dedriftresample") +" "+
                              resultsPath+" "+
                              sub+"\n"+
                              "sleep 1m"+"\n")

    ########################
    ######### DWI ##########
    ########################

    #get scan params and file names
    dwi_params = DWI_scan_params(rawdataPath, sub)

    batch_denoise_preproc_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic10_denoise_preproc",sub,logPath,"generic10_denoise_preproc",sub,"generic10_denoise_preproc") +" "+
                             resultsPath+" "+
                             sub+" "+
                             dwi_params[0]+" "+    # DWI image
                             dwi_params[1]+" "+    # DWI bvecs
                             dwi_params[2]+" "+    # DWI bval
                             dwi_params[3]+"\n")   # Phase-encoding dir

    batch_dwibiascorrect_dwi2mask_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic11_dwibiascorrect_dwi2mask",sub,logPath,"generic11_dwibiascorrect_dwi2mask",sub,"generic11_dwibiascorrect_dwi2mask") +" "+
                            resultsPath+" "+
                            sub +" "+
                            dwi_params[4]+" "+ # PE dir as 0x1x0 (ie. like ANTS format))
                            "True "+           # "Use Jacobian"
                            "True" + "\n")     # "Use bias field"


    # batch_dwiintensitynorm_list comes later, outside loop.
    batch_T1w2dwi_5ttgen_dwi2response_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic13_T1w2dwi_5ttgen_dwi2response",sub,logPath,"generic13_T1w2dwi_5ttgen_dwi2response",sub,"generic13_T1w2dwi_5ttgen_dwi2response") +" "+
                            resultsPath+" "+
                            sub+"\n")

    # batch_average_response_list.sh comes later, outside loop.
    batch_dwi_2fod_tckgen_sift2_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic15_dwi_2fod_tckgen_sift2",sub,logPath,"generic15_dwi_2fod_tckgen_sift2",sub,"generic15_dwi_2fod_tckgen_sift2") +" "+
                            resultsPath+" "+
                            sub+" "+
                            scratchPath+"\n")

    batch_create_diffusion_mask_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic16_create_diffusion_mask",sub,logPath,"generic16_create_diffusion_mask",sub,"generic16_create_diffusion_mask") +" "+
                            resultsPath+" "+
                            sub+"\n")

    batch_tck2connectome_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic17_tck2connectome",sub,logPath,"generic17_tck2connectome",sub,"generic17_tck2connectome") +" "+
                            resultsPath+" "+
                            sub+" "+
                            scratchPath+"\n")



    ########################
    ######### PET ##########
    ########################

    pet_params = PET_scan_params(rawdataPath, sub)

    batch_extract_PET_data_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic18_extract_PET_data",sub,logPath,"generic18_extract_PET_data",sub,"generic18_extract_PET_data") +" "+
                                resultsPath+" "+
                                sub+" "+
                                pet_params[0]+" "+
                                pet_params[1]+"\n")



    batch_extract_fmri_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic19_extract_fmri",sub,logPath,"generic19_extract_fmri",sub,"generic19_extract_fmri") +" "+
                                resultsPath+" "+
                                sub+" "+
                                "Restingstate"+"\n")

#batch12_dwiintensitynorm: only one line, uses all subs. write outside loop.
batch_dwiintensitynorm_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic12_dwiintensitynorm","generic12_dwiintensitynorm",logPath,"generic12_dwiintensitynorm","generic12_dwiintensitynorm","generic12_dwiintensitynorm") +" "+
                                  resultsPath)

#batch14_averageresponse: only one line, uses all subs. write outside loop.
batch_averageresponse_list.write("sbatch -o {}/{}/output_{}.txt -e {}/{}/error_{}.txt {}.sh".format(logPath,"generic14_averageresponse","generic14_averageresponse",logPath,"generic14_averageresponse","generic14_averageresponse","generic14_averageresponse") +" "+
                                 resultsPath)

# close the sbatch submitters
batch_prefreesurf_list.close()
batch_freesurf_list.close()
batch_postfreesurf_list.close()
batch_fmri_volume_list.close()
batch_fmri_surface_list.close()
batch_icafix_list.close()
batch_postfix_list.close()
batch_msmall_list.close()
batch_dedriftresample_list.close()
batch_denoise_preproc_list.close()
batch_dwibiascorrect_dwi2mask_list.close()
batch_dwiintensitynorm_list.close()
batch_T1w2dwi_5ttgen_dwi2response_list.close()
batch_averageresponse_list.close()
batch_dwi_2fod_tckgen_sift2_list.close()
batch_create_diffusion_mask_list.close()
batch_tck2connectome_list.close()
batch_extract_PET_data_list.close()
batch_extract_fmri_list.close()

#!/usr/bin/env python3
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=24:00:00
#SBATCH --partition=medium


# automated_MINDSJSON-writer
# This script produces a collection of MINDS JSONs, which describe the dataset
# according to HBP minimal metadata criteria (MINDS v1).

#To be done by user:
#1. specify paths in Part I.
#2. specify schema variants/names in Part III.
#3. In some cases (e.g. dataset schema), due to assumptions made, the user may want to modify attributes of classes in Part II. e.g.:
# dataset desciption/license, species ontologicalTerm or the ranges of method numbers included in each activity.
# This will differ based on individual use-case.

## I. Set-up
#import packages, set up links, create directory structure

#### import packages
import os
import pandas as pd
from braceexpand import braceexpand
import json

#### link to BIDS-organized dataset
# specify path to dataset, organized according to the BIDS specification.

BIDSroot = ""
participants_tsv = pd.read_csv(BIDSroot+"/participants.tsv", sep='\t',dtype={'participant_id': str})

#### create "MINDS JSONs" directory structure
# specify path to MINDS JSON collection. Create the directory structure specified by MINDS v1

MINDSroot = ""
for x in list(braceexpand(MINDSroot+'/core/{activity,agecategory,dataset,person,preparation,sex,species,specimengroup}/v1.0.0')): os.makedirs(x, exist_ok=True)
for x in list(braceexpand(MINDSroot+'/ethics/{approval,authority}/v1.0.0')): os.makedirs(x, exist_ok=True)
for x in list(braceexpand(MINDSroot+'/experiment/{method,subject}/v1.0.0')): os.makedirs(x, exist_ok=True)

## II. Define function & classes: used to create JSONs from schemas

#The function *openMINDSschemaWriter* accepts arguments for schema type, etc.
#The class *baseSchema* defines attributes common to all schemas. It also defines a default function for naming & writing JSON files (files are named: schemaName-0X.json)

#All further classes are based on the *baseSchema* class. They define additional attributes (fill the keys of the specific schemas (JSON templates)). Additionally, in some cases, they may implement a modified function to rename JSONs; JSONs will be named according to the schema's *name* field.

def openMINDSschemaWriter(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI=""):
    if schema_type == "person":
        return personSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "sex":
        return sexSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "species":
        return speciesSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "authority":
        return authoritySchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "approval":
        return approvalSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "method":
        return methodsSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "preparation":
        return preparationSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "activity":
        return activitySchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "agecategory":
        return agecategorySchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "specimengroup":
        return specimengroupSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "simulator":
        return simulatorSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "subject":
        return subjectSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)
    if schema_type == "dataset":
        return datasetSchema(schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI)

class baseSchema:
    def __init__(self, schema_type, MINDSroot, schema_dir, schema_name, schema_json, dataRoot, relatedIRI):
        self.schema_type = schema_type
        self.schema_dir = MINDSroot + schema_dir
        self.schema_name = schema_name
        self.schema_json = schema_json
        self.relatedIRI = relatedIRI
        self.fileNum = str(len([file for file in os.listdir(self.schema_dir) if os.path.isfile(os.path.join(self.schema_dir, file))]) + 1).zfill(3)
    def writeJSON(self):
        #generic JSON naming scheme [<schemaName>-0X.json]. override in specific class if "name" naming required.
        with open(self.schema_dir+"/"+self.schema_type+"-"+self.fileNum+".json","w") as f:
            json.dump(self.schema_json, f, indent=4)

class personSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        shortName = ""
        shortName = shortName + self.schema_name.split(",")[0] + ", "
        for w in self.schema_name.split(",")[1].split():
            shortName = shortName + w[0].upper() + ". "
        shortName.rstrip()
        self.schema_json["shortName"] = shortName

class sexSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
    def writeJSON(self): #overwrite baseSchema "writeJSON". #name.
        with open(self.schema_dir+"/"+self.schema_name+".json","w") as f:
            json.dump(self.schema_json, f, indent=4)

class speciesSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        self.schema_json["ontologicalTerm"] = [{"@id": "ontologies/core/metazoa/v1.0.0/63b90ba0-66be-4969-8a6a-d19ebea01115"}]
    def writeJSON(self): #overwrite baseSchema "writeJSON". #name.
        with open(self.schema_dir+"/homo-sapiens.json","w") as f:
            json.dump(self.schema_json, f, indent=4)

class authoritySchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name

class approvalSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        self.schema_json["generatedBy"] = [{"@id": "minds/ethics/authority/v1.0.0/"+file} for file in os.listdir(MINDSroot + "/ethics/authority/v1.0.0")]

class methodsSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        self.schema_json["relatedIRI"] = self.relatedIRI

class preparationSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name

class activitySchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        self.schema_json["approval"] = [{"@id": "minds/ethics/approval/v1.0.0/"+file} for file in os.listdir(MINDSroot + "/ethics/approval/v1.0.0")]
        self.schema_json["authority"] = [{"@id": "minds/ethics/authority/v1.0.0/"+file} for file in os.listdir(MINDSroot + "/ethics/authority/v1.0.0")]
        if self.schema_name == "MRI-T1w":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-001.json"}]
        elif self.schema_name == "MRI-T2W":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-002.json"}]
        elif self.schema_name == "MRI-T2STAR":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-003.json"}]
        elif self.schema_name == "MRI-FLAIR":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-004.json"}]
        elif self.schema_name == "resting state fMRI":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-005.json"},
                                           {"@id": "minds/experiment/method/v1.0.0/method-08.json"}]
        elif self.schema_name == "DWI":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-006.json"}]
        elif self.schema_name == "PET":
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-007.json"}]

        elif self.schema_name == "DWI-ImageProcessing": #(method#s: 6 & 9-15)
            methodNums = [str(6).zfill(3)] \
                        + [str(i).zfill(3) for i in range(9,15+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "T1-imageProcessing": #(method#s: 1 & 16-29)
            methodNums = [str(1).zfill(3)] \
                        + [str(i).zfill(3) for i in range(16,29+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "rsfMRI-ImageProcessing": #(method#s: 5 & 8 & 30-34 & 20 & 35 & 19 & 36-40)
            methodNums = [str(i).zfill(3) for i in [5,8]] \
                        + [str(i).zfill(3) for i in range(30,34+1)] \
                        + [str(20).zfill(3)] \
                        + [str(35).zfill(3)] \
                        + [str(19).zfill(3)] \
                        + [str(i).zfill(3) for i in range(36,40+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "PET-ImageProcessing": #(method#s: 7 & 41-44 & 34 & 22)
            methodNums = [str(7).zfill(3)] \
                        + [str(i).zfill(3) for i in range(41,44+1)] \
                        + [str(34).zfill(3)] \
                        + [str(22).zfill(3)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        ### not sure how far back in the pipeline to chain methods into the below activities
        #(e.g.: when creating cortical surfaces do we need to start as far back as T1 acquisition, or just start from creating subject-specific annot files?)
        # at the moment, the previous/upstream methods have not been included.
        elif self.schema_name == "create cortical surface and region mapping": #(method#s: 45-51)
            methodNums = [str(i).zfill(3) for i in range(45,51+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "compute source space":
            methodNums = [str(i).zfill(3) for i in range(52,54+1)] #(method#s: 52-54)
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "compute BEM model & EEG Locations": #(method#s: 55-60)
            methodNums = [str(i).zfill(3) for i in range(55,60+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "compute forward solution": #(method#s: 61-63)
            methodNums = [str(i).zfill(3) for i in range(61,63+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "save derivatives accoording to TVB specifications": # (method#: 64-70)
            methodNums = [str(i).zfill(3) for i in range(64,70+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        elif self.schema_name == "PhenotypicandAssessmentData": #(method#s: 71-81)
            methodNums = [str(i).zfill(3) for i in range(71,81+1)]
            self.schema_json["methods"] = [{"@id": "minds/experiment/method/v1.0.0/method-{}.json".format(i)} for i in methodNums]

        self.schema_json["preparation"] = [{"@id": "minds/core/preparation/v1.0.0/"+file} for file in os.listdir(MINDSroot + "/core/preparation/v1.0.0")]

class agecategorySchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name

class specimengroupSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        self.schema_json["subjects"] = []


class subjectSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.schema_name + ".json"
        self.schema_json["name"] = self.schema_name
        participants_tsv = pd.read_csv(BIDSroot + "/participants.tsv", sep='\t',dtype={'participant_id': str})
        self.schema_json["age"] = str(participants_tsv[participants_tsv["participant_id"]==self.schema_name]["Age"].item()) + " years"
        self.schema_json["ageCategory"] = [{"@id" : "minds/core/agecategory/v1.0.0/agecategory-01.json"}] #if participants_tsv[participants_tsv["participant_id"]==self.schema_name]["Age"].item() > 18 else []
        self.schema_json["sex"] = [{"@id" : "minds/core/sex/v1.0.0/male.json"}] if participants_tsv[participants_tsv["participant_id"]==self.schema_name]["Sex"].item() == "M" else [{"@id" : "minds/core/sex/v1.0.0/female.json"}]
        self.schema_json["species"] = [{"@id" : "minds/core/species/v1.0.0/homo-sapiens.json"}]
    def writeJSON(self): #overwrite baseSchema "writeJSON". #name by subject ID.
        with open(self.schema_dir+"/"+self.schema_name.replace(" ","")+".json","w") as f:
            json.dump(self.schema_json, f, indent=4)

class datasetSchema(baseSchema):
    def fillJSON(self):
        self.schema_json["@type"] = "https://schema.hbp.eu/minds/"+self.schema_type+".schema.json"
        self.schema_json["@id"] = "minds"+ self.schema_dir.split(MINDSroot,1)[1] + "/" + self.schema_type + "-" + self.fileNum + ".json"
        self.schema_json["name"] = self.schema_name
        self.schema_json["description"] = "Example MINDS metadata collection, created using data organized according to the BIDS specification.",
        self.schema_json["owners"] = [{"@id": "minds/core/person/v1.0.0/"+os.listdir(MINDSroot + "/core/person/v1.0.0")[0]}],
        self.schema_json["contributors"] = [ {"@id": "minds/core/person/v1.0.0/"+file} for file in os.listdir(MINDSroot + "/core/person/v1.0.0")],
        self.schema_json["embargoStatus"] = "free",
        self.schema_json["license"] = [{"@id": "licenses/core/information/v1.0.0/7377a480-6066-4c47-9be8-67c586713ed7"}],
        self.schema_json["activities"] = [{"@id": "minds/core/activity/v1.0.0"+"/"+file} for file in os.listdir(MINDSroot + "/core/activity/v1.0.0")]
        self.schema_json["specimenGroups"] = [{"@id": "minds/core/specimengroups/v1.0.0"+"/"+file} for file in os.listdir(MINDSroot + "/core/specimengroup/v1.0.0")]

## III. Specify schemas and instances. Fill & create JSONs using the functions/classes specified above.
#### person
person_schema = {
    "@type": "",
    "@id": "",
    "name": "",
    "shortName": "",
}

person_vec = ["Pai, Roopa Kalsank", "Doe, John", "Doe, Jane"]

for person_name in person_vec:
    person = openMINDSschemaWriter("person", MINDSroot, "/core/person/v1.0.0", person_name, person_schema, BIDSroot)
    person.fillJSON()
    person.writeJSON()

#### sex
sex_schema = {
  "@type": "",
  "@id": "",
  "name": "",
}

sex_vec = ["female","male"]

for sex_name in sex_vec:
    sex = openMINDSschemaWriter("sex", MINDSroot, "/core/sex/v1.0.0", sex_name, sex_schema, BIDSroot)
    sex.fillJSON()
    sex.writeJSON()

#### species
species_schema = {
  "@type": "",
  "@id": "",
  "name": "",
  "ontologicalTerm": []
}

species_vec = ["Homo sapiens"]

for species_name in species_vec:
    species = openMINDSschemaWriter("species", MINDSroot, "/core/species/v1.0.0", species_name, species_schema, BIDSroot)
    species.fillJSON()
    species.writeJSON()

#### ethics authority
authority_schema = {
  "@type": "",
  "@id": "",
  "name": ""
}
authority_vec = ["Ethics Board of ABC University"]

for authority_name in authority_vec:
    authority = openMINDSschemaWriter("authority", MINDSroot, "/ethics/authority/v1.0.0", authority_name, authority_schema, BIDSroot)
    authority.fillJSON()
    authority.writeJSON()

#### ethics approval
approval_schema = {
    "@type": "",
    "@id": "",
    "name": "",
    "generatedBy": []
}
approval_vec = ["EA/ID/01"]

for approval_name in approval_vec:
    approval = openMINDSschemaWriter("approval", MINDSroot, "/ethics/approval/v1.0.0", approval_name, approval_schema, BIDSroot)
    approval.fillJSON()
    approval.writeJSON()

#### method
#1. Depends on how many modalities you include / which processing stages you include.
#2. this script includes acquisition, image processing, and creation of TVB-format files.
#3. if user edits this, user will also need to edit "activity-methodrange" relationships in the activity schema in Part II.

method_schema = {
    "@type": "",
    "@id": "",
    "name": ""
}

method_vec = [#acquisition
              "T1-weighted magnetic resonance imaging (T1w-MRI)",
              "T2-weighted magnetic resonance imaging (T2w-MRI)",
              "T2star-weighted magnetic resonance imaging (T2star-MRI)",
              "FLAIR magnetic resonance imaging (FLAIR-MRI)",
              "functional magnetic resonance imaging (fMRI)",
              "diffusion-weighted magnetic resonance imaging (DWI)",
              "positron-emission tomography (PET)",
              "resting state",
              #DWI processing (6 & 9-15)
              "noise removal",
              "Gibbs ringing artifact removal",
              "eddy current correction",
              "motion correction",
              "bias field correction",
              "global intensity normalization",
              "tractography",
               #T1 processing (1 & 16-29)
              "ACPC alignment",
              "brain extraction",
              "readout distortion correction",
              "bias field correction",
              "registration to MNI space",
              "segmentation",
              "parcellation",
              "spline interpolated downsample",
              "cortical reconstruction",
              "adjust pial surface",
              "convert to GIFTI format",
              "create cortical ribbon",
              "myelin mapping",
              "multimodal surface matching",
               #rsfMRI processing (5 & 8 & 30-34 & 20 & 35 & 19 & 36-40)
              "motion correction",
              "EPI distortion correction",
              "boundary based registration",
              "gradient non-linearity distortion correction",
              "convert to CIFTI format",
              #"registration to MNI space" <---point to prev. one
              "intensity normalization",
              #"bias removal" <-- point to prev. one
              "ribbon volume to surface mapping",
              "surface smoothing",
              "subcortical processing",
              "generation of dense timeseries",
              "denoise using spatial ICA",
               #PET processing (7 & 41-44 & 34 & 22)
              "registration to T1w",
              "partial volume correction",
              "normalize by cerebellar white matter signal",
              "volume to surface mapping",
              #"conversion to CIFTI format", <---use prev one
              #"parcellation", <---use prev one

              #create TVB input files (45 - 70)
              ### create cortical surface and region mapping ### (45-51)
              "create a FreeSurfer-style subject-specific parcellation of subjects' brains using HCP atlas",
              "read surfaces, and convert units of the vertex positions",
              "merge left and right surfaces",
              "edit parcellation region names",
              "assign hemisphere to each region",
              "create region map of high-res pial surface",
              "remove subcortical vertices",

              ### compute source space ### (52-54)
              "decimate surface",
              "complete decimated surface",
              "construct source space dictionary",

              ### compute BEM model + EEG Locations ### (55-60)
              "make watershed BEM",
              "make bem model",
              "make bem solution",
              "make standard montage",
              "create info object",
              "project eeg locations onto surface",

              ### compute forward solution ### (61-63)
              "make forward solution",
              "convert forward solution",
              "remove subcortical vertices from leadfield",

              ### save derivatives according to TVB specifications ### (64-70)
              #
              "get region map for source space (downsampled pial), via nearest neighbour interpolation",
              "create GIfTI label table",
              #
              "affine transform surface vertices from ras-tkr coordinates (used by freesurfer) into ras-scanner",
              "zip pial triangles, vertices, normals to create cortical surfaces zipfile",
              #
              "affine transform BEM vertices from ras-tkr coordinates (used by freesurfer) into ras-scanner",
              "zip BEM triangles, vertices, normals to create skull surface zipfiles",
              #connectome.zip
              "zip connectome weights, tracts, centers, orientation, area, cortical, hemisphere",

              #Phenotypic and Assessment Data (71-81)
              "Alzheimer's Disease Assessment Scale",
              "Clinical Dementia Rating Scale",
              "Everyday Cognition - Patient",
              "Everyday Cognition – Study Partner",
              "Functional Activities Questionnaire",
              "Financial Capacity Instrument",
              "Geriatric Depression Scale - 15 item",
              "Mini Mental State Examination",
              "Montreal Cognitive Assessment",
              "Neuropsychological Battery",
              "Neuropsychiatric Inventory",
             ]
#vec order important

IRI_vec = [#acquisition
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              #DWI processing
              "",
              "",
              "",
              "",
              "",
              "",
              "",
               #T1 processing
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
               #rsfMRI processing
              "",
              "",
              "",
              "",
              "",
              #"registration to MNI space" <---point to prev. one
              "",
              #"bias removal" <-- use prev. one
              "",
              "",
              "",
              "",
              "",
               #PET processing
              "",
              "",
              "",
              "",
              #"conversion to CIFTI format", <---use prev one
              #"parcellation", <---use prev one

              #create TVB files
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",

              #Phenotypic and Assessment Data
              "http://uri.interlex.org/base/ilx_0346295",
              "http://uri.interlex.org/base/ilx_0102250",
              "",
              "",
              "",
              "",
              "",
              "http://uri.interlex.org/base/ilx_0106984",
              "",
              "",
              "http://uri.interlex.org/base/ilx_0239290"
             ]

for i,method_name in enumerate(method_vec):
    method = openMINDSschemaWriter("method", MINDSroot, "/experiment/method/v1.0.0", method_name, method_schema, BIDSroot,IRI_vec[i])
    method.fillJSON()
    method.writeJSON()

#### preparation
preparation_schema = {
  "@type": "",
  "@id": "",
  "name": ""
}

preparation_vec = ["in-vivo"]

for preparation_name in preparation_vec:
    preparation = openMINDSschemaWriter("preparation", MINDSroot, "/core/preparation/v1.0.0", preparation_name, preparation_schema, BIDSroot)
    preparation.fillJSON()
    preparation.writeJSON()

#### activity
# One *activity* needed for each *method*. Multiple *methods* can combine to create an *activity*. e.g. fMRI (method) + resting state (method) = resting state fMRI (activity)

activity_schema = {
    "@type": "",
    "@id": "",
    "name": "",
    "approval": [],
    "authority": [],
    "methods": [],
    "preparation":[]
}

activity_vec = [#acquisition
                "MRI-T1w",
                "MRI-T2W",
                "MRI-T2STAR",
                "MRI-FLAIR",
                "resting state fMRI",
                "DWI",
                "PET",
                #processing
                "DWI-ImageProcessing",
                "T1-ImageProcessing",
                "rsfMRI-ImageProcessing"
                "PET-ImageProcessing",

                #reorganize script/create TVB input files
                "create cortical surface and region mapping"
                "compute source space",
                "compute BEM model & EEG Locations",
                "compute forward solution",
                "save derivatives accoording to TVB specifications",

                # phenotypic data
                "PhenotypicandAssessmentData"
                ]
#vec order important

for activity_name in activity_vec:
    activity = openMINDSschemaWriter("activity", MINDSroot, "/core/activity/v1.0.0", activity_name, activity_schema, BIDSroot)
    activity.fillJSON()
    activity.writeJSON()

#### age category
agecat_schema = {
  "@type": "",
  "@id": "",
  "name": ""
}
age_vec = ["adult"]

for agecat_name in age_vec:
    agecat = openMINDSschemaWriter("agecategory", MINDSroot, "/core/agecategory/v1.0.0", agecat_name, agecat_schema, BIDSroot)
    agecat.fillJSON()
    agecat.writeJSON()

#### specimen group
specimengroup_schema = {
  "@type": "",
  "@id": "",
  "name": "",
  "subjects": []
}

specimengroup_vec = ["Cognitively Normal (CN)", "Mild Cognitive Impairment (MCI)", "Alzheimer's Disease (AD)"]

for specimengroup_name in specimengroup_vec:
    specimengroup = openMINDSschemaWriter("specimengroup", MINDSroot, "/core/specimengroup/v1.0.0", specimengroup_name, specimengroup_schema, BIDSroot)
    specimengroup.fillJSON()
    specimengroup.writeJSON()

#### subject
subject_schema = {
  "@type": "",
  "@id": "",
  "name": "",
  "age": "",
  "ageCategory": [],
  "sex": [],
  "species": []
}

subject_vec = [sub for sub in participants_tsv["participant_id"].tolist()]

for subject_name in subject_vec:
    subject = openMINDSschemaWriter("subject", MINDSroot, "/experiment/subject/v1.0.0", subject_name, subject_schema, BIDSroot)
    subject.fillJSON()
    subject.writeJSON()

#### loop back and add relevant data to specimen group JSONs
for sg_JSON_file in os.listdir(MINDSroot + "/core/specimengroup/v1.0.0"):
    with open(MINDSroot + "/core/specimengroup/v1.0.0"+"/"+sg_JSON_file,"r") as f:
        sg_JSON_data = json.load(f)
        sg_name = sg_JSON_data["name"]
        if "CN" in sg_name:
            for sub in participants_tsv["participant_id"].tolist():
                if participants_tsv[participants_tsv["participant_id"]==sub]["Research Group"].item() == "CN":
                    sg_JSON_data["subjects"].append({"@id": "minds/experiment/subject/v1.0.0/"+sub+".json"})
        elif "MCI" in sg_name:
            for sub in participants_tsv["participant_id"].tolist():
                if "MCI" in participants_tsv[participants_tsv["participant_id"]==sub]["Research Group"].item():
                    sg_JSON_data["subjects"].append({"@id": "minds/experiment/subject/v1.0.0/"+sub+".json"})
        elif "AD" in sg_name:
            for sub in participants_tsv["participant_id"].tolist():
                if participants_tsv[participants_tsv["participant_id"]==sub]["Research Group"].item() == "AD":
                    sg_JSON_data["subjects"].append({"@id": "minds/experiment/subject/v1.0.0/"+sub+".json"})
    with open(MINDSroot + "/core/specimengroup/v1.0.0"+"/"+sg_JSON_file,"w") as f:
        json.dump(sg_JSON_data, f, indent=4)

#### finally, write the dataset JSON
#Notes/assumptions:
#1. owners: default: first "person"
#2. contributors: all persons
#3. embargoStatus: leave as is for now
#4. license: leave as is for now
#5. description: hardcode or editable? for the moment, hardcode inside class definition. if other schemas also take descriptions, add "description" as function argument.

dataset_schema = {
  "@type": "",
  "@id": "",
  "name": "",
  "description": "",
  "owners": [],
  "contributors": [],
  "embargoStatus": "",
  "license": [],
  "activities": [],
  "specimenGroups": []
}

dataset_vec = ["Test dataset JSON-LD schema."]

for dataset_name in dataset_vec:
    dataset = openMINDSschemaWriter("dataset", MINDSroot, "/core/dataset/v1.0.0", dataset_name, dataset_schema, BIDSroot)
    dataset.fillJSON()
    dataset.writeJSON()

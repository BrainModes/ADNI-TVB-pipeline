#!/bin/bash

sbatch --export=ALL -D ./ -o output_batch01_reorganize.txt -e error_batch01_reorganize.txt /fast/work/groups/ag_ritter/MR_processing/ADNI/Paul/02_after-processing_scripts/01_reorganize.py

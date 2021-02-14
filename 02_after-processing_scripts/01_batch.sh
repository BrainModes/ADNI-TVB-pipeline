#!/bin/bash

#EDIT: location where scripts are located
sbatch --export=ALL -D ./ -o output_batch01_reorganize.txt -e error_batch01_reorganize.txt /path/to/02_after-processing_scripts/01_reorganize.py

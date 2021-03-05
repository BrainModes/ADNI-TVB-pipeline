#!/bin/bash

#EDIT: location where scripts are located
sbatch --export=ALL -D ./ -o output_01_reorganize.txt -e error_01_reorganize.txt /path/to/02_after-processing_scripts/01_reorganize.py

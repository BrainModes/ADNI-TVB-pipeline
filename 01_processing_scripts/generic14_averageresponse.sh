#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=12G
#SBATCH --time=08:30:00
#SBATCH --partition=medium

results_path=$1
average_response `find ${results_path} -name "RF_WM_tournier.txt"` ${results_path}/average_response.txt

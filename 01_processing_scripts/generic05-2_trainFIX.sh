#!/bin/bash
#SBATCH -D ./
#--export=ALL
#SBATCH --mem-per-cpu=6G
#SBATCH --time=12:00:00
#SBATCH --partition=medium

/usr/local/fix/fix -t <Training> [-l]  <Melodic1.ica> <Melodic2.ica> ...

#!/bin/bash 
#!/bin/bash
#$ -cwd
#$ -V
#$ -l h_vmem=12G
#$ -l h_rt=08:30:00
#$ -q medium.q
#$ -P medium

results_path=$1
average_response `find ${results_path} -name "RF_WM_tournier.txt"` ${results_path}/average_response.txt

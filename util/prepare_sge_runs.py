#!/usr/bin/env python3

"""
A script to setup numerous grid runs of the targeted assembly pipeline for a 
SGE environment. Copy the preparation_file_examples directory and modify the 
contents of those files accordingly except for those that start with 
PLACEHOLDER_*. 

Input: 
    1. A CSV file with each line containing: /path/to/reads1,/path/to/reads2

    2. An input directory which mirrors the contents of preparation_file_examples
    directory found in this repository's location. Contents of the files should be 
    modified except for those elements that start with PLACEHOLDER_*.

    3. Location of an output directory to have all these runs output to.

Output: 
    1. A set of directories at the specified path to populate with the results
    of the pipeline. Each will also contain its own *.sh and *.yml file for
    running the pipeline.

    2. A preparation_map.csv file which tells you which directory belongs to 
    which set of input reads. Columns are ID,qsub,reads1,reads2. These qsub
    commands can then be used individually to run each job on the grid. 

    3. Outputs to the terminal a command to run the pipelines as an array job.
    The benefit of this is that it will better constrain how many possible 
    resources this will consume on the grid (-tc argument). The downside is that
    all of the ~.err and ~.out files will be found in two consolidated files 
    making it harder to pinpoint errors in specific runs. 

Usage:
    prepare_grid_runs.py -c read_info_file.csv -i /dir/for/master/files -o /path/to/out/dir

Author: 
    James Matsumura
"""

import argparse
import errno
import os

def main():

    parser = argparse.ArgumentParser(description='Script to setup numerous targeted assembly runs in an SGE environment.')
    parser.add_argument('-c', type=str, required=True, help='Path to a two-column csv file with first column being the location of the reads1 and second being reads2.')
    parser.add_argument('-i', type=str, required=True, help='Input directory with cwl.sh,qsub,targeted_assembly.yml files present.')
    parser.add_argument('-o', type=str, required=True, help='Location to generate output directories.')
    args = parser.parse_args()

    make_directory(args.o)

    with open("{}/cwl.sh".format(args.i),'r') as sh_infile:
        sh_content = sh_infile.read()

    with open("{}/cwl.sh".format(args.o),'w') as sh_outfile:

        content = sh_content                   
        content = content.replace('PLACEHOLDER_OUTDIR',"{}/$SGE_TASK_ID".format(args.o))
        content = content.replace('PLACEHOLDER_YML',"{}/$SGE_TASK_ID/targeted_assembly.yml".format(args.o))

        sh_outfile.write("{}\n".format('#!/bin/sh'))
        sh_outfile.write(content)

    with open("{}/qsub".format(args.i),'r') as qsub_infile:
        qsub_content = qsub_infile.read().strip()

    with open("{}/targeted_assembly.yml".format(args.i),'r') as yml_infile:
        yml_content = yml_infile.read()

    with open("{}/preparation_map.csv".format(args.o),'w') as prep_map: 

        prep_map.write("{}\n".format((',').join(['ID','qsub','reads1','reads2'])))

        with open(args.c,'r') as reads_file: 

            run_id = 0
            
            for line in reads_file:

                run_id += 1 

                reads = line.strip().split(',')
                reads1,reads2 = reads[0],reads[1]

                cur_out_dir = "{}/{}".format(args.o,run_id) 
                make_directory(cur_out_dir)

                with open("{}/cwl.sh".format(cur_out_dir),'w') as sh_outfile:

                    content = sh_content                   
                    content = content.replace('PLACEHOLDER_OUTDIR',cur_out_dir)
                    content = content.replace('PLACEHOLDER_YML',"{}/targeted_assembly.yml".format(cur_out_dir))

                    sh_outfile.write(content)

                with open("{}/targeted_assembly.yml".format(cur_out_dir),'w') as yml_outfile:

                    content = yml_content
                    content = content.replace('PLACEHOLDER_READS1',reads1)
                    content = content.replace('PLACEHOLDER_READS2',reads2)

                    yml_outfile.write(content)

                qsub_cmd = replace_placeholders_in_qsub(qsub_content,cur_out_dir)

                prep_map.write("{}\n".format((',').join([str(run_id),qsub_cmd,reads1,reads2])))

    array_job = replace_placeholders_in_qsub(qsub_content,args.o)
    array_job = array_job.split()
    jobs = "-t 1-{} -tc 15".format(run_id) # by default, restrict to 15 simultaneous jobs
    print("{} {} {}".format((' ').join(array_job[:-1]),jobs,array_job[-1]))


def replace_placeholders_in_qsub(qsub_str,cur_dir):
    """ 
    Takes in a qsub command and a directory to rewrite the PLACEHOLDER_* 
    arguments found within the base qsub file.
    """
    qsub_str = qsub_str.replace('PLACEHOLDER_CWL_SH',"{}/cwl.sh".format(cur_dir))
    qsub_str = qsub_str.replace('PLACEHOLDER_CWL_OUT',"{}/cwl.out".format(cur_dir))
    qsub_str = qsub_str.replace('PLACEHOLDER_CWL_ERR',"{}/cwl.err".format(cur_dir))
    return qsub_str

def make_directory(path):
    """ Takes in a path and tries to build that directory """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


if __name__ == '__main__':
    main()
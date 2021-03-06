#!/usr/bin/env python3

# This script wraps the script to perform Hierarchical Genome Assembly (HGA):
# (https://github.com/aalokaily/Hierarchical-Genome-Assembly-HGA).
# The script needs to be wrapped in order to maintain the original read 
# storage structure as well as take advantage of SGE. This script requires
# the path to Python 2.7, the output map file from final_verdict.py, the path to 
# HGA.py, the path to Velvet, the path to SPAdes, the insert size + standard 
# deviation of the alignment (can use Picard Tools CollectInsertSIzeMetrics 
# to obtain this information), the number of threads to use, the path to 
# the output directory for HGA to write to, and the SGE ID. 
#
# Run the script using a command like this:
# wrap_HGA.py --python /path/to/python-2.7 --assembly_verdict_map /path/to/final_verdict_out.tsv --hga /path/to/HGA.py --velvet /path/to/velvet --spades /path/to/spades --insert insert_size -std standard_deviation --threads num_of_threads 6 --reads_dir /path/to/reads_dir --out_dir /path/to/out_dir --sge_id 1 -m 18
#
# Author: James Matsumura

import re,argparse,subprocess,sys

def main():

    parser = argparse.ArgumentParser(description='Script to run HGA.py on SGE.')
    parser.add_argument('--python', '-pyt', type=str, required=True, help='Path to Python 2.7 install.')
    parser.add_argument('--assembly_verdict_map', '-avm', type=str, required=True, help='Path to output from assembly_verdict.py.')
    parser.add_argument('--hga', '-hga', type=str, required=True, help='Path to HGA.py.')
    parser.add_argument('--velvet', '-vel', type=str, required=True, help='Path to Velvet installation.')
    parser.add_argument('--spades', '-spa', type=str, required=True, help='Path to SPAdes installation.')
    parser.add_argument('--insert', '-ins', type=int, required=True, help='Insert size.')
    parser.add_argument('--std', '-std', type=int, required=True, help='Standard deviation of insert size.')
    parser.add_argument('--threads', '-t', type=int, required=True, help='Number of threads to use.')
    parser.add_argument('--memory', '-m', type=int, required=True, help='How much memory, in GB, to request from SPAdes.')
    parser.add_argument('--partitions', '-p', type=int, required=True, help='Number of partitions to split into HGA.')
    parser.add_argument('--reads_dir', '-rd', type=str, required=True, help='Base path to where the reads are stored.')
    parser.add_argument('--out_dir', '-o', type=str, required=True, help='Base path to where HGA.py should write the new assemblies out to.')
    parser.add_argument('--sge_id', '-si', type=int, required=True, help='Newest assigned SGE ID of this particular assembly.')
    args = parser.parse_args()

    original_sge_id = 0 # find the previous SGE grid value for where the reads are stored
    reads_loc,out_loc = ("" for i in range(2))

    with open(args.final_verdict_map,'r') as i:
        for line in i:
            line = line.rstrip()
            elements = line.split('\t')
            if args.sge_id == int(elements[2]): # If we find the mapping point, leave
                original_sge_id = elements[1]
                break

    if original_sge_id == 0: # isn't mapped so doesn't need to be re-assembled
        sys.exit()

    reads_loc = "{0}/{1}/reads.fastq".format(args.reads_dir,original_sge_id)
    # By default, the reads are gunzipped so need to uncompress. 
    subprocess.call("gunzip {0}.gz".format(reads_loc).split())

    hga_assmb_path = "{0}/{1}".format(args.out_dir,original_sge_id)
    # Cleanup a bit of the unnecessary files. 
    remove_fastqs = "{0}/*.fastq".format(hga_assmb_path)
    remove_partitions = "{0}/part*assembly".format(hga_assmb_path)

    command = ("{0} {1} -velvet {2} -spades {3} -PA SPAdes -P12 {4} -R12 {5}"
         " -ins {6} -std {7} -Pkmer 31 -Rkmer 81 -t {8} -P {12} -out {9} -m {13}"
         " && rm {10} && rm -rf {11}"
         .format(args.python,args.hga,args.velvet,args.spades,reads_loc,reads_loc,args.ins,args.std,args.threads,hga_assmb_path,remove_fastqs,remove_partitions,args.partitions,args.memory)
    )

    subprocess.call(command.split())

if __name__ == '__main__':
    main()
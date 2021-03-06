#!/usr/bin/env python3

# This script wraps the scaffold_builder.py script:
# (https://github.com/metageni/Scaffold_builder).
# This script requires the path to Python 2.7, the output map file from 
# final_verdict.py, the path to scaffold_builder.py, the path to the output from
# extract_alleles.py, path to the original FASTA file, path to the directory where
# all the HGA assemblies have gone, and the SGE ID. 
#
# Run the script using a command like this:
# wrap_Scaffold_builder.py --python /path/to/python-2.7 -sb /path/to/scaffold_builder.py --assembly_verdict_map /path/to/final_verdict_out.tsv --ea_map /path/to/ea_map.tsv --fasta /path/to/original.fasta  --hga_dir /path/to/hga/assemblies --sge_id 1
#
# Author: James Matsumura

import re,argparse,subprocess,sys
import os.path
from Bio import SeqIO

def main():

    parser = argparse.ArgumentParser(description='Script to run HGA.py on SGE.')
    parser.add_argument('--python', '-pyt', type=str, required=True, help='Path to Python 2.7 install.')
    parser.add_argument('--sb', '-sb', type=str, required=True, help='Path to scaffold_builder.py.')
    parser.add_argument('--assembly_verdict_map', '-avm', type=str, required=True, help='Path to output from assembly_verdict.py.')
    parser.add_argument('--ea_map', '-eam', type=str, required=True, help='Path to output from extract_alleles.py.')
    parser.add_argument('--fasta', '-f', type=str, required=True, help='Path to original FASTA file (these should not have buffered regions).')
    parser.add_argument('--hga_dir', '-hd', type=str, required=True, help='Base path to where the HGA assemblies can be found.')
    parser.add_argument('--sge_id', '-si', type=int, required=True, help='Newest assigned SGE ID of this particular assembly.')
    args = parser.parse_args()

    original_sge_id = 0 # find the previous SGE grid value for where the reads are stored
    locus_of_interest,ea_locus = ("" for i in range(2))

    with open(args.final_verdict_map,'r') as i:
        for line in i:
            line = line.rstrip()
            elements = line.split('\t')
            if args.sge_id == int(elements[2]): # If we find the mapping point, leave
                original_sge_id = elements[1]
                locus_of_interest = elements[0]
                break

    if original_sge_id == 0: # not in the map so irrelevant
        sys.exit()

    # Now that we know where to do work, build the reference file for just the
    # relevant locus. First need to get all the correct sequences.
    allele_list = []
    with open(args.ea_map,'r') as i:
        for line in i:
            line = line.rstrip()
            elements = line.split('\t')

            # Need to handle the case where the reference locus is 
            # split into multiple like ABC123.1,ABC123.2,etc.
            if '.' in elements[0]:
                ea_locus = elements[0].split('.')[0]
            else:
                ea_locus = elements[0]

            if ea_locus == locus_of_interest:
                for x in range(1,len(elements)): # grab all the alleles
                    allele_list.append(elements[x].split('|')[4])

    # Extract and write out the sequences. 
    seq_dict = SeqIO.to_dict(SeqIO.parse(args.fasta,"fasta"))

    # First check if HGA worked
    query = "{0}/{1}/HGA_combined/contigs.fasta".format(args.hga_dir,original_sge_id)

    # If HGA built contigs, build both F/R scaffolds to align to
    if os.path.isfile(query):

        f_fasta = "{0}/{1}/f_locus.fasta".format(args.hga_dir,original_sge_id)
        with open(f_fasta,'w') as out:
            for allele in allele_list:
                seq = seq_dict[allele]
                SeqIO.write(seq,out,"fasta")

        r_fasta = "{0}/{1}/r_locus.fasta".format(args.hga_dir,original_sge_id)
        with open(r_fasta,'w') as out:
            for allele in allele_list:
                seq = seq_dict[allele]
                seq.seq = seq.seq.reverse_complement()
                SeqIO.write(seq,out,"fasta")

        f_out = "{0}/{1}/f".format(args.hga_dir,original_sge_id)
        r_out = "{0}/{1}/r".format(args.hga_dir,original_sge_id)

        command = "{0} {1} -q {2} -r {3} -p {4}".format(args.python,args.sb,query,f_fasta,f_out)
        subprocess.call(command.split())
        command = "{0} {1} -q {2} -r {3} -p {4}".format(args.python,args.sb,query,r_fasta,r_out)
        subprocess.call(command.split())

    else:
        print("HGA could not assemble locus:{0}\n".format(locus_of_interest))

if __name__ == '__main__':
    main()
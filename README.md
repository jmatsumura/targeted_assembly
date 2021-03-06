# targeted_assembly
A pipeline to perform targeted assembly of individual loci given WGS reads, reference genome assemblies, and a primary reference annotation (GFF3)

## Dependencies
- Python 3.5
  * [Biopython](https://pypi.python.org/pypi/biopython/1.66)
  * [pysam](https://pypi.python.org/pypi/pysam)
- Python 2.7 (Needed for the externally developed scripts, HGA+Scaffold Builder, as well as CWL)
  * [cwlref-runner](https://pypi.python.org/pypi/cwlref-runner)
  * [pyyaml](https://pypi.python.org/pypi/PyYAML)
- [GSNAP](http://research-pub.gene.com/gmap/) - tested with release 2017-01-14
- [SMALT](http://www.sanger.ac.uk/science/tools/smalt-0) - tested with v0.7.6
- [SPAdes](http://bioinf.spbau.ru/spades) - tested with v3.10.1
- [Velvet](https://www.ebi.ac.uk/~zerbino/velvet/) - tested with v1.2.10
- [EMBOSS](http://emboss.open-bio.org/) - tested with v6.6.0.0
- Python Scripts (automatically pulled when running the pipeline)
  * [Hierarchical Genome Assembly Tool (HGA)](https://github.com/jmatsumura/Hierarchical-Genome-Assembly-HGA)
    * [Original for reference](https://github.com/aalokaily/Hierarchical-Genome-Assembly-HGA)
  * [Scaffold Builder](https://github.com/jmatsumura/Scaffold_builder)
    * [Original for reference](https://github.com/metageni/Scaffold_builder)

## Required Inputs
* Annotated GFF3+FASTA file for a genome (FASTA containing the whole chromosomes/sequence-regions that matches the positions noted in GFF3)
* OPTIONAL 
  * A mapped (via GMAP) annotated reference genome to any others if one wants to pool together reference loci to recruit reads for one locus' assembly across alleles
* A TSV file noting the path of the GFF3+FASTA file(s) in the format specified in the top of [extract_alleles.py](https://github.com/jmatsumura/targeted_assembly/blob/master/bin/extract_alleles.py) -- [example](https://github.com/jmatsumura/targeted_assembly/blob/master/example_data/ea_input.tsv)
* A list of loci to focus the assembly on (note you will need to include all isoforms of a locus when using CWL and assembling at the locus level so ABC_123.1, ABC_123.2, etc.) -- [example](https://github.com/jmatsumura/targeted_assembly/blob/master/example_data/subset_list.txt)
* Two FASTQ paired reads files from the isolate to perform targeted assembly with

Example files can be found in the [`./example_data`](https://github.com/jmatsumura/targeted_assembly/tree/master/example_data) directory.

## Usage
The pipeline can be run as individual Python scripts or via Command Workflow Language ([CWL]((http://www.commonwl.org/draft-3/UserGuide.html#Writing_Workflows)))

### Pipeline steps (all scripts found in ./bin)
1. Build a map for the alleles extracted from GFF3
  * `extract_alleles.py` 
2. Extract sequences for all references given the previous scripts output
  * `extract_sequences.py`
3. Set up the working directories and locations for outputs
  * `build_workspace.py`
4. GSNAP
  * Build index
  * align
  * optional, but can compress SAM to BAM here
5. Analyze BAM to map reads to refs and vice-versa 
  * `analyze_bam.py`
6. Assign all the reads to their own directories for each reference
  * `fastq_reads_to_fastq_alleles.py`
7. Rename all the directories to format for running SPAdes on the grid 
  * `format_for_assembly.py`
8. Assembly (either via SPAdes or HGA)
  * `run_parallel_assembly.py`
9. Run alignment 
  * `threaded_alignment.py`
10. Run assessment to isolate the best assemblies and overall stats
  * `threaded_assess_alignment.py`
11. If there are any remaining loci that could not assemble at a desired minimum threshold, can isolate these reference sequences to another round of the pipeline and use a different aligner/sensitivity. Note that using this step will essentially format the data similar to the end of step 3
  * `assembly_verdict.py`
12. Obtain assembled sequences
  * `get_final_sequences.py`
13. Try assemble those that the previous assembler could not
  * `run_parallel_assembly.py`
14. Rerun alignment using these new assemblies
  * `threaded_alignment.py`
15. Assess these new assemblies
  * `threaded_assess_alignment.py`
16. Build a dataset for those that cannot align
  * `assembly_verdict.py`
17. Obtain assembled sequences (can concatenate these results with those from step `12`)
  * `get_final_sequences.py`
18. Repeat steps 4-18, but at step 4 use the SMALT aligner

### Workflow (all relevant files found in ./cwl)
Please refer to the [README.md](https://github.com/jmatsumura/targeted_assembly/tree/master/cwl#running-the-tool-via-common-workflow-language-cwl) under the `./cwl` directory for more information on how to run this tool via CWL.

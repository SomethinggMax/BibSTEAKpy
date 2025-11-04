import argparse
import history_manager
from utils import file_parser, file_generator, enrichment, cleanup, abbreviations_exec


def enr_clean_col(absolute_path):
    bib_file = file_parser.parse_bib(absolute_path)
    history_manager.initialise_history(bib_file)

    cleanup.cleanup(bib_file)
    enrichment.sanitize_bib_file(bib_file)
    cleanup.cleanup(bib_file)
    abbreviations_exec.execute_abbreviations(bib_file, True, 10000)

    file_generator.generate_bib(bib_file, absolute_path)
    history_manager.commit(bib_file)


if __name__ == '__main__':
    # You can run this script using 'python example_script.py -path=<absolute\path>'
    parser = argparse.ArgumentParser(
        description="Script that enriches, cleans and collapses original file, while saving history."
    )
    parser.add_argument("-path", required=True, type=str)
    args = parser.parse_args()

    enr_clean_col(args.path)

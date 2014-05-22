import argparse
import sys

from openelexdataia.parser import BaseParser, ParserState

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("infile", nargs='?', type=argparse.FileType('r'),
    default=sys.stdin, help="input filename")
arg_parser.add_argument("outfile", nargs='?', type=argparse.FileType('w'), 
    default=sys.stdout, help="output filename")

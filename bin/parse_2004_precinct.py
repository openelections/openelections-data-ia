#!/usr/bin/env python
"""
Parse 2004 precinct-level general election results.
"""
import csv

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia.parser.precinct2004 import ResultParser, fields

if __name__ == "__main__":
    args = arg_parser.parse_args()

    parser = ResultParser(args.infile)
    writer = csv.DictWriter(args.outfile, fields)
    try:
        parser.parse()
    except Exception:
        msg = "Exception at line {} of input file, in state {}\n"
        print(msg.format(parser.line_number, parser.current_state.name))
        print("Line: {}".format(parser.current_line))
        raise

    writer.writeheader()
    for result in parser.results:
        writer.writerow(result)

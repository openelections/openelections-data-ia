#!/usr/bin/env python

"""
Parse the precinct-level results for the 2011 State Senate District 35
contest

The PDF file is an image PDF, so we need to extract it by running the
ocr_2011_special_ss_35_precicnt.sh script.

"""
import csv
import re

from openelexdata.us.ia import arg_parser

# Just hard-code the candidate names.  The results file uses a weird
# numeric map
candidates = ["John Calhoun", "Jack Whitver", "WRITE-IN", "OVER VOTES", 
    "UNDERVOTES"] 

# Ditto for parties
parties = ["DEM", "REP", "", "", ""]

result_line_re = re.compile(r'\d{4}')


def clean_precinct_number(s):
    if s == "Z":
        return 2
    elif s == "l":
        return 1
    else:
        return s

def clean_place_name(s):
    if "EN" in s or s.startswith("ARE?"):
        return "ANKENY"
    elif s.startswith("CROCK"):
        return "CROCKER"
    elif s.endswith("RIMES"):
        return "GRIMES"
    elif s.startswith("SHELDAHL"):
        return "SEHLDAHL-UNION"
    elif s.endswith("ASHINGTON"):
        return "WASHINGTON"
    elif re.match(r'SA(Y|V)LOR', s):
        return "SAYLOR"
    else:
        return s

def clean_votes(s):
    if s in ("D", "[I", "(I", "(1"):
        return 0
    else:
        return s


fields = [
    'office',
    'district',
    'candidate',
    'party',
    'reporting_level',
    'jurisdiction',
    'precinct_code',
    'votes',
]


if __name__ == "__main__":
    args = arg_parser.parse_args()

    writer = csv.DictWriter(args.outfile, fields)

    for raw_line in args.infile:
        line = raw_line.strip()
        if result_line_re.match(line):
            bits = re.split(r'\s+', line) 
            precinct_code = bits[0]
            precinct_number_idx = len(bits) - len(candidates) - 1
            vote_start_idx = precinct_number_idx + 1
            precinct_number = clean_precinct_number(bits[precinct_number_idx])
            precinct_place_name = clean_place_name(
                " ".join(bits[1:precinct_number_idx]))

            if precinct_number == "SPECIAL":
                precinct_place_name = "SPECIAL"
                precinct_number = ""
            
            for i in range(vote_start_idx, len(bits)):
                votes = clean_votes(bits[i])
                writer.writerow({
                    'office': "State Senate",
                    'district': 35,
                    'candidate': candidates[i - vote_start_idx],
                    'party': parties[i - vote_start_idx],
                    'reporting_level': 'precinct',
                    'jurisdiction': "{} {!s}".format(precinct_place_name,
                        precinct_number).strip(),
                    'precinct_code': precinct_code,
                    'votes': votes,
                })

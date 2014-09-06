#!/usr/bin/env python

"""
Reshape the data from the format in the original PDF to the more
OpenElections-like format where there is one row per result.
"""

import csv

from openelexdata.us.ia import arg_parser

fields = [
    'office',
    'district',
    'candidate',
    'party',
    'reporting_level',
    'jurisdiction',
    'votes',
]

candidates = [
    "Total Votes",
    "Julian Garrett",
    "Mark Davin",
    "Write In",
]

if __name__ == "__main__":
    args = arg_parser.parse_args()

    reader = csv.DictReader(args.infile)
    writer = csv.DictWriter(args.outfile, fields)

    candidates = reader.fieldnames[1:]

    writer.writeheader()
    for row in reader:
        for candidate in candidates:
            writer.writerow({
                'office': "State House",
                'district': 25,
                'candidate': candidate,
                'party': "",
                'reporting_level': "precinct",
                'jurisdiction': row['Precinct'],
                'votes': row[candidate],
            })

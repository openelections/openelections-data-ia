#!/usr/bin/env python

import csv
import re

from openelexdataia import arg_parser

fields = [
    'office',
    'district',
    'party',
    'reporting_level',
    'jurisdiction',
    'county',
    'county_num',
    'votes',
]

whitespace_re = re.compile(r'\s{2,}')
numbers_only_re = re.compile(r'^[\d,]+\s+[\d,]+')

def parse_line(line):
    results = []

    if (line.startswith("COUNTY") or line.startswith("NUMBER") or 
        line == "#REF!" or line == ""):
        return results 

    cols = split_line(line)
    cols = fix_cols(cols)
    assert len(cols) == 24

    county_num = cols[0].lstrip("0")
    county = cols[1]
    precinct = cols[2]

    for i in range(3, len(cols) - 3):
        col = cols[i]
        if col == 'x':
            # Skip results with an x in the column
            continue

        office, district = get_office(i, cols)
        assert office is not None
        party = get_party(i)

        results.append({
            'office': office,
            'district': district,
            'party': party,
            'reporting_level': 'precinct',
            'jurisdiction': precinct,
            'county': county,
            'county_num': county_num,
            'votes': col,
        })

    return results

def get_office(i, cols):
    """Return the office and district number for a result column"""
    if i >= 3 and i <= 6:
        return "PRESIDENT", None
    elif i >= 7 and i <= 10:
        return "U.S REPRESENTATIVE", cols[-1]
    elif i >= 11 and i <= 12:
        return "CONST. QUES", None
    elif i >= 13 and i <= 16:
        return "IOWA SENATE", cols[-2]
    elif i >= 17 and i <= 20:
        return "IOWA HOUSE", cols[-3]
    else:
        return None, None

PARTIES = [
    "DEM",
    "REP",
    "GREEN",
    "SC",
    "DEM",
    "REP",
    "OTH",
    "SC",
    "YES",
    "NO",
    "DEM",
    "REP",
    "OTH",
    "SC",
    "DEM",
    "REP",
    "OTH",
    "SC",
]

def get_party(i):
   return PARTIES[i - 3]

def split_line(line):
    cols = []
    for col in whitespace_re.split(line):
        if (('x' in col and col != 'x') or
                numbers_only_re.match(col) or
                (col.startswith('?') and col != '?')):
            cols.extend(col.split(' '))
        else:
            cols.append(col)
    return cols

def fix_cols(cols):
    if cols[0] == "53" and cols[1] == "JONES" and cols[2] == "MORLEY":
        cols.insert(6, "None")
    elif cols[0] == "56" and cols[1] == "LEE" and cols[2] == "ABSENTEE & SPECIAL BALLOTS":
        cols.insert(10, "None")

    return cols


if __name__ == "__main__":
    args = arg_parser.parse_args()

    writer = csv.DictWriter(args.outfile, fields)

    writer.writeheader()

    line_num = 1
    for line in args.infile:
        clean_line = line.strip() 
        for result in parse_line(clean_line):
            writer.writerow(result)

#!/usr/bin/env python

"""Parse 2013 precinct-level general election results for the State Senate
District 13 contest"""

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState


district_re = re.compile(r'.* District (?P<district_num>\d+)')
whitespace_re = re.compile(r'\s{2,}')

def matches_page_header(line):
    return "Official Results Report" in line

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')

class PageHeader(ParserState):
    name = 'page_header'

    def handle_line(self, line):
        m = district_re.match(line)
        if m:
            self._context['district_num'] = m.group('district_num')
            self._context.change_state('results_header')

class ResultsHeader(ParserState):
    name = 'results_header'

    def handle_line(self, line):
        if line == "":
            return

        if line:
            cols = whitespace_re.split(line)
            clean_cols = []
            for col in cols:
                if col.endswith('SCATTERING'):
                    clean_cols.append(col.replace("SCATTERING", "").strip())
                    clean_cols.append("SCATTERING")
                else:
                    clean_cols.append(col)

            self._context['candidates'] = clean_cols[1:]
            self._context.change_state('results')

class Results(ParserState):
    name = 'results'

    def handle_line(self, line):
        if line == "":
            return
        
        cols = whitespace_re.split(line)

        assert len(cols) == len(self._context['candidates']) + 1

        jurisdiction = cols[0].strip(":")

        for i in range(1, len(cols)):
            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': self._context['candidates'][i-1],
                'reporting_level': "precinct", 
                'jurisdiction': jurisdiction, 
                'votes': cols[i].replace(',', ''), 
            })


        if jurisdiction.lower() == "total":
            self._context.change_state('root')

class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(PageHeader(self))
        self._register_state(ResultsHeader(self))
        self._register_state(Results(self))
        self._current_state = self._get_state('root')
        self['office'] = "State Senator"


fields = [
    'office',
    'district',
    'candidate',
    'party',
    'reporting_level',
    'jurisdiction',
    'votes',
]

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

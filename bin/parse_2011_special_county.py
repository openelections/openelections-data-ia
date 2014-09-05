#!/usr/bin/env python

"""
Parse county-level results for 2011 special elections.
"""

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState

contest_re = re.compile(r'(?P<office>State Senator) District (?P<district_num>\d+)')
whitespace_re = re.compile(r'\s{2,}')

def matches_page_header(line):
    return line.startswith("Control County")

def matches_contest_header(line):
    return contest_re.match(line) is not None 

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if self._context['done']:
            return
        elif matches_page_header(line):
            self._context.change_state('page_header')
        elif matches_contest_header(line):
            self._context.change_state('contest_header')

class PageHeader(ParserState):
    name = 'page_header'

    def handle_line(self, line):
        if line.startswith("Election"):
            self._context.change_state('root')

class ContestHeader(ParserState):
    name = 'contest_header'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        m = contest_re.match(line)
        if m is not None:
            self._context['office'] = m.group('office')
            self._context['district_num'] = m.group('district_num')
            self._context.change_state('results_header')

class ResultsHeader(ParserState):
    name = 'results_header'

    def handle_line(self, line):
        if line == "":
            return

        self._context['candidates'] = whitespace_re.split(line)
        assert self._context['candidates'][-1].lower() == "total"

        self._context.change_state('results')

class Results(ParserState):
    name = 'results'

    def handle_line(self, line):
        if line == "":
            return
        
        cols = whitespace_re.split(line)
        assert len(cols) == len(self._context['candidates']) + 1
        jurisdiction = cols[0]

        for i in range(1, len(cols)):
            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': self._context['candidates'][i-1],
                # There are no parties specified in these results
                'party': '', 
                'reporting_level': "county", 
                'jurisdiction': jurisdiction, 
                'votes': cols[i].replace(',', ''), 
            })

        if jurisdiction.lower() == "total":
            self._context['done'] = True
            self._context.change_state('root')


class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(PageHeader(self))
        self._register_state(ContestHeader(self))
        self._register_state(ResultsHeader(self))
        self._register_state(Results(self))
        self._current_state = self._get_state('root')

        self['done'] = False

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

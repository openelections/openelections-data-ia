#!/usr/bin/env python

"""Parse 2014 county-level primary election results"""

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState
from openelexdata.us.ia.util import get_column_breaks, split_into_columns 


office_district_party_re = re.compile(r'(?P<office>U.S. Senator|U.S. Rep|Governor|Secretary of State|Secretary of Agriculture|Auditor of State|Treasurer of State|Attorney General|State Senator|State Rep.)'
    '( Dist. (?P<district_num>\d+)|) - (?P<party>(Dem|Rep))')
whitespace_re = re.compile(r'\s{2,}')
footer_re = re.compile(r'\d+ of \d+')


def matches_page_header(line):
    return line == "IOWA SECRETARY OF STATE"


class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')
        elif office_district_party_re.match(line):
            self._context.change_state('contest_header')
        elif (line and 'candidates' in self._context and
                line.startswith(self._context['candidates'][0])):
            # In some cases, results for a contest are split across pages but
            # the contest header is not repeated.  Only the results table header
            # is repeated.
            self._context.change_state('results_header') 

class PageHeader(ParserState):
    name = 'page_header'

    def handle_line(self, line):
        if "PRIMARY ELECTION CANVASS SUMMARY" in line:
            self._context.change_state('root')

class ContestHeader(ParserState):
    name = 'contest_header'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line == "":
            return

        m = office_district_party_re.match(line)
        if m:
            self._context['office'] = m.group('office')
            self._context['district_num'] = m.group('district_num')
            self._context['party'] = m.group('party')
            self._context.change_state('results_header')

class ResultsHeader(ParserState):
    name = 'results_header'

    def enter(self):
        self.header_lines = []

    def handle_line(self, line):
        if line == "" and len(self.header_lines) > 1:
            self._context.change_state('results') 
        elif line:
            self.header_lines.append(self._context.raw_line)

    def exit(self):
        candidates = self.parse_header_lines(self.header_lines)
        candidates = self._clean_candidates(candidates)
        self._context['candidates'] = candidates

    def parse_header_lines(self, lines):
        breaks = get_column_breaks(lines)
        parsed_lines = split_into_columns(lines, breaks)
        candidates = []
        for line in parsed_lines:
            for i in range(len(candidates), len(line)):
                candidates.append("")

            for i in range(len(line)):
                if candidates[i] and line[i]:
                    candidates[i] += " "

                candidates[i] += line[i]

        return candidates

    def _clean_candidates(self, candidates):
        if candidates[0] == "Mark James Joe M. Seng Riley":
            # In this case, the columns in the extracted text are only one
            # space apart.  Fix this
            return ["Mark Riley", "Joe M. Seng"] + candidates[1:]

        return candidates

class Results(ParserState):
    name = 'results'

    def handle_line(self, line):
        if line == "":
            return

        m = footer_re.match(line)
        if m:
            self._context.change_state('root')
            return
        
        cols = whitespace_re.split(line)
        assert len(cols) == len(self._context['candidates']) + 1

        for i in range(1, len(cols)):
            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': self._context['candidates'][i-1],
                'party': self._context['party'],
                'reporting_level': "county", 
                'jurisdiction': cols[0], 
                'votes': cols[i].replace(',', ''), 
            })

        if cols[0].lower == "total":
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

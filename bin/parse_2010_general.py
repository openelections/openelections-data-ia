#!/usr/bin/env python

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState
from openelexdata.us.ia.util import get_column_breaks, split_into_columns 

contest_re = re.compile(r'(?P<office>Governor|Secretary of Agriculture|'
        'Secretary of State|Attorney General|Auditor of State|'
        'State Representative|State Senator|Treasurer of State|'
        'U.S. Representative|U.S. Senator|'
        'Governor/Lieutenant Governor|President/Vice President)'
        '( District (?P<district_num>\d{1,3})| (?P<us_district_num>\d)(st|th|rd)|)( - (?P<party>Democrat|Iowa Green Party|Republican)|)')
whitespace_re = re.compile(r'\s{2,}')
page_number_re = re.compile(r'Page \d+')

def matches_page_header(line):
    return line.startswith("State of Iowa") or page_number_re.match(line) 

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')
        elif contest_re.match(line):
            self._context.change_state('contest_header')

class PageHeader(ParserState):
    name = 'page_header'

    def handle_line(self, line):
        if "General Election" in line:
            self._context.change_state('root')

class ContestHeader(ParserState):
    name = 'contest_header'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        m = contest_re.match(line)
        if m:
            self._context['office'] = m.group('office')
            self._context['district_num'] = (m.group('district_num') or
                m.group('us_district_num'))
        elif line == "":
            return
        else:
            self._context.change_state('results_header')

class ResultsHeader(ParserState):
    name = 'results_header'

    def enter(self):
        self.header_lines = []
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line == "" and len(self.header_lines) > 1:
            self._context.change_state('results') 
        else:
            self.header_lines.append(self._context.raw_line)

    def exit(self):
        candidates, parties = self.parse_header_lines(self.header_lines)
        self._context['candidates'] = candidates
        self._context['parties'] = parties

    def parse_header_lines(self, lines):
        breaks = get_column_breaks(lines)
        parsed_lines = split_into_columns(lines, breaks)

        # Initialize the candidate and party lists.
        # For this particular set of election results, there isn't any
        # party information.
        candidates = ["" for i in range(len(parsed_lines[0]))]
        parties = ["" for i in range(len(parsed_lines[0]))]
        for line in parsed_lines:
            for i in range(len(line)):
                if candidates[i] and line[i]:
                    candidates[i] += " "

                candidates[i] += line[i]

        if candidates[-4] == "Write-In":
            candidates[-4] = "Write-in"

        assert candidates[-1] == "Total"
        assert candidates[-2] == "Under Votes"
        assert candidates[-3] == "Over Votes"
        assert candidates[-4] == "Write-in"

        # Remove first column, "County"
        return candidates[1:], parties[1:]

class Results(ParserState):
    name = 'results'

    def handle_line(self, line):
        if line == "":
            return
        elif matches_page_header(line):
            self._context.change_state('page_header')
            return
        
        cols = whitespace_re.split(line)
        assert len(cols) == len(self._context['candidates']) + 1

        for i in range(1, len(cols)):
            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': self._context['candidates'][i-1],
                'party': self._context['parties'][i-1],
                'reporting_level': "county", 
                'jurisdiction': cols[0], 
                'votes': cols[i], 
            })

        if cols[0] == "Total":
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

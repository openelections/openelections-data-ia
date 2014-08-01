#!/usr/bin/env python

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState
from openelexdata.us.ia.util import get_column_breaks, split_into_columns 

contest_re = re.compile(r'(?P<office>Governor|Secretary of Agriculture|'
        'Secretary of State|Attorney General|Auditor of State|'
        'State Representative|State Senator|Treasurer of State|'
        'United States Representative|United States Senator|'
        'Governor/Lieutenant Governor|President/Vice President)'
        '( District (?P<district_num>\d{1,3})|)( - (?P<party>Democrat|Iowa Green Party|Republican)|)')
whitespace_re = re.compile(r'\s{2,}')

def matches_page_header(line):
    return (("Official Canvass Summary" in line) or 
            line.startswith("Page") or
            line.startswith("P a g e"))

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
            self._context['district_num'] = m.group('district_num')
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
        parties = []
        candidates = []

        breaks = get_column_breaks(lines)
        parsed_lines = split_into_columns(lines, breaks)
        parsed_lines = self.merge_columns(parsed_lines)

        # Go through the header columns column by column
        for col_idx in range(len(parsed_lines[0])):
            party_done = False
            for row_idx in range(len(parsed_lines)):
                val = parsed_lines[row_idx][col_idx]

                if row_idx == 0:
                    # Handle the first row specially to ensure that all the
                    # candidate and party lists have the same number of values
                    if val in ("OVER VOTES", "UNDER VOTES", "SCATTERING",
                        "TOTAL"):
                        parties.append("")
                        candidates.append(val)
                    else:
                        parties.append(val)
                        candidates.append("")
                else:
                    if party_done and val:
                       space = " " if candidates[col_idx] else ""
                       candidates[col_idx] += space + val
                    else:
                        if val:
                            space = " " if parties[col_idx] else ""
                            parties[col_idx] += space + val

                        if val in ("", "Party", "Liberation"):
                            party_done = True

        assert candidates[-1] == "TOTAL"
        assert candidates[-2] == "SCATTERING"
        assert candidates[-3] == "UNDER VOTES"
        assert candidates[-4] == "OVER VOTES"

        return candidates, parties

    def merge_columns(self, lines):
        # The way we split columns on whitespace causes "OVER VOTES" and
        # "UNDER VOTES" to be detected as two columns.  Merge these together.
        merged = []
        for row_idx in range(len(lines)):
            new_row = [] 
            for col_idx in range(len(lines[row_idx])):
                if lines[0][col_idx] != "VOTES":
                    val = lines[row_idx][col_idx]
                    if val in ("OVER", "UNDER"):
                        val += " VOTES"
                    new_row.append(val)
            merged.append(new_row)

        return merged



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

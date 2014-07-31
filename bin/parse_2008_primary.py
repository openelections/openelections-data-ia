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
    return (("Official Results Report" in line) or line.startswith("I-VOTERS"))

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if self._context['done']:
            # We've seen all the county-level results.  The rest of the results
            # are racewide aggregates.  Ignore!
            return
        elif matches_page_header(line):
            self._context.change_state('page_header')
        elif contest_re.match(line):
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
        if m:
            self._context['office'] = m.group('office')
            self._context['district_num'] = m.group('district_num')
            self._context['party'] = m.group('party')
            if (self._context['office'] == "State Representative" and
                    self._context['district_num'] == "100" and
                    self._context['party'] == "Republican"):
                # This file contains both county-level aggregates and racewide
                # aggregates.  The county-level aggregates come first.  Detect
                # when we see the header of the last race and ignore everything
                # after that.
                self._context['last_contest'] = True

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
        if line == "":
            self._context.change_state('results') 
        else:
            self.header_lines.append(self._context.raw_line)

    def exit(self):
        candidates, parties = self.parse_header_lines(self.header_lines)
        self._context['candidates'] = candidates
        if 'party' not in self._context:
            self._context['parties'] = parties

    def parse_header_lines(self, lines):
        parties = []
        if len(lines) == 1:
            candidates = self.parse_header_line_simple(lines[0])
        else:
            breaks = get_column_breaks(lines)
            parsed_lines = split_into_columns(lines, breaks)
            candidates = ["" for col in parsed_lines[0]]

            for cols in parsed_lines: 
                for i in range(len(cols)):
                    space = " " if len(candidates[i]) else ""
                    candidates[i] = candidates[i] + space + cols[i] 

            candidates = self.merge_candidate_cols(candidates)

        candidates = [self.clean_candidate(c) for c in candidates]

        assert candidates[-1] == "TOTAL"
        assert candidates[-2] == "SCATTERING"
        assert candidates[-3] == "UNDER VOTES"
        assert candidates[-4] == "OVER VOTES"

        return candidates, parties

    def parse_header_line_simple(self, line):
        return whitespace_re.split(line.strip())

    def merge_candidate_cols(self, cols):
        merged_cols = []
        i = 0

        while i < len(cols):
            col = cols[i].strip().replace("- ", "-")
            if col not in ("SCATTERING", "TOTAL") and " " not in col:
                col = col + " " + cols[i+1].strip()
                i += 1

            merged_cols.append(col)

            i += 1

        return merged_cols

    def clean_candidate(self, candidate):
        if candidate == "CHRISTOPHE R REED":
            # PDF and text conversion break the final "R" of "CHRISTOPHER"
            # across 2 lines.  I'm pretty sure the candidate's name is
            # Christopher and not Christophe. See 
            # http://en.wikipedia.org/wiki/Christopher_Reed
            return "CHRISTOPHER REED"

        return candidate


class Results(ParserState):
    name = 'results'

    def handle_line(self, line):
        if line == "":
            return
        elif matches_page_header(line):
            self._context.change_state('page_header')
            return
        
        cols = whitespace_re.split(line)
        cols = self.fix_cols(cols)
        assert len(cols) == len(self._context['candidates']) + 1

        jurisdiction = cols[0]
        for i in range(1, len(cols)):
            votes = cols[i]
            try:
                party = self._context['party'] 
            except KeyError:
                party = self._context['parties'][i-1]

            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': self._context['candidates'][i-1],
                'party': party, 
                'reporting_level': "county", 
                'jurisdiction': jurisdiction,
                'votes': votes, 
            })

        if cols[0] == "Total":
            if self._context['last_contest']:
                # We've seen the last result of the last contest's county-level
                # results.  Set the flag so we ignore everything else.
                self._context['done'] = True

            self._context.change_state('root')

    def fix_cols(self, cols):
        if (self._context['office'] == "State Senator" and
                self._context['district_num'] == "22" and
                'party' in self._context and
                self._context['party'] == "Republican" and
                cols[0] == "Franklin"):
            return cols + [0]
        elif (self._context['office'] == "State Representative" and
                self._context['district_num'] == "044" and
                'party' in self._context and
                self._context['party'] == "Republican" and
                cols[0] == "Franklin"):
            return cols + [0]

        return cols



class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(PageHeader(self))
        self._register_state(ContestHeader(self))
        self._register_state(ResultsHeader(self))
        self._register_state(Results(self))
        self._current_state = self._get_state('root')

        self['last_contest'] = False
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
        print(parser['candidates'])
        raise

    writer.writeheader()
    for result in parser.results:
        writer.writerow(result)

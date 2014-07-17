#!/usr/bin/env python

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState

contest_re = re.compile(r'(?P<office>Governor|Secretary of Agriculture|'
        'Secretary of State|Attorney General|Auditor of State|'
        'State Representative|State Senator|Treasurer of State|'
        'United States Representative|United States Senator|'
        'Governor/Lieutenant Governor|President/Vice President)'
        '( District (?P<district_num>\d{1,3})|)( - (?P<party>Democrat|Iowa Green Party|Republican)|)')
whitespace_re = re.compile(r'\s{2,}')

def _parse_contest_details(m):
    fields = ['office', 'party', 'district_num'] 
    return {k:m.group(k) for k in fields}

def matches_page_header(line):
    return "2006 PRIMARY ELECTION" in line

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')
        elif line == "":
            return
        else:
            self._context.change_state('contest_header')

class PageHeader(ParserState):
    name = 'page_header'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if "PRIMARY" in line:
            self._context['primary'] = True
        elif line == "OFFICIAL RESULTS":
            self._context.change_state('root')

class ContestHeader(ParserState):
    name = 'contest_header'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        m = contest_re.match(line)

        if m:
            self._context.update(_parse_contest_details(m))
            self._context.change_state('results_header')
        else:
            raise ValueError("Unexpected value when parsing contest header")

class ResultsHeader(ParserState):
    name = 'results_header'

    def handle_line(self, line):
        assert line.endswith("Totals")
        self._context['candidates'] = self._parse_candidates(line)
        self._context.change_state('results')

    def _parse_candidates(self, line):
        candidates = whitespace_re.split(line)
        if (candidates[-2].endswith("Scattering")
                and candidates[-2] != "Scattering"):
            candidates[-2] = candidates[-2].replace(" Scattering", "")
            candidates.insert(len(candidates) - 1, "Scattering") 
            
        return candidates

class Results(ParserState):
    name = 'results'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')
            return

        cols = whitespace_re.split(line)
        assert len(cols) == len(self._context['candidates']) + 1

        jurisdiction = cols[0]
        for i in range(1, len(cols)):
            votes = cols[i]
            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': self._context['candidates'][i-1],
                'party': self._context['party'], 
                'reporting_level': "county", 
                'jurisdiction': jurisdiction,
                'votes': votes, 
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

        self['primary'] = False

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

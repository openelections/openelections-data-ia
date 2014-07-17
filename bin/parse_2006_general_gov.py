#!/usr/bin/env python

import csv
import re

from openelexdata.us.ia import BaseParser, ParserState, arg_parser
from openelexdata.us.ia.util import get_column_breaks, split_into_columns

whitespace_re = re.compile(r'\s{2,}')

def matches_page_header(line):
    return ("Official" in line and "Results" in line and "Report" in line)

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')

class PageHeader(ParserState):
    name = 'page_header'

    def handle_line(self, line):
        if line.startswith("Governor"):
            self._context.change_state('contest_header')

class ContestHeader(ParserState):
    name = 'contest_header'

    def handle_line(self, line):
        if line.startswith("Democrat"):
            self._context.change_state('results_header')

class ResultsHeader(ParserState):
    name = 'results_header'

    def enter(self):
        self._header_lines = []
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line == "":
            return
        elif (line.startswith("Adair") or line.startswith("Clinton") or
              line.startswith("Howard") or line.startswith("Monona") or
              line.startswith("Van Buren")):
            self._context.change_state('results')
        else:
            self._header_lines.append(self._context.raw_line.rstrip())

    def exit(self):
        if 'candidates' in self._context:
            return

        breaks = get_column_breaks(self._header_lines) 
        parsed_header_lines = split_into_columns(self._header_lines, breaks) 
        for row in parsed_header_lines:
            row[5] = "{} {}".format(row[5], row[6]).strip()
            row[7] = "{} {}".format(row[7], row[8]).strip()
            del row[6]
            del row[7]

        for i in range(len(parsed_header_lines)):
            row = parsed_header_lines[i]

            for j in range(len(row)):
                row[j] = re.sub(r'I$', ' /', row[j])

                if row[j] == "libertarian":
                    row[j] = "Libertarian"

                if row[j] == "PATTYJUDGE":
                    row[j] = "PATTY JUDGE"

        self._context['parties'] = []
        for i in range(5):
            party = "{} {}".format(parsed_header_lines[0][i],
                parsed_header_lines[1][i]).strip()
            self._context['parties'].append(party)

        for i in range(len(parsed_header_lines[0]) - 5):
            self._context['parties'].append('')
       
        self._context['candidates'] = []
        for i in range(5):
            candidate_bits = []
            for row in parsed_header_lines[2:]:
                candidate_bits.append(row[i])

            candidate = " ".join(candidate_bits).strip()
            self._context['candidates'].append(candidate)

        self._context['candidates'] += parsed_header_lines[0][5:]
                

class Results(ParserState):
    name = 'results'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line == "":
            return

        if line.startswith("I-VOTERS"):
            self._context.change_state('root') 
            return

        cols = whitespace_re.split(line)
        assert len(cols) == len(self._context['candidates']) + 1

        jurisdiction = cols[0]
        for i in range(1, len(cols)):
            votes = cols[i]
            self._context.results.append({
                'office': "Governor", 
                'district': "", 
                'candidate': self._context['candidates'][i-1],
                'party': self._context['parties'][i-1], 
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

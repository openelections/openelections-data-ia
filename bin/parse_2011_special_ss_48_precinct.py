#!/usr/bin/env python

"""Parse the precinct-level results for the 2011 State Senate District 48 contest"""

import csv
import re

from openelexdata.us.ia import arg_parser
from openelexdata.us.ia import BaseParser, ParserState

county_re = re.compile(r'(?P<county>[A-Za-z]+) County')
whitespace_re = re.compile(r'\s{2,}')

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if line == "":
            return

        if line == "State Senate District 48":
            self._context.change_state('contest_header')
            return

        if line.startswith("Ruth"):
            self._context.change_state('results_header')

        m = county_re.match(line)
        if m:
            self._context['county'] = m.group('county')
            self._context.change_state('results')
            return

        # Handle the page break that starts in the middle of
        if line.startswith("Gold Fair Building"):
            self._context.change_state('results')
            return

class ContestHeader(ParserState):
    name = 'contest_header'

    def handle_line(self, line):
        if line.startswith("Special Election"):
            self._context.change_state('root')

class ResultsHeader(ParserState):
    name = 'results_header'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line == "":
            return

        if 'candidates' not in self._context:
            # No candidates key has been set.  This means this is the first
            # line of the header
            self._context['candidates'] = []
            # The first line of the header has some spaces in column values.
            # Luckily, only the first two columns have values.  We can just
            # split on r'\s{2,}'
            cols = whitespace_re.split(line)
            for col in cols:
                self._context['candidates'].append(col)
        else:
            # The candidates key has been set.  This is the second line of the
            # header
            # The second line of the header has no spaces in column values.
            # We can split on runs of whitespace.
            cols = re.split(r'\s+', line)
            for i in range(len(cols)):
                if i < len(self._context['candidates']): 
                    # There's a partial value already in this column,
                    # combine the two strings
                    self._context['candidates'][i] += " " + cols[i]
                else:
                    # Nothing in this column yeat, just add the value
                    self._context['candidates'].append(cols[i])

        if line.endswith("Total"):
            self._context.change_state('root')

class Results(ParserState):
    name = 'results'

    def enter(self):
        if self._context.current_line.startswith("Gold Fair Building"):
            # Handle the case where county results were interrupted by a page
            # break
            self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line == "":
            return

        if line.startswith("Prepared"):
            self._context.change_state('root')
            return

        cols = whitespace_re.split(line)

        assert len(cols) == len(self._context['candidates']) + 1

        jurisdiction = cols[0]

        for i in range(1, len(cols)):
            self._context.results.append({
                'office': "State Senate", 
                'district': 48,
                'candidate': self._context['candidates'][i-1],
                # There are no parties specified in these results
                'party': '', 
                'reporting_level': "precinct", 
                'jurisdiction': jurisdiction, 
                'county': self._context['county'],
                'votes': cols[i], 
            })

        if cols[0] == "Total":
            self._context.change_state('root')


class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
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
    'county',
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

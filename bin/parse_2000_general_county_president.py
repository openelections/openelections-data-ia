#!/usr/bin/env python

import csv
import re

from openelexdataia import BaseParser, ParserState, arg_parser
from openelexdataia.util import parse_fixed_widths


fieldwidths = [14, 11, 11, 13, 11, 15, 16, 18, 18, 15, 13, 6]

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if line.strip() == "President and Vice President":
            self._context.change_state('header')
            
class HeaderState(ParserState):
    name = 'header'

    def enter(self):
        self._header_bits = []

    def handle_line(self, line):
        stripped = line.strip()

        if stripped == "": 
            return

        if 'candidates' not in self._context:
            cols = parse_fixed_widths(fieldwidths, line[:-1])
            self._header_bits.append(cols)
            
        if stripped.startswith("Lieberman"):
            if 'candidates' not in self._context:
                assert len(self._header_bits) == 4 
                self._context['candidates'] = self.build_candidates(self._header_bits)
            self._context.change_state('results')

    def build_candidates(self, header_bits):
        candidates = []
        for i in range(1, len(header_bits[0])):
            if (header_bits[1][i] == "Scattering" or
                    header_bits[1][i] == "Totals"):
                party = ""
            elif header_bits[0][i] == "":
                party = header_bits[1][i]
            else:
                party = header_bits[0][i] + " " + header_bits[1][i]

            if (header_bits[1][i] == "Scattering" or
                    header_bits[1][i] == "Totals"):
                candidate = header_bits[1][i]
            else:
                candidate = "{} / {}".format(header_bits[2][i],
                    header_bits[3][i])

            candidates.append((candidate, party))
        return candidates
            

class ResultsState(ParserState):
    name = 'results'

    whitespace_re = re.compile(r'\s{2,}')
    multiple_numbers_re = re.compile(r'[\d,]+\s[\d,]+')

    def enter(self):
        self._seen_results = False

    def handle_line(self, line):
        stripped = line.strip()
        
        if stripped != "":
            self._seen_results = True
            self._context.results.extend(
                self.parse_result(line.strip(), self._context['candidates']))
        elif (stripped == "" and self._context.previous_line.strip() == "" and
                self._seen_results):
            self._context.change_state('root')

    def parse_result(self, line, candidates):
        results = []
        cols = self.clean_cols(self.whitespace_re.split(line))
        assert len(cols) == len(candidates) + 1 
        county = cols[0]
        for i in range(len(candidates)):
            results.append({
                'office': "President",
                'candidate': candidates[i][0],
                'party': candidates[i][1],
                'reporting_level': "county",
                'jurisdiction': county,
                'votes': cols[i + 1].replace(',', ''),
            })
        
        return results

    def clean_cols(self, cols):
        cleaned = []
        for col in cols:
            if self.multiple_numbers_re.match(col):
                cleaned.extend(col.split(' '))
            else:
                cleaned.append(col)
        return cleaned



class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(HeaderState(self))
        self._register_state(ResultsState(self))
        self._current_state = self._get_state('root')

    def parse(self):
        for line in self.infile:
            # Don't strip the line.  We're going to do a fixed-width parse
            # of header rows
            self.handle_line(line)


fields = [
    'office',
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
        print("Line: '{}'".format(parser.current_line))
        print(len(parser.current_line))
        raise

    writer.writeheader()
    for result in parser.results:
        writer.writerow(result)

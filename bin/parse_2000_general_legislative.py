#!/usr/bin/env python

import csv
import re

from openelexdata.us.ia import BaseParser, ParserState, arg_parser
from openelexdata.us.ia.util import get_column_breaks, split_into_columns

whitespace_re = re.compile(r'\s{2,}')
page_number_re = re.compile(r'- \d+ -')
number_re = re.compile(r'[\d,]+')
district_re = re.compile(r'(?P<district_num>\d{1,3})(st|nd|rd|th) District:')

class RootState(ParserState):
    name = 'root'
    

    def handle_line(self, line):
        if line.startswith("November 7, 2000"):
            self._context.change_state('pageheader')
            return

        m = district_re.match(line)
        if m is None:
            return

        self._context['district_num'] = m.group('district_num')
        self._context.change_state('contestheader')


class PageHeaderState(ParserState):
    name = 'pageheader'

    def handle_line(self, line):
        if line == "State House of Representatives":
            self._context['office'] = line
            self._context.change_to_previous_state()



class ContestHeaderState(ParserState):
    name = 'contestheader'


    def enter(self):
        self._context['header_lines'] = []

    def handle_line(self, line):
        cols = whitespace_re.split(line)
        if page_number_re.match(line):
            # This can be split across pages
            self._context.change_state('pageheader')
        elif len(cols) > 1 and number_re.match(cols[1]):
            self._context.change_state('results')
        else:
            self._context['header_lines'].append(self._context.raw_line)



class ResultsState(ParserState):
    name = 'results'

    def enter(self):
        if self._context.previous_state == 'contestheader':
            self._candidates, self._parties = self._parse_header()
            self.handle_line(self._context.current_line)

    def exit(self):
        if self._context.next_state == "root":
            del self._context['district_num']
            del self._context['header_lines']

    def handle_line(self, line):
        has_totals = False

        if line == "":
            return
        elif page_number_re.match(line):
            # This can be split across pages
            self._context.change_state('pageheader')
            return

        if line.startswith("Totals"):
            has_totals = True

        cols = whitespace_re.split(line.strip())
        assert cols[0] != ""
        assert number_re.match(cols[1])
        jurisdiction = cols[0]
        reporting_level = "racewide" if jurisdiction == "Totals" else "county"
        vote_index = 1
        for i in range(len(self._candidates)):
            candidate = self._candidates[i]
            if candidate:
                votes = cols[vote_index].replace(',', '')
                vote_index += 1
                self._context.results.append({
                    'office': self._context['office'], 
                    'district': self._context['district_num'],
                    'candidate': candidate,
                    'party': self._parties[i],
                    'reporting_level': reporting_level, 
                    'jurisdiction': jurisdiction,
                    'votes': votes, 
                })

        if has_totals:
            self._context.change_state('root')
        
    def _parse_header(self, header_lines=None):
        if header_lines is None:
            header_lines = self._context['header_lines']
        self._breaks = get_column_breaks(header_lines, whitespace_re)
        header_cols = split_into_columns(header_lines, self._breaks)

        parties = ['']*len(header_cols[0])
        candidates = ['']*len(header_cols[0])
        has_parties = False
        for row in header_cols:
            for i in range(len(row)):
                col = row[i]
                if not col:
                    continue

                if has_parties or col == "Scattering" or col == "Totals":
                    sep = " " if candidates[i] else ""
                    candidates[i] += sep + col
                else:
                    sep = " " if parties[i] else ""
                    parties[i] += sep + col

                if col == "Totals":
                    has_parties = True

        return candidates, parties


class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(PageHeaderState(self))
        self._register_state(ContestHeaderState(self))
        self._register_state(ResultsState(self))
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

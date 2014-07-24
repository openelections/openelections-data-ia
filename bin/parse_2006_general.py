#!/usr/bin/env python

import csv
import re

from openelexdata.us.ia import BaseParser, ParserState, arg_parser

contest_re = re.compile(r'(?P<office>United States Representative|'
        'Secretary of State|Auditor of State|Treasurer of State|'
        'Secretary of Agriculture|Attorney General|State Senator|'
        'State Representative)'
        '( District (?P<district_num>\d{1,3})|)')
whitespace_re = re.compile(r'\s{2,}')

def matches_page_header(line):
    return line.startswith("Election:")

def matches_contest_header(line):
    return contest_re.match(line)


class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if matches_page_header(line):
            self._context.change_state('page_header')
        else:
            m = matches_contest_header(line)
            if m:
                self._context['contest_header_match'] = m
                self._context.change_state('contest_header')


class PageHeader(ParserState):
    name = 'page_header'

    def handle_line(self, line):
        m = matches_contest_header(line)
        if m:
            self._context['contest_header_match'] = m
            self._context.change_state('contest_header')


class ContestHeader(ParserState):
    name = 'contest_header'

    def enter(self):
        m = self._context['contest_header_match']
        self._context['office'] = m.group('office')
        self._context['district'] = m.group('district_num')
        self._context['vacancy'] = self._context.current_line.endswith("Vacancy")
        del self._context['contest_header_match']

    def handle_line(self, line):
        if line == "":
            return
        elif line.endswith("TOTAL"):
            bits = whitespace_re.split(line)
            candidate_start = bits.index("OVER VOTES")
            self._context['candidates'] = bits[candidate_start:]
            self._context['parties'] = bits[0:candidate_start]
            assert self._context['candidates'][-1] == "TOTAL"
            assert self._context['candidates'][-2] == "SCATTERING"
            assert self._context['candidates'][-3] == "UNDER VOTES"
            assert self._context['candidates'][-4] == "OVER VOTES"
        else:
            bits = re.split(r'\s+', line)
            if len(bits) > 2 and re.match(r'\d+', bits[2]):
                self._context.change_state('results')
            else:
                self._context['candidates'] = whitespace_re.split(line) + self._context['candidates']
            

class Results(ParserState):
    name = 'results'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        cols = re.split(r'\s+', line)
        if line == "":
            self._context.change_state('root')
            return
        elif not re.match(r'\d+', cols[1]):
            cols[0] = cols[0] + " " + cols[1]
            del cols[1]

        try:
            assert len(cols) == len(self._context['candidates']) + 1
        except AssertionError:
            print cols
            print self._context['candidates']

        jurisdiction = cols[0]

        for i in range(1, len(cols)):
            try:
                party = self._context['parties'][i-1]
            except IndexError:
                party = ""

            self._context.results.append({
                'office': self._context['office'],
                'district': self._context['district'],
                'candidate': self._context['candidates'][i-1],
                'party': party,
                'reporting_level': "county",
                'jurisdiction': jurisdiction,
                'votes': cols[i],
                'vacancy': self._context['vacancy'],
            })

        if jurisdiction == "Total":
            self._context.change_state('root') 


class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(PageHeader(self))
        self._register_state(ContestHeader(self))
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
    'vacancy',
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

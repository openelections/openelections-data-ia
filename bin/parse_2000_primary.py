#!/usr/bin/env python

import csv
import re

from openelexdataia import BaseParser, ParserState, arg_parser
from openelexdataia.util import district_word_to_number

HEADER_PREFIX_RE = re.compile(r'^(JUNE 6, 2000|PRIM CANV)')

class RootState(ParserState):
    name = 'root'
    office_re = re.compile(r'^(?P<office>U\.S\. REPRESEN[TA]+TIVE|STATESENATOR|STATE REPRESENTATIVE)\s+(?P<district>\S+)\s+DISTRICT$')

    def handle_line(self, line):
        m = self.office_re.match(line)
        if m:
            self._context['office'] = m.group('office')
            self._context['district'] = district_word_to_number(m.group('district'))
            self._context.change_state('contest')
        elif line == "STATE REPRESENTATIVE ONE HUNDREDRETH DISTRICT":
            # Keep self.office_re simple and just handle the one exception
            # explicitly
            self._context['office'] = "STATE_REPRESENTATIVE"
            self._context['district'] = 100
            self._context.change_state('contest')

            
class ContestState(ParserState):
    name = 'contest'
    whitespace_re = re.compile(r'\s{2,}')

    def enter(self):
        self._context['candidate_bits'] = []

    def handle_line(self, line):
        bits = self.whitespace_re.split(line)

        if HEADER_PREFIX_RE.match(line):
            # Skip header
            return
        elif line.startswith("---"):
            candidates, parties = self.build_candidates(self._context['candidate_bits'])
            self._context['candidates'] = candidates
            self._context['parties'] = parties
        elif 'candidates' not in self._context:
            if line != "":
                self._context['candidate_bits'].append(self.clean_bits(bits)) 
        elif line != "" and 'candidates' in self._context:
            results = self.parse_result_row(line,
                self._context['office'], self._context['district'],
                self._context['candidates'], self._context['parties'])
            self._context.results.extend(results)
        elif line == "": 
            if self._context.previous_line == "":
                self._context.change_state('root')

    def exit(self):
        keys = ['office', 'district', 'first_names', 'middle_names',
                'last_names', 'candidates', 'parties']
        for key in keys:
            try:
                del self._context[key]
            except KeyError:
                pass

    def build_candidates(self, candidate_bits): 
        assert len(candidate_bits) >= 2 and len(candidate_bits) <= 4

        candidates = []

        if len(candidate_bits) == 2:
            first_names = []
            middle_names = []
            last_names = candidate_bits[0]
            parties = candidate_bits[1]
        elif len(candidate_bits) == 3:
            first_names = candidate_bits[0]
            middle_names = []
            last_names = candidate_bits[1]
            parties = candidate_bits[2]
        elif len(candidate_bits) == 4:
            first_names = candidate_bits[0]
            middle_names = candidate_bits[1]
            last_names = candidate_bits[2]
            parties = candidate_bits[3]

        try:
            # Detect and handle the case where the "SCATTERING" and 
            # "TOTALS" header are moved up to the first names row
            # and the party is moved up to the last names row
            scattering_idx = first_names.index("SCATTERING")

            final_name_idx = 0
            for i in range(len(first_names)):
                name = first_names[i]
                if name != "SCATTERING" and name != "TOTALS":
                    final_name_idx = i

            if (scattering_idx > final_name_idx and
                scattering_idx != len(first_names) - 1):
                extra_last_names = first_names[scattering_idx:]
                first_names = first_names[:scattering_idx] 
                rep_idx = last_names.index("REP")
                parties.extend(last_names[rep_idx:])
                del last_names[rep_idx:]
                last_names.extend(extra_last_names)
            elif scattering_idx == len(first_names) - 1:
                last_names.insert(scattering_idx, "SCATTERING")
                del first_names[scattering_idx]
            else:
                parties.insert(scattering_idx, last_names[scattering_idx])
                last_names[scattering_idx] = first_names[scattering_idx]
                del first_names[scattering_idx]
        except ValueError:
            pass

        if "SCATTERING" in middle_names:
            # Handle the case where the last_names line is split across two
            # lines
            middle_names.extend(last_names)
            last_names = middle_names[:]
            middle_names = []

        assert len(parties) == len(last_names)
        for party in parties:
            assert party in ["DEM", "REP"]

        fname_idx = 0
        for lname in last_names:
            name = lname
            if lname not in ["SCATTERING", "TOTALS", "TOTAL"] and first_names:
                name = first_names[fname_idx]
                if middle_names:
                    name + " " + middle_names[fname_idx] 

                name = name + " " + lname
                fname_idx += 1

            candidates.append(name)

        return candidates, parties

    def clean_bits(self, bits):
        cleaned = []
        for s in bits:
            cleaned.extend(self.clean_bit(s))
        return cleaned

    def clean_bit(self, bit):
        if (("SCATTERING" in bit and bit != "SCATTERING") or
            ("TOTALS" in bit and bit != "TOTALS") or
            bit == "REP REP" or bit == "DEM DEM"):
            return bit.split(' ')
        else:
            return [bit]

    def parse_result_row(self, s, office, district, candidates, parties):
        results = []
        cols = self.whitespace_re.split(s)
        candidate_idx = 0
        county = cols[0]
        for col in cols[1:]:
            result = {
                'office': office,
                'district': district,
                'candidate': candidates[candidate_idx],
                'party': parties[candidate_idx],
                'reporting_level': 'county',
                'jurisdiction': county,
                'votes': int(col.replace(',', '')),
            }
            results.append(result)
            candidate_idx += 1
        return results

class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(ContestState(self))
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

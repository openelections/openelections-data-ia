import re

from openelexdata.us.ia import BaseParser, ParserState
from openelexdata.us.ia.util import get_column_breaks, split_into_columns


contest_re = re.compile(r'(?P<office>Governor|Secretary of Agriculture|'
        'Secretary of State|Attorney General|Auditor of State|'
        'State Representative|State Senator|Treasurer of State|'
        'United States Representative|United States Senator|'
        'Governor/Lieutenant Governor|President/Vice President)'
        '( District (?P<district_num>\d{1,3})|)( - (?P<party>Democrat|Iowa Green Party|Republican)|)')
       
whitespace_re = re.compile(r'\s{2,}')
number_re = re.compile('^[\d,]+$')

def _parse_contest_details(m):
    fields = ['office', 'party', 'district_num'] 
    return {k:m.group(k) for k in fields}

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        m = contest_re.match(line)
        if m:
            self._context.update(_parse_contest_details(m))
            self._context.change_state('result_header')
        elif line.startswith("State of Iowa"):
            self._context.change_state('document_header')
        elif line.startswith("ELECTION:"):
            self._context.change_state('page_header')

class DocumentHeaderState(ParserState):
    name = 'document_header'

    def handle_line(self, line):
        if line.startswith("Secretary of State"):
            self._context.change_state('root')


class PageHeader(ParserState):
    name = 'page_header'

    def enter(self):
        if "Primary" in self._context.current_line:
            self._context['primary'] = True

    def handle_line(self, line):
        m = contest_re.match(line)
        if m:
            self._context.update(_parse_contest_details(m))
            self._context.change_state('result_header')

class ResultHeader(ParserState):
    name = 'result_header'

    def enter(self):
        self._context['header_lines'] = []

    def handle_line(self, line):
        if not line:
            return

        cols = whitespace_re.split(line)
        m = contest_re.match(line)
        if m:
            self._context.update(_parse_contest_details(m))
            self._context.change_state('result_header')
        elif len(cols) > 1 and number_re.match(cols[1]):
            self._context.change_state('results')
        else:
            self._context['header_lines'].append(self._context.raw_line)


class Results(ParserState):
    name = 'results'

    def enter(self):
        if self._context.previous_state == 'result_header':
            self._candidates, self._parties = self._parse_header()
            #print(self._candidates)
            #print(self._parties)
            self.handle_line(self._context.current_line)

    def exit(self):
        if self._context.next_state == "root":
            del self._context['header_lines']

    def handle_line(self, line):
        if line.startswith("ELECTION:"):
            self._context.change_state('page_header')
            return

        cols = whitespace_re.split(line)
        if len(cols) < 2:
            return

        cols = self._fix_cols(cols)
        jurisdiction = cols[0]
        reporting_level = 'racewide' if jurisdiction == "Totals" else 'county'
        vote_index = 1
        for i in range(len(self._candidates)):
            candidate = self._candidates[i]
            party = self._parties[i]
            if not party and self._context['primary']:
                party = self._parties[0]

            try:
                votes = cols[vote_index].replace(',', '')
            except IndexError:
                # Some result files have no values in a column.  In particular
                # this is the case for the Secretary of State results.
                votes = ''

            vote_index += 1
            self._context.results.append({
                'office': self._context['office'], 
                'district': self._context['district_num'],
                'candidate': candidate,
                'party': party, 
                'reporting_level': reporting_level, 
                'jurisdiction': jurisdiction,
                'votes': votes, 
            })

        if cols[0] == "Totals":
            self._context.change_state('root')

    def _fix_cols(self, cols):
        # Fix known case where there's only one space separating the first
        # (jurisdiction) and second columns.
        if cols[0] == "POTTAWATTAMIE 12,090":
            split_vals = cols[0].split(" ")
            cols[0] = split_vals[0]
            cols.insert(1, split_vals[1])
        
        return cols

    def _parse_header(self, header_lines=None):
        #candidate_col_vals = ["Write-In", "Votes", "Totals"]
        party_col_vals = ["Democratic", "Iowa Green", "Party", "Republican",
            "Libertarian", "Nominated by", "Petition",
            "Constitution", "Socialist", "Workers Party"]
        if header_lines is None:
            header_lines = self._context['header_lines']
        #print(header_lines)
        self._breaks = get_column_breaks(header_lines)
        header_cols = split_into_columns(header_lines, self._breaks)

        parties = ['']*len(header_cols[0])
        candidates = ['']*len(header_cols[0])
        for row in header_cols:
            for i in range(len(row)):
                col = row[i]
                if not col:
                    continue

                if col in party_col_vals:
                    sep = " " if parties[i] else ""
                    parties[i] += sep + col
                else:
                    sep = " " if candidates[i] else ""
                    candidates[i] += sep + col

        # Some result headers do not include parties, grab the party from the
        # contest headers we parsed earlier 
        if parties[0] == '' and 'party' in self._context:
            parties[0] = self._context['party']

        # HACK: Misaligned columns in first page of 2002 general Governor
        # results.  Fix it.
        if (self._context['office'] == "Governor" and
                not self._context['primary']):
            return self._general_gov_candidates_parties()

        return candidates, parties

    def _general_gov_candidates_parties(self):
        candidates = [
            "Tom Vilsack & Sally Pederson",
            "Doug Gross & Debi Durham",
            "Jay Robinson & Holly Jane Hart",
            "Clyde Cleveland & Richard Campagna",
            "Write-In Votes",
            "Totals"
        ]
        parties = [
            "Democratic Party",
            "Republican Party",
            "Iowa Green Party",
            "Libertarian Party",
            "",
            ""
        ]
        return candidates, parties


class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(DocumentHeaderState(self))
        self._register_state(PageHeader(self))
        self._register_state(ResultHeader(self))
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

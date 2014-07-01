import re

from openelexdata.us.ia.util import split_line_into_columns
from openelexdata.us.ia.parser import BaseParser, ParserState

whitespace_re = re.compile(r'\s{2,}')
number_re = re.compile(r'[0-9,]+')
clean_number_re = re.compile(r'^\d+$')

class RootState(ParserState):
    name = 'root'

    def handle_line(self, line):
        if line.startswith("GENERAL ELECTION"):
            self._context.change_state('header')


class HeaderState(ParserState):
    name ='header'

    party_cols = [
        "COUNTY",
        "CO #",
        "PRECINCT NAME",
        "DEM",
        "REP",
        "OTH",
        "SC",
        "DEM",
        "REP",
        "OTH",
        "SC",
        "DEM",
        "REP",
        "OTH",
        "SC",
        "DEM",
        "REP",
        "OTH",
        "SC",
        "DEM",
        "REP",
        "OTH",
        "SC",
        "IA HOUSE",
        "IA SENATE",
        "US REP",
    ] 

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line.startswith("GENERAL ELECTION"):
            self._parse_offices(line)
        elif line.startswith("COUNTY"):
            self._parse_parties(line)
            self._context['breaks'] = self._detect_column_breaks(self._context.raw_line)
        else:
            # It's a result!
            self._context.change_state('results')

    def _parse_offices(self, line):
        if 'offices' in self._context:
            # We've already parsed offices, continue
            return

        cols = whitespace_re.split(line) 
        # Ignore the first bit "GENERAL ELECTION" and the last
        # "IOWA DISTRICTS NUMBERS".  The rest are office names
        self._context['offices'] = cols[1:-1]

    def _parse_parties(self, line):
        if 'parties' in self._context:
            # We've already parsed parties, continue
            return

        cols = whitespace_re.split(line)
        # Skip the leading colums, which are county name, county number and
        # precinct name and the final one which are the distrct number headers
        self._context['parties'] = cols[3:7]

    @classmethod
    def _detect_column_breaks(cls, line):
        breaks = []
        last_idx = 0
        break_idx = 0

        for s in cls.party_cols:
            if s == "COUNTY":
                breaks.append(0)
            elif s == "PRECINCT NAME":
                breaks.append(breaks[break_idx - 1] + 4)
            else:
                i = line.index(s, last_idx)
                breaks.append(i)
                last_idx = i

            break_idx += 1

        return breaks


class ResultsState(ParserState):
    name = 'results'

    def enter(self):
        self.handle_line(self._context.current_line)

    def handle_line(self, line):
        if line.startswith("GENERAL ELECTION"):
            self._context.change_state('header')
            return
        elif line == "":
            return
        elif ("Douglas Melville N 1/2 Leroy Twps N 1/2 Audubon" in line or
              "Audubon Exire Greeley Hamlin Twps & Exira City" in line or
              "Jamestown Twp., Saratoga Twp., & Howard Center" in line):
            # Some lines in the PDF get split into two lines when converted to
            # text.  Save the initial columns and merge them with
            # columns from the next row later.
            self._context['previous_cols'] = whitespace_re.split(line) 
            return
        elif 'previous_cols' in self._context:
            clean_line = self._context.raw_line.replace("City", "    ")
            clean_line = clean_line.replace("Twp.", "    ")
            cols = split_line_into_columns(clean_line,
                self._context['breaks'])
            cols = self._merge(self._context['previous_cols'],
                cols)
            del self._context['previous_cols']

        else:
            # Split on fixed width instead of whitespace re because some
            # cols have missing values

            # Generally, the columns line up with the headers
            breaks = self._context['breaks']

            if line.startswith("Grand Total"):
                # The last line in the file has column breaks that don't
                # quite line up with the headers
                breaks = [0, 17, 21, 54, 66, 76, 85, 93, 103, 113, 122, 130, 140, 150, 157, 165, 173, 181, 189, 197, 209, 219, 228, 236, 245, 255]

            cols = split_line_into_columns(self._context.raw_line, breaks)
                
        # Fourth column (index 3) should be the start of vote results
        # and therefore a number
        if not number_re.match(cols[3]):
            if cols[0].endswith("Total"):
                cols = self._split_totals(cols)
            elif ("Absentee and Special Ballots" in cols[2] or
                  "Oskaloosa Ward 2" in cols[2] or
                  "Oskaloosa Ward 3" in cols[2]):
                # Some rows just have blank values in certain columns. Onward.
                pass
            elif "Falls Plymouth Lime Creek Mason N Twps Pct" in line:
                cols[2] = "Falls Plymouth Lime Creek Mason N Twps Pct"
                cols[3] = "265"
            else:
                print(cols)
                raise AssertionError("Unexpected column alignment")

        county = cols[0]
        county_num = cols[1]
        jurisdiction = cols[2]
        votes = cols[3:-3]
        district_numbers = cols[-3:]

        for i in range(len(votes)):
            vote = votes[i].replace(',', '')

            if vote == "" or vote == "X":
                continue

            assert clean_number_re.match(vote), "Invalid vote value: {}".format(vote)

            office_idx = i / len(self._context['parties'])
            office = self._context['offices'][office_idx]
            party = self._context['parties'][i % len(self._context['parties'])]

            if office == "US REPRESENTATIVE":
                district = district_numbers[2]
            elif office == "IOWA SENATE":
                district = district_numbers[1]
            elif office == "IOWA HOUSE":
                district = district_numbers[0]
            else:
                district = ""

            result = {
                'office': office, 
                'district': district, 
                'candidate': '',
                'party': party, 
                'reporting_level': 'precinct', 
                'jurisdiction': jurisdiction,
                'county': county,
                'county_number': county_num,
                'votes': vote, 
            }
            self._context.results.append(result)

    @classmethod
    def _merge(cls, l1, l2):
        if (len(l1) > len(l2)):
            longer = l1
            shorter = l2
        else:
            longer = l2
            shorter = l1

        return shorter[0:] + longer[len(shorter):]

    def _split_totals(self, cols):
        """
        Split first column into county name, county number and precinct name
        """
        cols[0] = ' '.join(re.split(r'\s+', cols[0])[1:-1])
        cols.insert(1, "Total")
        cols.insert(2, "")
        # There should be 23 columns.  Total rows don't have the legislative
        # district cols
        assert len(cols) == 23
        return cols


class ResultParser(BaseParser):
    def __init__(self, infile):
        super(ResultParser, self).__init__(infile)
        self._register_state(RootState(self))
        self._register_state(HeaderState(self))
        self._register_state(ResultsState(self))
        self._current_state = self._get_state('root')

        self['primary'] = False

fields = [
    'office',
    'district',
    'candidate',
    'party',
    'reporting_level',
    'jurisdiction',
    'county',
    'county_number',
    'votes',
]

from unittest import TestCase

from openelexdata.us.ia.util import (district_word_to_number, parse_fixed_widths,
    get_column_breaks)

class TestUtil(TestCase):
    def test_district_word_to_number(self):
        self.assertEqual(district_word_to_number("SIXTY-FIFTH"), 65)
        self.assertEqual(district_word_to_number("NINETIETH"), 90)
        self.assertEqual(district_word_to_number("fifty fifth", " "), 55)
        self.assertEqual(district_word_to_number("eighth"), 8)

    def test_parse_fixed_width(self):
        line = "   County     Democratic Republican Party of Iowa   Party   Reform Party   Workers         Constitution          USA           by Petition    Scattering   Totals"
        expected = [
            "County",
            "Democratic",
            "Republican",
            "Party of Iowa",
            "Party",
            "Reform Party",
            "Workers",
            "Constitution",
            "USA",
            "by Petition",
            "Scattering",
            "Totals",
        ]
        fieldwidths = [14, 11, 11, 13, 11, 15, 16, 18, 18, 15, 13, 6]
        bits = parse_fixed_widths(fieldwidths, line)
        self.assertEqual(len(bits), len(fieldwidths))
        self.assertEqual(bits, expected)

    def test_get_column_breaks(self):
        lines = [
            "                Democratic       Republican            Scattering        Totals ",
            "                                Dwayne Arlan ",
        ]
        breaks = get_column_breaks(lines)
        self.assertEqual(breaks, [16, 32, 55, 73])

        lines = [
            "                Democratic       Republican            Scattering        Totals",
            "                 Wesley            Greg",
            "                 Whitead         Hoversten",
        ]
        breaks = get_column_breaks(lines)
        self.assertEqual(breaks, [16, 33, 55, 73])

        lines = [
            "                Doug Gross     Steve Sukup   Bob Vander ",
            "                                               Plaats     Write-In ",
            "                 Republican    Republican                  Votes         Totals",
            "                                              Republican",
        ]
        breaks = get_column_breaks(lines)
        self.assertEqual(breaks, [16, 31, 45, 58, 73])

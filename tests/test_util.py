from unittest import TestCase

from openelexdataia.util import district_word_to_number, parse_fixed_widths

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

from unittest import TestCase

from openelexdataia.util import district_word_to_number

class TestUtil(TestCase):
    def test_district_word_to_number(self):
        self.assertEqual(district_word_to_number("SIXTY-FIFTH"), 65)
        self.assertEqual(district_word_to_number("NINETIETH"), 90)
        self.assertEqual(district_word_to_number("fifty fifth", " "), 55)
        self.assertEqual(district_word_to_number("eighth"), 8)

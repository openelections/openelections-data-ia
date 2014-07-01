"""
Test parsing of 2004 general election precinct-level file
"""

from unittest import TestCase

from openelexdata.us.ia.parser.precinct2004 import HeaderState

class HeaderStateTestCase(TestCase):
    def test_detect_column_breaks(self):
        lines = [
            "     COUNTY       CO #               PRECINCT NAME          DEM     REP     OTH   SC   DEM    REP      OTH   SC   DEM         REP    OTH SC     DEM     REP    OTH   SC   DEM     REP     OTH   SC   IA HOUSE IA SENATE US REP",
        ]

        expected_breaks = [
            [0, 18, 37, 60, 68, 76, 82, 87, 94, 103, 109, 114, 126, 133, 137,
            144, 152, 159, 165, 170, 178, 186, 192, 197, 206, 216],
        ]

        for i in range(len(lines)):
            breaks = HeaderState._detect_column_breaks(lines[i])
            self.assertEqual(breaks, expected_breaks[i])

import re
import struct

NUMBER_WORDS = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
    'thirty': 30,
    'forty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90,

    'first': 1,
    'second': 2,
    'third': 3,
    'fourth': 4,
    'fifth': 5,
    'sixth': 6,
    'seventh': 7,
    'eighth': 8,
    'ninth': 9,
    'tenth': 10,
    'eleventh': 11,
    'twelfth': 12,
    'thirteenth': 13,
    'fourteenth': 14,
    'fifteenth': 15,
    'sixteenth': 16,
    'seventeenth': 17,
    'eighteenth': 18,
    'nineteenth': 19,
    
    'twentieth': 20,
    'thirtieth': 30,
    'fortieth': 40,
    'fiftieth': 50,
    'sixtieth': 60,
    'seventieth': 70,
    'eightieth': 80,
    'ninetieth': 90,
}

def district_word_to_number(word, sep='-'):
    """Convert a district number, represented in English words, to an int"""
    bits = word.lower().split(sep)
    first = int(NUMBER_WORDS[bits[0]])
    if len(bits) == 1:
        return first
    else:
        return first + district_word_to_number(sep.join(bits[1:]), sep)

def parse_fixed_widths(fieldwidths, line):
    expected_length = sum(fieldwidths)
    line = line.ljust(expected_length, ' ')
    fmts = ' '.join("{}{}".format(w, "s") for w in fieldwidths)
    return [col.strip() for col in struct.unpack(fmts, line)]

def get_column_breaks(lines, whitespace_re=re.compile(r'\s')):
    """
    Get breakpoints for whitespace-defined columns in lines of text

    This is needed because the columns are not aligned and some columns
    are empty.

    Args:
        lines: List of strings representing a line of data in columns
        whitespace_re: Compiled regex used to test that text is whitespace.

    Returns:
        A list of integers representing the start indexes of the columns
    """
    smap = []
    breaks = []

    for line in lines:
        ldiff = len(line) - len(smap)
        if ldiff > 0:
            smap.extend([False] * ldiff)

        for i in range(len(line)):
            smap[i] = smap[i] or whitespace_re.match(line[i]) is None

    for i in range(len(smap)):
        if smap[i] and not smap[i -1 ]:
            breaks.append(i)

    return breaks

def split_into_columns(lines, breaks):
    cols = []
    for line in lines: 
        cols.append(split_line_into_columns(line, breaks))
    return cols

def split_line_into_columns(line, breaks):
    cols = []
    for i in range(len(breaks) - 1):
        cols.append(line[breaks[i]:breaks[i+1] - 1].strip())
    cols.append(line[breaks[-1]:].strip())
    return cols


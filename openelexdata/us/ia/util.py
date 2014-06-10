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

def old_get_column_breaks(lines, whitespace_re):
    num_cols = 0
    baseline = None
    baseline_idx = 0
    rows = []

    # Determine which line has the most columns.
    for i in range(len(lines)):
        line = lines[i]
        cols = whitespace_re.split(line.strip())
        rows.append(cols)
        if len(cols) > num_cols:
            num_cols = len(cols)
            baseline = line
            baseline_idx = i

    # Determin the breakpoints for the row with most columns
    breaks = []
    for col in rows[baseline_idx]: 
        brk = baseline.index(col)
        breaks.append(brk)

    for i in range(len(lines)):
        if i == baseline_idx:
            continue
 
        line = lines[i]
        cols = rows[i]
        for col in cols:
            brk = line.index(col)
            for j in range(len(breaks)):
               if brk <= breaks[j]:
                   print(col, brk)
                   breaks[j] = brk
                   break

    return breaks

def get_column_breaks(lines, whitespace_re):
    """
    Get breakpoints for whitespace-defined columns in lines of text

    This is needed because the columns are not aligned and some columns
    are empty.

    Args:
        lines: List of strings representing a line of data in columns
        whitespace_re: Compiled regex used to split text into columns

    Returns:
        A list of integers representing the start indexes of the columns
    """
    all_breaks = []
    breaks = None
    baseline_idx = 0

    # Detect the columns and record the start and end indices of
    # non-whitespace text
    for i in range(len(lines)):
        line = lines[i]
        breaks_for_line = []
        cols = whitespace_re.split(line.strip())
        for col in cols:
            brk = line.index(col)
            end = brk + len(col) - 1
            breaks_for_line.append((brk, end))

        all_breaks.append(breaks_for_line)

        # We want to determine which line has the most columns.
        # We'll use this as the baseline for all the other columns.
        if breaks is None or len(cols) > len(breaks):
            breaks = breaks_for_line
            baseline_idx = i
   
    for i in range(len(all_breaks)):
        # Skip the baseline
        if i == baseline_idx:
            continue

        for start, end in all_breaks[i]:
            # Iterate through the columns and try to determine which baseline
            # column it corresponds to
            for j in range(len(breaks)):
                cur_start, cur_end = breaks[j]
                new_start = cur_start
                new_end = cur_end
                if start < cur_end and end > cur_start:
                    # A column in this line overlaps with one of the baseline
                    # columns.

                    # Check if we need to adjust the start and end indices of
                    # the column.
                    if start < cur_start:
                        new_start = start

                    if end > cur_end:
                        new_end = end

                    breaks[j] = (new_start, new_end)
                    break

    return [start for start, end in breaks]

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


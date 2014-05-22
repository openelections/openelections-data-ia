# openelections-data-ia

Election results for Iowa.

These are machine readable results converted from the PDF results published at http://sos.iowa.gov/elections/results/.

## Methodology

### Conversion script

Files were converted to text using the pdftotext command and the text output was passed through a filter to convert the raw text to CSV:

```
pdftotext -layout pdf/20000606__ia__primary__county.pdf - | ./bin/parse_2000_primary.py > 20000606__ia__primary__county.csv
```

### Manual entry

Some files had a small number of results and were in a format that was difficult to parse.  These were entered manually.

This process was used for the following elections:

* 2000-01-04 Special Election, State Representative, District 53

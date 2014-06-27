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

## TODO

I'm prioritizing non-special elections and getting the most coverage possible so there are some results I'm putting on the backburner. These include:

* 20020122__ia__special__general__state_house__28__county.pdf
* 20020219__ia__special__general__state_senate__39__county.pdf
* 20020312__ia__special__general__state_senate__10__state.pdf
* 20021105__ia__general__precinct.pdf
* 20030114__ia__special__general__state_senate__26__county.pdf
* 20030211__ia__special__general__state_house__62__county.pdf
* 20030805__ia__special__general__state_house__100__county.pdf
* 20030826__ia__special__general__state_house__30__county.pdf
* 20040203__ia__special__general__state_senate__30__county.pdf

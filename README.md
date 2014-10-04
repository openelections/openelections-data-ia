# openelections-data-ia

Election results for Iowa.

These are machine readable results converted from the PDF results published at http://sos.iowa.gov/elections/results/.

## Methodology

### Parsing script

Files were converted to text using the pdftotext command and the text output was passed through a filter to convert the raw text to CSV:

```
pdftotext -layout pdf/20000606__ia__primary__county.pdf - | ./bin/parse_2000_primary.py > 20000606__ia__primary__county.csv
```

There are parsing scripts for many of the results files with descriptive names
or docstrings.  These scripts aren't very DRY, because figuring out what changed
between vintages of files and abstracting this out seemed a low priority. 

### Manual preprocessing

#### 2006 General

pdftotext couldn't extract the text from the PDF file for the county-level 2006-11-07 general election results.  I used Adobe Acrobat Pro 9 to extract the text from the file and saved it to ``txt/20061107__ia__general__county.orig.txt``.  Some of the text was transposed and the spacing made it difficult to parse, so I had to manually clean it up using vim and LibreOffice Calc.  The cleaned text file is saved in ``txt/20061107__ia__general__county.txt``.

#### 2013 Special Election, State Senate District 13 Warren County

This was an image PDF. I used pdftoppm, ImageMagick and Tesseract to extract text from the PDF.  These steps are performed in ``bin/ocr_2013_special_ss_13_precinct_warren``.

I then copied and pasted the text into LibreOffice Calc and manually corrected some of the values that were incorrectly recognized by Tesseract.  This data mirrors the layout of the PDF file and is saved in ``input/20131119__ia__special__general__warren__state_senate__13__precinct.csv``.

Finally, I used the script ``bin/reshape_2013_special_precinct_ss_13_warren.py`` to reshape the data from the raw format to our more standard format, with one row per candidate (or pseudo-candidate) result. 

#### 2014 Special Election, State House District 25

These were image PDFs. I used pdftoppm, ImageMagick and Tesseract to extract text from the PDF.  These steps are performed in ``bin/ocr_2014_special_sh_25_precinct_(warren|madison)``. 

I then copied and pasted the text into LibreOffice Calc and manually corrected some of the values that were incorrectly recognized by Tesseract.  This data mirrors the layout of the PDF file and is saved in ``20140107__ia__special__general__(madison|warren)__state_house__25__precinct.csv``.

Finally, I used the script ``bin/reshape_2014_special_precinct_sh_25.py`` to reshape the data from the raw format to our more standard format, with one row per candidate (or pseudo-candidate) result.

### Manual entry

Some files had a small number of results and were in a format that was difficult to parse.  These were entered manually.

This process was used for the following elections:

* 2000-01-04 Special Election, State Representative, District 53
* 2002-03-12 Special Election, State Senate, District 10


## TODO

I'm prioritizing non-special elections and getting the most coverage possible so there are some results I'm putting on the backburner.  This is mostly because they are image PDFs. 

These include:

* 20020122__ia__special__general__state_house__28__county.pdf
* 20020219__ia__special__general__state_senate__39__county.pdf
* 20021105__ia__general__precinct.pdf
* 20030114__ia__special__general__state_senate__26__county.pdf
* 20030211__ia__special__general__state_house__62__county.pdf
* 20030805__ia__special__general__state_house__100__county.pdf
* 20030826__ia__special__general__state_house__30__county.pdf
* 20040203__ia__special__general__state_senate__30__county.pdf
* 20091124__ia__special__general__state_house__33__precinct.pdf
* 20100608__ia__primary__county.pdf - Candidate names are in annoying diagonal orientation.  We could manually data enter these, or try to convert to image, rotate, and OCR.
* 20111108__ia__special__general__state_senate__18__precinct.pdf

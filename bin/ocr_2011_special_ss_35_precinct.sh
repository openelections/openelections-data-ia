#!/bin/bash

pdfpath=$1
pdffile=$(basename "$pdfpath")
filename="${pdffile%.*}"
pdftoppm -gray $pdfpath $filename
tesseract "$filename-1.pgm" stdout
rm "$filename-1.pgm"

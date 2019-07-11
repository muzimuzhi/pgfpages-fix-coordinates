# pgfpage-fix-link

LaTeX package `pgfpages` can produce a n-pages-on-1 (nup, from the Linux command [`pdfnup`](https://linux.die.net/man/1/pdfnup)) PDF from within LaTeX, except for the broken hyperlinks. This Python 3 script tries to fix it.

## Dependency
  - [PyPDF2](https://github.com/mstamy2/PyPDF2/)

## How to use
  1. Prepare a pair of PDFs produced by LaTeX, with and without using `pgfpages`
  2. Set PDF file names, as well as the nup layout in Python script
  3. Run the script

## Limitations
  * Limited support for `pgfpages` options.
  * Limited support for all kinds of destinations and regions supported by PDF. At present, only named destinations and simple `/GOTO` are handled. 
  * Tests using PDFs produced by LaTeX engines other than XeLaTeX are not conducted yet.

## Miscellaneous

  * This script is, in part, a response to GitHub issue https://github.com/CTeX-org/forum/issues/45 .

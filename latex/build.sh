#!/bin/bash

TEXFILE='main.tex'
NORMAL='normal'
MERGED='merged'
XDVOPT='-z0'
# XDVOPT='-z0 -C 0x0010'

latexCompile () {
    output=$1
    echo -n 'Compiling '$1'.pdf ... '

    {
        xelatex -no-pdf -8bit -jobname=${output} ${TEXFILE}
        xelatex -no-pdf -8bit -jobname=${output} ${TEXFILE}
        xdvipdfmx ${XDVOPT} ${output}
    } &> /dev/null

    echo 'done'
}

# normal output
sed -i '' 's/^\(\\usepackage{pgfpages}\)/%\1/g' ${TEXFILE}
sed -i '' 's/^\(\\\pgfpagesuselayout\)/%\1/g' ${TEXFILE}

latexCompile ${NORMAL}

# merged output
sed -i '' 's/^%\(\\usepackage{pgfpages}\)/\1/g' ${TEXFILE}
sed -i '' 's/^%\(\\\pgfpagesuselayout\)/\1/g' ${TEXFILE}

latexCompile ${MERGED}

rm *.aux *.log *.out *.xdv

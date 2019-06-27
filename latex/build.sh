#!/bin/bash

TEXFILE='main.tex'
SUFFIX_NORMAL='normal'
SUFFIX_MERGED='nup'
XDVIPDFMX_OPTIONS=''
# XDVOPT='-z0 -C 0x0010'

latexCompile () {
    echo 'Input = '${TEXFILE}

    suffix=$1
    output=${TEXFILE%.*}-${suffix}
    echo -n '  Compiling '${output}'.pdf ... '

    {
        xelatex -no-pdf -8bit -jobname=${output} ${TEXFILE}
        xelatex -no-pdf -8bit -jobname=${output} ${TEXFILE}
        xdvipdfmx ${XDVIPDFMX_OPTIONS} ${output}
    } &> /dev/null

    echo 'done'
}

# normal output
sed -i '' 's/^\(\\usepackage{pgfpages}\)/%\1/g' ${TEXFILE}
sed -i '' 's/^\(\\\pgfpagesuselayout\)/%\1/g' ${TEXFILE}

latexCompile ${SUFFIX_NORMAL}

# merged output
sed -i '' 's/^%\(\\usepackage{pgfpages}\)/\1/g' ${TEXFILE}
sed -i '' 's/^%\(\\\pgfpagesuselayout\)/\1/g' ${TEXFILE}

latexCompile ${SUFFIX_MERGED}

rm *.aux *.log *.out *.xdv

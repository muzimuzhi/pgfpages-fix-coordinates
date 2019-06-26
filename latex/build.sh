#!/bin/bash

TEXFILE='from-forum.tex'
NORMAL='normal'
MERGED='merged'
XDVOPT='-z0'
#XDVOPT='-z0 -C 0x0010'

latexCompile () {
    echo -n 'Compiling '$1'.pdf ... '

    {
#        xelatex -no-pdf -8bit -jobname=$1 main.tex
#        xelatex -no-pdf -8bit -jobname=$1 main.tex
#        xdvipdfmx -C 0x0010 -z0 $1

#        optDest=$1-opt-dest
        optDest=$1
        xelatex -no-pdf -8bit -jobname=${optDest} ${TEXFILE}
        xelatex -no-pdf -8bit -jobname=${optDest} ${TEXFILE}
        xdvipdfmx ${XDVOPT} ${optDest}
    } &> /dev/null

    echo 'done'
}

#rm *.pdf

# normal output
sed -i '' 's/^\(\\usepackage{pgfpages}\)/%\1/g' ${TEXFILE}
sed -i '' 's/^\(\\\pgfpagesuselayout\)/%\1/g' ${TEXFILE}

latexCompile ${NORMAL}

# merged output
sed -i '' 's/^%\(\\usepackage{pgfpages}\)/\1/g' ${TEXFILE}
sed -i '' 's/^%\(\\\pgfpagesuselayout\)/\1/g' ${TEXFILE}

latexCompile ${MERGED}

rm *.aux *.log *.out *.xdv

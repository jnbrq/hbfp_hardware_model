#!/bin/bash

# silent pushd
function pushd() {
    command pushd "$@" > /dev/null
}

# silent popd
function popd() {
    command popd "$@" > /dev/null
}

function list_all() {
    pushd chisel3_generated

    for d in *
    do
        pushd $d
        
        b=`basename $(ls *.v) .v`

        echo bash ./synthesize.bash \""$d"\" \""$b"\"

        popd
    done

    popd
}

list_all | xargs --max-procs=16 -I CMD bash -c CMD

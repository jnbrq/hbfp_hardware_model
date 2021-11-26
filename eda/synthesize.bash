#!/bin/bash

# silent pushd
function pushd() {
    command pushd "$@" > /dev/null
}

# silent popd
function popd() {
    command popd "$@" > /dev/null
}

function run_dc() {
    DESIGN_DIR="$1"
    DESIGN_NAME="$2"
    WORK_DIR="./output/$DESIGN_DIR"

    echo "run_dc DESIGN_DIR=$DESIGN_DIR DESIGN_NAME=$DESIGN_NAME"

    mkdir -p "$WORK_DIR"
    pushd "$WORK_DIR"

    HDL_DIR="../../chisel3_generated/$DESIGN_DIR"

    if [[ ! -d "$HDL_DIR" ]]
    then
        echo "HDL folder is not found."
        echo "Make sure that you execute the Emitter from sbt."
        exit 1
    fi

    if [[ ! -d "HDL" ]]
    then
        ln -s "$HDL_DIR" "HDL"
    fi

    # execute the synthesizer
    SYN_DESIGN="$DESIGN_NAME" dc_shell -f "../../SCRIPTS/syn.tcl" 2>&1 >dc_shell.log

    popd
}

run_dc "$@"

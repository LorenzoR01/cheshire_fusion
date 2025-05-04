#!/bin/bash

EMBENCH_DIR=$(realpath ../../../sw/deps/embench-iot)
ROOT_DIR=$(realpath .)

# Generate a timestamp for the runs folder
TIMESTAMP=$(date +"%Y_%m_%d_%H_%M_%S")
RUN_DIR="$ROOT_DIR/eembc_runs/$TIMESTAMP"

# Define the list of tests
TESTLIST=(
    aha-mont64
    crc32
    cubic
    edn
    huffbench
    matmult-int
    md5sum
    minver
    nbody
    nettle-aes
    nettle-sha256
    nsichneu
    picojpeg
    primecount
    qrduino
    sglib-combined
    slre
    st
    statemate
    tarfind
    ud
    wikisort
)

# Clean env
rm -rf work

# Create the base runs directory with the timestamp
mkdir -p "$RUN_DIR"

# Compile the design once
# questa-2022.4 vsim -64 -c -do "source $ROOT_DIR/compile.cheshire_soc.tcl; exit"
vsim -64 -c -do "source $ROOT_DIR/compile.cheshire_soc.tcl; exit"

# Function to run a single test
run_test() {
    TESTNAME=$1
    mkdir -p "$RUN_DIR/$TESTNAME"
    cd "$RUN_DIR/$TESTNAME" || exit

    #questa-2022.4 vsim -64 -c -do " \
    vsim -64 -c -do " \
    set BINARY $EMBENCH_DIR/bd/src/$TESTNAME/$TESTNAME; \
    set BOOTMODE 0; \
    set PRELMODE 1; \
    vmap work $ROOT_DIR/work; \
    source $ROOT_DIR/start.cheshire_soc.tcl; \
    run -a; \
    exit -f \
    "

    cd "$ROOT_DIR" || exit
}

export -f run_test
export EMBENCH_DIR ROOT_DIR RUN_DIR

# Run tests in parallel with xargs (16 jobs)
printf "%s\n" "${TESTLIST[@]}" | xargs -n 1 -P 2 -I {} bash -c 'run_test "{}"' > /dev/null 2>&1

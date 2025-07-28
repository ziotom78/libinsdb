#!/bin/sh

# This script uses 'dotool' to type the commands that are captured in
# the `.asciinema` file in the Git repository. This is used to
# generate the GIF animation shown as a demo of the 'insdb' command.
#
# To re-record the animation, activate a virtual environment and
# install `libinsdb` in it with `pip install -e .`. Then, record the
# video by opening a new console with some known size (we assume
# 96×24) and run asciinema with this command:
#
# asciinema rec \
#    --title "Libinsdb interactive demo" \
#    --format=asciicast-v2 \
#    --idle-time-limit 2.0 \
#    --overwrite \
#    --quiet \
#    -c sh \
#    docs/libinsdb-96x24.asciinema
#
# Then run this script from another window. The output file can be
# converted using asciinema-agg:
#
#    agg docs/libinsdb-96x24.asciinema demo.gif
#
# (This is the reason for the --format= parameter used with `asciinema
# rec`, as at the time of writing `agg` does not recognize the new
# asciicast-v3 format.)
#
# CAUTION: this script assumes that `asciinema` is executed within the
#          `libinsdb` directory.

enter() {
    dotool <<EOF
key enter
EOF
}

type() {
    dotool <<EOF
typedelay 50
type $1
EOF
}

run_command() {
    type "$1"
    sleep 1s
    enter
    sleep 2s
}

echo "Focus the Konsole window and wait"
sleep 3s

# These weird characters are due to the bad interaction between
# keyd and dotool on my system, where I use an italian keyboard
# but with an 'en' layout modified by keyd…
# To understand the meaning of the weird characters, you must
# map the key on the italian keyboard with the same key in the
# english layout. For instance, the ' character corresponds to -
#
# See this for reference:
#
#    https://en.wikipedia.org/wiki/British_and_American_keyboards

run_command "insdb ''help"
run_command "ls tests-mock?db?json"
run_command "insdb tests-mock?db?json"
run_command "help"
run_command "help ls"
run_command "ls"
run_command "cd LFI"
run_command "ls"
run_command "cd frequency?030?ghz"
run_command "tree"
run_command "cd .."
run_command "ls"
run_command "help show"
run_command "show full?focal?plane"
run_command "show a862183e'572f'4629'9eec'fb3abeb21aa2"
run_command "show 87230a9f'70c7'4fa3'8843'834d52c9fd06"
run_command "help metadata"
run_command "metadata 87230a9f'70c7'4fa3'8843'834d52c9fd06"
run_command "quit"

run_command "insdb ''command àmetadata 87230a9f'70c7'4fa3'8843'834d52c9fd06à tests-mock?db?json"

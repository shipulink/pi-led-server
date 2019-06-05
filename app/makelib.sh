#!/bin/sh

as -o lib.o lib.s
gcc -shared -o lib.so lib.o
rm -f lib.o
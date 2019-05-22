#!/bin/bash

as -o ledtest.o ledtest.s
gcc -o ledtest ledtest.o -L. -l:ledlib.so -Wl,-rpath,$(pwd)
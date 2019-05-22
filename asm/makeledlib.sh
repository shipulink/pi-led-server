#!/bin/bash

as -o ledlib.o ledlib.s
gcc -shared -o ledlib.so ledlib.o
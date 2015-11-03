#!/usr/bin/env python

import sys

import eric6dbgstub

def main():
    print("Hello World!")
    sys.exit(0)
    
if __name__ == "__main__":
    if eric6dbgstub.initDebugger("standard"):
# or   if eric6dbgstub.initDebugger("threads"):
        eric6dbgstub.debugger.startDebugger()

    main()

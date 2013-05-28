#!/bin/bash

res=$( ./Ref_clock_detector | grep "Ref_clock:" | cut -f2 -d ' ')

echo "$HOSTNAME;$res"

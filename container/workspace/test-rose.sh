#!/bin/bash

git clone https://github.com/LLNL/backstroke.git
cd backstroke
make
sudo make install
make check
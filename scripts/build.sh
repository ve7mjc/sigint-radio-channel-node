#!/bin/bash

cd RTLSDR-Airband/
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DNFM=ON -DMIRISDR=OFF -DSOAPYSDR=ON ../

make -j8
sudo make install


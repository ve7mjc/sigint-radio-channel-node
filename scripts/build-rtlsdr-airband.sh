#!/bin/bash

# Ubuntu 22 LTS at least..
sudo apt install -y pkg-config libconfig++-dev libmp3lame-dev libshout-dev libfftw3-dev librtlsdr-dev

cd ext/RTLSDR-Airband/
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DRTLSDR=ON -DNFM=ON -DMIRISDR=OFF -DSOAPYSDR=ON ..

make -j8
sudo make install


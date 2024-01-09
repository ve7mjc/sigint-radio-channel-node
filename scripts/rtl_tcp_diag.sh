#!/bin/bash

# LOCAL_ADDR="172.17.149.108"
LOCAL_ADDR="0.0.0.0"
FS=1800000

rtl_tcp -a ${LOCAL_ADDR} -p 5010 -d 0 -s $FS


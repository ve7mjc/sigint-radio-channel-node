#!/bin/bash

sudo cp -v blacklist-rtlsdr.conf /etc/modprobe.d/

sudo modprobe -r dvb_core
sudo modprobe -r dvb_usb_rtl2832u
sudo modprobe -r dvb_usb_rtl28xxu
sudo modprobe -r dvb_usb_v2
sudo modprobe -r r820t
sudo modprobe -r rtl2830
sudo modprobe -r rtl2832
sudo modprobe -r rtl2832_sdr
sudo modprobe -r rtl2838

sudo depmod -a

sudo update-initramfs -u

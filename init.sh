#!/bin/bash

user="sdr"
group="sdr"

echo "creating group ${group}"
sudo groupadd $group

echo "creating user ${user}"
sudo useradd -g $group -s /bin/bash -m $user

echo "adding $user to plugdev for usb devices"
sudo usermod -aG plugdev $user

CURRENT_USER=$(whoami)
echo "adding user '${CURRENT_USER}' to group '${group}'"
sudo usermod -aG $group $CURRENT_USER

# Get the full path to the script
SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

sudo chgrp -R sdr $SCRIPT_DIR
sudo chmod -R g+rw $SCRIPT_DIR

service_name="sigint-node.service"
sudo cp $service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name


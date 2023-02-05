#!/bin/bash

# Find the location of this *.sh script.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Copy discover_shutters.py into a root-owned directory.
TPATH=/usr/local/sbin/trigs_discover_shutters.py
cp "$SCRIPT_DIR/discover_shutters.py" $TPATH

# Make the script owned and accessible only for root.
chown root:root $TPATH
chmod 700 $TPATH

# Give all users permission to execute the script with sudo and without a password.
echo "ALL  ALL=(ALL) NOPASSWD: $TPATH" > /etc/sudoers.d/discover_shutters

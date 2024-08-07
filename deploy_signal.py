#!/usr/bin/env python

# Automatize the signal-cli deployment

import re
import subprocess
import sys

print("signal-cli deployment script by Antoine Marzin - 2024")

def check_java():
    print("Check java runtime environment", end='', flush=True)
    try:
        p = subprocess.run(["java",
                            "-version"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
        
        # "java -version" weirdly output on stderr
        # Extract version from the whole output using regex
        stderr = p.stderr.decode()
        pattern = '\"(\d+).*\"'
        version = re.search(pattern, stderr).groups()[0]

        if int(version) < 21:
            print(f" -> JRE v21 is required, you have v{version}")
            sys.exit(1)
        else:
            print(f" -> OK (found v{version})")


    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

def check_signal_cli():
    print("Check signal-cli")
    # TODO check/install signal-cli

def register():
    print("Register account")
    # TODO register account with phone/QR code (qrencode app)

def install_daemon():
    print("Install daemon")
    # TODO install and run signal-cli daemon (jsonRpc)

def check_test():
    print("Check test final")
    # TODO check with sending a msg (note to self)


check_java()
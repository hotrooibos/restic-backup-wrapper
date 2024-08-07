#!/usr/bin/env python

# Automatize the signal-cli deployment

import re
import subprocess
import sys

REQ_JAVA_VERSION = 21

print("signal-cli deployment script by Antoine Marzin - 2024")

def check_java():
    print("Check java runtime environment", end='', flush=True)
    try:
        # Note : oddly, java send "-version" output to stderr, not stdout
        p = subprocess.run(["java",
                            "-version"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
        
        # Extract version from the whole output using regex
        stderr = p.stderr.decode()
        pattern = '(\\d+).*'
        version = re.search(pattern, stderr).groups()[0]

        # Check version requirement
        if int(version) < REQ_JAVA_VERSION:
            print(f" -> KO (JRE v{REQ_JAVA_VERSION}+ is required, you have v{version})")
            sys.exit(1)
        else:
            print(f" -> OK (JRE v{version} found)")

    except FileNotFoundError as e:
        print(f" -> JRE not found, install it (v{REQ_JAVA_VERSION}+) if it's not, or check your PATH")
        print(f"\nOutput :\n\t{e}")
        sys.exit(1)


def check_signal_cli():
    print("Check signal-cli", end='', flush=True)
    
    try:
        p = subprocess.run(["signal-cli",
                            "--version"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
        
        print(f" -> OK")

    except FileNotFoundError as e:
        print(f" -> signal-cli not found, install it if it's not, or check your PATH")
        print(f"\nOutput :\n\t{e}")
        sys.exit(1)


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
check_signal_cli()
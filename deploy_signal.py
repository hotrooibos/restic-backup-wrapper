#!/usr/bin/env python

# Automatize the signal-cli deployment

import re
import subprocess
import sys

REQ_JAVA_VERSION = 21

print("signal-cli deployment script by Antoine Marzin - 2024\n")

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
            print(f" -> KO, JRE v{REQ_JAVA_VERSION}+ is required, you have v{version}." \
                  "\n\nDownload the latest JRE packages here : " \
                  "https://www.oracle.com/java/technologies/downloads/.")
            sys.exit(1)
        else:
            print(f" -> OK (JRE v{version} found)")

    except FileNotFoundError as e:
        print(f" -> KO, JRE not found, install it (v{REQ_JAVA_VERSION}+) if it's not, " \
              "or check your PATH.\n\nDownload the latest JRE packages here : " \
              "https://www.oracle.com/java/technologies/downloads/." \
              f"\nOutput :\n\t{e}")
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
        print(" -> KO, signal-cli not found, install it if it's not, or check your PATH." \
              "\n\nDownload the latest linux native release here : " \
              "https://github.com/AsamK/signal-cli/releases/latest, and " \
              "install it in /usr/local/bin/." \
              f"\nOutput :\n\t{e}")
        sys.exit(1)


def check_qrencode():
    print("Check qrencode", end='', flush=True)

    try:
        p = subprocess.run(["qrencode"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
        
        print(f" -> OK")

    except FileNotFoundError as e:
        print(" -> KO, qrencode not found, please install it first " \
              "\n(ex : dnf install qrencode / apt install qrencode)." \
              f"\nOutput :\n\t{e}")
        sys.exit(1)


def register():
    print("Register account")
    # TODO register account with phone/QR code (qrencode app)

    check_qrencode()
    pair = input("Do you wish to link to an existing device ? [y/N]")

    # TODO signal-cli link | tee >(xargs -L 1 qrencode -t utf8)

    # if pair == "y":
    #     ps1 = subprocess.run(["signal-cli link | tee >[xargs -L 1 qrencode -t utf8]"],
    #                          shell=True)
        

def install_daemon():
    print("Install daemon")
    # TODO install and run signal-cli daemon (jsonRpc)

def check_test():
    print("Check test final")
    # TODO check with sending a msg (note to self)


check_java()
check_signal_cli()
register()

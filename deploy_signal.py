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
    try:
        p = subprocess.run(["qrencode"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)

    except FileNotFoundError as e:
        print("Qrencode not found, please install it first " \
              "\n(ex : dnf install qrencode / apt install qrencode)." \
              f"\nOutput :\n\t{e}")
        sys.exit(1)


def register():
    while True:
        print("\nRegister account")
        # TODO check if existing account exists, if so ask to use it y/n
        
        inp = input("Do you wish to link to an existing master (phone) ? [y/N]")
        
        if inp in ("y", "Y"):
            check_qrencode()

            device_name = input("What should this device named ? [default : cli] ")
            
            if device_name == "": device_name = "cli"
            
            input("Your terminal display theme must be dark (light text/dark background) " \
                  "for the QR code to be read by Signal app. Press ENTER when ready.")

            print("Flash the following QR code from your phone's Signal settings.\n" \
                  "Press Ctrl+C to abort.\n")

            # Request a Signal linking URL, and print the output in stdout
            # both in string, and as a QR code. Equivalent to the following cmd :
            # signal-cli link | tee >(xargs -L 1 qrencode -t utf8)
            # Ref : https://github.com/AsamK/signal-cli/wiki/Linking-other-devices-%28Provisioning%29
            ps = subprocess.Popen(['signal-cli', 'link',
                                   '-n', device_name],
                                   stdout=subprocess.PIPE)

            for line in ps.stdout:
                strline = line.decode('utf-8')
                subprocess.run(['qrencode', '-t', 'utf8'],
                                input=strline.encode('utf-8'))
                print(strline, end='')

            ps.wait()
            break

        # TODO process to create a new Signal master device
        elif inp in ("n", "N", ""):
            inp = input("Do you wish to create a new master device ? [y/N]")

            if inp in ("y", "Y"):
                print("Create new master device : https://github.com/AsamK/signal-cli/wiki/Quickstart#set-up-an-account")
                break

            elif inp in ("n", "N", ""):
                break
        

def install_daemon():
    print("\nTODO Install systemd service/timer")
    # TODO install systemd service/timer that run signal-cli daemon (jsonRpc)
    # ask for port (default 8080)
    # run the following at startup and now
    # signal-cli -a +33123456789 daemon --http=localhost:8080 

def check_test():
    print("Check test final")
    # TODO check with sending a msg (note to self)


while True:
    inp = input("\n[0] Check config\n" \
                "[1] Setup Signal\n" \
                "[2] Install Signal API (JSON-RPC requests) daemon\n" \
                "[9] Exit\n:")

    if inp == "0":
        check_java()
        check_signal_cli()
        check_test()
    elif inp == "1":
        register()
    elif inp == "2":
        install_daemon()
    elif inp == "9":
        sys.exit(0)
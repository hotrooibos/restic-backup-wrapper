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
    inp = menu_gen("\nRegister account",
                   "List local Signal accounts",
                   "Link this device to an existing master (phone)",
                   "Create a new master device",
                   "(Destructive!) Remove all local Signal data")

    if inp == "1":
        ps = subprocess.run(['signal-cli', 'listAccounts'],
                            stdout=subprocess.PIPE)
        if ps.stdout.decode() == "":
            print("No local Signal account data found.")
        else:
            print(ps.stdout.decode())


    if inp == "2":
        check_qrencode()

        device_name = input("What should this device be named ? [default : cli] ")
        
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
 
    if inp == "3":
        # TODO create new master device
        print("Create new master device : https://github.com/AsamK/signal-cli/wiki/Quickstart#set-up-an-account")
    
    if inp == "4":
        inp = input("This is a destructive action that will delete all local Signal data "\
                    "(registered/linked accounts).\nType \"DELETE\" to proceed.\n:")
        if inp == "DELETE":
            subprocess.run(['signal-cli', 'deleteLocalAccountData'])
            print("Local data removed.")
        else:
            print("Abort.")


def install_daemon():
    print("\nTODO Install systemd service/timer")
    # TODO install systemd service/timer that run signal-cli daemon (jsonRpc)
    # ask for port (default 8080)
    # run the following at startup and now
    # signal-cli -a +33123456789 daemon --http=localhost:8080 

def check_test():
    print("Check test final")
    # TODO check with sending a msg (note to self)

def menu_gen(title, *args):
    """
    Generate a CLI selection menu
    """
    if 99 < len(args) == 0:
        raise Exception("Error in menu generator")

    while True:
        print(title)
        for idx, val in enumerate(args):
            print(f"  [{idx+1}] {val}")

        if idx == len(args)-1:
            print(f"  [0] Exit / cancel")

        res = input(":")

        try:
            if (int(res) > len(args)):
                continue
            else:
                return res
        except ValueError:
            continue

while True:
    inp = menu_gen("\nMain menu",
                "Check config",
                "Setup Signal",
                "Install Signal API (JSON-RPC requests) daemon")

    if inp == "1":
        check_java()
        check_signal_cli()
        check_test()
    elif inp == "2":
        register()
    elif inp == "3":
        install_daemon()
    elif inp == "0":
        sys.exit(0)
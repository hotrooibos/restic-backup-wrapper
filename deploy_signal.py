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


def manage():
    while True:
        inp = menu_gen("Signal management",
                    ["List local Signal accounts",
                    "Link this device to an existing master (phone)",
                    "Create a new master device",
                    "Remove local accounts"])

        # Exit register
        if inp == "0":
            return
        
        # List accounts
        if inp == "1":
            ps = subprocess.run(['signal-cli', 'listAccounts'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            if ps.stdout.decode() == "" \
            and ps.stderr.decode() == "":
                print("No local Signal account data found.")
            else:
                print(ps.stdout.decode()) if ps.stdout.decode() else None
                print(ps.stderr.decode()) if ps.stderr.decode() else None
            continue

        # Link to a device (gen a QR code)
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
            continue
    
        # Create a new master device
        if inp == "3":
            # https://github.com/AsamK/signal-cli/wiki/Quickstart#set-up-an-account")
            phone_number = input("Phone number with country code" \
                                "(french mobile example: +33612345678)\n:")
            ps = subprocess.run(['signal-cli', '-u', phone_number, 'register'],
                                stderr=subprocess.PIPE)
            
            if "CAPTCHA" in ps.stderr.decode():
                captcha_link = input("Captcha required. Open https://signalcaptchas.org/registration/generate.html " \
                                ", resolve the captcha, and paste here the URL from the " \
                                "\"Open Signal\" link\n:")
                ps = subprocess.run(['signal-cli', '-u', phone_number, 'register',
                                    '--captcha', captcha_link])

            verif_code = input("Type the verification code you received by SMS." \
                               "The format should match 123-456\n:")

            subprocess.run(['signal-cli', '-u', phone_number,
                            'verify', verif_code])

            continue
                
        # Delete accounts
        if inp == "4":
            ps = subprocess.run(['signal-cli', 'listAccounts'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            
            # Get phone numbers (format "+XXXXXXXXXX")
            # from 'signal-cli listAccounts' output
            # with regex, and store them in a list
            output = ps.stdout.decode().split("\n") + \
                ps.stderr.decode().split("\n")
            pattern = "\+\d+"
            accounts = []

            for line in output:
                if len(line) > 0:
                    match = re.search(pattern, line)
                    if match:
                        accounts.append(match.group())
            
            while len(accounts) > 0:
                inp = menu_gen("Which account do you want to remove ?",
                                accounts)
                
                if inp == "0":
                    break

                acc_to_del = accounts[int(inp)-1]
                ps = subprocess.run(['signal-cli',
                                    '-u',
                                    acc_to_del,
                                    'deleteLocalAccountData'],
                                    stderr=subprocess.PIPE)
                
                if ps.returncode == 0:
                    print(f"Local data removed for {acc_to_del}.")
                    accounts.pop(int(inp)-1)
                    break
                else:
                    err_msg = ps.stderr.decode()
                    print(err_msg)

                    if "--ignore-registered" in err_msg:
                        inp_unreg = input("Do you want to " \
                            f"unregister {acc_to_del} ? [y/N]")
                        
                        if inp_unreg in ("Y", "y"):
                            ps = subprocess.run(['signal-cli',
                                                'unregister'])
                            if ps.returncode == 0:
                                print(f"{acc_to_del} unregistered.")
                    else:
                        break
            
                        

            else:
                print("No local Signal account data found.")

            continue

def install_daemon():
    print("\nTODO Install systemd service/timer")
    # TODO install systemd service/timer that run signal-cli daemon (jsonRpc)
    # ask for port (default 8080)
    # run the following at startup and now
    # signal-cli -a +33123456789 daemon --http=localhost:8080 

def check_test():
    print("Check test final")
    # TODO check with sending a msg (note to self)

def menu_gen(title: str, entries: list) -> str:
    """
    Generate a CLI selection menu
    """
    if 99 < len(entries) == 0:
        raise Exception("Error in menu generator")

    while True:
        print(f"\n{title}")

        for i, v in enumerate(entries):
            print(f"  [{i+1}] {v}")

            if i == len(entries)-1:
                print(f"  [0] Exit / cancel")

        res = input(":")

        try:
            if (int(res) > len(entries)):
                continue
            else:
                return res
        except ValueError:
            continue

while True:
    inp = menu_gen("Main menu",
                   ["Check config",
                   "Signal management",
                   "Install Signal API (JSON-RPC requests) daemon"])

    if inp == "0":
        sys.exit(0)
    
    elif inp == "1":
        check_java()
        check_signal_cli()
        check_test()
    
    elif inp == "2":
        manage()
    
    elif inp == "3":
        install_daemon()
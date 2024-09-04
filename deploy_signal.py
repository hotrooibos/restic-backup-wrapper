#!/usr/bin/env python

# Automatize the signal-cli deployment

import json
import getpass
import re
import requests
import set_systemd
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
    print("Check signal-cli installation", end='', flush=True)
    
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
              "copy it in /usr/local/bin/." \
              f"\nOutput :\n\t{e}")
        sys.exit(1)

    print("Check signal-cli daemon", end='', flush=True)

    # Check if signalcli process is running and get its arguments
    ps = subprocess.run(
        ['ps', '-eo', 'comm=,args='],  # `comm` for command name, `args` for full command line
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    match = [
        line for line in ps.stdout.splitlines()
        if line.startswith("signal-cli") and "daemon" in line
    ]

    if match:
        print(f" --> OK, daemon is running")

        for process_info in match:
            parts = process_info.split(maxsplit=1)
            argument_list = parts[1].split() if len(parts) > 1 else []

        for arg in argument_list:
            if "--http" in arg:
                url = arg.split('=')[1]
        
        if url:
            url = f'http://{url}/api/v1/check'

            response = requests.get(url)

            if response.status_code == 200:
                print("Test JSON-RPC HTTP API --> OK")
            else:
                print(f"Test JSON-RPC HTTP API --> KO (code {response})")

        else:
            print(f"Test JSON-RPC HTTP API --> KO (no HTTP endpoint found)")
            return
        
    else:
        print(f" --> KO, no 'signal-cli' process found")
        return
    

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


def get_local_accounts(return_unregistered:bool=True) -> list:
    """
    Run "signal-cli listAccounts" and extract from its
    output (with regex) the local Signal accounts.
    Return a list of accounts/phone numbers.
    ex : ['+33633333333', '+33699999999', '+33651515151']
    """
    ps = subprocess.run(['signal-cli', 'listAccounts'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    
    # Get phone numbers (format "+XXXXXXXXXX")
    # from 'signal-cli listAccounts' output
    # with regex, and store them in a list
    reg_acc = ps.stdout.decode().split("\n") 
    unreg_acc = ps.stderr.decode().split("\n")
    
    output = reg_acc
    if return_unregistered:
        output += unreg_acc

    pattern = "\\+\\d+"
    accounts = []

    for line in output:
        if len(line) > 0:
            match = re.search(pattern, line)
            if match:
                accounts.append(match.group())
    
    return accounts


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
            try:
                ps = subprocess.Popen(['signal-cli', 'link',
                                      '-n', device_name],
                                      stdout=subprocess.PIPE)

                for line in ps.stdout:
                    strline = line.decode('utf-8')
                    subprocess.run(['qrencode', '-t', 'utf8'],
                                    input=strline.encode('utf-8'))
                    print(strline, end='')

                ps.wait()

            except KeyboardInterrupt:
                continue
            
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
                
                if ps.returncode != 0:
                    continue

            verif_code = input("Type the verification code you received by SMS." \
                               "The format should match 123-456\n:")

            subprocess.run(['signal-cli', '-u', phone_number,
                            'verify', verif_code])

            continue
                
        # Delete accounts
        if inp == "4":
            accounts = get_local_accounts()
            
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


def setup_daemon() -> tuple:
    """
    Show a setup menu for the Signal daemon
    Port should be in range 1024-65535 and account should
    already be registered locally and given at the format "+XXXXXXXXXXX".
    
    Returns a tuple with two strings : port, signal account

    Example :

        ("8008", "+33612345678")
    """
    # Set tcp port listened by daemon
    while True:
        port = input("On what local host port will signal-cli daemon " \
                     "run ? [default : 8008]\n:")
                
        if port == "":
            port = "8008"

        # Numbers from 1024 to 65535 
        pattern = "^(102[4-9]|10[3-9]\\d|1[1-9]\\d{2}|[2-9]\\d{3}|[1-5]" \
                  "\\d{4}|6[0-4]\\d{3}|65[0-4]\\d|655[0-2]\\d|6553[0-5])$"

        match = re.search(pattern, port)

        if match:
            break
        else:
            print("Port must be in range 1024-65535).")

    # Pick the Signal account (phone number) to be used by daemon
    accounts = get_local_accounts(return_unregistered=False)

    if len(accounts) == 0:
        print("No registered Signal account found, register one first.")
        return

    while len(accounts) > 0:
        inp = menu_gen("Which Signal account will be used ?",
                    accounts)
        
        if inp == "0":
            return
        elif int(inp) in range(1, len(accounts)+1):
            account = accounts[int(inp)-1]
            break
    
    # Define which local user account will be used to run the daemon
    # By default, it will use the user used to run this script
    curr_user = getpass.getuser()

    user = input(f"What user should be used to run the daemon ? [default : {curr_user}]")
    
    if not user:
        user = curr_user
    
    return port, account, user


def run_daemon(port: str=None,
               account: str=None):
    """
    Run the JSON RPC API daemon via HTTP.
    If no argument are given, will run the daemon setup.

    Exemple : run_daemon(port="8080", account="+33612345678")
    """
    print("\nRun daemon")

    # Run daemon setup menu if no port/account given
    if not port or not account:
        setup_values = setup_daemon()
        port = setup_values[0]
        account = setup_values[1]

    # Run daemon
    # signal-cli -a +33123456789 daemon --http=localhost:8008
    print(f"\nRunning daemon with user account {account} on port {port}" \
          "\nPress Ctrl+C at any time to shut it down.")
    try:
        ps = subprocess.run(['signal-cli', '-a', account,
                             'daemon', f'--http=localhost:{port}'])
    except KeyboardInterrupt:
        return
    

def install_daemon():
    """
    Install JSON RPC API daemon with Systemd.
    """
    print("\nInstall daemon")
    # Run daemon setup menu
    setup_values = setup_daemon()
    port = setup_values[0]
    account = setup_values[1]
    user = setup_values[2]

    set_systemd.service(unit_filename="signal-daemon",
                        description="Signal-cli daemon for JSON-RPC API",
                        after="network.target",
                        type="simple",
                        execstart=f"signal-cli -a {account} daemon " \
                                  f"--http=localhost:{port}",
                        restart="on-failure",
                        restartsec="60",
                        user=user,
                        startnow=True)


def message_test(port, account):
    """
    Send a Signal self note (msg to self)
    """
    url = f'http://localhost:{port}/api/v1/rpc'

    payload = {
        'jsonrpc': '2.0',
        'method': 'send',
        'params': {
            'recipient': [account],
            'message': 'Test from Signal deployment script !'
        },
        'id': 1
    }

    headers = {
        'Content-Type': 'application/json'
    }

    # Sending the request
    try:
        response = requests.post(url,
                                headers=headers,
                                data=json.dumps(payload))

        # Handling the response
        if response.status_code == 200:
            print('Message sent successfully!')
            print('Response:', response.json())
        else:
            print('Failed to send message')
            print('Status code:', response.status_code)
            print('Response:', response.text)
    except requests.ConnectionError:
        print("Connection error, check if Signal daemon is running.")


def menu_gen(title:str,
             entries:list) -> str:
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


"""
Program entry point
"""
if __name__ == "__main__":
    while True:
        inp = menu_gen("Main menu",
                    ["Check config",
                    "Signal management",
                    "Run API daemon (JSON RPC)",
                    "Install/uninstall API daemon with Systemd"])

        if inp == "0":
            sys.exit(0)
        
        elif inp == "1":
            check_java()
            check_signal_cli()
            # message_test("8008", "+33612345678")
        
        elif inp == "2":
            manage()
        
        elif inp == "3":
            run_daemon()

        elif inp == "4":
            install_daemon()
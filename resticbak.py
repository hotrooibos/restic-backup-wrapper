#!/usr/bin/env python

# Restic backups script by Antoine Marzin
#
# This script automates restic local backups.
# Linux OS only. Auto installation (service) designed for systemd (init must be done manually).

import json
import os
import requests
import settings
import subprocess
import set_systemd
import sys

os.environ['RESTIC_REPOSITORY'] = settings.RESTIC_REPOSITORY
os.environ['RESTIC_PASSWORD'] = settings.REPO_PASSWORD

# Set cache dir to /var/cache if script called by root (systemd)
if os.getuid() == 0:
    os.environ['RESTIC_CACHE_DIR'] = "/var/cache/restic"

EXCLUDE_FILE = f'{settings.RESTIC_REPOSITORY}/.resticignore'


def backup():
    dirs_to_bak = settings.DATA_TO_BAK
    dirs_to_ignore = settings.DATA_TO_IGNORE

    # Check if dirs to be backed up exists
    for k, v in enumerate(dirs_to_bak):
        if not os.path.exists(v):
            print(f"Directory {v} does not exist. Check your settings.")
            sys.exit(1)
    
    if len(dirs_to_bak) < 1:
        quit()

    # Set .resticignore file
    with open(file=f'{settings.RESTIC_REPOSITORY}/.resticignore',
              mode='w',
              encoding='utf-8') as file:
        dirs_to_ignore = "\r".join(dirs_to_ignore)
        file.write(dirs_to_ignore)

    # Build Restic command for subprocess.run
    subp_args = ["restic", "backup"]

    for ele in dirs_to_bak:
        subp_args.append(ele)

    subp_args.append(f"--exclude-file={EXCLUDE_FILE}")
    subp_args.append("--json")
    subp_args.append("--tag")
    subp_args.append(settings.SNAPSHOT_TAG)
    # subp_args.append("--dry-run")

    # Run Restic command
    # ex : restic backup /path/to/data --exclude-file=/path/to/repo/.resticignore --json --tag "Run by resticbackup.py script"
    ps = subprocess.Popen(subp_args,
                          text=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

    for line in ps.stdout:
        out_json = json.loads(line)

        if out_json['message_type'] == "summary":
            sumj = out_json

    for error_line in ps.stderr:
        print(error_line, end='')

    ps.wait()

    if ps.returncode == 0:
        if settings.NOTIFY:
            summary = "Backup successful\n" \
                     f"- {sumj['files_new']} new files\n" \
                     f"- {sumj['files_changed']} changed files\n" \
                     f"- {sumj['files_unmodified']} unmodified files\n" \
                     f"- {sumj['dirs_new']} new directories\n" \
                     f"- {sumj['dirs_changed']} changed directories\n" \
                     f"- {sumj['dirs_unmodified']} unmodified directories\n" \
                     f"- {sumj['data_blobs']} data blobs\n" \
                     f"- {sumj['tree_blobs']} tree blobs\n" \
                     f"- {sumj['data_added']} data added\n" \
                     f"- {sumj['total_files_processed']} files processed\n" \
                     f"- {sumj['total_bytes_processed']} bytes processed\n" \
                     f"- Backup duration : {sumj['total_duration']}s\n" \
                     f"- Snapshot ID : {sumj['snapshot_id']}"
            notify(settings.SIGNAL_API_URL,
                   settings.SIGNAL_RECEIVER,
                   summary)
    else:
        if settings.NOTIFY:
            notify(settings.SIGNAL_API_URL,
                   settings.SIGNAL_RECEIVER,
                   "Backup ERROR")
        sys.exit(1)


def check():
    """
    Perform a structural consistency and integrity verifications of the repository,
    and an integrity check for the given % from user settings of the backed up data
    (restic repository pack files), randomly chosen by restic.
    If data == "100%", it will read the whole, which can be extremely long.
    
    NB : Restic also support file size (in K/M/G/T), so for example it can be data="1G"
    to check 1 Gigabyte randomly picked from the backup data.
    """
    # restic check --read-data-subset=x%
    ps = subprocess.Popen(["restic", "check",
                          f"--read-data-subset={settings.CHECK_SUBSET}"],
                          text=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    
    for line in ps.stdout:
        print(line, end='')

    for err_line in ps.stderr:
        print(err_line, end='')

    ps.wait()

    if ps.returncode == 0:
        if settings.NOTIFY:
            notify(settings.SIGNAL_API_URL,
                   settings.SIGNAL_RECEIVER,
                   f"Check successful\n{line}")
    else:
        if settings.NOTIFY:
            notify(settings.SIGNAL_API_URL,
                   settings.SIGNAL_RECEIVER,
                   f"Check ERROR\n{line}")
        sys.exit(1)


def forget():
    # restic forget --prune --keep-last 5 --keep-daily 5 --keep-weekly 5 --keep-monthly 5 --keep-yearly 5 --json
    ps = subprocess.Popen(["restic", "forget",
                           "--prune",
                           "--keep-last", str(settings.KEEP_LAST),
                           "--keep-daily", str(settings.KEEP_DAILY),
                           "--keep-weekly", str(settings.KEEP_WEEKLY),
                           "--keep-monthly", str(settings.KEEP_MONTHLY),
                           "--keep-yearly", str(settings.KEEP_YEARLY),
                           # "--dry-run",
                           "--json"],
                           text=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    
    out_str = ""
    err_str = ""

    # Will iterate only once : as of Restic v0.17,
    # output of forget command is one single json object
    for line in ps.stdout:
        print(line, end='')
        out_str = line

    for err_line in ps.stderr:
        print(err_line, end='')
        err_str = err_line

    ps.wait()

    if ps.returncode == 0:
        if settings.NOTIFY:

            out_json = json.loads(out_str)

            total_keep = 0
            total_remove = 0

            for v in out_json:
                if v["keep"]:
                    total_keep += len(v["keep"])

                if v["remove"]:
                    total_remove += len(v["remove"])

            summary = "Forget successful\n" \
                    f"Snapshots kept : {str(total_keep)}\n" \
                    f"Snapshots removed : {str(total_remove)}\n"

            notify(settings.SIGNAL_API_URL,
                   settings.SIGNAL_RECEIVER,
                   summary)
            
    else:
        if settings.NOTIFY:
            notify(settings.SIGNAL_API_URL,
                settings.SIGNAL_RECEIVER,
                f"Forget ERROR\n{err_str}")

        sys.exit(1)


def install():
    """
    Install Systemd services and timers for each restic process
    """
    print("Install Systemd services and timers")

    python_path = sys.executable
    curr_script_path = os.path.abspath(sys.argv[0])

    systemd_descr = "Service for Restic Backup script"
    
    # Backup process
    set_systemd.service(unit_filename="resticbackup-backup",
                        description=systemd_descr,
                        after="",
                        type="oneshot",
                        execstart=f"{python_path} {curr_script_path} backup",
                        restart="on-failure",
                        restartsec="2400",
                        user="tda")
    
    set_systemd.timer(unit_filename="resticbackup-backup",
                      description=systemd_descr,
                      oncalendar=settings.CALENDAR_BACKUP)

    # Check process
    set_systemd.service(unit_filename="resticbackup-check",
                        description=systemd_descr,
                        after="",
                        type="oneshot",
                        execstart=f"{python_path} {curr_script_path} check",
                        restart="on-failure",
                        restartsec="60",
                        user="tda")
    
    set_systemd.timer(unit_filename="resticbackup-check",
                      description=systemd_descr,
                      oncalendar=settings.CALENDAR_CHECK)

    # Forget process
    set_systemd.service(unit_filename="resticbackup-forget",
                        description=systemd_descr,
                        after="",
                        type="oneshot",
                        execstart=f"{python_path} {curr_script_path} forget",
                        restart="on-failure",
                        restartsec="600",
                        user="tda")
    
    set_systemd.timer(unit_filename="resticbackup-forget",
                      description=systemd_descr,
                      oncalendar=settings.CALENDAR_FORGET)


def uninstall():
    """
    Remove Systemd services and timers for each restic process
    """
    print("Remove Systemd services and timers")

    set_systemd.uninstall('resticbackup-backup.service',
                          'resticbackup-backup.timer',
                          'resticbackup-check.service',
                          'resticbackup-check.timer',
                          'resticbackup-forget.service',
                          'resticbackup-forget.timer',)


def check_setup():
    # Test if restic is installed, check backup
    # repository, and remove any stale locks
    try:
        p = subprocess.run(["restic", "unlock"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE)
        
    except FileNotFoundError:
        print("Error : Restic not found. Install it first.")
        sys.exit(1)

    # Others errors
    if p.returncode != 0:
        print(p.stderr.decode())
        sys.exit(1)

    # TODO Test if signal-cli jsonRpc API daemon is up


def notify(url: str,
           receiver: str,
           msg: str) -> int:
    """Execution report via Signal messenger API.

    Returns the response HTTP status code.

    Example :
    notify("http://localhost:8008/api/v1/rpc",
           "+33612345678",
           "Restic script execution complete")
    """

    payload = {
        'jsonrpc': '2.0',
        'method': 'send',
        'params': {
            'recipient': [receiver],
            'message': f"Resticbak notifier\n{msg}"
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

        if response.status_code == 200:
            print("Notification sent")
            # print('Response:', response.json())
        else:
            print(f"Failed to send notification (code {response.status_code})")
            print('Response:', response.text)
            
    except requests.ConnectionError:
        print("Connection error, check if Signal daemon is running.")


"""
Program entry point
"""
if __name__ == "__main__":
    print("Restic backup wrapper script")

    check_setup()

    if len(sys.argv) == 1:
        print("Usage : resticback up.py <argument>\n" \
            "Arguments :\n" \
            "\tbackup : run a Restic backup\n" \
            "\tcheck : full check the Restic backup repository\n" \
            "\tforget : remove (Restic forget + prune) older snapshots applying the user settings (settings.py) policy\n" \
            "\tinstall : install Systemd units (service and timer)\n" \
            "\tuninstall : remove Systemd units")
        sys.exit(0)

    elif len(sys.argv) > 2:
        print("This scripts takes only one argument")
        sys.exit(1)

    arg = sys.argv[1]

    match arg:
        case "backup": backup()  
        case "check": check()
        case "forget": forget()
        case "install": install()
        case "uninstall": uninstall()
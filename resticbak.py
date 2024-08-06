#!/usr/bin/env python

# Restic backups script by Antoine Marzin
#
# This script automates restic local backups.
# Linux OS only. Auto installation (service) designed for systemd (init must be done manually).

from configparser import ConfigParser
import os
import settings
import subprocess
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
    subp_args.append("--no-cache")
    subp_args.append("--json")
    subp_args.append("--tag")
    subp_args.append(settings.SNAPSHOT_TAG)
    # subp_args.append("--dry-run")

    # Run Restic command
    # ex : restic backup /path/to/data --exclude-file=/path/to/repo/.resticignore --json --tag "Run by resticbackup.py script"
    p = subprocess.run(subp_args)

    print(p)

    if p.returncode != 0:
        sys.exit(1)


def check():
    '''
    Perform a structural consistency and integrity verifications of the repository,
    and an integrity check for the given % from user settings of the backed up data
    (restic repository pack files), randomly chosen by restic.
    If data == "100%", it will read the whole, which can be extremely long.
    
    NB : Restic also support file size (in K/M/G/T), so for example it can be data="1G"
    to check 1 Gigabyte randomly picked from the backup data.
    '''
    # restic check --read-data-subset=x% --json
    p = subprocess.run(["restic",
                        "check",
                        f"--read-data-subset={settings.CHECK_SUBSET}",
                        "--json"])

    if p.returncode != 0:
        sys.exit(1)


def forget():
    # restic forget --prune --keep-last 5 --keep-daily 5 --keep-weekly 5 --keep-monthly 5 --keep-yearly 5
    p = subprocess.run(["restic",
                        "forget",
                        "--keep-last", str(settings.KEEP_LAST),
                        "--keep-daily", str(settings.KEEP_DAILY),
                        "--keep-weekly", str(settings.KEEP_WEEKLY),
                        "--keep-monthly", str(settings.KEEP_MONTHLY),
                        "--keep-yearly", str(settings.KEEP_YEARLY),
                        # "--dry-run",
                        "--prune"])
    
    print(p)

    if p.returncode != 0:
        sys.exit(1)


def install_proc(process):
    '''
    Auto configure and install Systemd units (service and timer)
    for the given process (backup, check, or forget)
    '''
    working_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    python_path = sys.executable
    
    # Auto configure service unit file (resticbackup.service)
    execstart = f'{python_path} {os.path.abspath(sys.argv[0])} {process}'
    service_file_path = f'{working_dir}/systemd-units/resticbackup.service'

    service_config = ConfigParser()
    service_config.optionxform = str # preserve case
    service_config.read(service_file_path)
    service_config.set('Service', 'ExecStart', execstart)

    with open(service_file_path, 'w') as file:
        service_config.write(file,
                             space_around_delimiters=False)

    # Auto configure timer unit file (resticbackup.timer)
    timer_file_path = f'{working_dir}/systemd-units/resticbackup.timer'
    timer_config = ConfigParser()
    timer_config.optionxform = str
    timer_config.read(timer_file_path)

    match process:
        case "backup":
            oncalendar_setting = settings.CALENDAR_BACKUP
        case "check":
            oncalendar_setting = settings.CALENDAR_CHECK
        case "forget":
            oncalendar_setting = settings.CALENDAR_FORGET

    timer_config.set('Timer', 'OnCalendar', oncalendar_setting)

    with open(timer_file_path, 'w') as file:
        timer_config.write(file,
                           space_around_delimiters=False)

    # Copy units to /etc/systemd/system/ and run timer
    p = subprocess.run(['sudo', 'cp',
                        f'{working_dir}/systemd-units/resticbackup.service',
                        f'/etc/systemd/system/resticbackup-{process}.service'])
    p = subprocess.run(['sudo', 'cp',
                        f'{working_dir}/systemd-units/resticbackup.timer',
                        f'/etc/systemd/system/resticbackup-{process}.timer'])
    p = subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
    p = subprocess.run(['sudo', 'systemctl', 'enable', f'resticbackup-{process}.timer'])
    p = subprocess.run(['sudo', 'systemctl', 'start', f'resticbackup-{process}.timer'])

def install():
    '''
    Install Systemd services and timers for each restic process
    '''
    print("Install Systemd services and timers")
    install_proc("backup")
    install_proc("check")
    install_proc("forget")
    
def uninstall_proc(process):
    '''
    Remove Systemd units (service and timer) for the current script
    '''
    working_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    p = subprocess.run(['sudo', 'systemctl', 'stop', f'resticbackup-{process}.timer'])
    p = subprocess.run(['sudo', 'systemctl', 'disable', f'resticbackup-{process}.timer'])
    p = subprocess.run(['sudo', 'rm',
                        f'/etc/systemd/system/resticbackup-{process}.service',
                        f'/etc/systemd/system/resticbackup-{process}.timer'])
    
def uninstall():
    '''
    Remove Systemd services and timers for each restic process
    '''
    print("Remove Systemd services and timers")
    uninstall_proc("backup")
    uninstall_proc("check")
    uninstall_proc("forget")

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

    print(p.stderr.decode())

    if p.returncode != 0:
        print(p.stderr.decode())
        sys.exit(1)

    # TODO check config : URLs in settings exist ?



print("Restic Backup script by Antoine Marzin")

check_setup()

if len(sys.argv) == 1:
    print("Usage : resticbackup.py <argument>\n" \
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
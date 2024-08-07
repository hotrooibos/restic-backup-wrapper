# restic-backup-wrapper
This is a wrapper script written in Python for [Restic backup app](https://github.com/restic/restic/).
As of now, it only support local backups.

## Prerequisites :
- Linux OS (tested on Fedora 40 and WSL2)
- Restic v0.16+
- (for service auto install) Systemd

## Setup
- Clone this repo anywhere `git clone https://github.com/hotrooibos/restic-backup-wrapper.git`
- Edit `settings.py` file to suit your needs

## Run manually
- Data backup / create a snapshot : `python3 ./resticbak.py backup`
- Check backup repository and datas : `resticbak.py check`
- Forget old snapshots + and prune (destroy) datas according to your settings : `resticbak.py forget`

## Systemd jobs
This script allows you to easily install systemd units (service + timer) for each above actions to run automatically, as a job.
It uses unit files templates from the systemd-units directory and dynamically edit some of its parameters to suit your system configuration and your settings.

- Install systemd jobs according to settings : `resticbak.py install `
- Uninstall : `resticbak.py uninstall `
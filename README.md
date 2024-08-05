# restic-backup-wrapper
Wrapper script for [Restic backup app](https://github.com/restic/restic/)

## Setup
- Clone this repo anywhere `git clone https://github.com/hotrooibos/restic-backup-wrapper.git`
- Edit settings.py to your needs

## Run manually
- backup : `python3 ./resticbackups.py backup`
- check : `python3 ./resticbackups.py check`
- forget : `python3 ./resticbackups.py forget`

## Systemd jobs
- Run automatically as systemd jobs according to settings : `python3 ./resticbackups.py install `
- Uninstall systemd jobs : `python3 ./resticbackups.py uninstall `
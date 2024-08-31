# User settings file for Restic backup script

# Repository settings
RESTIC_REPOSITORY = "/media/usbdrive/"
REPO_PASSWORD = "password"

# Backup settings
DATA_TO_BAK = ["/media/usbdrive/work/",
               "/media/usbdrive/personal/",
               "/media/usbdrive/catmemes/",]
DATA_TO_IGNORE = ["/media/usbdrive/confidential/",
                  "/media/usbdrive/catmemes/cats_with_sombreros/",]
SNAPSHOT_TAG = "Run by resticbackup.py script"

# Check settings
CHECK_SUBSET = "10%" # Subset of random data to read/check, in % or M/G/T

# Forget settings / backup snapshots an datas retention
KEEP_LAST = 5 # Will keep the 5 last snaphots
KEEP_DAILY = 5 # Will keep the last snapshot from the 5 last days
KEEP_WEEKLY = 5 # " 5 last weeks
KEEP_MONTHLY = 5 # "
KEEP_YEARLY = 5 # "

# Systemd timer settings for executions periodicity
# Informations about timer OnCalendar syntax : https://silentlad.com/systemd-timers-oncalendar-(cron)-format-explained
CALENDAR_BACKUP = "daily"           # Every day except sunday, at midnight
CALENDAR_CHECK = "*-*-* 04:00:00"   # Every day at 4:00am
CALENDAR_FORGET = "monthly"         # Every month (the first of each month)

# Notify settings
NOTIFY = False
SIGNAL_API_URL = "http://localhost:8008/api/v1/rpc"
SIGNAL_RECEIVER = "+33612345678"
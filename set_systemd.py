from configparser import ConfigParser
import os
import subprocess
import sys

def set_systemd(process_name,
                execstart,
                calendar):
    """
    Auto configure and install Systemd units (service and timer)
    for the given process (backup, check, or forget)
    """
    
    working_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Auto configure service unit file (resticbackup.service)
    service_template_path = f'{working_dir}/systemd-units/resticbackup.service'

    service_config = ConfigParser()
    service_config.optionxform = str # preserve case
    service_config.read(service_template_path)
    service_config.set('Service', 'ExecStart', execstart)

    with open(service_template_path, 'w') as file:
        service_config.write(file,
                             space_around_delimiters=False)

    # Auto configure timer unit file (resticbackup.timer)
    timer_template_path = f'{working_dir}/systemd-units/resticbackup.timer'

    timer_config = ConfigParser()
    timer_config.optionxform = str
    timer_config.read(timer_template_path)
    timer_config.set('Timer', 'OnCalendar', calendar)

    with open(timer_template_path, 'w') as file:
        timer_config.write(file,
                           space_around_delimiters=False)

    # Copy units to /etc/systemd/system/ and run timer
    subprocess.run(['sudo', 'cp',
                    f'{working_dir}/systemd-units/resticbackup.service',
                    f'/etc/systemd/system/resticbackup-{process_name}.service'])
    
    subprocess.run(['sudo', 'cp',
                    f'{working_dir}/systemd-units/resticbackup.timer',
                    f'/etc/systemd/system/resticbackup-{process_name}.timer'])
    
    subprocess.run(['sudo', 'systemctl',
                    'daemon-reload'])
    
    subprocess.run(['sudo','systemctl',
                    'enable', f'resticbackup-{process_name}.timer'])
    
    subprocess.run(['sudo', 'systemctl',
                    'start', f'resticbackup-{process_name}.timer'])
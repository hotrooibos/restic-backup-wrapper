from configparser import ConfigParser
import os
import subprocess
import sys

def service(unit_filename: str,
            description: str,
            after: str,
            type: str,
            execstart: str,
            restart: str,
            restartsec: str,
            startnow: bool = False):
    """
    Auto configure and install Systemd units (service and timer)
    for the given process (backup, check, or forget)
    """
    
    working_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Auto configure service unit file (resticbackup.service)
    template_path = f'{working_dir}/systemd-units/template.service'

    service_config = ConfigParser()
    service_config.optionxform = str # preserve case
    service_config.read(template_path)

    # Fill settings
    service_config.set('Unit', 'Description', description)
    service_config.set('Unit', 'After', after)
    service_config.set('Service', 'Type', type)
    service_config.set('Service', 'ExecStart', execstart)
    service_config.set('Service', 'Restart', restart)
    service_config.set('Service', 'RestartSec', restartsec)

    # Write changes to template file
    with open(template_path, 'w') as file:
        service_config.write(file,
                             space_around_delimiters=False)

    # Copy units to /etc/systemd/system/ and run timer
    subprocess.run(['sudo', 'cp',
                    f'{working_dir}/systemd-units/template.service',
                    f'/etc/systemd/system/{unit_filename}.service'])

    subprocess.run(['sudo', 'systemctl',
                    'daemon-reload'])
    
    subprocess.run(['sudo','systemctl',
                    'enable', f'{unit_filename}.service'])

    if startnow == True:
        subprocess.run(['sudo', 'systemctl',
                        'start', f'{unit_filename}.timer'])


def timer(unit_filename: str,
          description: str,
          oncalendar: str):
    """
    Auto configure and install Systemd timer unit
    for the given process (backup, check, or forget)
    """
    
    working_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Get timer template file and change its settings
    timer_template_path = f'{working_dir}/systemd-units/template.timer'

    timer_config = ConfigParser()
    timer_config.optionxform = str # preserve case
    timer_config.read(timer_template_path)

    # Fill settings
    timer_config.set('Unit', 'Description', description)
    timer_config.set('Timer', 'OnCalendar', oncalendar)

    # Write changes to file
    with open(timer_template_path, 'w') as file:
        timer_config.write(file,
                        space_around_delimiters=False)

    # Copy file in the systemd file structure and run it
    subprocess.run(['sudo', 'cp',
                    f'{working_dir}/systemd-units/template.timer',
                    f'/etc/systemd/system/{unit_filename}.timer'])

    subprocess.run(['sudo', 'systemctl',
                    'daemon-reload'])
    
    subprocess.run(['sudo','systemctl',
                    'enable', f'{unit_filename}.timer'])

    subprocess.run(['sudo', 'systemctl',
                    'start', f'{unit_filename}.timer'])
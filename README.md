# pSSID Daemon Provisioning Documentation
> pssid-daemon.py reads the pssid-config.json file, generates schedules based on cron expressions in the batch, and runs batches with pscheduler from perfSONAR. The daemon can be run manually or daemonized
## Contents
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#File Structure">File Structure</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Materials Needed">Materials Needed</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Initial Setup">Initial Setup</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Ansible Bootstrapping">Ansible Bootstrapping</a><br>

See Also: <a href="https://github.com/UMNET-perfSONAR/pssid-daemon/blob/main/TROUBLESHOOTING.md">Troubleshooting</a>
## File Structure
This shows the comprehensive file structure on a RPi after configuration. 
```shell
/usr/bin/pssid/
├── pssid-daemon.py                   
├── batch_processor_format_template.j2
└── README.md

/etc/pssid/
├── pssid_config.json       

/etc/wpa_supplicant/
├── wpa_supplicant_{ssid_profile}.conf

/usr/lib/exec/pssid/
├── pssid-80211
├── pssid-dhcp
├── libpssid.sh
├── LICENSE
└── README.md
```

## Materials Needed
- Raspberry Pi 4
- 64gb SD Card
- Additional SD Card (optional, for updating eeprom)
- Power Over Ethernet Cable (optional, varies by setup)
## Initial Setup 
> Preparing the pi for ansible bootstrapping, configuring ssh
1. Download Ubuntu 22.04 or 24 LTS (server edition) for the Raspberry Pi 4. This can be acquired through the official [Raspberry Pi Imaging Software](https://www.raspberrypi.com/software/) 
2. Allow the pi to boot and log in with the default credentials `ubuntu ubuntu`
3. To access the pi over ssh, go to `/etc/ssh/sshd_config.d/` and make sure the files in this directory has password authentication enabled
```
PasswordAuth yes
```

4. Create a root password (by typing `passwd` as the root user) and reboot the pi, this time logging in as root (ensures there are no problems with the next steps)
5. Create a new user account, which will be used with ansible bootstrapping, and set a password
```
useradd -m usernamehere
passwd usernamehere
```

6. Disable the ubuntu user by modifying `/etc/passwd` and changing the shell to `/usr/bin/false `
7. Change the hostname to be the IP of the pi (helps with avoiding errors with the daemon later)
```
hostnamectl set-hostname <IP>
```

## Ansible Bootstrapping 
Refer to Refer to <a href="https://github.com/UMNET-perfSONAR/pssid-daemon/blob/main/MANUAL_BOOTSTRAPPING.md">Manual Bootstrapping</a> if you would like to provision the probes by hand
> Setting up the daemon on the probes
1. Create a working directory that will hold the ansible repos and cd into that working directory
2. Clone the daemon repo
```
git clone https://github.com/UMNET-perfSONAR/ansible-playbook-pssid-daemon.git
```
3. Edit the `hosts` files located at `ansible-playbook-pssid-daemon/inventory/hosts` to contain the IPs of your probes
4. Install roles:
```shell
ansible-galaxy install -f -r requirements.yml --ignore-errors
```
5. cd into the root of the `ansible-playbook-pssid-daemon` directory and run the following command to set up the daemon on each of the probes (NOTE: pscheduler will take a VERY long time to install, also sometimes cloning fails for no reason, just run it again)
```
ansible-playbook --ask-vault-pass --ask-pass --ask-become-pass --user usernamehere --become --become-user root --become-method su --inventory inventory/ playbook.yml
```
6. The configuartion file is located on the pi at `/etc/pssid/pssid_config.json` needs to be sourced from the web server after being generated in the web interface. This file is located at `/var/lib/pssid/output/pssid_config.json`


# pSSID Daemon Provisioning Documentation
> pssid-daemon.py reads the pssid-config.json file, generates schedules based on cron expressions in the batch, and runs batches with pscheduler from perfSONAR. The daemon can be run manually or daemonized
## Contents
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#File Structure">File Structure</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Materials Needed">Materials Needed</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Initial Setup">Initial Setup</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Ansible Bootstrapping">Ansible Bootstrapping</a><br>
<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Manual Bootstrapping">Manual Bootstrapping</a><br>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Syslog Configuration">Syslog Configuration</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Network Configuration Tools">Network Configuration Tools</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Install Additional Dependencies">Install Additional Dependencies</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Usage">Usage</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Manual Daemonization">Manual Daemonization</a><br>

<a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Troubleshooting">Troubleshooting</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Layer 2 Errors">Layer 2 Errors</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Editing WPA Config">Editing WPA Config</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Layer 3 Errors">Layer 3 Errors</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Service Not Starting (Restart Limit)">Service Not Starting (Restart Limit)</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#IP Not Found in Host Group">IP Not Found in Host Group</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Testing Outside of Lab">Testing Outside of Lab</a>
- <a href="https://github.com/UMNET-perfSONAR/pssid-daemon#Remote Power Cycling + eeprom Flashing">Remote Power Cycling + eeprom Flashing</a>

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
1. Download Ubuntu 22.04 LTS (server edition) for the Raspberry Pi 4. This can be acquired through the official [Raspberry Pi Imaging Software](https://www.raspberrypi.com/software/) 
2. Allow the pi to boot and log in with the default credentials `ubuntu ubuntu`
3. To access the pi over ssh, go to `/etc/ssh/sshd_config.d/` and make sure the files in this directory has password authentication enabled
```
PasswordAuth yes
```

4. Create a root password (by typing `passwd` as the root user) and reboot the pi, this time logging in as root (ensures there are no problems with the next steps)
5. Remove the ubuntu user
```
deluser --remove-home ubuntu
```

6. Create a new user account, which will be used with ansible bootstrapping, and set a password
```
useradd -m usernamehere
usernamehere passwd
```

7. Change the hostname to be the IP of the pi (helps with avoiding errors with the daemon later)
```
hostnamectl set-hostname <IP>
```

## Ansible Bootstrapping 
Refer to Refer to Manual Bootstrapping if you would like to provision the probes by hand
> Setting up the daemon on the probes
1. Create a working directory that will hold the ansible repos and cd into that working directory
2. Clone the daemon repo
```
git clone https://github.com/UMNET-perfSONAR/ansible-playbook-pssid-daemon.git
```
5. Edit the `hosts` files located at `ansible-playbook-pssid-daemon/inventory/hosts` to contain the IPs of your probes
6. Install roles with `ansible-galaxy install -f -r requirements.yml --ignore-errors`
7. cd into the root of the `ansible-playbook-pssid-daemon` directory and run the following command to set up the daemon on each of the probes (NOTE: pscheduler will take a VERY long time to install, also sometimes cloning fails for no reason, just run it again)
```
ansible-playbook --ask-vault-pass --ask-pass --ask-become-pass --user usernamehere --become --become-user root --become-method su --inventory inventory/ playbook.yml
```

## Manual Bootstrapping
1. Install pscheduler
```shell
curl -s https://raw.githubusercontent.com/perfsonar/project/master/install-perfsonar \
  | sh -s - --auto-updates --tunings testpoint
```
### Syslog Configuration
By default, pssid-daemon.py uses Local0 and write to pssid.log under /var/log.
1. Add `local0.* /var/log/pssid.log` to the end of `/etc/rsyslog.conf`
```shell
echo 'local0.* /var/log/pssid.log' >> /etc/rsyslog.conf
```

2. Restart syslog service
```shell
systemctl restart rsyslog
```

### Network Configuration Tools
1. Clone VT-collab tools. Copy the files inside VT-collab folder to `usr/lib/exec/pssid/`
```shell
git clone https://github.com/UMNET-perfSONAR/VT-collab.git
```

2. Follow the base setup instruction in the repo, or as follows
```shell
apt install jq dhcpcd5
systemctl --now disable dhcpcd.service unattended-upgrades wpa_supplicant
```

3. Ensure both `pssid-80211` and `pssid-dhcp` are executable
```shell
chmod +x pssid-80211
chmod +x pssid-dhcp
```

3. For testing these scripts specifically, refer to the VT-Tools repo
4. Move the wpa_supplicant configuration file to `etc/wpa_supplicant/`. Name the file `wpa_supplicant_{ssid}.conf`, and ensure the ssid is consistent with your Wi-Fi testing environment.

### Install Additional Dependencies
```shell
apt install python3-pip
apt install iw
pip install croniter
```

### Usage
1. Clone this repo and move the daemon and batch processor into `/usr/bin/pssid/`. Move the configuration file (which you will have to modify) into `/etc/pssid/`.
```shell
git clone https://github.com/UMNET-perfSONAR/pssid-daemon.git
```

```shell
mkdir /usr/bin/pssid
mv pssid-daemon.py batch_processor_format_template.j2 /usr/bin/pssid/
mkdir /etc/pssid
mv pssid_config.json /etc/pssid
```

2. The daemon must be run as root, with no arguments, the daemon will assume the hostname of the machine is its IP and the location of the config. These can be specified as follows
```shell
python3 pssid-daemon.py --hostname "198.111.226.184" --config /etc/pssid/pssid_config.json
```

3. Specifying syslog facility
```shell
python3 pssid-daemon.py --facility local1
```

4. Validating the `pssid_config.json` file before running batches
```shell
python3 pssid-daemon.py  --validate
```

5. Enable batch processor debug message
```shell
python3 pssid-daemon.py  --debug
```

6. Checking syslog with live updates
```shell
tail -f /var/log/pssid.log
```

### Manual Daemonization
> Probes running pssid-daemon program may be interrupted by provisioning. Daemonizing the program is thus necessary. 
1. First, create a systemd service file, called pssid-daemon.service.
```shell
cd /etc/systemd/system
vim pssid-daemon.service
```

2. Add the following contents to the file. Make sure hostname is the GUI configuration file, otherwise, please specify using --hostname argument.
```shell
[Unit]
Description=”Pssid-Daemon”

[Service]
Restart=always
WorkingDirectory=/usr/bin/pssid/
ExecStart=/usr/bin/python3 pssid-daemon.py

[Install]
WantedBy=multi-user.target
```

3. Restart daemon service, check status, and enable the service.
```shell
systemctl daemon-reload
systemctl restart pssid-daemon.service
systemctl status pssid-daemon.service
systemctl enable pssid-daemon.service
```

## Troubleshooting
### Layer 2 Errors
1. Start by running `wpa_supplicant` by hand and check for errors. This is what the `pssid-80211` code uses.
```
wpa_supplicant -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant_<SSID>.conf
```
2. If wlan0 is not found, the network namespace is still enabled and needs to be deleted 
3. Start by stopping the daemon
```
systemctl stop pssid-daemon.service
```
4. List out the network namespaces and delete the namespace holding wlan0 (it is likely named pssid_wlan0)
```
ip netns list
ip netns delete pssid_wlan0
```
5. You can alternatively choose to keep the namespace and run commands through it like this `ip netns exec pssid_wlan0 command_here`
6. Rerun the `wpa_supplicant` command, there might be a problem with the config syntax
### Editing WPA Config
1. If it is just the formatting that needs to be changed, that can be done by modifying `ansible-playbook-pssid-daemon/roles/ansible-role-pssid-VT-tools/templates/wpa_supplicant.conf.j2`
2. If actual variable values need to be changed, you need the vault password and can edit the file `ansible-playbook-pssid-daemon/roles/ansible-role-pssid-VT-tools/defaults/wpa_supplicant_profiles.yml` with the following command
```
ansible-vault edit ansible-playbook-pssid-daemon/roles/ansible-role-pssid-VT-tools/defaults/wpa_supplicant_profiles.yml
```
3. Enter insert mode to edit with `i` and write your changes and exit with `esc` followed by `:wq`
### Layer 3 Errors
1. These are usually layer 2 errors that weren't caught because layer 2 has marginally unhelpful error output and false positives
2. Especially if the error has something to do with a time out waiting for a carrier, it is most likely a layer 2 issue
3. If it truly is layer 3, double check to ensure that both `pssid-80211` and `pssid-dhcp` are executable (you can check with `ls -la` and modify with `chmod +x <file>`)
### Service Not Starting (Restart Limit)
1. This is usually because something is preventing the daemon from running correctly, and systemctl restarts it multiple times in quick succession as essentially gets rate limited by its own configuration
2. Run the daemon code by hand to see if there is any error output
```
cd /usr/bin/pssid
python3 pssid-daemon.py
```
3. A common issue is forgetting to set the hostname to be the IP. Since the service file does not include a hostname parameter for replicability (though it is an option) the hostname is assumed to be the IP
### IP Not Found in Host Group
1. This just means that the IP was not assigned any tasks in the configuration file
2. Go to `/etc/pssid/pssid_config.json` and edit it by hand or through the web GUI to add tasks for the probe specifically
### Testing Outside of Lab
1. You will need a router of some sort and a POE switch
2. Power on the router, connect your laptop to the router's wifi, connect the routers LAN to the POE switch, and connect the pi to the POE switch as well
3. The pi should show up on your router's dashboard as a device which will tell you the IP and allow for ssh
4. This is mostly helpful for armed pis that do not have any ports exposed (no hdmi out or keyboard access)
### Remote Power Cycling + eeprom Flashing
1. Testing new features over ssh that have the potential to break ssh access and make the pi unusable if it's remote
2. Setup power cycling timers (the below is a reboot in 5 minutes):
```
shutdown -r +5
```
3. Sometimes pis do not come back up at all, and flashing eeprom can help with this
4. Plug a blank (or unimportant) SD card into your laptop and bring up the Rasberry Pi Imager
5. Choose Raspberry Pi 4 for the device, OS - Utilities, and SD Card boot, then Storage - SD card and flash
6. Power off the target pi and remove its SD card (be sure not to mix up which card is which)
7. Plug in the eeprom SD card and power the pi on
8. It is done flashing when there is a green screen on the monitor output and/or constant flashing output on the pi LEDs
9. Power the pi off, remove the eeprom SD, replace the original SD, and power the pi back on

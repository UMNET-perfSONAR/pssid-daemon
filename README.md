# pssid-daemon
#### pSSID scheduler/test daemon
pssid-daemon.py reads pssid-config.json file, generates schedules based on cron expressions in the batch,
and run batch with batch processor with pscheduler from perfSONAR. 

Tested Environment:
Ubuntu Server 22.04.4 LTS (64-bit)
Raspberry Pi 4 


## File structure
This shows the comprehensive file structure on a RPi after configuration. Follow instructions to complete configuration.
```bash
. 
├── pssid-daemon.py                   
├── batch_processor_format_template.j2
└── README.md

/var/lib/pssid/
├── pssid_config.json       

/etc/wap_supplicant/
├── wpa_supplicant_{ssid_profile}.conf

/usr/lib/exec/pssid
├── pssid-80211
├── pssid-dhcp
├── libpssid.sh
├── LICENSE
└── README.md
```

## Note 
Manually setup the environment as follows. Or, use our ansible scripts will automate this process.
```bash
https://github.com/UMNET-perfSONAR/ansible-playbook-pssid-daemon.git
```


## Install pscheduler
- User may be prompted to the latest installation script.
```bash
curl -s https://raw.githubusercontent.com/perfsonar/project/master/install-perfsonar \
  | sh -s - --auto-updates --tunings testpoint
```


## Setup syslog configuration
User can define a customizable log facility, see Usage. By default, pssid-daemon.py uses Local0 and write to pssid.log under /var/log.

- Open the rsyslog.conf file.
```bash
vi /etc/rsyslog.conf
```

- Add the following line at the end:
```bash
local0.* /var/log/pssid.log
```

- Restart syslog service
```bash
systemctl restart rsyslog
```


## Tools for network configuration (Layer 2 & Layer 3 tools)
- Clone VT-collab tools. Copy the files inside VT-collab folder to  </usr/lib/exec/pssid/>
```bash
git clone --branch waldrep https://github.com/UMNET-perfSONAR/VT-collab.git
```

- Then, follow setup instructions in the repo, or as follows.
```bash
systemctl --now disable \
  wpa_supplicant \
  unattended-upgrades
```

- Next,
```bash
apt install jq dhcpcd5
```

- Next,
```bash
systemctl --now disable dhcpcd.service
```

- Put wpa_supplicant configuration file to </etc/wpa_supplicant/>. Name the file as wpa_supplicant_{ssid}.conf.
Make sure the ssid is consistent with your Wi-Fi testing evironment. 


## Install dependencies on Raspberry Pi
```bash
apt install python3-pip
apt install iw
pip install croniter
```


## Usage
- Clone this repo.
```bash
git clone https://github.com/UMNET-perfSONAR/pssid-daemon.git
```

- Get root access.  
```bash
su
```

- How to run pssid-daemon.py with pssid_config.json file in this repo. Run in root. 
```bash
python3 pssid_daemon_dev.py --hostname "198.111.226.184" --config ./pssid_config.json
```

#### Other examples
- Default mode, assuming hostname is in pssid_config.json file at the default location. Syslog is configured using LOCAL0.
```bash
python3 pssid_daemon_dev.py
```

- How to specify syslog facility.
```bash
python3 pssid_daemon_dev.py --hostname "198.111.226.184" --facility local1
```

- How to specify the path of pssid_config.json file.
```bash
python3 pssid_daemon_dev.py --hostname "198.111.226.184" --config ./pssid_config.json
```

- How to validate the pssid_config.json file before run any batch.
```bash
python3 pssid_daemon_dev.py --hostname "198.111.226.184" --config ./pssid_config.json --validate
```

- How to enable batch processor debug message.
```bash
python3 pssid_daemon_dev.py --hostname "198.111.226.184" --config ./pssid_config.json --debug
```

- How to check syslog information.
```bash
tail -f /var/log/pssid.log
```


## How to deamonlize
- Probes running pssid-daemon program may be interrupted by provisioning. Daemonizing the program is thus necessary.
First, create a systemd service file, called pssid-daemon.service.
```bash
cd /etc/systemd/system
vi pssid-daemon.service
```

- Add the following contents to the file. Make sure hostname is the GUI configuration file, otherwise, please specify using hostname argument.
```bash
[Unit]
Description=”Pssid-Daemon”

[Service]
Restart=always
WorkingDirectory=/home/dianluhe/pssid-daemon
ExecStart=/usr/bin/python3 pssid-daemon.py --hostname "198.111.226.184"

[Install]
WantedBy=multi-user.target
```

Then, restart daemon service, check status, and enable the service.
```bash
systemctl daemon-reload
systemctl restart pssid-daemon.service
systemctl status pssid-daemon.service
systemctl enable pssid-daemon.service
```


# Screenshots
![alt text](/example/pssid-daemon.png)
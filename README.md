# pssid-daemon
#### pSSID scheduler/test daemon
pssid-daemon.py reads pssid-config.json file, generates schedules based on cron expressions in the batch,
and run batch with batch processor with pscheduler from perfSONAR.


## File structure
```bash
.
├── pssid-daemon.py                   
├── batch_processor_format_template.j2
└── README.md
```


## Setup syslog configuration
User need to define the customizable log facility. By default, pssid-daemon.py will syslog to /var/log/pssid.log using facility Local0. The setup is as follows.

- Open the rsyslog.conf file.
```bash
vi /etc/rsyslog.conf
```

- Add the following line at the end:
```bash
local0.*    /var/log/pssid.log
```

- Restart syslog service
```bash
systemctl restart rsyslog
```


## Setup Layer 2 & Layer 3 tools
#### Important 
The following steps are for manual setup. Our ansible script will automate this process.
<link to ansible repo>

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


## Usage/Examples
Clone this branch
```bash
git clone --branch lu-implement-passid-daemon https://github.com/UMNET-perfSONAR/pssid-daemon.git
```


By default, pssid-daemon.py and pssid_config.json are in the same folder.
Run this program in root.

"198.111.226.184" is the only host defined in the pssid_config.json, run specifically with the hsot name.

Modify pssid_config.json, update "ssid_profiles" according to your test environment.

```javascript
python3 pssid-daemon.py --hostname "198.111.226.184"
```

--config flag can specify the path for the config file
```javascript
python3 pssid-daemon.py --config "./pssid_config.json" --hostname "198.111.226.184"
```

## Debug
If namespace pssid was created previously, remember to delete the namespace and reboot to resolve related errors.




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

Then, restart daemon service, check status, and complete daemonization
```bash
systemctl daemon-reload
systemctl restart pssid-daemon.service
systemctl status pssid-daemon.service
systemctl enable pssid-daemon.service
```
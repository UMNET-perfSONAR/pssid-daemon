# pssid-daemon
pSSID scheduler/test daemon
1. pssid-daemon.py reads pssid-config.json file and generates schedules based on cron expressions. 
2. Information will be directed to syslog.


# setup syslog configuration
After configuration, pssid-daemon.py will syslog to pssid.log.
1. Open the rsyslog.conf file.
```bash
  vi /etc/rsyslog.conf
```
2. Add the following line at the end:
```bash
local0.*    /var/log/pssid.log
```
3. Restart syslog service
```bash
systemctl restart rsyslog
```


# Setup Layer 2 & Layer 3 tools
Customize the following two functions in pssid-daemon.py
```bash
build_netns_and_layers(interface='wlan0', wpa_file='/etc/wpa_supplicant/wpa_M.conf')
teardown_netns_and_layers(interface='wlan0', wpa_file='/etc/wpa_supplicant/wpa_M.conf')
```

1. Clone this repo to the following path:  /usr/lib/exec/pssid/
```bash
git clone https://github.com/UMNET-perfSONAR/VT-collab.git
```
2. Follow VT-collab repo's setup procedure

2. Setup the wpa_supplicant config file to this path: /etc/wpa_supplicant/


# Install dependencies
```bash
  apt install python3-pip
  apt install iw
  pip install croniter
```


# Usage/Examples
By default, pssid-daemon.py and pssid_config.json are in the same folder.
```javascript
python3 pssid-daemon.py --hostname "198.111.226.184"
```

--config flag can specify the path for the config file
```javascript
python3 pssid-daemon.py --config "./pssid_config.json" --hostname "198.111.226.184"
```
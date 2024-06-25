# first activate the virtual environment
# python3 pssid_daemon_dev.py --hostname "198.111.226.184"

# in the target node
# -- apt install pip3
# -- pip install croniter 


import json
import socket
import re
import queue
import time
import subprocess
import syslog
import sys
import argparse
import datetime
import sched
import time
from croniter import croniter

# currently not object oriented
# class Daemon:
#     def __init__(self):
#         pass

# load the json file
def load_json(filename):
    try:
        with open(filename, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        syslog.syslog(syslog.LOG_ERR, f"Error loading JSON from {filename}: {e}")
        sys.exit(1)      



# get device information 
def get_hostname():
    print("get hostname func called")
    try:
        hostname = socket.gethostname()
        return hostname
    except socket.error as e:
        syslog.syslog(syslog.LOG_ERR, f"Failed to obtain hostname: {e}")
        # terminate if log-err
        sys.exit(1)



# find matching regex
def find_matching_regex(regexes, hostname):
    for regex in regexes:
        try:
            if re.match(regex, hostname) is not None:
                return True
        except re.error as e:
            syslog.syslog(syslog.LOG_WARNING, f"Regex '{regex}' matching error: {e}")
    return False



def run_batch(s, batch, data, cron_expression):
    print('\n')
    batch_name = batch["name"]
    print(f"Running batch at {datetime.datetime.now()} of batch {batch['name']} with cron_expression {cron_expression}")   # syslog at info level
    syslog.syslog(syslog.LOG_INFO, f"Running batch at {datetime.datetime.now()} of name of {batch_name} with cron_expression {cron_expression}")
    # perform test
    execute_batch(batch)
    schedule_batch(s, batch, data)
    

def schedule_batch(s, batch, data):
    earliest_next_run_time = None
    batch_name = batch["name"]
    for schedule_name in batch["schedules"]:
        cron_expression = None

        # find the cron expression for the schedule
        for schedule in data['schedules']:
            if schedule['name'] == schedule_name:
                cron_expression = schedule['repeat']
                break

        if not cron_expression:
            syslog.syslog(syslog.LOG_WARNING, f"No cron expression found for schedule: {schedule_name}")
            continue
        
        # print('cron-expression: ', cron_expression) # for debugging   # comment out 

        # cacluate the next run time
        current_time = datetime.datetime.now()

        cron = croniter(cron_expression, current_time)
        next_run_time = cron.get_next(datetime.datetime)
        # print("NEXT_run_time:          ", next_run_time) # for debugging  # comment out 

        # determine the earliest next run time for the batch
        if earliest_next_run_time is None or next_run_time < earliest_next_run_time:
            earliest_next_run_time = next_run_time
            earliest_cron_expression = schedule['repeat']

    # add the batch to the priority queue with the earliest next run time
    if earliest_next_run_time is None:
        syslog.syslog(syslog.LOG_WARNING, f"Cannot schedule a batch, batch does not have a schedule.")
    else:
        #print('earliest_next_run_time: ', earliest_next_run_time) 
        syslog.syslog(syslog.LOG_INFO, f"Schedule batch '{batch_name}', earlist next run time: {earliest_next_run_time}, cron expression: {earliest_cron_expression}")
        # print('\n') # for debugging
        s.enterabs(earliest_next_run_time.timestamp(), batch["priority"], run_batch, (s, batch, data, earliest_cron_expression))
       
    
    
# add batches
def initilize_batches(batch_name_list, data, s):
    for batch_name in batch_name_list:
        # find the batch by name
        batch = next((b for b in data['batches'] if b['name'] == batch_name), None)
        if batch is None:
            syslog.syslog(syslog.LOG_WARNING, f"Batch '{batch_name}' not found.")
            continue
        
        schedule_batch(s, batch, data)
            


# add metadata
def add_metadata(metadata_list, metadata_set, origin):
    existing_lhs = {item[0] for item in metadata_set}
    for lhs, rhs in metadata_list:
        if lhs not in existing_lhs:
            metadata_set.add((lhs, rhs, origin))
            existing_lhs.add(lhs) # update the lhs


# def get_test_interface(metadata_set):  # deleted query as a parameter !
#     target_wireless_interface = None
#     for entry in metadata_set:
#         if entry[0] == 'interface':
#             target_wireless_interface = entry[1]
#     return target_wireless_interface



def process_gui_conf(data, s, metadata_set, hostname):
    host_match = None
    for host in data["hosts"]:
        if host["name"] == hostname:
            host_match = host["name"]
            initilize_batches(host["batches"], data, s)
            add_metadata(host["data"].items(), metadata_set, host["name"])

            syslog.syslog(syslog.LOG_INFO, f"Host {hostname} identified in hosts")


    # syslog warning if no match
    if host_match == None: 
        syslog.syslog(syslog.LOG_ERR, f"No host with name '{hostname}' found.")
        sys.exit(1)       
    
    # check host groups for further matches
    for group in data["host_groups"]:
        group_name = group["name"]
        if host in group["hosts"] or find_matching_regex(group["hosts_regex"], host_match):
            initilize_batches(group["batches"], data, s)
            add_metadata(group["data"].items(), metadata_set, group["name"])

            syslog.syslog(syslog.LOG_INFO, f"Host {hostname} identified in {group_name} group")

    return s, metadata_set



def print_metadat_set(metadata_set):
    print("**************************************")
    print('metadata')
    print("**************************************")
    for item in metadata_set:
        print(item)
    print("**************************************")



# def execute_test(test_name):
#     print(f"Executing test: {test_name}")
#     # Split the test name to get the command and arguments
#     test_args = test_name.split()
#     pscheduler_command = ["pscheduler"] + test_args
    
#     try:
#         # Run the pscheduler command and capture the output
#         result = subprocess.run(pscheduler_command, capture_output=True, text=True)
#         # print should go to syslog
#         if result.returncode == 0:
#             print(f"Test {test_name} succeeded:\n{result.stdout}")
#             return True
#         else:
#             print(f"Test {test_name} failed:\n{result.stderr}")
#             return False
#     except Exception as e:
#         print(f"Error executing test {test_name}: {e}")
#         return False
    
#/etc/wpa_supplicant/wpa_M.conf
def build_netns_and_layers(interface='wlan0', wpa_file='/etc/wpa_supplicant/wpa_M.conf'):     # take wpa_supplicant config file       interface default value :  wlan0, 
    # create namespace pssid 
    create_namespace_command = f"ip netns add pssid"
    subprocess.run(create_namespace_command, shell=True, check=True)
    print('>>>>>>>>>>>> create namespace pssid\n')

    # bond interface with namespace pssid 
    print('>>>>>>>>>>>> bond interface to namespace\n')
    bond_interface_namespace_command = f"iw phy0 set netns name pssid"
    subprocess.run(bond_interface_namespace_command, shell=True, check=True)
    syslog.syslog(syslog.LOG_INFO, f"created namespace pssid and bond with interface {interface}")

    # call layer 2 tool 
    print('>>>>>>>>>>>> build layer 2')
    build_layer2_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c {wpa_file} -i {interface}"
    layer2_process = subprocess.run(build_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
    syslog.syslog(syslog.LOG_INFO, f"pssid-80211: {layer2_process.stdout.strip()}")

    # call layer 3 tool 
    print('\n>>>>>>>>>>>> build layer 3')
    build_layer3_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i {interface}"
    layer3_process = subprocess.run(build_layer3_tool_command, shell=True, check=True, capture_output=True, text=True)
    syslog.syslog(syslog.LOG_INFO, f"pssid-dhcp: {layer3_process.stdout.strip()}")



def teardown_netns_and_layers(interface='wlan0', wpa_file='/etc/wpa_supplicant/wpa_M.conf'):
    # teardown l3
    print('\n>>>>>>>>>>>> teardown layer 3')
    teardown_layer3_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i {interface} -d"
    layer3_process = subprocess.run(teardown_layer3_tool_command, shell=True, check=True, capture_output=True, text=True)
    syslog.syslog(syslog.LOG_INFO, f"pssid-dhcp: {layer3_process.stdout.strip()}")
    
    # teardown l2
    print('\n>>>>>>>>>>>> teardown layer 2')
    teardown_layer2_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c {wpa_file} -i {interface} -d"
    layer2_process = subprocess.run(teardown_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
    syslog.syslog(syslog.LOG_INFO, f"pssid-80211: {layer2_process.stdout.strip()}")
    
    # delete namespace pssid using command line
    create_namespace_command = f"ip netns delete pssid"
    subprocess.run(create_namespace_command, shell=True, check=True)
    print('\n>>>>>>>>>>>> delete namespace pssid\n')
    


def execute_batch(batch):  # previously called def execute_job(job, ssid_profiles)
    
    for ssid in batch["ssid_profiles"]:
        # build process
        build_netns_and_layers()

        print('\n>>>>>>>>>>>> run wget test')   # syslog at info level
        test_simulation_command = f"wget -P /home/dianluhe www.google.com"
        # subprocess.run(test_simulation_command, shell=True, check=True)      # capture the output --> capture_output=True and syslog it , how??
        wget_process = subprocess.run(test_simulation_command, shell=True, check=True, capture_output=True, text=True)      # capture the output --> capture_output=True and syslog it , how??
        syslog.syslog(syslog.LOG_INFO, f"wget output: {wget_process.stdout.strip()}")

        # teardown process
        teardown_netns_and_layers()

        


# def copy_execute_batches(batch, metadata_set, data):  # previously called def execute_job(job, ssid_profiles)
#     target_wireless_interface = get_test_interface(metadata_set)
#     for ssid in batch["ssid_profiles"]:
#         for job in batch["jobs"]:
#             try:
#                 build_netns_and_layers(target_wireless_interface)
                
#                 # simulation a test
#                 print('\n>>>>>>>>>>>> run wget test')
#                 test_simulation_command = f"wget -P /home/dianluhe www.google.com"
#                 subprocess.run(test_simulation_command, shell=True, check=True)

#                 # for job in data["jobs"]:
#                 #     for test in job["tests"]:
#                 #         if not execute_test(test):
#                 #             if not job.get('continue-if', True):
#                 #                 print("Job stopped due to test failure.")
#                 #                 # to syslog
#                 #                 break

#                 teardown_netns_and_layers(target_wireless_interface)

#             except subprocess.CalledProcessError as e:
#                 print(f"Error executing command for SSID Mwireless: {e}")
#                 # log error to syslog or handle as needed


def main():

    

    # command line parsing for specifications   
    parser = argparse.ArgumentParser(
        description='Pssid daemon commanline arguments: debug mode, hostname, and config file.'
    )
    parser.add_argument('--debug', action='store_true',
        help='Enable debug mode.'
    )
    parser.add_argument('--hostname', type=str,
        help='Specify the hostname.'
    )
    parser.add_argument('--config', type=str,
        help='Specify the path to the config file.'
    )

    # add an argument, called validate-config  



    # evaluate cli arguments
    args = parser.parse_args()

    # if args.debug
    # either implement here, or put the in the class Daemon's constructor  
         
    if args.hostname:
        hostname = args.hostname
    else:
        hostname = get_hostname()
    
    if args.config:
        pssid_config_path = args.config
    else:
        pssid_config_path = "./pssid_config.json"  # replace the default path for pssid config file  --> /var/lib/pssid/pssid_config.json

    # initialization of scheduler and metadata set
    metadata_set = set()
    s = sched.scheduler(time.time, time.sleep)
    # open syslog
    syslog.openlog(ident='pssid', facility=syslog.LOG_LOCAL0)

    pssid_conf_json = load_json(pssid_config_path)

    s, metadata_set = process_gui_conf(pssid_conf_json, s, metadata_set, hostname)

    print_metadat_set(metadata_set)
    print('\n')


    # check if the scheudle is empty, if empty, syslog at error level , program die at this point.
    # if validate-config, exit with 0    die happily.   syslog config at location is validated. 

    # print(s.queue)   lowest priority. 
    s.run()

if __name__ == "__main__":
    main()

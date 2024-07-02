# first activate the virtual environment
# python3 pssid_daemon_dev.py --hostname "198.111.226.184"

# in the target node
# -- apt install pip3
# -- pip install croniter 

# ip netns exec pssid_wlan0 /usr/lib/exec/pssid/pssid-80211 -c '/etc/wpa_supplicant/wpa_supplicant_Mwireless.conf' -i wlan0 -d
# ip netns exec pssid_wlan0 /usr/lib/exec/pssid/pssid-dhcp -i wlan0 -d

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



def run_batch(s, batch, data, cron_expression, scheduled_batches):
    
    print('\n')
    batch_name = batch["name"]
    print(f"Running batch at {datetime.datetime.now()} of batch {batch['name']} with cron_expression {cron_expression}")   # syslog at info level
    syslog.syslog(syslog.LOG_INFO, f"Running batch at {datetime.datetime.now()} of name of {batch_name} with cron_expression {cron_expression}")
    # perform test
    execute_batch(batch)
    schedule_batch(s, batch, data, scheduled_batches)
    

def schedule_batch(s, batch, data, scheduled_batches):

    # print('007007007')
    # for item in scheduled_batches:
    #     print(item)

    earliest_next_run_time = None
    batch_name = batch["name"]

    # if batch_name in scheduled_batches:
    #     print(f"Batch '{batch_name}' scheduled already.")
    #     syslog.syslog(syslog.LOG_WARNING, f"Batch '{batch_name}' already scheduled.")
    #     return
    
    # print("schedule_batch:", batch_name)
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
        syslog.syslog(syslog.LOG_WARNING, f"Cannot schedule a batch name {batch_name}, batch does not have a schedule.")
    else:
        #print('earliest_next_run_time: ', earliest_next_run_time) 
        syslog.syslog(syslog.LOG_INFO, f"Schedule batch '{batch_name}', earlist next run time: {earliest_next_run_time}, cron expression: {earliest_cron_expression}")
        # print('\n') # for debugging
        # s.enterabs(earliest_next_run_time.timestamp(), batch["priority"], run_batch, (s, batch, data, earliest_cron_expression))
        # kwargs = {"batch_name": batch_name}
        s.enterabs(earliest_next_run_time.timestamp(), batch["priority"], run_batch, (s, batch, data, earliest_cron_expression, scheduled_batches))
        scheduled_batches.add(batch_name)

       
def find_phy0():
    pass

def batch_variable_substition(batch, data):
    pass

# def transform_job_list_for_batch_processing(batch, data):

#     # initialize list for transformed data
#     transformed_job_list = []

#     # iterate through each job in the batch
#     for job_name in batch["jobs"]:
#         job = next((j for j in data['jobs'] if j['name'] == job_name), None)
#         if job is None:
#                 syslog.syslog(syslog.LOG_WARNING, f"Job '{job_name}' not found.")
#                 batch["schedules"] = []
#                 continue 
                
#         job_label = job['name']
#         tests = job['tests']

#         # construct transformed JSON based on perfsonar batch processing format
#         transformed_data = {
#             "label": job_label,
#             "iterations": 1,
#             "parallel": True,
#             "backoff": "PT1M",
#             "task": {
#                 "reference": {
#                     "tests": [
#                         {
#                             "type": tests[0]["type"],
#                             "spec": tests[0]["spec"] 
#                         }
#                     ]
#                 },
#                 "#": "This is intentionally empty:",
#                 "test": {}
#             },
#             "task-transform": {
#                 "script": [
#                     "# Replace the test section of the task with one of the",
#                     "# tests in the reference block based on the iteration.",
#                     ".test = .reference.tests[$iteration]"
#                 ]
#             }
#         }

#         # # construct transformed JSON based on perfsonar batch processing format
#         # func beginning of a job
#         # # transformed_data = {
#         # #     "label": job_label,
#         # #     "iterations": 1,
#         # #     "parallel": True,
#         # #     "backoff": "PT1M",
#         # #     "task": {
#         # #         "reference": {
#         # #             "tests": [
        
#         #                 # func for each test in the job
#         #                 {
#         #                     "type": tests[0]["type"],
#         #                     # for each spec 
#         #                     # func for each specification 
#         #                     "": tests[0]["spec"] 
#         #                 }
#         #             ]
#         #         },
#         #         "#": "This is intentionally empty:",
#         #         "test": {}
#         #     },
#         #     "task-transform": {
#         #         "script": [
#         #             "# Replace the test section of the task with one of the",
#         #             "# tests in the reference block based on the iteration.",
#         #             ".test = .reference.tests[$iteration]"
#         #         ]
#         #     }
#         # }

#         # append transformed data to a list
#         transformed_job_list.append(transformed_data)
#     return transformed_job_list


    
# add batches
# 
def initilize_batches(batch_name_list, data, s, scheduled_batches):

    
    

    for batch_name in batch_name_list:
        # check s batch name , if found ,return
        # for event in s.queue:
        #     print(event)
        #     if event[3] == batch_name:
        #         continue

        # if batch_name in s.queue:
        #     syslog.syslog(syslog.LOG_WARNING, f"Batch '{batch_name}' already scheduled.")
        #     continue
        if batch_name in scheduled_batches:
            print(f"Batch '{batch_name}' scheduled already.")
            syslog.syslog(syslog.LOG_WARNING, f"Batch '{batch_name}' already scheduled.")
            return


        # find the batch by name
        batch = next((b for b in data['batches'] if b['name'] == batch_name), None)
        if batch is None:
            syslog.syslog(syslog.LOG_WARNING, f"Batch '{batch_name}' not found.")
            continue
        
        # build batch string for pschduler 
        # check if variable substition needed?  if undefined variable, warn, not add it. ssid substition,
        # check the metadata set to update variable substitution
        # in perf doc , if schema is required 

        # func to do variable substi

        # 
        # transformed_job_list = transform_job_list_for_batch_processing(batch, data)

        # batch.setdefault("transformed_data", []).extend(transformed_job_list)
        

        schedule_batch(s, batch, data, scheduled_batches)
            


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



def process_gui_conf(data, s, metadata_set, hostname, scheduled_batches):
    host_match = None
    for host in data["hosts"]:
        if host["name"] == hostname:
            host_match = host["name"]
            initilize_batches(host["batches"], data, s, scheduled_batches)
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
            initilize_batches(group["batches"], data, s, scheduled_batches)
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

# obsolete
def netns_delete():
    # check if namespace 'pssid' exists
    check_namespace_command = "ip netns list | grep -q pssid"
    namespace_exists = subprocess.run(check_namespace_command, shell=True, capture_output=True).returncode == 0
    if not namespace_exists:
        return
    if namespace_exists:
        # 
        kill_netns_processes_command = "ip netns pids pssid | xargs kill"
        subprocess.run(kill_netns_processes_command, shell=True, check=True)
        syslog.syslog(syslog.LOG_INFO, f"Killed processes in namespace pssid for reinitialization")
        print('>>>>>>>>>>>> Killed processes in namespace pssid for reinitialization\n')
        # if namespace exists, delete it first
        delete_namespace_command = "ip netns delete pssid"
        subprocess.run(delete_namespace_command, shell=True, check=True)
        syslog.syslog(syslog.LOG_INFO, f"Deleted existing namespace pssid")
        print('>>>>>>>>>>>> Deleted existing namespace pssid\n')


def interface_in_namespace(interface):
    try:
        # check if interface is in namespace
        check_interface_command = f"ip netns exec pssid_wlan0 ip link ls"
        interface_in_namespace = subprocess.run(check_interface_command, shell=True, capture_output=True, text=True).stdout.find(interface) != -1
        # print("interface_in_namespace: ", interface_in_namespace)
        if not interface_in_namespace:
            return False
        if interface_in_namespace:
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking interface in namespace: {e}")
        syslog.syslog(syslog.LOG_ERR, f"Error checking {interface} in namespace: {e}")
        return False


def setup_netns(batch):
    interface = batch["test_interface"]
    namespace = f"pssid_{interface}"
    check_namespace_command = f"ip netns list | grep {namespace}"
    # print(check_namespace_command)
    namespace_exists = subprocess.run(check_namespace_command, shell=True, capture_output=True).returncode == 0
    # print("namespace_exists: ", namespace_exists)
    if not namespace_exists:
                 
        try:
            # create namespace
            create_namespace_command = f"ip netns add {namespace}"
            subprocess.run(create_namespace_command, shell=True, check=True)
            syslog.syslog(syslog.LOG_INFO, f"Create namespace {namespace}")
            print(f'>>>>>>>>>>>> create namespace {namespace}\n')

        except subprocess.CalledProcessError as e:
            print(f"Error setting up namespace for interface {interface}: {e}")
            syslog.syslog(syslog.LOG_ERR, f"Error setting up namespace for interface {interface}: {e}")
            return
    
    # check if interface is in namespace
    if not interface_in_namespace(interface):
        try:
            # bond interface with namespace pssid 
            bond_interface_namespace_command = f"iw phy0 set netns name {namespace}"
            subprocess.run(bond_interface_namespace_command, shell=True, check=True)
            print(f'>>>>>>>>>>>> bond {interface} to {namespace}\n')
            syslog.syslog(syslog.LOG_INFO, f"Add interface {interface} to namespace {namespace}")
        except subprocess.CalledProcessError as e:
            print(f"Error bonding interface {interface} with namespace {namespace}")
            syslog.syslog(syslog.LOG_ERR, f"Error bonding interface {interface} with namespace {namespace}")
            return




def process_on_layer_2(batch, ssid_profile):
    interface = batch["test_interface"]
    namespace = f"pssid_{interface}"
    try:
        # call layer 2 tool 
        build_layer2_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_supplicant_{ssid_profile}.conf -i {interface}"
        # print("debug: ",build_layer2_tool_command)
        layer2_process = subprocess.run(build_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
        syslog.syslog(syslog.LOG_INFO, f"pssid-80211: {layer2_process.stdout.strip()}")
        print('>>>>>>>>>>>> build layer 2\n')

    except subprocess.CalledProcessError as e:
        print(f"Error building layer 2")
        syslog.syslog(syslog.LOG_ERR, f"Error building layer 2")
        return
    
    process_on_layer_3(batch)

    try:
        # teardown l2
        teardown_layer2_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_supplicant_{ssid_profile}.conf -i {interface} -d"
        layer2_process = subprocess.run(teardown_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
        syslog.syslog(syslog.LOG_INFO, f"pssid-80211: {layer2_process.stdout.strip()}")
        print('\n>>>>>>>>>>>> tear down layer 2')

    except subprocess.CalledProcessError as e:
        print(f"Error building layer 2")
        syslog.syslog(syslog.LOG_ERR, f"Error tearing down layer 2")
        

def debug_resolv_conf():
    # subprocess ls -l /etc/resolv.conf
    etc_resolv_conf_command = "ls -l /run/systemd/resolve/stub-resolv.conf"
    content = subprocess.run(etc_resolv_conf_command, shell=True, check=False, capture_output=True, text=True)
    cat_etc_resolv_conf_command = "cat /run/systemd/resolve/stub-resolv.conf"
    resolv_conf_content = subprocess.run(cat_etc_resolv_conf_command, shell=True, check=False, capture_output=True, text=True)
    output = content.stdout.strip()
    output2 = resolv_conf_content.stdout.strip()
    # cat /etc/resolv.conf
    print(output)
    print("etc_resolv_conf_conent:")
    print(output2)
    print('------------------------------------------------\n')
    
    
    # subprocess ls -l /etc/netns/pssid_wlan0/resolv.conf
    netns_resolv_conf_command = "ls -l /etc/netns/pssid_wlan0/resolv.conf"
    content = subprocess.run(netns_resolv_conf_command, shell=True, check=False, capture_output=True, text=True)
    cat_netns_resolv_conf_command = "cat /etc/netns/pssid_wlan0/resolv.conf"
    resolv_conf_content = subprocess.run(cat_netns_resolv_conf_command, shell=True, check=False, capture_output=True, text=True)
    output = content.stdout.strip()
    output2 = resolv_conf_content.stdout.strip()
    # cat /etc/netns/pssid_wlan0/resolv.conf
    print(output)
    print("netns_resolv_conf_conent:")
    print(output2)
    print('------------------------------------------------\n')

    
    
    

def process_on_layer_3(batch):
    
    interface = batch["test_interface"]
    namespace = f"pssid_{interface}"
    try:
        # copy original /etc/resolv.conf to a temp location /tmp/resolv.conf
        copy_resolv_conf_command = f"cp /etc/resolv.conf /tmp/"
        subprocess.run(copy_resolv_conf_command, shell=True, check=True)
        print("start layer 3 func")
        print(f"Successfully copied /etc/resolv.conf to /tmp/resolv.conf ")
        
    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_INFO, f"Failed to copy default namespace's /etc/resolv.conf to /tmp/resolv.conf")
        return
    
    print("debug function called before calling layer 3 tool") 
    debug_resolv_conf()
    

    try:
        # call layer 3 tool ###########################
        
        build_layer3_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-dhcp -i {interface}"
        layer3_process = subprocess.run(build_layer3_tool_command, shell=True, check=True, capture_output=True, text=True)
        print('\n>>>>>>>>>>>> build layer 3')
        syslog.syslog(syslog.LOG_INFO, f"pssid-dhcp: {layer3_process.stdout.strip()}")

    except subprocess.CalledProcessError as e:
        print(f"Error building layer 3")
        revert_resolv_conf_command = f"cp /tmp/resolv.conf /etc/"
        subprocess.run(revert_resolv_conf_command, shell=True, check=True)
        syslog.syslog(syslog.LOG_ERR, f"Error building layer 3")
        return
    
    print("debug function called AFTER calling layer 3 tool") 
    debug_resolv_conf()

    try:
        print("marker------------A")
        # make a directory /etc/netns/{namespace}/
        make_directory_command = f"mkdir -p /etc/netns/{namespace}/"
        subprocess.run(make_directory_command, shell=True, check=True)

        # copy layer3 generated /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf
        copy_resolv_conf_command = f"cp /etc/resolv.conf /etc/netns/{namespace}/"
        subprocess.run(copy_resolv_conf_command, shell=True, check=True)
        print(f"Successfully copied /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf ")
    
    except subprocess.CalledProcessError as e:
        print(f"failed to copy /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf")
        syslog.syslog(syslog.LOG_ERR, f"Failed to copy /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf")
        return
    
    print(f"debug function called after copy resolv.conf to /etc/netns/{namespace}/resolv.conf") 

    debug_resolv_conf()

    try:
        # copy original /tmp/resolv.conf to /etc/resolv.conf to solve DNS issue
        copy_resolv_conf_command = f"cp /tmp/resolv.conf /etc/"
        subprocess.run(copy_resolv_conf_command, shell=True, check=True)

    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_ERR, f"Failed to copy /tmp/resolv.conf to /etc/resolv.conf")
        return
    
    print('\n>>>>>>>>>>>> run wget test') 
    test_simulation_command = f"ip netns exec {namespace} wget -P /home/dianluhe www.google.com"
    wget_process = subprocess.run(test_simulation_command, shell=True, check=True, capture_output=True, text=True)    
    syslog.syslog(syslog.LOG_INFO, f"Run wget, return code: {wget_process.returncode}")


    try:
        # teardown l3
       
        teardown_layer3_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-dhcp -i {interface} -d"
        layer3_process = subprocess.run(teardown_layer3_tool_command, shell=True, check=True, capture_output=True, text=True)
        print('\n>>>>>>>>>>>> teardown layer 3')
        syslog.syslog(syslog.LOG_INFO, f"pssid-dhcp: {layer3_process.stdout.strip()}")

    except subprocess.CalledProcessError as e:
        print(f"Error tearing down layer 3")
        syslog.syslog(syslog.LOG_ERR, f"Error tearing down layer 3")
        return
    
    try:
        deltete_resolv_conf_command = f"rm /etc/netns/{namespace}/resolv.conf"
        subprocess.run(deltete_resolv_conf_command, shell=True, check=True)
        print(f"Successfully deleted /etc/netns/{namespace}/resolv.conf ")
    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_ERR, f"Failed to delete /etc/netns/{namespace}/resolv.conf")
        return




#/etc/wpa_supplicant/wpa_M.conf
# pyh0 is hard coded now, need change. a lookup table is needed. 
# local
def build_netns_and_layers(interface='wlan0', wpa_file='/etc/wpa_supplicant/wpa_M.conf'):     # take wpa_supplicant config file       interface default value :  wlan0, 
    # create namespace pssid 
    create_namespace_command = f"ip netns add pssid"
    subprocess.run(create_namespace_command, shell=True, check=True)
    print('>>>>>>>>>>>> create namespace pssid\n')

    # bond interface with namespace pssid 
    print('>>>>>>>>>>>> bond interface to namespace\n')
    bond_interface_namespace_command = f"iw phy0 set netns name pssid"
    subprocess.run(bond_interface_namespace_command, shell=True, check=True)
    syslog.syslog(syslog.LOG_INFO, f"Create namespace pssid and bond with interface {interface}")

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
    


# def execute_batch(batch):  # previously called def execute_job(job, ssid_profiles)
    
#     for ssid in batch["ssid_profiles"]:
        
#         # build process
#         build_netns_and_layers()

#         print('\n>>>>>>>>>>>> run wget test') 
#         test_simulation_command = f"wget -P /home/dianluhe www.google.com"
#         wget_process = subprocess.run(test_simulation_command, shell=True, check=True, capture_output=True, text=True)    
#         syslog.syslog(syslog.LOG_INFO, f"Run wget, return code: {wget_process.returncode}")

#         # teardown process
#         teardown_netns_and_layers()


def execute_batch(batch): 
    
    for ssid in batch["ssid_profiles"]:

        setup_netns(batch)
        
        # build process
        process_on_layer_2(batch, ssid)

    


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
    parser.add_argument('--validateConfig', type=str,
        help='Validate the config file processing.'
    )
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
    scheduled_batches = set()
    # open syslog
    syslog.openlog(ident='pssid', facility=syslog.LOG_LOCAL0)  # default to local0, able to implement in cli .

    pssid_conf_json = load_json(pssid_config_path)
    s, metadata_set = process_gui_conf(pssid_conf_json, s, metadata_set, hostname, scheduled_batches)

    print_metadat_set(metadata_set)
    # print('\n')

    # check if the scheudle is empty
    if s is None:
        syslog.syslog(syslog.LOG_ERR, f"The schedule is empty")
        sys.exit(1)

    # validate the config file processing
    if args.validateConfig:
        sys.exit(0)

    # print(s.queue)   lowest priority. 
    s.run()

if __name__ == "__main__":
    main()

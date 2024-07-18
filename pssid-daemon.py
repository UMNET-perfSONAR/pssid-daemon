# first activate the virtual environment
# python3 pssid_daemon_dev.py --hostname "198.111.226.184"

# in the target node
# -- apt install pip3
# -- pip install croniter 

# ip netns exec pssid_wlan0 /usr/lib/exec/pssid/pssid-80211 -c '/etc/wpa_supplicant/wpa_supplicant_Mwireless.conf' -i wlan0 -d
# ip netns exec pssid_wlan0 /usr/lib/exec/pssid/pssid-dhcp -i wlan0 -d

# ip netns pids pssid_wlan0 | xargs kill
# cat /etc/netns/pssid_wlan0/resolv.conf
# tail -f /var/log/pssid.log

# cat /etc/resolv.conf

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
import os
from croniter import croniter
from jinja2 import Template
import pscheduler.batchprocessor



# load the json file
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        print(f"{e}")
        syslog.syslog(syslog.LOG_ERR, f"{e}")
        sys.exit(1)      



# get device information 
def get_hostname():
    try:
        hostname = socket.gethostname()
        return hostname
    except socket.error as e:
        syslog.syslog(syslog.LOG_ERR, f"Failed to obtain hostname: {e}")
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


# scheduler run function
def run_batch(s, batch, data, cron_expression):
    batch_name = batch["name"]
    print(f"\nRunning batch at {datetime.datetime.now()}, batch name: {batch['name']}, cron_expression: {cron_expression}")   # syslog at info level
    syslog.syslog(syslog.LOG_INFO, f"Running batch at {datetime.datetime.now()} of name of {batch_name} with cron_expression {cron_expression}")
    # execute the batch
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
        
        # cacluate the next run time
        current_time = datetime.datetime.now()
        cron = croniter(cron_expression, current_time)
        next_run_time = cron.get_next(datetime.datetime)

        # determine the earliest next run time for the batch
        if earliest_next_run_time is None or next_run_time < earliest_next_run_time:
            earliest_next_run_time = next_run_time
            earliest_cron_expression = schedule['repeat']

    # add the batch to the priority queue with the earliest next run time
    if earliest_next_run_time is None:
        syslog.syslog(syslog.LOG_WARNING, f"Cannot schedule a batch name {batch_name}, batch does not have a schedule.")
    else:
        syslog.syslog(syslog.LOG_INFO, f"Schedule batch '{batch_name}', earlist next run time: {earliest_next_run_time}, cron expression: {earliest_cron_expression}")
        s.enterabs(earliest_next_run_time.timestamp(), batch["priority"], run_batch, (s, batch, data, earliest_cron_expression))



# apply variable substitution if the key in metadata_set is a substring of the key in object
def variable_substitution(object, metadata_set):
    substituted = True
    # iterate through each key-value pair in a dictionary
    for key, value in object.items():
        if isinstance(value, str) and '$' in value:
            # check if the value is a string and needs substitution
            for lhs, rhs, origin in metadata_set:
                if lhs in key:
                    object[key] = rhs
                    print(f"Variable '{value}' of '{key}' substituted with '{rhs}' from '{lhs}'")
            value = object[key]        
            if '$' in value:
                substituted = False
                print(f"Variable '{value}' in '{key}' not found in metadata.")
            
        elif isinstance(value, list):
            # recursively process lists
            for item in value:
                if isinstance(item, dict):
                    variable_substitution(item, metadata_set)
        elif isinstance(value, dict):
            # recursively process dictionaries
            variable_substitution(value, metadata_set)

    return object, substituted



def transform_job_list_for_batch_processing(batch, data, metadata_set, syslog_facility):
    with open('batch_processor_format_template.j2', 'r') as template_file:
        template_str = template_file.read()

    transformed_job_list = []
    job_tests = []
    valid_Batch = True

    # Perform variable substitution on batch
    batch, substituted = variable_substitution(batch, metadata_set)
    if not substituted:
        valid_Batch = False
        syslog.syslog(syslog.LOG_ERR, f"Batch '{batch['name']}' has unresolved variables.")
        print(f"Batch '{batch['name']}' has unresolved variables.")
        return batch, valid_Batch
    
    interface = batch["test_interface"]

    # Iterate through each job in the batch
    for job_name in batch["jobs"]:
        job = next((j for j in data['jobs'] if j['name'] == job_name), None)
        if job is None:
            valid_Batch = False
            syslog.syslog(syslog.LOG_ERR, f"Job '{job_name}' not found.")
            print(f"Job '{job_name}' not found.")
            return batch, valid_Batch

        job_label = job['name']
        tests_list = job['tests']
        parallel = job['parallel']

        for test_name in tests_list:
            test = next((t for t in data['tests'] if t['name'] == test_name), None)
            if test is None:
                valid_Batch = False
                syslog.syslog(syslog.LOG_ERR, f"Test '{test_name}' not found.")
                print(f"Test '{test_name}' not found.")
                return batch, valid_Batch

            # Perform variable substitution on batch's test 
            test, substituted = variable_substitution(test, metadata_set)
            if not substituted:
                valid_Batch = False
                syslog.syslog(syslog.LOG_ERR, f"Test '{test['name']}' has unresolved variables.")
                print(f"Test '{test['name']}' has unresolved variables.")
                return batch, valid_Batch
  
            job_tests.append(test)
        
        template = Template(template_str)
        iteration = job_tests.__len__()
        transformed_data_str = template.render(job_label=job_label, tests=job_tests, iteration=iteration, parallel=parallel, interface = interface, facility = syslog_facility)
        transformed_data = json.loads(transformed_data_str)
        transformed_job_list.append(transformed_data) 
       
    # iterate through transformed_data in batch to update boolean literals to conform python object type (later formed batch_4_batchProcessor can be directly dump to pscheduler)
    for job in transformed_job_list:
        if "parallel" in job:
            if job["parallel"] == "True":
                job["parallel"] = True
            elif job["parallel"] == "False":
                job["parallel"] = False
   
    batch.setdefault("batch_4_batchProcessor", []).extend(transformed_job_list)

    return batch, valid_Batch


# collect batch names
def initilize_batch_list(batch_name_list, identified_batch_list):
    for batch_name in batch_name_list:
        identified_batch_list.add(batch_name)
 


# add metadata
def add_metadata(metadata_list, metadata_set, origin):
    existing_lhs = {item[0] for item in metadata_set}
    for lhs, rhs in metadata_list:
        if lhs not in existing_lhs:
            metadata_set.add((lhs, rhs, origin))
            existing_lhs.add(lhs) # update the lhs



def process_gui_conf(data, s, metadata_set, hostname, identified_batch_list, syslog_facility):
    host_match = None
    for host in data["hosts"]:
        if host["name"] == hostname:
            host_match = host["name"]
            initilize_batch_list(host["batches"], identified_batch_list)
            add_metadata(host["data"].items(), metadata_set, host["name"])
            syslog.syslog(syslog.LOG_INFO, f"Host {hostname} identified in hosts")

    # syslog warning if no match
    if host_match == None: 
        syslog.syslog(syslog.LOG_ERR, f"No host with name '{hostname}' found.")
        print(f"No host with name '{hostname}' found.")
        sys.exit(1)       
    
    # check host groups for further matches
    for group in data["host_groups"]:
        group_name = group["name"]
        if host in group["hosts"] or find_matching_regex(group["hosts_regex"], host_match):
            initilize_batch_list(group["batches"], identified_batch_list)
            add_metadata(group["data"].items(), metadata_set, group["name"])
            syslog.syslog(syslog.LOG_INFO, f"Host {hostname} identified in {group_name} group")

    # print metadata set
    print_metadat_set(metadata_set)

    # check if the identified batche list is empty
    if not identified_batch_list:
        syslog.syslog(syslog.LOG_ERR, f"No batch found.")
        sys.exit

    # for each batch name in set validate and schedule
    for batch_name in identified_batch_list:
        # find the batch by name
        batch = next((b for b in data['batches'] if b['name'] == batch_name), None)
        if batch is None:
            syslog.syslog(syslog.LOG_WARNING, f"Batch '{batch_name}' not found.")
            continue

        # transform the jobs in batch for batch processing
        batch, valid_Batch = transform_job_list_for_batch_processing(batch, data, metadata_set, syslog_facility)
        if not valid_Batch:
            syslog.syslog(syslog.LOG_ERR, f"Batch '{batch_name}' is invalid.")
            return
        
        schedule_batch(s, batch, data)



def print_metadat_set(metadata_set):
    num_dash = 50
    print("-" * num_dash)
    print('Metadata')
    print("-" * num_dash)
    for item in metadata_set:
        print(item)
    print("-" * num_dash)



# check if interface is in namespace
def interface_in_namespace(interface):
    try:
        # check if interface is in namespace
        check_interface_command = f"ip netns exec pssid_{interface} ip link ls"
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



# fetch interfaces
def fetch_interfaces():
    # Initialize lookup table
    interface_phy_mapping = {}

    print('>> run iw dev')
    iw_dev_command = f"iw dev"
    get_interface_info = subprocess.run(iw_dev_command, shell=True, check=True, capture_output=True, text=True)
    output = get_interface_info.stdout.strip()

    # Regular expression pattern to match each phy# and its associated interface
    pattern = r'^phy#(\d+)\n\s+Interface (\S+)'
    # Find all matches in the output
    matches = re.finditer(pattern, output, re.MULTILINE)

    for match in matches:
        phy_number = match.group(1)
        interface_name = match.group(2)
        interface_phy_mapping[interface_name] = f"phy{phy_number}"
    
    return interface_phy_mapping



# get default interface
def get_default_phy(interface_name, interface_phy_mapping):
    # Assuming interface_phy_mapping is a dictionary mapping interface names to phy identifiers
    return interface_phy_mapping.get(interface_name)



# setup network namespace
def setup_netns(batch, ssid_profile):
    interface = batch["test_interface"]
    namespace = f"pssid_{interface}"
    check_namespace_command = f"ip netns list | grep {namespace}"
    namespace_exists = subprocess.run(check_namespace_command, shell=True, capture_output=True).returncode == 0
    if not namespace_exists:
                 
        try:
            # create namespace
            create_namespace_command = f"ip netns add {namespace}"
            subprocess.run(create_namespace_command, shell=True, check=True)
            syslog.syslog(syslog.LOG_INFO, f"Create namespace {namespace}")
            print(f'>> create namespace {namespace}\n')

        except subprocess.CalledProcessError as e:
            print(f"Error setting up namespace for interface {interface}: {e}")
            syslog.syslog(syslog.LOG_ERR, f"Error setting up namespace for interface {interface}: {e}")
            return
    
    # check if interface is in namespace
    if not interface_in_namespace(interface):
        interface_phy_mapping = fetch_interfaces()
        phy_name = get_default_phy(interface, interface_phy_mapping)

        try:
            # bond interface with namespace pssid 
            bond_interface_namespace_command = f"iw {phy_name} set netns name {namespace}"
            subprocess.run(bond_interface_namespace_command, shell=True, check=True)
            print(f'>> bond {interface} to {namespace}\n')
            syslog.syslog(syslog.LOG_INFO, f"Add interface {interface} to namespace {namespace}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error bonding interface {interface} with namespace {namespace}")
            syslog.syslog(syslog.LOG_ERR, f"Error bonding interface {interface} with namespace {namespace}")
            return
        
    ## clean the namespace
    # check if there are processes in namespace
    netns_process_exists_command = f"ip netns pids {namespace}"
    netns_process_exists = subprocess.run(netns_process_exists_command, shell=True, capture_output=True, text=True)
    
    # kill all processes in namespace
    if netns_process_exists.stdout.strip():        
        ## make sure layer 2 and layer 3 tools are not running
        # force teardown l3
        try:
            teardown_layer3_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-dhcp -i {interface} -d"
            layer3_process = subprocess.run(teardown_layer3_tool_command, shell=True, check=False, capture_output=True, text=True)
            print('\n>> clear netns layer 3')
        except subprocess.CalledProcessError as e:
            print(f"Error init netns due to failure of tearing down layer 3")
            syslog.syslog(syslog.LOG_ERR, f"Error init netns due to failture of tearing down layer 3")
            return
            
        # force teardown l2  # check set to false 
        try:
            teardown_layer2_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_supplicant_{ssid_profile}.conf -i {interface} -d"
            layer2_process = subprocess.run(teardown_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
            print('\n>> clear netns layer 2')
        except subprocess.CalledProcessError as e:
            print(f"Error init netns due to failure of tearing down layer 2")
            syslog.syslog(syslog.LOG_ERR, f"Error init netns due to failure of tearing down layer 2")
            return
    
    # remove existing resolv.conf in namespace
    if os.path.exists(f"/etc/netns/{namespace}/resolv.conf"):
        try:
            rm_existing_resolv_conf_command = f"rm /etc/netns/{namespace}/resolv.conf" # possible remaining resolv.conf after interupted pssid-daemon, the file might be the one copied from /tmp/resolv.conf to /etc/resolv.conf in previous run 
            subprocess.run(rm_existing_resolv_conf_command, shell=True, check=False) # ignore error if file not found
            syslog.syslog(syslog.LOG_INFO, f"Remove existing resolv.conf in namespace {namespace}")
            print(f'\n>> Remove existing resolv.conf in namespace {namespace}')
        except subprocess.CalledProcessError as e:
            print(f"Error removing existing resolv.conf in namespace {namespace}")
            syslog.syslog(syslog.LOG_ERR, f"Error removing existing resolv.conf in namespace {namespace} : {e}")



# process on layer 2
def process_on_layer_2(batch, ssid_profile):
    interface = batch["test_interface"]
    namespace = f"pssid_{interface}"
    
    wpa_supplicant_conf_file = f"/etc/wpa_supplicant/wpa_supplicant_{ssid_profile}.conf"
    if not os.path.exists(wpa_supplicant_conf_file):
        syslog.syslog(syslog.LOG_ERR, f"Error: wpa_supplicant conf file {wpa_supplicant_conf_file} does not exist.")
        print(f"Error: wpa_supplicant conf file {wpa_supplicant_conf_file} does not exist.")
        return
    
    try:
        # call layer 2 tool 
        build_layer2_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_supplicant_{ssid_profile}.conf -i {interface}"
        layer2_process = subprocess.run(build_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
        syslog.syslog(syslog.LOG_INFO, f"pssid-80211: {layer2_process.stdout.strip()}")
        print('\n>> built layer 2')

    except subprocess.CalledProcessError as e:
        print(f"Error in building layer 2")
        syslog.syslog(syslog.LOG_ERR, f"Error in building layer 2")
        return
    
    # call process on layer 3
    process_on_layer_3(batch)

    try:
        # tear down l2
        teardown_layer2_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_supplicant_{ssid_profile}.conf -i {interface} -d"
        layer2_process = subprocess.run(teardown_layer2_tool_command, shell=True, check=True, capture_output=True, text=True)
        syslog.syslog(syslog.LOG_INFO, f"pssid-80211: {layer2_process.stdout.strip()}")
        print('\n>> tore down layer 2')

    except subprocess.CalledProcessError as e:
        print(f"Error tearing down layer 2")
        syslog.syslog(syslog.LOG_ERR, f"Error tearing down layer 2")

    print('\n>> continue ...\n')
        


# debug resolv.conf
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

    

# process on layer 3
def process_on_layer_3(batch):
    interface = batch["test_interface"]
    namespace = f"pssid_{interface}"
    
    try:
        # copy original /etc/resolv.conf to a temp location /tmp/resolv.conf
        copy_resolv_conf_command = f"cp /etc/resolv.conf /tmp/"
        subprocess.run(copy_resolv_conf_command, shell=True, check=True)
        print(f"\n>> copied /etc/resolv.conf to /tmp/resolv.conf ")
    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_INFO, f"Failed to copy default namespace's /etc/resolv.conf to /tmp/resolv.conf")
        return
    
    # debug_resolv_conf() # for debugging
    
    try:
        # call layer 3 tool
        build_layer3_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-dhcp -i {interface}"
        layer3_process = subprocess.run(build_layer3_tool_command, shell=True, check=True, capture_output=True, text=True)
        print('\n>> built layer 3')
        syslog.syslog(syslog.LOG_INFO, f"pssid-dhcp: {layer3_process.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error building layer 3")
        revert_resolv_conf_command = f"cp /tmp/resolv.conf /etc/"
        subprocess.run(revert_resolv_conf_command, shell=True, check=True)
        syslog.syslog(syslog.LOG_ERR, f"Error building layer 3")
        return
    
    # debug_resolv_conf() # for debugging

    try:
        # make a directory /etc/netns/{namespace}/
        make_directory_command = f"mkdir -p /etc/netns/{namespace}/"
        subprocess.run(make_directory_command, shell=True, check=True)

        # copy layer3 generated /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf
        copy_resolv_conf_command = f"cp /etc/resolv.conf /etc/netns/{namespace}/"
        subprocess.run(copy_resolv_conf_command, shell=True, check=True)
        print(f"\n>> copied /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf")
    except subprocess.CalledProcessError as e:
        print(f"failed to copy /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf")
        syslog.syslog(syslog.LOG_ERR, f"Failed to copy /etc/resolv.conf to /etc/netns/{namespace}/resolv.conf")
        return
    
    # debug_resolv_conf() # for debugging

    try:
        # copy original /tmp/resolv.conf to /etc/resolv.conf to solve DNS issue
        copy_resolv_conf_command = f"cp /tmp/resolv.conf /etc/"
        subprocess.run(copy_resolv_conf_command, shell=True, check=True)
        print(f"\n>> copied /tmp/resolv.conf to /etc/resolv.conf")
    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_ERR, f"Failed to copy /tmp/resolv.conf to /etc/resolv.conf")
        return

    # run batch processor
    print('\n>> run batch processor ...')
    run_batch_processor(batch)

    try:
        # teardown l3
        teardown_layer3_tool_command = f"ip netns exec {namespace} /usr/lib/exec/pssid/pssid-dhcp -i {interface} -d"
        layer3_process = subprocess.run(teardown_layer3_tool_command, shell=True, check=True, capture_output=True, text=True)
        print('\n>> tore down layer 3')
        syslog.syslog(syslog.LOG_INFO, f"pssid-dhcp: {layer3_process.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error in tearing down layer 3")
        syslog.syslog(syslog.LOG_ERR, f"Error in tearing down layer 3")
        return
    
    try:
        deltete_resolv_conf_command = f"rm /etc/netns/{namespace}/resolv.conf"
        subprocess.run(deltete_resolv_conf_command, shell=True, check=True)
        print(f"\n>> deleted /etc/netns/{namespace}/resolv.conf ")
    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_ERR, f"Failed to delete /etc/netns/{namespace}/resolv.conf")
        return

  

def execute_batch(batch): 
    for ssid in batch["ssid_profiles"]:
        setup_netns(batch, ssid)
        process_on_layer_2(batch, ssid)



def debug(message):
    """
    Callback function for the batch processor to emit a line of
    debug.
    """
    print(message, file=sys.stderr)



def run_batch_processor(batch):
    # form the batch for batch processor
    batch_4_batchProcessor = {
    "schema": 3,
    "jobs": batch["batch_4_batchProcessor"]
    }

    processor = pscheduler.batchprocessor.BatchProcessor(batch_4_batchProcessor)
    if debug:
        print('')
        result = processor(debug=debug)
    else:
        result = processor()




def main():
    # command line parsing for specifications   
    parser = argparse.ArgumentParser(
        description='Pssid daemon commanline arguments: debug mode, hostname, and config file.'
    )
    parser.add_argument('--debug', action='store_true',
        help='Enable debug mode on cli batch processor process.'
    )
    parser.add_argument('--hostname', type=str,
        help='Specify the hostname.'
    )
    parser.add_argument('--config', type=str,
        help='Specify the path to the config file.'
    )
    parser.add_argument('--facility', type=str,
        help='Specify the syslog facility.'
    )
    parser.add_argument('--validate', action='store_true',
        help='Validate the config file processing.'
    )
    # evaluate cli arguments
    args = parser.parse_args()

    if args.debug:
        debug = True
         
    if args.hostname:
        hostname = args.hostname
    else:
        hostname = get_hostname()
    
    if args.config:
        pssid_config_path = args.config     # "./pssid_config.json"
    else:
        pssid_config_path = "/var/lib/pssid/pssid_config.json"      # default path

    if args.facility:
        syslog_facility = args.facility
    else:
        # batch processor archive log facility
        syslog_facility = "local0"

    # generate the syslog facility constant
    constant_name = "LOG_" + syslog_facility.upper()
    facility_for_openlog = getattr(syslog, constant_name)   

    # initialization of scheduler and metadata set
    metadata_set = set()
    s = sched.scheduler(time.time, time.sleep)
    scheduled_batches = set()

    # open syslog with ident 'pssid' and facility LOG_LOCAL0
    syslog.openlog(ident='pssid', facility=facility_for_openlog) 

    # load and process the json configuration file
    pssid_conf_json = load_json(pssid_config_path)

    process_gui_conf(pssid_conf_json, s, metadata_set, hostname, scheduled_batches, syslog_facility)

    # check if the scheudle is empty
    if s is None:
        syslog.syslog(syslog.LOG_ERR, f"The schedule is empty")
        sys.exit(1)

    # validate the config file processing
    if args.validate:
        print("The config file is validated.")
        syslog.syslog(syslog.LOG_INFO, f"The config file is validated.")
        sys.exit(0)

    s.run()



if __name__ == "__main__":
    main()

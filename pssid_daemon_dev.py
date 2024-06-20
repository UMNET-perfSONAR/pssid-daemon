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

class Daemon:
    def __init__(self):
        pass
        # self.pq = queue.PriorityQueue()

    # def __iter__(self):
    #     # creates a copy of the priority queue items
    #     items = []
    #     while not self.pq.empty():
    #         items.append(self.pq.get())
    #     # Put items back into the priority queue
    #     for item in items:
    #         self.pq.put(item)
    #     return iter(items)

    # def put(self, job, next_run_time, priority, interval):
    #     self.pq.put((priority, next_run_time, job, interval))
    # def put(self, batch):
    #     self.pq.put(batch)

    # def put(self, next_run_time, priority, batch):
    #     self.pq.put((next_run_time, priority, batch))

    # def get(self):
    #     return self.pq.get()

    # def is_empty(self):
    #     return self.pq.empty()

def load_json(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        return json.load(f)
    
# get device information
def get_hostname():
    try:
        hostname = socket.gethostname()
        return hostname
    except:
        print("Failed to obtain hostname")


# find matching regex
def find_matching_regex(regexes, hostname):
    for regex in regexes:
        try:
            #print("regex",regex,"hostname",hostname)
            if re.match(regex, hostname) is not None:
                return True
        except re.error:
            print("Regex matching error.")
    return False

def run_batch(s, batch, data, cron_expression):
    print('\n')
    print(f"Running batch at {datetime.datetime.now()} of batch {batch['name']} with cron_expression {cron_expression}")  #  print( time stamp + batch name)
    schedule_batch(s, batch, data)
    

def schedule_batch(s, batch, data):

    #print("current-time--marker-01: ", datetime.datetime.now())

    earliest_next_run_time = None
    #print("schedule_batch at: ", current_time, "type of:", type(current_time))
    for schedule_name in batch["schedules"]:
        cron_expression = None

        # find the cron expression for the schedule
        for schedule in data['schedules']:
            if schedule['name'] == schedule_name:
                cron_expression = schedule['repeat']
                break

        if not cron_expression:
            print(f"No cron expression found for schedule: {schedule_name}")
            continue
        
        print('cron-expression: ', cron_expression)
        
        
        # cacluate the next run time
        current_time = datetime.datetime.now()
        #print('current-time--marker-02: ', current_time)

        cron = croniter(cron_expression, current_time)
        next_run_time = cron.get_next(datetime.datetime)
        # -debug-print("type of next_run_time: ", type(next_run_time))
        print("NEXT_run_time:          ", next_run_time)

        # determine the earliest next run time for the batch
        if earliest_next_run_time is None or next_run_time < earliest_next_run_time:
            earliest_next_run_time = next_run_time
            earliest_cron_expression = schedule['repeat']


    # add the batch to the priority queue with the earliest next run time
    if earliest_next_run_time is None:
        print("warning")
    else:
        print('earliest_next_run_time: ', earliest_next_run_time)
        print('\n')
        s.enterabs(earliest_next_run_time.timestamp(), batch["priority"], run_batch, (s, batch, data, earliest_cron_expression))
       
    
    


# add batches
# def add_batches(batches, priority_queue):
def initilize_batches(batch_name_list, data, s):

    if not batch_name_list:
        # print("batch_name_list is empty.")
        return
    
    
    #print(batch_name_list)
    for batch_name in batch_name_list:
    
        # find the batch by name
        batch = next((b for b in data['batches'] if b['name'] == batch_name), None)
        if batch is None:
            print(f"Batch {batch_name} not found.")
            continue
        
        schedule_batch(s, batch, data)
            

# $ abstract into a func
#         current_time = datetime.datetime.now()
#         earliest_next_run_time = None

#         for schedule_name in batch["schedules"]:
#             cron_expression = None

#             # find the cron expression for the schedule
#             for schedule in data['schedules']:
#                 if schedule['name'] == schedule_name:
#                     cron_expression = schedule['repeat']
#                     break

#             if not cron_expression:
#                 print(f"No cron expression found for schedule: {schedule_name}")
#                 continue
            
#             # cacluate the next run time
#             cron = croniter(cron_expression, current_time)
#             next_run_time = cron.get_next(datetime.datetime)

#             # determine the earliest next run time for the batch
#             if earliest_next_run_time is None or next_run_time < earliest_next_run_time:
#                 earliest_next_run_time = next_run_time

#         # add the batch to the priority queue with the earliest next run time
# #        if earliest_next_run_time is not None:
#         if earliest_next_run_time is None:
#             print("warning")
#             continue

#             #print("check intial if is empty: ", priority_queue.is_empty())
#         priority_queue.put(earliest_next_run_time, batch["priority"], batch)
           




# add metadata
def add_metadata(metadata_list, metadata_set, origin):
    existing_lhs = {item[0] for item in metadata_set}
    for lhs, rhs in metadata_list:
        if lhs not in existing_lhs:
            metadata_set.add((lhs, rhs, origin))
            existing_lhs.add(lhs) # update the lhs

def process_gui_conf(data, s, metadata_set, hostname):
    # print("func called")
    # hostname = get_hostname()
    # hostname = "198.111.226.182"
    host_match = None
    for host in data["hosts"]:
        if host["name"] == hostname:
            host_match = host["name"]

            initilize_batches(host["batches"], data, s)

            add_metadata(host["data"].items(), metadata_set, host["name"])
            
    # syslog warning if no match
    if host_match == None: 
        syslog.syslog(syslog.LOG_WARNING, f"No host with name '{hostname}' found.")
        
        # if debug print it out
        sys.exit()

    # check host groups for further matches
    for group in data["host_groups"]:
        # if host_match["name"] in group["hosts"] or find_matching_regex(group["hosts_regex"], host_match):
        #print("the result is: ", find_matching_regex(group["hosts_regex"], host_match))

        if host in group["hosts"] or find_matching_regex(group["hosts_regex"], host_match):
            # add_batches(group["batches"], priority_queue)
            initilize_batches(group["batches"], data, s)

            add_metadata(group["data"].items(), metadata_set, group["name"])

    return s, metadata_set

def print_metadat_set(metadata_set):
    print("**************************************")
    print('metadata')
    print("**************************************")

    for item in metadata_set:
        print(item)
    print("**************************************")


def print_priority_queue(s):
    for item in s:
        print(item)
    


    

# process schedule$$
# def process_batches(batches):
#     pq = SchedulePriorityQueue()
#     for batch in batches:
#         priority = batch['priority']
#         ssid_profiles = batch['ssid_profiles']
#         for schedule in batch['schedules']:
#             if "every_1_min" in schedule:
#                 interval = 60
#             elif "every_5_min" in schedule:
#                 interval = 300
#             elif "every_10_min" in schedule:
#                 interval = 600
#             # Add more conditions for other schedules if necessary
#             next_run_time = time.time() + interval
#             for job in batch['jobs']:
#                 pq.put((job, ssid_profiles, batch['name']), next_run_time, priority, interval)
#     return pq

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
    

def execute_job(job, ssid_profiles):  # execute_batches()
    for ssid in ssid_profiles:
        try:
            # create namespace pssid using command line
            create_namespace_command = f"sudo ip netns add pssid"
            subprocess.run(create_namespace_command, shell=True, check=True)

            
            # bond interface with namespace pssid using command line
            bond_interface_namespace_command = f"sudo iw phy0 set netns name pssid"
            subprocess.run(bond_interface_namespace_command, shell=True, check=True)

            # call layer 2 tool using command line
            layer2_tool_command = f"sudo ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/{ssid}.conf -i wlan0"
            subprocess.run(layer2_tool_command, shell=True, check=True)

            # call layer 3 tool using command line
            layer3_tool_command = f"sudo ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i wlan0"
            subprocess.run(layer3_tool_command, shell=True, check=True)

            # simulation a test
            test_simulation_command = f"wget www.goog.com"
            subprocess.run(test_simulation_command, shell=True, check=True)

            # for test in job['tests']:
            #     if not execute_test(test):
            #         if not job.get('continue-if', True):
            #             print("Job stopped due to test failure.")
            #             # to syslog
            #             break
            #     # delay between tests, or return code is true, then start next test

        except subprocess.CalledProcessError as e:
            print(f"Error executing command for SSID '{ssid}': {e}")
            # log error to syslog or handle as needed


def main():

    # function to load jason data

    # JSON data
    #data = {}

    # command line parsing for mode specification    
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

    args = parser.parse_args()

    # debug
    # if args.debug:
    #     print("Debug mode is enabled.")
    # if args.hostname:
    #     print("hostname is enabled.")
    # if args.config:
    #     print("config is enabled.")
        
    if args.hostname:
        hostname = args.hostname
    else:
        hostname = get_hostname()
    
    if args.config:
        pssid_config_path = args.config
    else:
        pssid_config_path = "./pssid_config.json"  # replace the default path for pssid config file

    # initialization priority queue and metadata set
    # pq = SchedulePriorityQueue()
    metadata_set = set()
    # Initialize the scheduler
    s = sched.scheduler(time.time, time.sleep)

    stuff = load_json(pssid_config_path)
    #print(stuff)



 
    #_ , metadata_set = process_gui_conf(stuff, pq, metadata_set)
    s , metadata_set = process_gui_conf(stuff, s, metadata_set, hostname)

    print_metadat_set(metadata_set)
    print('\n')
    # print_priority_queue(priority_queue)

    # print(s.queue)
    s.run()
    # while True:
    #     if not pq.is_empty():
    #          print(priority_queue.get())


    #device_info = get_device_info()
   

    # extract batches and process schedules
 
   # batches =  add_batches_and_metadata(device_info, data)
    #pq = process_batches(batches)

    # continuously process the schedules
    # while True:
    #     if not pq.is_empty():
    #         priority, next_run_time, job_info, interval = pq.get()
    #         job, ssid_profiles, batch_name = job_info
    #         current_time = time.time()
    #         if current_time >= next_run_time:
    #             # run the job 
    #             print(f"Running job: {job['name']} from batch: {batch_name} with priority {priority}")
                

    #             execute_job(job, ssid_profiles)

    #             # for test in job['tests']:
    #             #     success = execute_test(test)
    #             #     if not success and not job['continue-if']:
    #             #         print(f"Stopping further tests for job: {job['name']} due to test failure and 'continue-if' set to False.")
    #             #         break
                
    #             # calculate the new current time after job execution
    #             current_time = time.time()
                
    #             # calculate the next run time based on the original schedule interval
    #             next_run_time += interval * ((current_time - next_run_time) // interval + 1)
    #             pq.put((job, batch_name), next_run_time, priority, interval)
    #         else:
    #             # if it's not time to run yet, put it back into the queue
    #             pq.put((job, batch_name), next_run_time, priority, interval)

    #             # sleep until it's time to run the next schedule
    #             time.sleep(next_run_time - current_time)
    #     else:
    #         # if the queue is empty, wait for a bit before checking again
    #         time.sleep(1)

if __name__ == "__main__":
    main()

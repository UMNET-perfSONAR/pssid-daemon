# su to root first 

import subprocess
import time

def execute_test():  # execute_batches()
    #for ssid in ssid_profiles:  # debug should be indented
    try:
        # create namespace pssid using command line
        create_namespace_command = f"ip netns add pssid"
        subprocess.run(create_namespace_command, shell=True, check=True)
        print('>>>>>>>>>>>> create namespace pssid\n')

        # bond interface with namespace pssid using command line
        print('>>>>>>>>>>>> bond interface to namespace\n')
        bond_interface_namespace_command = f"iw phy0 set netns name pssid"
        subprocess.run(bond_interface_namespace_command, shell=True, check=True)

        # call layer 2 tool using command line
        print('>>>>>>>>>>>> build layer 2')
        build_layer2_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_M.conf -i wlan0"
        subprocess.run(build_layer2_tool_command, shell=True, check=True)
        
        # call layer 3 tool using command line
        print('\n>>>>>>>>>>>> build layer 3')
        build_layer3_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i wlan0"
        subprocess.run(build_layer3_tool_command, shell=True, check=True)
        
        # simulation a test
        print('\n>>>>>>>>>>>> run wget test')
        test_simulation_command = f"wget -P /home/dianluhe www.google.com"
        subprocess.run(test_simulation_command, shell=True, check=True)

                    # for test in job['tests']:
            #     if not execute_test(test):
            #         if not job.get('continue-if', True):
            #             print("Job stopped due to test failure.")
            #             # to syslog
            #             break
            #     # delay between tests, or return code is true, then start next test
        
        # Sleep for a specified period
        sleep_duration = 30  # Time to sleep in seconds
        print(f">>>>>>>>>>>> sleeping for {sleep_duration} seconds...")
        time.sleep(sleep_duration)
        print('>>>>>>>>>>>> done sleeping \n')

        # teardown l3
        print('\n>>>>>>>>>>>> teardown layer 3')
        teardown_layer3_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i wlan0 -d"
        subprocess.run(teardown_layer3_tool_command, shell=True, check=True)
        
        # teardown l2
        print('\n>>>>>>>>>>>> teardown layer 2')
        teardown_layer2_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_M.conf -i wlan0 -d"
        subprocess.run(teardown_layer2_tool_command, shell=True, check=True)
        
        # create namespace pssid using command line
        create_namespace_command = f"ip netns delete pssid"
        subprocess.run(create_namespace_command, shell=True, check=True)
        print('\n>>>>>>>>>>>> delete namespace pssid\n')

    except subprocess.CalledProcessError as e:
        print(f"Error executing command for SSID Mwireless: {e}")
        # log error to syslog or handle as needed

def main():
    execute_test()

if __name__ == "__main__":
    main()

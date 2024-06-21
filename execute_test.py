
import subprocess
import time

def execute_test():  # execute_batches()
    #for ssid in ssid_profiles:  # debug should be indented
    try:

        # # Delete existing namespace if it exists
        # delete_namespace_command = f"sudo ip netns delete pssid"
        # subprocess.run(delete_namespace_command, shell=True, check=True)
        # print("Existing namespace deleted.")

        # create namespace pssid using command line
        create_namespace_command = f"sudo ip netns add pssid"
        subprocess.run(create_namespace_command, shell=True, check=True)
        print('>>>>>>>>>>>> create namespace pssid\n')

        # # Check if namespace exists
        # check_namespace_command = f"ip netns list | grep -w pssid"
        # result = subprocess.run(check_namespace_command, shell=True, capture_output=True, text=True)
        
        # if result.returncode != 0:  # Namespace does not exist
        #     # create namespace pssid using command line
        #     create_namespace_command = f"sudo ip netns add pssid"
        #     subprocess.run(create_namespace_command, shell=True, check=True)
        #     print("Namespace pssid created.")
        # else:
        #     print("Namespace pssid already exists. Reusing it.")

        # bond interface with namespace pssid using command line
        bond_interface_namespace_command = f"sudo iw phy0 set netns name pssid"
        subprocess.run(bond_interface_namespace_command, shell=True, check=True)
        print('>>>>>>>>>>>> bond interface with namespace\n')

        # open a namespace bash 
        # execute_namespace_bash_command = f"sudo ip netns exec pssid bash"
        # subprocess.run(execute_namespace_bash_command, shell=True, check=True)
        # print('open a namespace bash')

        # call layer 2 tool using command line
        # layer2_tool_command = f"sudo ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/{ssid}.conf -i wlan0"
        build_layer2_tool_command = f"sudo ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_M.conf -i wlan0"
        subprocess.run(build_layer2_tool_command, shell=True, check=True)
        print('>>>>>>>>>>>> build layer 2\n')

        # call layer 3 tool using command line
        build_layer3_tool_command = f"sudo ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i wlan0"
        subprocess.run(build_layer3_tool_command, shell=True, check=True)
        print('>>>>>>>>>>>> build layer 3\n')

        # simulation a test
        test_simulation_command = f"wget -P ~/dianluhe www.goog.com"
        subprocess.run(test_simulation_command, shell=True, check=True)
        print('>>>>>>>>>>>> run test\n')

        # Sleep for a specified period
        sleep_duration = 120  # Time to sleep in seconds
        print(f">>>>>>>>>>>> Sleeping for {sleep_duration} seconds...")
        time.sleep(sleep_duration)
        print('>>>>>>>>>>>> done sleeping \n')

        # teardown l3
        teardown_layer3_tool_command = f"sudo ip netns exec pssid /usr/lib/exec/pssid/pssid-dhcp -i wlan0 -d"
        subprocess.run(teardown_layer3_tool_command, shell=True, check=True)
        print('>>>>>>>>>>>> teardown layer 3')
        
        # teardown l2
        teardown_layer2_tool_command = f"ip netns exec pssid /usr/lib/exec/pssid/pssid-80211 -c /etc/wpa_supplicant/wpa_M.conf -i wlan0 -d"
        subprocess.run(teardown_layer2_tool_command, shell=True, check=True)
        print('>>>>>>>>>>>> teardown layer 2')

    except subprocess.CalledProcessError as e:
        print(f"Error executing command for SSID Mwireless: {e}")
        # log error to syslog or handle as needed

def main():
    execute_test()


if __name__ == "__main__":
    main()

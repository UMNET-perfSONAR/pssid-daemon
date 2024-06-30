import subprocess
import re

def fetch_interfaces():
    # Initialize lookup table
    interface_phy_mapping = {}

    print('>> run iw dev')
    iw_dev_command = f"iw dev"
    get_interface_info = subprocess.run(iw_dev_command, shell=True, check=True, capture_output=True, text=True)
    # print({get_interface_info.stdout.strip()})
    output = get_interface_info.stdout.strip()
    print(output)
    print(type(output))

#     output = """phy#0
# 	Interface wlan0
# 		ifindex 3
# 		wdev 0x1
# 		addr dc:a6:32:6d:7e:80
# 		type managed
# 		channel 104 (5520 MHz), width: 40 MHz, center1: 5510 MHz
# phy#1
# 	Interface wlan1
# 		ifindex 3
# 		wdev 0x1
# 		addr dc:a6:32:6d:7e:80
# 		type managed
# 		channel 104 (5520 MHz), width: 40 MHz, center1: 5510 MHz
    
#    """
    print(output)

    # Regular expression pattern to match each phy# and its associated interface
    pattern = r'^phy#(\d+)\n\s+Interface (\S+)'

    # Find all matches in the output
    matches = re.finditer(pattern, output, re.MULTILINE)

    for match in matches:
        phy_number = match.group(1)
        interface_name = match.group(2)
        interface_phy_mapping[interface_name] = f"phy{phy_number}"
    
    return interface_phy_mapping

def get_default_phy(interface_name, interface_phy_mapping):
    # Assuming interface_phy_mapping is a dictionary mapping interface names to phy identifiers
    return interface_phy_mapping.get(interface_name)

interface_phy_table = fetch_interfaces()
for interface, phy in interface_phy_table.items():
    print(f"{interface}: {phy}")

phy_name = get_default_phy("wlan0", interface_phy_table)
print(phy_name)





# fetch_interface()
# lookup_table = {}
# parsed_base = base.splitlines()

# for line in parsed_base:
#     if "Interface" in line:
#         interface = line.split("Interface ")[1]
#         lookup_table[interface] = "phy0"
#         for interface, phy in lookup_table.items():
#             if phy.startswith("phy"):
#                 # Do something with the interface and phy
#                 print(f"Interface: {interface}, Phy: {phy}")
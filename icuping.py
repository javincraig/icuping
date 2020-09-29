import subprocess
import time
import datetime
from signal import signal, SIGINT
from sys import exit
import sys


# Using raw, these are line separated entries
ping_these_raw = """8.8.8.8
1.1.1.1
google.com
192.168.0.1
192.168.0.100
"""


print('Running. Press CTRL-C to exit.')

ping_these = ping_these_raw.splitlines() #Creates a list from the ping these raw
#ping_these = ['8.8.8.8', '1.1.1.1', 'google.com', '192.168.0.1','192.168.0.100'] # Create a list


ifconfig_raw = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE).communicate()[0].decode() # Get network interface configuration
ip_route_raw = subprocess.Popen(['ip', 'route'], stdout=subprocess.PIPE).communicate()[0].decode() #Get ip route information for gateway

interface_dict = {}
record = {}


def build_int_dict():
    for index, line in enumerate(ifconfig_raw.splitlines()):
        if "inet " in line:
            interface_dict[ifconfig_raw.splitlines()[index - 1].split(':')[0]] = {}
            for interface, entry in enumerate(line.split()):
                if entry == "inet":
                    interface_dict[ifconfig_raw.splitlines()[index - 1].split(':')[0]]["inet"] = line.split()[interface + 1]
                if entry == "netmask":
                    interface_dict[ifconfig_raw.splitlines()[index - 1].split(':')[0]]["netmask"] = line.split()[
                        interface + 1]
                if entry == "broadcast":
                    interface_dict[ifconfig_raw.splitlines()[index - 1].split(':')[0]]["broadcast"] = line.split()[
                        interface + 1]

    for line in ip_route_raw.splitlines():
        if "default via" in line:
            if line.split()[4] in interface_dict.keys():
                interface_dict[line.split()[4]]['gateway'] = line.split()[2]


build_int_dict()

def build_record_dict():
    for interface in interface_dict:
        if 'gateway' in interface_dict[interface].keys():
            record[interface] = {}
            for host in ping_these:
                record[interface][host] = {}
                record[interface][host]['up'] = []
                record[interface][host]['down'] = []
                record[interface][host]['status'] = "up"
                record[interface][host]['downtime_sets'] = []


def get_arp_commands(interface):
    arp_commands = ['arp', '-a', '-i']
    arp_commands.append(interface)
    arp_commands.append(interface_dict[interface]['gateway'])
    return arp_commands


build_record_dict()
orig_stdout = sys.stdout

def export_results():
    current_time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    #filename = f"monitor_results({current_time}).txt"
    sys.stdout = open("monitor_results.txt", "a+")
    overall_end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'===================================================================')
    print(f'Monitoring period: {overall_start_time} - {overall_end_time}')
    print(f'===================================================================')
    for interface in record:
        print(f"------------------------{interface}-------------------------------")
        for host in record[interface]:
            if len(record[interface][host]['downtime_sets']) > 1:
                print(f'{interface} to {host}Outage sets are as follows: ')
                for entry in record[interface][host]['downtime_sets']:
                    print(f'  {entry}')
            if record[interface][host]['down'] == []:
                print(f"{interface} never lost connection to {host}")
            else:
                #print(f"{interface} lost connection to {host} at these times {record[interface][host]['down']}")
                pass
    sys.stdout.close()
    sys.stdout = orig_stdout
	
def final_results():
    overall_end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'===================================================================')
    print(f'Monitoring period: {overall_start_time} - {overall_end_time}')
    print(f'===================================================================')
    for interface in record:
        print(f"------------------------{interface}-------------------------------")
        for host in record[interface]:
            if len(record[interface][host]['downtime_sets']) > 1:
                print(f'{interface} to {host}Outage sets are as follows: ')
                for entry in record[interface][host]['downtime_sets']:
                    print(f'  {entry}')
            if record[interface][host]['down'] == []:
                print(f"{interface} never lost connection to {host}")
            else:
                #print(f"{interface} lost connection to {host} at these times {record[interface][host]['down']}")
                pass


def handler(signal_received, frame):
    # Handle any cleanup here
    print('')
    print('CTRL-C detected. Saving Results')
    export_results()
    final_results()
    exit(0)

# Tell Python to run the handler() function when SIGINT is recieved
signal(SIGINT, handler)


overall_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
number = 10000
skip = True

while number > 0:
    start_time = time.time()
    if skip != True:
        time.sleep(10 - (start_time - end_time))
    number-=1
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for interface in record:
        fping_command = ['fping', '-I', interface]
        for entry in ping_these:
            fping_command.append(entry)
        print(f'--------Pinging from {interface} at {current_time}----------')
        fping_raw = subprocess.Popen(fping_command, stdout=subprocess.PIPE).communicate()[0].decode()
        if skip == False:
            for response in fping_raw.splitlines():
                host = response.split()[0]
                if "is alive" not in response:
                    if record[interface][response.split()[0]]['status'] == "up":
                        arp_raw = subprocess.Popen(get_arp_commands(interface), stdout=subprocess.PIPE).communicate()[0].decode() #Get ARP of gateway
                        for line in arp_raw.strip().splitlines():
                            if ":" in line.split()[3]:
                                record[interface][host]['downtime_sets'].append(f"DOWN {str(current_time)}(Gateway Address:{line.split()[3]})")
                            else:
                                record[interface][host]['downtime_sets'].append(f"DOWN {str(current_time)}(Gateway Address:NO ARP)")
                    record[interface][host]['status'] = "down"
                    record[interface][host]['down'].append(str(current_time))
                else:
                    if record[interface][response.split()[0]]['status'] == "down":
                        arp_raw = subprocess.Popen(get_arp_commands(interface), stdout=subprocess.PIPE).communicate()[0].decode() #Get ARP of gateway
                        for line in arp_raw.strip().splitlines():
                            if ":" in line.split()[3]:
                                record[interface][host]['downtime_sets'].append(f"UP {str(current_time)}(Gateway Address:{line.split()[3]})")
                            else:
                                record[interface][host]['downtime_sets'].append(f"UP {str(current_time)}(Gateway Address:NO ARP)")
                    record[interface][host]['up'].append(str(current_time))
                    record[interface][host]['status'] = "up"
            print(fping_raw)
        else:
            for response in fping_raw.splitlines():
                host = response.split()[0]
                arp_raw = subprocess.Popen(get_arp_commands(interface), stdout=subprocess.PIPE).communicate()[0].decode() #Get ARP of gateway
                for line in arp_raw.strip().splitlines():
                    if ":" in line.split()[3]:
                        record[interface][host]['downtime_sets'].append(f'START {str(current_time)}({line.split()[3]})')
                    else:
                        record[interface][host]['downtime_sets'].append(f"UP {str(current_time)}(NO ARP)")
            print(fping_raw)
    end_time = time.time()
    skip = False
    print('Running. Press CTRL-C to exit.')
        


export_results()
final_results()

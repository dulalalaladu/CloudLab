import argparse
import os
import os_client_config
import MasterScript
import test
import ipaddress
import sys
from openstack import connection
from openstack import profile
from openstack import utils

#Starting code to update the CTL IP address in the hosts file.
while True:
	try:
		CTL = ipaddress.ip_address(input("Please enter the IP address of the CTL\n"))
		break
	except ValueError:
		print("Not a valid IP address")	
MasterScript.update_hosts_file(CTL)

while True:
	print ("1 to Establish a New Connection")
	print ("2 to List All Subnets By CIDR")
	print ("3 to List All Images By Name")
	print ("4 to Create a New Subnet")
	print ("5 to List All Flavors By Name")
	print ("6 to Create New VM Instance")
	print ("7 to List All Configured Instances")
	print ("8 to List All Configured and Unassigned Public IP Addresses")
	print ("9 to Create a New Floating IP Address")
	print ("10 to Create a New Network Router")
	print ("11 to Attach Router to New Network")
	print ("12 to Take a Snapshot of a Server")
	print ("13 to Start a VM")
	print ("14 to Stop a VM")
	print ("15 to add new IP address to a VM")
	print ("Press 999 at anytime to quit")
	Choice = int(input("Please input the value of the operation you would like to perform\n"))

	if Choice == 1:
		#Code to ask for the username and password for the OpenStack instance.
		#Create connection will be used.
		URL = input("Please input the authorization URL from admin-openrc.sh\n")
		region = input("Please enter the region\n")
		p_name = input("Please enter the project name\n")
		p_username = input("Please enter the project username\n")
		p_password = input("Please enter the password\n")
		connection = MasterScript.create_connection(URL,region,p_name,p_username,p_password)
	elif Choice == 2:
		MasterScript.list_all_subnets(connection)

	elif Choice == 3:
		MasterScript.list_all_images(connection)

	elif Choice == 4:
		netname = input("Please input the desired network name\n")
		subname = input("Please input the desired subnet name\n")
		version = input("Please input the version 4 or 6\n")
		while True:
			try:
				CIDR = ipaddress.ip_network(input("Please input the CIDR Block\n"))
				gateway = ipaddress.ip_address(input("Please input the gatewayIP\n"))
				break
			except ValueError:
				print("Error in your CIDR or gateway, please retry")

		MasterScript.create_new_subnet(connection,netname,subname,version,CIDR,gateway)
	
	elif Choice == 5:
		MasterScript.list_all_flavors(connection)

	elif Choice == 6:
		MasterScript.create_new_instance(connection)

	elif Choice == 7:
		MasterScript.list_all_instances(connection)

	elif Choice == 8:
		MasterScript.list_free_floating(connection)

	elif Choice == 9:
		MasterScript.create_floating_ip(connection)

	elif Choice == 10:
		MasterScript.create_new_router(connection)	

	elif Choice == 11:
		MasterScript.create_new_router_interface(connection)

	elif Choice == 12:
		MasterScript.take_server_snapshot(connection)

	elif Choice == 13:
		MasterScript.start_VM_instance(connection)

	elif Choice == 14:
		MasterScript.stop_VM_instance(connection)
	
	elif Choice == 15:
		MasterScript.add_VM_IP(connection)

	elif Choice == 999:
		break

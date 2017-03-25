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
		CTL = ipaddress.ip_address(input("Please enter the IP address of the CTL"))
		break
	except ValueError:
		print("Not a valid IP address")	
MasterScript.update_hosts_file(CTL)

while True:
	print ("1 to Establish a New Connection")
	print ("2 to List All Subnets By CIDR")
	print ("3 to List All Images By Name")
	print ("4 to Create a New Subnet")
	print ("Press 999 at anytime to quit")
	Choice = int(input("Please input the value of the operation you would like to perform"))

	if Choice == 1:
		#Code to ask for the username and password for the OpenStack instance.
		#Create connection will be used.
		URL = input("Please input the authorization URL from admin-openrc.sh")
		region = input("Please enter the region")
		p_name = input("Please enter the project name")
		p_username = input("Please enter the project username")
		p_password = input("Please enter the password")
		connection = MasterScript.create_connection(URL,region,p_name,p_username,p_password)
#		test.upload_image(connection)
	elif Choice == 2:
		MasterScript.list_all_subnets(connection)

	elif Choice == 3:
		MasterScript.list_all_images(connection)

	elif Choice == 4:
		netname = input("Please input the desired network name")
		subname = input("Please input the desired subnet name")
		version = input("Please input the version 4 or 6")
		while True:
			try:
				CIDR = ipaddress.ip_network(input("Please input the CIDR Block"))
				gateway = ipaddress.ip_address(input("Please input the gatewayIP"))
				break
			except ValueError:
				print("Error in your CIDR or gateway, please retry")

		MasterScript.create_new_subnet(connection,netname,subname,version,CIDR,gateway)

	elif Choice == 999:
		break

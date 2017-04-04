import sys
import ipaddress
import os
import os_client_config
from openstack import connection
from openstack import profile
from openstack import utils
from python_hosts import Hosts, HostsEntry

#The function update_hosts_file is responsible for update the hosts file inside a Linux environment.
#It is included for use to update with the IP of the CTL server in case the OpenStack instance has 
#changed or IP has been modified. It first finds and deletes previous definitions of ctl before
#establishing a new one.
#Input varible to this function is the IP address of the CTL, which can be retrieved by a simple
#ifconfig command on the Shell of the CTL.
def update_hosts_file(IP):
	hosts = Hosts(path='/etc/hosts')
	hosts.remove_all_matching(name='ctl')
	new_entry = HostsEntry(entry_type='ipv4', address=str(IP), names=['ctl'])
	hosts.add([new_entry])
	hosts.write()

#The function create_connection is responsible for establishing a new connection with the 
#OpenStack instance. This connection is needed by other functions to grab information or create
#newer ones. 
#Input variables are the authentication URL, region, project name, username and password.
#These input variables can be grabbed from OpenStack by gooing through Access and Security Tab, under
#Project Menu, and downloading the admin-openrc file.
def create_connection(URL, region, p_name, p_username, p_password):
    prof = profile.Profile()
    prof.set_region(profile.Profile.ALL, region)

    return connection.Connection(
        profile=prof,
        auth_url=URL,
        project_name = p_name,
	user_domain_name = 'default',
	project_domain_name = 'default',
        username = p_username,
        password = p_password
    )

#Input variable is the established connection to the OpenStack instance.
#Output is a list of configured subnets.	
# PROBLEM TO LOOK INTO: NETWOKS AE SORTED IN A WAY DIFFERENT THAN SUBNETS, THE DIRECT CORRELATION IN ZIP NEEDS TO BE FIXED!
# NEED TO CHECK HOW OPENSTACK SORT BOTH NETWORK AND SUBNET TO RECONCILE THE OUTPUT FOR INTEGRITY
def list_all_subnets(conn):
    print("Network  are:")
    for networks,subnets in zip(conn.network.networks(),conn.network.subnets()):
        print ("Network Name: "+networks.name+" || Subnet Name: " + subnets.name + " || CIDR Range: " + subnets.cidr)

#Input variable is the easblished connection to the OpenStack instance.
#Output is a list of the uploaded images.
def list_all_images(conn):
    print("Images are:")
    for image in conn.image.images():
        print(image.name)

#The function list_all_flavors is tasked with retreiving all the flavors on an instance.
#Input variable is the easblished connection to the OpenStack instance.
#Output is a list of the uploaded images.
def list_all_flavors(conn):
    print("Flavors are:\n")
    for flavor in conn.compute.flavors():
        print(flavor.name)

#The function create_new_subnet is tasked with creating a new subnet into the OpenStack instance.
#Input variables are the established connection to the OpenStack instance, as well as network name, subnet name,
#CIDR Block, and gateway IP address.
def create_new_subnet(conn, net_name, sub_name, versionIP, cidr, gatewayIP):
    print("Creating New Network Procedure:")
    new_network = conn.network.create_network(name=net_name)
    new_subnet = conn.network.create_subnet(name=sub_name, network_id=new_network.id, ip_version=versionIP, cidr=str(cidr), gateway_IP=str(gatewayIP))

#The function upload_new_image is tasked with uploading a new image into the OpenStack instance.
#Assumption is that the user has the image stored locally on the control machine, knows the name and its details.
#Input variables are the established connection to the OpenStack instance, the image name and location, the image format (VDI, ISO, RAW)
def upload_new_image (conn, image_name, image_location, image_format):
    print("Hello World:")

#The function create_new_instance is tasked with instantiating a new VM instance in the OpenStack instnce.
#Input variable are the established connection to the OpenStack instance, the instance name, the image name, the flavor name and the attached network.
def create_new_instance(conn):
    image_name = input("Please input the image name you would like to use:\n")
    flavor_name = input("Please input the flavor name you would like to use:\n")
    network_name = input("Please input the network name you would like to use:\n")
    instance_name = input("Please input the name you would like to give your instance:\n")
    image = conn.compute.find_image(image_name)
    flavor = conn.compute.find_flavor(flavor_name)
    network = conn.network.find_network(network_name)
    server = conn.compute.create_server(name=instance_name, image_id=image.id, flavor_id=flavor.id, networks=[{"uuid": network.id}])
    server = conn.compute.wait_for_server(server)

#The function list_all_instances is tasked with returning a list of all the configured VM instances.
#It will provide the list of names, which can be modified to also add a list of IDs, images per VM,...
#Input varibales are the established connection to the OpenStack instance.
def list_all_instances(conn):
    print("Configured Servers and their states are:")
    for server in conn.compute.servers():
        print(server.name+"||"+server.status)
        print("*************************************")

#The function start_VM_instance is tasked with turning on a VM.
#Input variables are the established connection to the OpenStack instance and the VM ID or VM name.
def start_VM_instance(conn,VM_ID):
    print("Hello World:")

#The function stop_VM_instance is tasked with turning off a VM.
#Input variables are the established connection to the OpenStack instance and the VM ID or VM name.
def stop_VM_instance(conn,VM_ID):
    print("Hello World:")

#The function create_new_router is tasked with creating a new router instance inside OpenStack.
#Input variables are the established connection to the OpenStack instance and the Router Namee.
def create_new_router(conn,Router_Name):
    print("Hello World:")

#The function list_free_floating is tasked with returning a list of all configured and unassigned.
#Input varibales are the established connection to the OpenStack instance.
def list_free_floating(conn):
    print("Free Unassigned Floating IP Addresses are are:")
    for ip in conn.network.ips():
        print (ip.floating_ip_address)

#The function create_floating_ip is tasked with creating a new floating IP address from the assigned pool.
#Input varibales are the established connection to the OpenStack instance.
def create_floating_ip(conn):
    print("Creating New Floating IP.")
    external_network = conn.network.find_network("ext-net")
    conn.network.create_ip(floating_network_id=external_network.id)

#The function create_new_router is tasked with creating a new network router.
#Input varibales are the established connection to the OpenStack instance.
def create_new_router(conn):
    router_name = input("Please enter desired router name\n")
    conn.network.create_router(name=router_name)

#The function create_new_router_interface is tasked with attaching a router to an interface.
#The function will first list the different networks available for the router to hook unto.
#Input varibales are the established connection to the OpenStack instance.
# PROBLEM TO LOOK INTO: THE ROUTER DOES NOT SHARE ITS PRIVATE SUBNET INTERFACE DETAILS! ONLY THE PUBLIC INTERFACES!
def create_new_router_interface(conn):
    print ("List of available configured routers:")
    for router in conn.network.routers():
        print(router.name)
    router_name = input("Please enter desired router name\n")
    print ("Selected Router is connected to the following networks:")
    for routers in conn.network.routers():
        print (routers)


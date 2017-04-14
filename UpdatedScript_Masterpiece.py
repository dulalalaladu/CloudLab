import sys
import ipaddress
import os
import os_client_config
import time
import datetime
import xml.etree.ElementTree as ET
from lxml import objectify,etree
from openstack import connection
from openstack import profile
from openstack import utils
from python_hosts import Hosts, HostsEntry
from xml.etree import ElementTree as etree
from xml.dom import minidom

def create_from_xml(conn):
    xmlFile = input("Please enter the name of the XML to load from\n")
    file_root = objectify.parse(xmlFile).getroot()
    Networks = {}
    Subnets = {}
    Routers = {}
    counter = 1
    counterNested = 1 
    counterRouter = 1

    #Parse the XML File to Create Router Dictionary
    for Router in file_root.Routers.iterchildren():
        temp = {counterRouter:Router.attrib}
        Routers.update(temp)
        counterRouter = counterRouter + 1

    #Parse the XML File to Create Networks and Subnets Dictionaries 
    for Net in file_root.Networks.iterchildren():
        temp = {counter:Net.attrib}
        Networks.update(temp)
        for Sub in Net.getchildren():
            tempNested = {counterNested:{counter:Sub.attrib}}
            for CIDR in Sub.iterchildren():
                tempNested[counterNested][counter][CIDR.tag] = CIDR.text
            Subnets.update (tempNested)
            counterNested = counterNested + 1
        counter = counter + 1
    
    #Itemize the Router Dictionary and Create the routers by name
    for RoutNum,RouterNew in Routers.items():
        if RouterNew['Name'] != 'tun0-router' and RouterNew['Name'] != 'flat-lan-router':
            conn.network.create_router(name=RouterNew['Name'])    


    #Itermize the Network and Subnet Dictionaries and Create them on OpenStack
    for Net,Na in Networks.items():
        if Na['Name'] != 'ext-net' and Na['Name'] != 'tun0-net' and Na['Name'] != 'flat-lan-1-net':
            #net = conn.network.create_network(name=Na['Name'])
            for Sub,Sa in Subnets.items():
                for SNet,S in Sa.items():
                    if SNet == Net:
                        print("")
                        #conn.network.create_subnet(name=S['Name'], network_id=net.id, ip_version='4', cidr=S['Subnet_CIDR'])

def prettify(elem):
    rough_string = etree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

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
def list_all_subnets(conn):
    for networks in conn.network.networks():
        name = networks.name
        netid = networks.id
        print ("########################################################")
        print ("Network Name: "+name+" || ",end="")
        for subnets in conn.network.subnets():
            if subnets.network_id == netid:
                print("Subnet Name: " + subnets.name + " || CIDR Range: " + subnets.cidr+" ||",end=" ")
        print ("########################################################")    
    print ("########################################################")

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
def upload_new_image (conn):
   image_name =  input("Plese enter the name of the image you would like to upload")
   container = input("Please enter the Container Format as one of ami, ari, aki, bare,ovf, ova, or docker")
   disk = input ("Please enter the Disk Format as one of ami, ari, aki, vhd, vmdk, raw, qcow2, vdi, or iso")
   with open(image_name) as fimage:
       conn.image.upload_image(container_format=container, disk_format=disk,data=fimage)

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
def start_VM_instance(conn):
    list_all_instances(conn)
    instance_name = input("Please enter the name of the server you would like to start")
    instance = conn.compute.find_server(instance_name)
    conn.compute.start_server(instance)

#The function stop_VM_instance is tasked with turning off a VM.
#Input variables are the established connection to the OpenStack instance and the VM ID or VM name.
def stop_VM_instance(conn):
    list_all_instances(conn)
    instance_name = input("Please enter the name of the server you would like to stop")
    instance = conn.compute.find_server(instance_name)
    conn.compute.stop_server(instance)

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
def create_new_router_interface(conn):
    print("*************************************")
    print ("List of available configured routers:")
    for routers in conn.network.routers():
        print (routers.name)
    print("*************************************")
    router_name = input("Please enter desired router name\n")
    router_id = conn.network.find_router(router_name)
    router_idd = router_id.id
    print ("Selected Router has the following configured IP addresses:")
    print("*************************************")
    for ports in conn.network.ports():
        if ports.device_id == router_idd:
            print (ports.fixed_ips[0]['ip_address'])
    print("*************************************")
    list_all_subnets(conn)
    new_interface_network = input ("Please enter the network name you would like add")
    new_network = conn.network.find_network(new_interface_network)
    conn.network.create_port(admin_state_up=True, device_id=router_idd, network_id=new_network.id)

#The function take_server_snapshot is tasked with taken a snapshot of a given VM
#The snapshot will be available at the CTL on the /var/lib/glance/images folder
#We start by listing the configured instances, find the server instance based on name and passing it to the API call
#Input variables are the established connection to the OpenStack instance.
def take_server_snapshot(conn):
    list_all_instances(conn)
    instance_name = input ("Please enter the name of the instance you wish to snapshot")
    instance = conn.compute.find_server(instance_name)
    conn.compute.shelve_server(instance)

#The function add_VM_IP is tasked with adding a Fixed IP Address to a VM of choice
#The function starts by listing all the configured subnets and instances
#User is prompted to enter the desired VM to add an IP to, as well as the desired network
#Inpute variables are the established connection to the OpenStack instance.
def add_VM_IP(conn):
    list_all_subnets(conn)
    list_all_instances(conn)
    instance_name = input ("Please choose VM to add IP to")
    instance = conn.compute.find_server(instance_name)
    print("**************************")
    print("The Selected Server has the following IP addresses configured")
    for ip in conn.compute.server_ips(instance):
        print(ip)
    network_name = input ("Please enter the network name you would like to add")
    network = conn.network.find_network(network_name)
    port = conn.network.create_port(admin_state_up=True, network_id=network.id)
    conn.compute.create_server_interface(server=instance, port_id=port.id)


def Profile_OpenStack(conn):
    Profile = etree.Element('Profile')
    Networks = etree.SubElement(Profile, 'Networks')
    
    for networks in conn.network.networks():
        Network_Name = etree.SubElement(Networks,'Network')
        Network_Name.attrib['Name'] = networks.name
        for subnets in conn.network.subnets():
            if subnets.network_id == networks.id:
                Subnet_Details = etree.SubElement(Network_Name,'Subnet')
                Subnet_Details.attrib['Name'] = subnets.name
                #Subnet_Detail_ID = etree.SubElement(Subnet_Details,'Subnet_ID')
                #Subnet_Detail_ID.text = subnets.id
                Subnet_Detail_CIDR = etree.SubElement(Subnet_Details,'Subnet_CIDR')
                Subnet_Detail_CIDR.text = subnets.cidr
    
    Routers = etree.SubElement(Profile,'Routers')
    for routers in conn.network.routers():
        Router_Name = etree.SubElement(Routers,'Router')
        Router_Name.attrib['Name'] = routers.name
        for ports in conn.network.ports():
            if ports.device_id == routers.id:
                Router_Interface = etree.SubElement(Router_Name,'Interface')
                Router_Interface.attrib['ID'] = ports.id
                Router_IP = etree.SubElement(Router_Interface,'IP')
                Router_IP.text = ports.fixed_ips[0]['ip_address']
    
    Images = etree.SubElement(Profile,'Images')
    for images in conn.image.images():
        Image_Name = etree.SubElement(Images,'Image')
        Image_Name.attrib['Name'] = images.name
        Image_Container_Format = etree.SubElement(Image_Name,'ContainerFormat')
        Image_Container_Format.text = images.container_format
        Image_Disk_Format = etree.SubElement(Image_Name,'DiskFormat')
        Image_Disk_Format.text = images.disk_format

    Flavors = etree.SubElement(Profile,'Flavors')
    for flavors in conn.compute.flavors():
        Flavor_Name = etree.SubElement(Flavors,'Flavor')
        Flavor_Name.attrib['Name'] = flavors.name
        Flavor_VCPU = etree.SubElement(Flavor_Name,'VCPU')
        Flavor_VCPU.text = str(flavors.vcpus)
        Flavor_Disk = etree.SubElement(Flavor_Name,'Disk')
        Flavor_Disk.text = str(flavors.disk)
        Flavor_Ram = etree.SubElement(Flavor_Name,'RAM')
        Flavor_Ram.text = str(flavors.ram)

    Instances = etree.SubElement(Profile,'Instances')
    for instances in conn.compute.servers():
        Instances_Name = etree.SubElement(Instances,'Instance')
        Instances_Name.attrib['Name'] = instances.name
        Instances_Status = etree.SubElement(Instances_Name,'Status')
        Instances_Status.text = instances.status
        for flavor in conn.compute.flavors():
            if flavor.links[1]['href'] == instances.flavor['links'][0]['href']:
                Instances_Flavor = etree.SubElement(Instances_Name,'Flavor')
                Instances_Flavor.text = flavor.name
		
        for image in conn.image.images():
            if image.id == instances.image['id']:
                Instances_Image = etree.SubElement(Instances_Name,'Image')
                Instances_Image.text = image.name
		
        for ports in conn.network.ports():
            if ports.device_id == instances.id:
                Instances_Interface = etree.SubElement(Instances_Name,'Interface')
                Instances_Interface.attrib['ID'] = ports.id
                Instances_IP = etree.SubElement(Instances_Interface,'IP')
                Instances_IP.text = ports.fixed_ips[0]['ip_address']
 
    TimeStamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d--%H-%M-%S') 
    Filename = 'OpenStackProfile-' + TimeStamp + ".xml"
    print(prettify(Profile))
    Profile_Output = open(Filename,'w')
    print (prettify(Profile),file=Profile_Output)
    Profile_Output.close()

def list_all_routers(conn):
    for router in conn.network.routers():
        print (router)

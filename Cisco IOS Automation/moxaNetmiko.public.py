#!/usr/bin/python3.7

from netmiko import ConnectHandler, redispatch
import netmiko
import time
import os

moxaTermServer = {
    'ip':'192.168.88.xx', #ip address of moxa serial server
    'device_type':"generic_termserver_telnet", #setting device type to generic terminal server for interface with Moxa Nport terminal server
    'port': '4001', #default port 1
    'global_delay_factor' : 2 
}

CURRENT_VERSION='/c3750e-universalk9-mz.152-4.E10.bin' #current CISCO IOS Version
BOOT_HOST = '192.168.88.xx' #device that contains boot Cisco IOS image - uses TFTP
TFTP_HOST = '192.168.88.xx' #can be the same as above - uses HTTP in code
ROUTER_IP = '192.168.88.xx' #gateway IP
SWITCH_IP = '192.168.88.xx' #temp switch ip
SUB_MASK = '255.255.255.0' #subnet mask

#Commands
mgmt_cmd = ['inter Fa0', 'ip address dhcp', 'no shut']
copy_cmd = 'copy tftp://' + TFTP_HOST + CURRENT_VERSION + ' flash:'
no_cmd = 'no'
boot_cmd = 'boot'
tftp_boot = 'boot tftp://' + BOOT_HOST + CURRENT_VERSION
set_cmd = ['set DEFAULT_ROUTER ' + ROUTER_IP, 'set IP_ADDR ' + SWITCH_IP + '/' + '255.255.255.0']

#Credentials - each array must be of equal length
usr = ['cisco', 'cisco']
pwd = ['cisco', 'password']

#CLI Port Entry - Moxa Nport 1-16 - checks valid entry 
port = int(input('Please Enter Port Number:'))
while port < 1 or port > 16:
    print("Port number out of range. Please try again...")
    port = int(input('Please Enter Port Number:'))
port = port + 4000
moxaTermServer['port'] = str(port)

#function used for No Cisco IOS image detected
def noIos():
    moxa = netmiko.ConnectHandler(**moxaTermServer)
    print(moxa.find_prompt())
    output = moxa.write_channel(boot_cmd +'\n')
    print(output)
    print('[Status]: No CISCO IOS Image detected...')
    moxa.write_channel(set_cmd[0])
    print(moxa.find_prompt())
    moxa.write_channel('\r')
    time.sleep(1)
    moxa.write_channel(set_cmd[1])
    print(moxa.find_prompt())
    moxa.write_channel('\r')
    time.sleep(1)
    moxa.write_channel(tftp_boot + '\r')
    time.sleep(1)
    print('[Task]: Connecting TFTP')
    print(moxa.find_prompt())
    print('[Task]: Booting from TFTP')
    moxa.disconnect()
    initialCheck()

#function used when Cisco IOS is present and accessible
def cleanBoot():
    moxa = netmiko.ConnectHandler(**moxaTermServer)
    redispatch(moxa, device_type = 'cisco_ios') #redispatch connection to use Cisco commands using Netmiko
    output = moxa.find_prompt()
    print(output)
    moxa.enable()
    print("[Status]: Checking Version...")
    version = moxa.send_command('show version', use_textfsm=True)#uses textfsm for parsing
    version = version[0]
    if version['running_image'] == CURRENT_VERSION: #current version termination
        print("[TASK]: Current CISCO IOS found - " + version['running_image'])
        print('[Success]: CISCO IOS PreCheck - Complete!')
        moxa.disconnect()
    else: #Cisco version out of date
        print("[TASK]: CISCO IOS found: " + version['running_image'])
        print("[Status]: CISCO IOS Upgrade Required")
        moxa.config_mode()
        moxa.send_config_set(mgmt_cmd)
        moxa.enable()
        if moxa.check_enable_mode() == True:
            moxa.send_command_timing('del /f /r *')
            print('[Status]: Cisco IOS Updating.')
            output = moxa.send_command(copy_cmd, delay_factor=20)
            print(output)
            if output[-1] != ')':
                print('File Transfer Failed.')
                moxa.disconnect()
                cleanBoot()
        print('[Task]: CISCO IOS Updated.')
        output = moxa.send_command('wr erase')
        if 'Continue?' in output:
            moxa.send_command_timing('\n')
        output = moxa.send_command_timing('reload')
        if 'yes/no' in output:
            output = moxa.send_command_timing(no_cmd)
        if 'confirm' in output:
            moxa.send_command_timing('\n')
        print('[Status]: Reboot Initiated')
        moxa.disconnect()
        initialCheck()

#function that attempts to access switch when login required using usr & pwd arrays
def credentials():
    moxa = netmiko.ConnectHandler(**moxaTermServer)
    access = False
    for x in range(4):
        moxa.write_channel(usr[x] + '\n')
        time.sleep(1)
        moxa.write_channel(pwd[x] + '\n')
        time.sleep(1)
        output = moxa.find_prompt()
        if '#' in output:
            access = True
            print('[TASK]: Credentials Accepted')
            break
    if access == True:
        moxa.disconnect()
        cleanBoot()
    else:
        print('[FAIL]:Login Attempts Failed')
        moxa.disconnect()

def initialCheck(): #checks initial prompts to determine state of switch
    moxa = netmiko.ConnectHandler(**moxaTermServer)
    print('[Status]: Connected...')
    output = moxa.find_prompt()
    while True:
        output = moxa.find_prompt()
        if 'switch:' in output:
            moxa.write_channel(boot_cmd)
            time.sleep(3)
            output = moxa.find_prompt()
            if output[-1] == '@':
                moxa.disconnect()
                initialCheck()
                break
            else:
                moxa.disconnect()
                noIos()
                break

        elif 'initial configuration dialog? [yes/no]:' in output:
            moxa.write_channel('no\n')
            moxa.disconnect()
            cleanBoot()
            break

        elif 'witch#' in output:
            moxa.disconnect()
            cleanBoot()
            break

        elif 'witch>' in output:
            moxa.disconnect()
            cleanBoot()
            break

        elif 'sername:' in output:
            moxa.disconnect()
            credentials()
            break
        
        else:
            print('[Live Feed]: ' + output)
            time.sleep(30)
            continue

initialCheck()

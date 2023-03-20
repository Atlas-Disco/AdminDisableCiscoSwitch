import datetime
import re
from netmiko import ConnectHandler
from getpass import getpass

def get_credentials_and_days():
    switch_ip = input("Enter the switch IP address: ")
    username = input("Enter your username: ")
    password = getpass("Enter your password: ")
    days_inactive = int(input("Enter the number of days to check for inactivity: "))
    return switch_ip, username, password, days_inactive

def connect_to_switch(switch_ip, username, password):
    device = {
        'device_type': 'cisco_ios',
        'ip': switch_ip,
        'username': username,
        'password': password,
    }
    return ConnectHandler(**device)

def get_inactive_ports(connection, days_inactive):
    inactive_ports = []
    now = datetime.datetime.now()
    timedelta_days = datetime.timedelta(days=days_inactive)
    
    interface_output = connection.send_command("show interfaces")
    last_input_regex = re.compile(r"^\w+?Ethernet\d+/\d+.*\n.*Last input (\w+),", re.MULTILINE)

    for match in last_input_regex.finditer(interface_output):
        last_input = match.group(1)
        if last_input == "never":
            inactive_ports.append(match.group(0).split()[0])
        else:
            last_input_date = datetime.datetime.strptime(last_input, "%Y-%m-%d")
            if now - last_input_date > timedelta_days:
                inactive_ports.append(match.group(0).split()[0])

    return inactive_ports

def disable_inactive_ports(connection, inactive_ports):
    for port in inactive_ports:
        connection.send_config_set([
            f"interface {port}",
            "shutdown",
            "description Disabled by script due to inactivity",
        ])

def main():
    switch_ip, username, password, days_inactive = get_credentials_and_days()
    connection = connect_to_switch(switch_ip, username, password)
    inactive_ports = get_inactive_ports(connection, days_inactive)

    if inactive_ports:
        print(f"The following ports have been inactive for {days_inactive} days or more:")
        for port in inactive_ports:
            print(port)

        choice = input("Do you want to disable these ports? (y/n): ")
        if choice.lower() == 'y':
            disable_inactive_ports(connection, inactive_ports)
            connection.send_command("write memory")
            print("The inactive ports have been disabled and the changes have been saved.")
        else:
            print("No action has been taken.")
    else:
        print("No inactive ports found.")

    connection.disconnect()

if __name__ == "__main__":
    main()

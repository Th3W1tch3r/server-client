import socket
import subprocess
import platform
import psutil
import os

def bytes_to_gb(bytes_value):
    return bytes_value / (1024 ** 3)

def get_running_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        processes.append({
            'pid': proc.info['pid'],
            'name': proc.info['name'],
            'username': proc.info['username']
        })
    return processes

def get_open_ports():
    open_ports = []
    for conn in psutil.net_connections('inet'):
        if conn.status == psutil.CONN_LISTEN:
            try:
                service_name = socket.getservbyport(conn.laddr.port)
            except (OSError, socket.error):
                service_name = "unknown"
            open_ports.append({
                'port': conn.laddr.port,
                'service_name': service_name
            })
    return open_ports

def get_installed_apps():
    installed_apps = []
    if os.path.exists('/usr/share/applications'):
        for filename in os.listdir('/usr/share/applications'):
            if filename.endswith('.desktop'):
                with open(os.path.join('/usr/share/applications', filename), 'r') as file:
                    for line in file:
                        if line.startswith('Name='):
                            app_name = line.strip()[5:]
                            installed_apps.append(app_name)
                            break
    return installed_apps

def get_pc_manufacturer():
    try:
        with open('/sys/class/dmi/id/sys_vendor') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_bluetooth_device():
    try:
        bluetooth_output = subprocess.check_output(['bluetoothctl', 'info']).decode().split('\n')
        connected_device = None
        for line in bluetooth_output:
            if "Connected: yes" in line:
                connected_device = line.split()[-1]
                break
        return connected_device
    except subprocess.CalledProcessError:
        return None

def get_physical_ports():
    ports = {}

    # Get USB ports
    try:
        lsusb_output = subprocess.check_output(['lsusb']).decode().split('\n')
        usb_ports = [line.split()[5:] for line in lsusb_output if line]
        ports['USB'] = usb_ports
    except subprocess.CalledProcessError:
        pass

    # Get HDMI ports
    try:
        xrandr_output = subprocess.check_output(['xrandr']).decode().split('\n')
        hdmi_ports = [line.split()[0] for line in xrandr_output if ' connected' in line and 'HDMI' in line]
        ports['HDMI'] = hdmi_ports
    except subprocess.CalledProcessError:
        pass

    # Get VGA ports
    try:
        xrandr_output = subprocess.check_output(['xrandr']).decode().split('\n')
        vga_ports = [line.split()[0] for line in xrandr_output if ' connected' in line and 'VGA' in line]
        ports['VGA'] = vga_ports
    except subprocess.CalledProcessError:
        pass

    # Get Ethernet ports
    try:
        ifconfig_output = subprocess.check_output(['ifconfig']).decode().split('\n')
        eth_ports = [line.split()[0] for line in ifconfig_output if 'flags' in line and 'Ethernet' in line]
        ports['Ethernet'] = eth_ports
    except subprocess.CalledProcessError:
        pass

    return ports

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
server_address = ('192.168.1.17', 12345)
client_socket.connect(server_address)

# Collect system information
system_info = {
    'PC Manufacturer': get_pc_manufacturer(),
    'Bluetooth Device': get_bluetooth_device(),
    'Physical Ports': get_physical_ports(),
    'System': platform.uname(),
    'CPU Count': psutil.cpu_count(logical=True),
    'Physical Cores': psutil.cpu_count(logical=False),
    'CPU Usage Per Core': psutil.cpu_percent(percpu=True),
    'Total CPU Usage': psutil.cpu_percent(),
    'Memory': bytes_to_gb(psutil.virtual_memory().total),
    'Memory Used': bytes_to_gb(psutil.virtual_memory().used),
    'Memory Free': bytes_to_gb(psutil.virtual_memory().free),
    'Memory Available': bytes_to_gb(psutil.virtual_memory().available),
    'Memory Percentage': psutil.virtual_memory().percent,
    'Disk Usage': bytes_to_gb(psutil.disk_usage('/').total),
    'Disk Used': bytes_to_gb(psutil.disk_usage('/').used),
    'Disk Free': bytes_to_gb(psutil.disk_usage('/').free),
    'Disk Percentage': psutil.disk_usage('/').percent,
    'Running Processes': get_running_processes(),
    'Open Ports': get_open_ports(),
    'Installed Apps': get_installed_apps(),
}

# Convert system_info to a string
data = str(system_info).encode()

# Send data to the server
client_socket.sendall(data)

# Close the connection
client_socket.close()
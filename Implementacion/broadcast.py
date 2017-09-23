# Import modules
import subprocess
import ipaddress
import time

# Create the network
ip_net = ipaddress.ip_network(u'10.20.161.0/24')

# Get all hosts on that network
all_hosts = list(ip_net.hosts())

# Configure subprocess to hide the console window
info = subprocess.STARTUPINFO()
info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
info.wShowWindow = subprocess.SW_HIDE

# For each IP address in the subnet, 
# run the ping command with subprocess.popen interface

online = []
start = time.time()
for i in range(len(all_hosts)):
    output = subprocess.Popen(['ping', '-n', '1', '-w', '500', str(all_hosts[i])], stdout=subprocess.PIPE, startupinfo=info).communicate()[0]
    
    print "Host de destino inaccesible" not in output and "Tiempo de espera agotado para esta solicitud" not in output
    if "Host de destino inaccesible" not in output and "Tiempo de espera agotado para esta solicitud" not in output:
        online.append(str(all_hosts[i]))
fin = time.time()

print str(fin - start)
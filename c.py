import os
import socket
import time
from threading import Timer
import sys


def time_out():
    global timeout
    timeout = 1
    return



def carry_add(word1, word2):
    result = word1 + word2
    return (result & 0xffff) + (result >> 16)



def checksum(data):
    checksum_local = 0
    if (len(data) % 2) == 0:
        for i in range(0, len(data), 2):
            word = ord(data[i]) + (ord(data[i+1]) << 8)
            checksum_local = carry_add(checksum_local, word)
    else:
        for i in range(0, len(data)-1, 2):
            word = ord(data[i]) + (ord(data[i+1]) << 8)
            checksum_local = carry_add(checksum_local, word)
        word = ord(data[len(data)-1]) + (ord(' ') << 8)
        checksum_local = carry_add(checksum_local, word)
    checksum_local = ~checksum_local & 0xffff
    return bin(checksum_local).lstrip('0b').zfill(16)



def make_segment(data,seq_no):
    sep = '###' 
    segment = seq_no + sep + checksum(data) + sep + '0101010101010101' + sep +  data
    segment = segment.encode()
    return segment



timeout = 0
print(sys.argv)
sep = '###'
n = len(sys.argv)-3
filename = sys.argv[n+1]
MSS = int(sys.argv[n+2])
server_port = int(sys.argv[n])
server_ip_list = sys.argv[1:n]
server_not_acked = []
for server in server_ip_list:
    server_not_acked.append(server)
bytesToSend = []

if os.path.isfile(filename):
    print('File is present')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print('Created the socket')
    with open(filename, mode = 'rb') as f:
        sequence_number = 0
        bytesToSend = '.'
        log_time_first = time.perf_counter()
        
        print("Starting File Transfer")
        
        while bytesToSend != "":                                                             
            server_ip_list = sys.argv[1:n]
            bytesToSend = f.read(MSS)
            bytesToSend = bytesToSend.decode()
            client_socket.settimeout(1)
            seq_no = '{0:032b}'.format(sequence_number)                                     
            for server_ip in server_ip_list:                                                
                segment = make_segment(bytesToSend, seq_no)                              
                client_socket.sendto(segment,(server_ip, server_port))
            initial_time = time.perf_counter()
            server_not_acked = server_ip_list                                               

            while len(server_not_acked) != 0:
                try:
                    acknowledgement, ServerAddress = client_socket.recvfrom(1500)           
                    present_time = time.perf_counter()
                    sock_timeout = 1 - (present_time - initial_time)
                    client_socket.settimeout(sock_timeout)
                    acknowledgement = acknowledgement.decode()
                    ack = acknowledgement.split(sep)                                            
                    if ack[0] != seq_no or ack[1] != '0000000000000000' or ack[2]!= '1010101010101010':
                        continue
                    server_not_acked.remove(ServerAddress[0])
                except socket.timeout:
                    for server_addr in server_not_acked:                                        
                        client_socket.sendto(segment, (server_addr, server_port))
                        print("Time out, Sequence Number:",sequence_number," from:",server_addr)
                    initial_time = time.perf_counter()
            sequence_number += len(bytesToSend)                                                             
            
        log_time_last = time.perf_counter()
        
        print ("File Transfer complete in :",log_time_last - log_time_first)
        
        client_socket.close()
        
else:
    print('File not found')
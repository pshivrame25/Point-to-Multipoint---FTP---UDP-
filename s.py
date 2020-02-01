import sys
import socket
import time
import random

#*******************************************************************************************************************************************************************************************
#
#--------------- 1 6   B I T    O N E ' S    C O M P L E M E N T    A D D I T I O N---------------------------------------------------------------------------------------------------------
#
#*******************************************************************************************************************************************************************************************

def carry_add(word1, word2):
    result = word1 + word2
    return (result & 0xffff) + (result >> 16)

#**********************************************************************************************************************************************************************

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

#*******************************************************************************************************************************************************************************************
#
#--------------- S E R V E R   R E P L Y    &    F I L E     W R I T E----------------------------------------------------------------------------------------------------------------------------------------------------
#
#*******************************************************************************************************************************************************************************************
def server_reply_write(conn_socket, seq_no, file_ptr, data):
    '''Replies with ACK message with seq_no'''
    ack_id_field = '1010101010101010'
    zero_field = '0000000000000000'
    out_msg = seq_no + sep + zero_field + sep + ack_id_field
    out_msg = out_msg.encode()
    conn_socket.sendto(out_msg,clientAddress)
    data=data.encode()
    file_ptr.write(data)
    return

#*******************************************************************************************************************************************************************************************
#
#--------------- C H E C K S U M M I N G    &     S E Q U E N C E    N O.    C H E C K------------------------------------------------------------------------------------------------------
#
#*******************************************************************************************************************************************************************************************
def check_pckt(conn_socket, in_msg, file_ptr):
    '''Checks the UDP checksum and sequence no and if proper the packet is ACKed'''
    global exp_in_msg_seq_no
    in_msg_split = in_msg.split(sep)
    in_msg_seq_no = in_msg_split[0]
    in_msg_checksum = in_msg_split[1]
    in_msg_data_id = in_msg_split[2]
    in_msg_data = in_msg_split[3]

    checksum_local = 'checksum'
    
    if checksum_local == in_msg_checksum:                                                  # if checksum matches the received checksum
        ack_id_field = '1010101010101010'
        zero_field = '0000000000000000'
        out_msg = in_msg_seq_no + sep + zero_field + sep + ack_id_field
        if int(in_msg_seq_no, 2) == exp_in_msg_seq_no:                                     # if sequence number matches the expected sequence number
            if in_msg_data == '':
                out_msg = out_msg.encode()
                conn_socket.sendto(out_msg,clientAddress)
                file_ptr.close()
                conn_socket.close()
            else:
                server_reply_write(conn_socket, in_msg_seq_no, file_ptr, in_msg_data)             # reply to client and write the data onto file
                exp_in_msg_seq_no += len(in_msg_data)
        else:
            out_msg = out_msg.encode()
            conn_socket.sendto(out_msg,clientAddress)
    else:
        print("ERROR::xxx::Checksum doesn't match. Received a corrupted packet::xxx::ERROR")
        return False
    return True

#*******************************************************************************************************************************************************************************************
#
#--------------- P R O B A B I L I S T I C    L O S S    S E R V I C E----------------------------------------------------------------------------------------------------------------------
#
#*******************************************************************************************************************************************************************************************
def loss_service(drop_prob):
    '''Generates random value between 0 and 1. If generated random value greater than user input then processing is done''' 
    # rand_prob = 1.1
    rand_prob = random.random()
    if rand_prob < drop_prob:
        return False
    else:
        return True

#*******************************************************************************************************************************************************************************************
#
#--------------- E X E C U T I O N     O F    M A I N    C O D E---------------------------------------------------------------------------------------------------------------------------------------------------------
#
#*******************************************************************************************************************************************************************************************

server_port = int(sys.argv[1])
file_name = sys.argv[2]
drop_prob = float(sys.argv[3])
exp_in_msg_seq_no = 0
file_ptr = open(file_name, 'wb')
sep ='###'
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server = socket.gethostbyname(socket.gethostname())
server_port = 7735                                                                           # common welcome port on all RFC servers
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((server, server_port))                                                        # binding this socket to the welcome port
server_socket.settimeout(500)
#in_msg, clientAddress = server_socket.recvfrom(1500)
while True:
    in_msg, clientAddress = server_socket.recvfrom(1500)
    server_socket.settimeout(500)
    process_flag = loss_service(drop_prob)
    in_msg = in_msg.decode()
    msg = in_msg.split(sep)
    if process_flag:
        check_pckt(server_socket, in_msg, file_ptr)
    else:
        print("Packet loss, sequence number = ",int(msg[0], 2))


        
    
import os
import time
import random
import sqlite3

DB_PATH = "sqlite3.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
#Select all unique tag epc from athletes
query = "SELECT DISTINCT tag_epc FROM athlete"
cursor.execute(query)
hex_strings = [row[0] for row in cursor.fetchall() if row[0] is not None]
conn.close()
already_chosen = []

nRandomReadings = int(input("Digite a quantidade de tags por rodada: \n"))

def checksum(packet):
    u_sum = sum(packet)  # Soma todos os elementos da lista
    u_sum = (~u_sum & 0xFF) + 1  # Calcula o complemento de um e adiciona 1
    return u_sum

def string_to_bytes(s):
    # Quebrar a string em pares de dois caracteres
    byte_pairs = [s[i:i+2] for i in range(0, len(s), 2)]
    
    # Transformar os pares de caracteres hexadecimais em bytes
    byte_array = bytes.fromhex(''.join(byte_pairs))
    
    return byte_array

def create_packet(*args):
    
    packet = bytearray()
    for arg in args:
        packet.append(arg)

    packet.append(checksum(packet))
    return packet
        
def error(cmd, error_code):
    print("ERROR")
    return create_packet(0xA0, 0x04, 0x00, cmd, error_code)

def sucess(command):
    print(f"Comando {hex(command)} executado com sucesso")
    return create_packet(0xA0, 0x04, 0x00, command, 0x10)

def reset(reader):
    if random.randint(0, 10) < 3:
        return error(0x70 ,0x20)
    print("Restarting reader, please wait...")
    time.sleep(2)
    #playsound.playsound("buzz.mp3")
    reader.close()
    return sucess(0x70)
    
def set_uart_baudrate(reader, packet):
    baudrate = packet[4]
    if baudrate == 0x03:
        baudrate = 38400
    elif baudrate == 0x04:
        baudrate = 115200
    else:
        return error(0x71, 0x11)
    reader.baudrate = baudrate
    print("Baudrate set to: ", baudrate)
    return sucess(0x71)

def get_firmware_version(reader):
    print("Get firmware version")
    major = reader.firmware_version.split(".")[0]
    minor = reader.firmware_version.split(".")[1]
    major = int(major)
    minor = int(minor)

    
    return (create_packet(0xA0, 0x05, 0x0A, 0x72, major, minor))

def get_output_power(reader):
    return (create_packet(0xA0, 0x04, 0x00, 0x77, 0x00))
def set_reader_identifier(reader, packet):
    identifier = packet[4:16]
    identifier = str(identifier.hex()).upper()
    print("Set reader identifier")
    print("Identifier: ", identifier)
    reader.identifier = identifier
    return sucess(0x67)

def get_reader_identifier(reader):
    print("Get reader identifier:", reader.identifier)
    byte_data = string_to_bytes(reader.identifier)
    
    return create_packet(0xA0, 0x0F, 0x00, 0x68, *byte_data)

#0x74
def set_work_antenna(reader, packet):
    antenna_id = packet[4]
            
    match antenna_id:
        case 0x00:
            reader.working_antenna = 0
        case 0x01:
            reader.working_antenna = 1
        case 0x02:
            reader.working_antenna = 2
        case 0x03:
            reader.working_antenna = 3
        case _:
            return error(0x74, 0x11)
        
    print("Set working antenna: ", reader.working_antenna)
    return sucess(0x74)


def fast_switch_ant_inventory(reader, packet):
    return create_random_packets()
    return create_packet(0xA0, 0x13, 0x00, 0x8A, 0x32, *b'\x30\x00', *tag, 0x5A, 0x3F)
    
    
def create_random_packets():
    
    base_packet = bytearray(b'\xa0\x13\x01\x8a\xec0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00e\x893\x85')
    packets = []
    n_readings = nRandomReadings
    chosen_tags = random.choices(hex_strings, k=n_readings)
    #chosen_tags = [hex_strings[0]] Uncomment for a single tag only
    
    print("Chosen tags: ", chosen_tags)
    #time.sleep(0.5)
    
    for tag_hex in chosen_tags:
        #tag_hex = "726900" # Descomentar para forçar Bug de length de pacote.
        packet_min_len = 9-1 # Actual len, subtracting the checksum because it will be appended at the end.
        head_min_len = packet_min_len-1 # Length to be inside packet
        tag_len = len(tag_hex)//2 # length in bytes len
        
        tag_epc = bytearray.fromhex(tag_hex)
        packet = [0]*(packet_min_len+tag_len)
        length = head_min_len + tag_len

        packet[0] = 0xA0
        packet[1] = length
        packet[2] = 0x01
        packet[3] = 0x8A
        packet[4] = 0xFC
        packet[5] = 0x00
        packet[6] = 0xFF
        packet[7:7+tag_len] = tag_epc
        packet[-1] = 0x00
        packet.append(checksum(packet))
        packets.append(bytearray(packet))
    return packets



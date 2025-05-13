import binascii
import struct
import crcmod
import time
import serial.tools.list_ports

def find_com_port():
    vid_pid = "10C4:EA60"
    serial_number = "0001"
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if vid_pid:
            if vid_pid not in port.hwid:
                continue
        if serial_number:
            if serial_number not in port.hwid:
                continue
        return port.device
    return None

# Função para se conectar à porta serial
def connect_to_serial():
    baudrate = 57600
    porta = find_com_port()
    timeout = 1
    
    try:
        ser = serial.Serial(porta, baudrate, timeout=timeout)
        print(f"Conectado à {porta} com baudrate {baudrate}")
        return ser
    except serial.SerialException as e:
        print(f"Erro ao conectar na porta {porta}: {e}")
        raise e

# Função para enviar o comando e receber a resposta
def send_command(ser, packet):
    try:
        # Enviar o packet
        ser.write(packet)
        print(f"Packet enviado: {packet.hex()}")

        # Aguardar e ler a resposta, se houver
        time.sleep(0.5)  # Pode ajustar conforme a resposta do dispositivo
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"Resposta recebida: {response.hex()}")
            return response
        else:
            print("Nenhuma resposta recebida.")
    except serial.SerialTimeoutException:
        print("Timeout ao enviar comando.")
    except Exception as e:
        print(f"Erro ao enviar comando: {e}")
        
def readTag(epc, pwd, ser):
    
    address = 0x00     # Endereço
    cmd = 0x02         # Comando
    
    #Data Package
    enum = 0x06 # ENum: comprimento do EPC em unidades de word
    epc_bytes  = binascii.unhexlify(epc)
    epc_words = struct.unpack('>6H', epc_bytes)  # EPC: número EPC a ser operado
    mem = 0x01       # Mem: 0x00 para Password, 0x01 para EPC, 0x02 para TID, 0x03 para User memory
    word_ptr = 0x01    # WordPtr: endereço de início para leitura
    num = 0x06         # Num: número de 16 bits a serem lidos (1 a 119)
    pwd = 0x00000000  # Pwd: senha de acesso (4 bytes) ou zero se nao tiver senha
    mask_adr = 0x00    # MaskAdr: endereço inicial para a máscara
    mask_len = 0x00    # MaskLen: comprimento da máscara!!!!!!!!!!!!!!!!

     # Criar o campo Data[]
    data = struct.pack('>B6HBBBIBB', enum, *epc_words, mem, word_ptr, num, pwd, mask_adr, mask_len)
    packet = create_packet(data, address, cmd)
    
    return send_command(ser, packet)
    
    
def create_packet(data, *args):
    packet = bytearray()
    length = len(data) + 4  # Tamanho de Data[] mais 4 bytes (Len, Adr, Cmd, CRC)
    packet.append(length)
    for arg in args:
        packet.append(arg)
    for byte in data:
        packet.append(byte)
    
    # Calcular CRC
    lsb_crc, msb_crc = get_crc16(packet)
    
    # Adicionar os valores de CRC ao pacote
    packet.append(lsb_crc)
    packet.append(msb_crc)
    
    return bytearray(packet)

def get_crc16(data):
    crc = crc16_cal(data)
    
    # Extrai o LSB e o MSB
    lsb_crc = crc & 0xFF        # 8 bits menos significativos
    msb_crc = (crc >> 8) & 0xFF # 8 bits mais significativos
    
    return lsb_crc, msb_crc

def crc16_cal(packet):

    # Definições do preset e polinômio
    PRESET_VALUE = 0xFFFF
    POLYNOMIAL = 0x11021  # Polinômio refletido de 0x1021 (CRC-16-CCITT)
    #POLYNOMIAL = 0x8408

    # Função de CRC usando crcmod
    crc16_func = crcmod.mkCrcFun(POLYNOMIAL, initCrc=PRESET_VALUE, xorOut=0x0000, rev=True)
    crc = crc16_func(packet)

    # Computa o valor CRC
    return crc
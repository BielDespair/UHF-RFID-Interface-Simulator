import queue
import socket
import time
import responses
import random

roundInterval: float = float(input("Digite o intervalo entre rounds de tags (Exemplos: 0.1 para 1/10 de um segundo, 0.5 para meio segundo, 1 para um segundo, 2 para dois segundos, 2.5 para dois segundos e meio): \n"))

class Reader():
    def __init__(self, ip='127.0.0.1', port=4001, baudrate=115200):
        #Propriedades de rede
        self.ip = ip
        self.port = port
        self.baudrate = baudrate
        self.client_socket = None
        self.client_adress = None
        self.timeout = 15
        
        #Threading
        self.queue = queue.Queue(maxsize=20)
        self.running = False
        
        #Propriedades do leitor
        self.firmware_version = '9.7'
        self.buzzer_behavior = 0
        self.identifier = 'A1B2C3D4F5A1B2C3D4F5A1B2'
        self.antenna_slots = 2
        self.working_antenna = 0
        
        #Cache
        self.cache = {'count': 0, 'lastCmd': None}
        
        #Debug
        self.totalReceived = 0
        self.totalSent = 0
        self.sentMap = {}
        
    #Server methods
    def start(self):
        # Crate TCP/IP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.server_socket.settimeout(self.timeout)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(1)
        self.running = True
        print(f"Server listening on {self.ip}:{self.port}")
        

    def run_server(self):
        try:
            while self.running:                
                self.accept_client()
                if self.client_connected:
                    self.receive_client_command()
        except (TimeoutError, KeyboardInterrupt):
            print("Server interrupted")
        except Exception as e:
            print("Unexpected error:", e)
        finally:
            self.close()
            
        
    def accept_client(self):
        try:
            self.client_socket, self.client_adress = self.server_socket.accept()
            self.client_connected = True
        except Exception as e:
            print(e)
            self.client_connected = False
        print(f"Client connected from {self.client_adress}")
        
    def receive_client_command(self):
        while self.client_connected:
            try:
                # Read client command
                data = self.client_socket.recv(1024)
                if not data:
                    self.client_connected = False
                    break
                self.process_client_command(data)
            except socket.error as e:
                print(e)
                self.client_connected = False
                break

    def close(self):
        if self.client_socket:
            self.client_socket.close()
        self.server_socket.close()
        self.client_connected = False
        self.running = False
        print("Server closed")
        
        print("Final Reader attributes:")
        print("Firmware version: ", self.firmware_version)
        print("Buzzer behavior: ", self.buzzer_behavior)
        print("Identifier: ", self.identifier)
        
        print(f"Received/Sented: {self.totalReceived}/{self.totalSent}")
        print(f"Sented tag count")
        total = 0
        for key, value in self.sentMap.items():
            print(key, value)
            total += value
        print("Total sented tags: ", total)

        
        
    #Protocol methods
    def process_client_command(self, packet):
        print("Pacote recebido: " + ' '.join(f'{byte:02x}' for byte in packet))
        if not packet: 
            return
        cmd = packet[3]
        assert packet[-1] == responses.checksum(packet[:-1])
        
        print("Cmd received: ", (hex(cmd)))
        self.totalReceived += 1
        match cmd:
            case 0x00:
                self.restart()
                response = responses.sucess(cmd)
            case 0x70:
                response = responses.reset(self)
            case 0x71:
                response = responses.set_uart_baudrate(self, packet)
            case 0x72:
                response = responses.get_firmware_version(self)
            
            case 0x74:
                response = responses.set_work_antenna(self, packet)
            case 0x67:
                print("Set reader identifier packet: ", packet)
                response = responses.set_reader_identifier(self, packet)
            case 0x68:
                response = responses.get_reader_identifier(self)
            case 0x66:
                print("Get output power packet")
                response = responses.get_output_power(self)
            case 0x8b:
                response = responses.customized_session_target_inventory(self, packet)
            case 0x8a:
                response = responses.fast_switch_ant_inventory(self, packet)
            case _:
                response = responses.error(cmd, 0x11)
        response = [response] if type(response) != list else response
        if response:
            for resp in response:
                self.client_socket.sendall(resp)
                self.totalSent += 1
                print("Packet sended: ", end="")
                print(' '.join(f'{byte:02x}' for byte in resp))
                if cmd == 0x8a:
                    tag = ''.join(f'{byte:02x}' for byte in resp[7:19])
                    print("The tag is: ", tag)
                    if tag in self.sentMap:
                        self.sentMap[tag] += 1
                    else:
                        self.sentMap[tag] = 1
            time.sleep(roundInterval)
            if cmd == 0x8a:
                print("Sending inventory finished")
                inventory_finished = [0xA0, 0x0A, 0x00, 0x8B, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xAA]
                self.client_socket.sendall(bytes(inventory_finished))
        else:
            pass
            self.client_socket.sendall(responses.error(cmd, 0x11))
            
        self.last_cmd = cmd
        
        

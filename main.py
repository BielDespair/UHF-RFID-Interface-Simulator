from reader import Reader


reader = Reader(ip='127.0.0.1', port=8080, baudrate=115200)
reader.start()


reader.run_server()
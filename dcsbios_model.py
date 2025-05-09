import json
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread, Slot
import socket
from dcsbios import ProtocolParser, IntegerBuffer, StringBuffer

class BiosModel(QObject):
    data_updated = Signal(str, int)
    
    def __init__(self, config_path="dcs_params.json"):
        super().__init__()
        self.parser = ProtocolParser()
        self.parameters_config = self._load_config(config_path)
        self.parameters = {p['name']: 0 for p in self.parameters_config}
        self._setup_handlers()
        self.sock = None
        self.running = False
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self._run)

    def _load_config(self, config_path):
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Config file {config_path} not found")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Конвертируем hex-строки в числа
            for param in config:
                param['address'] = int(param['address'], 16)
                param['mask'] = int(param['mask'], 16)
                if 'length' in param:
                    param['length'] = int(param['length'])
                    
            return config
            
        except Exception as e:
            print(f"Error loading config: {e}")
            return []

    def _setup_handlers(self):
        for param in self.parameters_config:
            if param['type'] == 'int':
                IntegerBuffer(
                    parser=self.parser,
                    address=param['address'],
                    mask=param['mask'],
                    shift_by=param['shift_by'],
                    callback=lambda val, p=param: self._handle_data(p['name'], val)
                )
            elif param['type'] == 'str':
                StringBuffer(
                    parser=self.parser,
                    address=param['address'],
                    length=param.get('length', 32),
                    callback=lambda s, p=param: self._handle_data(p['name'], s)
                )

    def _handle_data(self, param_id, value):
        if param_id in self.parameters:
            self.parameters[param_id] = value
            self.data_updated.emit(param_id, value)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        print("Остановка потока...")
        self.running = False
        self.thread.quit()  # Завершаем поток
        self.thread.wait()  # Ожидаем завершения потока
        print("Поток завершен")

    @Slot()
    def _run(self):
        print("Поток запущен")
        # Настройка сетевого подключения
        MCAST_GRP = '239.255.50.10'
        MCAST_PORT = 5010
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', MCAST_PORT))

        # Подписка на мультикаст
        mreq = socket.inet_aton(MCAST_GRP) + socket.inet_aton('0.0.0.0')
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Устанавливаем таймаут для сокета (например, 100 мс)
        self.sock.settimeout(0.1)

        print("Соединение с DCS-BIOS установлено")

        try:
            while self.running:
                try:
                    data, _ = self.sock.recvfrom(1024)
                    for byte in data:
                        self.parser.processByte(byte)
                except socket.timeout:
                    continue  # Продолжаем цикл, если таймаут
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            if self.sock:
                self.sock.close()  # Закрываем сокет только здесь
                print("Сокет закрыт")
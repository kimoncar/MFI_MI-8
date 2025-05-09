from PySide6.QtWidgets import QWidget
from gauges.variometer_vr30 import GaugeWidgetPng

class MainWindow(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.gauges = {}  # Словарь для хранения приборов
        self.initUI()
        self.connect_model_signals()

    def initUI(self):
        self.setFixedSize(1024, 768)
        self.setStyleSheet("background-color: black;")

        # Прибор png
        self.gauge_png = GaugeWidgetPng("ui/scale.png", "ui/row.png", size=250)
        self.gauge_png.setParent(self)
        self.gauge_png.move(400, 50)
        self.gauge_png.set_value(65535/2)

    def connect_model_signals(self):
        """Подключает сигналы модели к обновлению приборов"""
        self.model.data_updated.connect(self.update_gauge)

    #def map_range(self, value, from_low, from_high, to_low, to_high):
    #    return (value - from_low) * (to_high - to_low) / (from_high - from_low) + to_low

    def update_gauge(self, param_id, value):
        """Обновляет прибор при получении сигнала"""
        if param_id == "VARIOMETER_L":
            self.gauge_png.set_value(value)
            #print(f"VARIOMETER_L: {value}")
        
        if param_id == "LEFT_ENGINE_RPM":
            #self.gauge_png.set_value(value)
            print(f"LEFT_ENGINE_RPM: {value}")

    def closeEvent(self, event):
        """Переопределяем метод закрытия окна"""
        print("Закрытие окна...")
        self.model.stop()  # Останавливаем поток
        event.accept()  # Подтверждаем закрытие
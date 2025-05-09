from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QPixmap, QTransform, QFont
from PySide6.QtCore import Qt, QPoint
import bisect

class GaugeWidgetPng(QWidget):
    def __init__(self, scale_path, needle_path, size=200, parent=None):
        super().__init__(parent)
        self.scale_path = scale_path
        self.needle_path = needle_path
        self.size = size

        # Калибровочные точки в формате (raw_value, angle, display_value)
        self.calibration_points = [
            (0,      -180,  -30),
            (9082,   -140,  -20),
            (18580,  -80,   -10),
            (25737,  -40,   -5),
            (32767,  0,     0),
            (40406,  40,    5),
            (46975,  80,    10),
            (56125,  140,   20),
            (65535,  180,   30)
        ]
        
        # Отсортированные списки для бинарного поиска
        self.sorted_raw = [p[0] for p in self.calibration_points]
        self.sorted_angles = [p[1] for p in self.calibration_points]
        self.sorted_values = [p[2] for p in self.calibration_points]

        self.rotation_center = QPoint(size//2, size//2)
        self.initUI()

    def initUI(self):
        self.setFixedSize(self.size, self.size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Шкала
        self.scale_label = QLabel(self)
        scale_pix = QPixmap(self.scale_path).scaled(
            self.size, self.size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.scale_label.setPixmap(scale_pix)
        self.scale_label.setGeometry(0, 0, self.size, self.size)

        # Текстовое значение
        self.value_label = QLabel(self)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("color: #5ec5ee; font: bold 26px Arial; background: transparent;")
        self.value_label.setGeometry(0, 0, self.size, self.size)

        # Стрелка
        self.needle_label = QLabel(self)
        self.needle_pixmap = QPixmap(self.needle_path).scaled(
            self.size, self.size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.needle_label.setPixmap(self.needle_pixmap)
        self.needle_label.setGeometry(0, 0, self.size, self.size)
        self.needle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def interpolate(self, raw_value):
        """Интерполяция между калибровочными точками"""
        pos = bisect.bisect_left(self.sorted_raw, raw_value)
        
        if pos == 0:
            return self.sorted_angles[0], self.sorted_values[0]
        if pos == len(self.sorted_raw):
            return self.sorted_angles[-1], self.sorted_values[-1]
        
        # Линейная интерполяция
        prev_raw = self.sorted_raw[pos-1]
        next_raw = self.sorted_raw[pos]
        prev_angle = self.sorted_angles[pos-1]
        next_angle = self.sorted_angles[pos]
        prev_value = self.sorted_values[pos-1]
        next_value = self.sorted_values[pos]
        
        ratio = (raw_value - prev_raw) / (next_raw - prev_raw)
        angle = prev_angle + ratio * (next_angle - prev_angle)
        value = prev_value + ratio * (next_value - prev_value)
        
        return angle, value

    def set_value(self, raw_value):
        # Получаем угол и значение
        angle, display_value = self.interpolate(raw_value)
        
        # Поворот стрелки
        transform = QTransform()
        transform.translate(self.rotation_center.x(), self.rotation_center.y())
        transform.rotate(angle)
        transform.translate(-self.rotation_center.x(), -self.rotation_center.y())
        
        rotated_pixmap = self.needle_pixmap.transformed(
            transform, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Коррекция позиции
        x_offset = (self.size - rotated_pixmap.width()) // 2
        y_offset = (self.size - rotated_pixmap.height()) // 2
        
        self.needle_label.setPixmap(rotated_pixmap)
        self.needle_label.setGeometry(
            x_offset,
            y_offset,
            rotated_pixmap.width(),
            rotated_pixmap.height()
        )

        # Обновление текста
        self.value_label.setText(f"{display_value:.1f}")
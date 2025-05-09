import sys
from PySide6.QtWidgets import QApplication
from dcsbios_model import BiosModel
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = BiosModel()
    window = MainWindow(model)
    window.show()
    model.start()

    app.aboutToQuit.connect(model.stop)
    sys.exit(app.exec())
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QTextEdit, QPushButton, QLineEdit, QPlainTextEdit, \
    QComboBox, QFileDialog, QTableWidget, QTableWidgetItem, QAbstractItemView, QCalendarWidget, QRadioButton, QGridLayout
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QPainter, QPen, QBrush, QTextCursor
from PyQt5.QtCore import Qt, QObject, QDate

import time
import ast
import json
import logging
from datetime import datetime
import sys
import pandas as pd
import os

INIT_BROKER = "IBKR"
INIT_PRODUCT = "AAPL"
INIT_DIRECTION = "LONG"
INIT_ORDER_SIZE = "100"
INIT_ADDITIONAL_ORDER_SIZE = "30"
INIT_TP_LEVEL = "1.5"
INIT_NUM_ADD_ORDER = "3"
INIT_PRICE_DOWN_LEVEL = "1.5"


class MessageBox(QWidget):
    countChanged = pyqtSignal(str)

    def __init__(self, message):
        self.message = message
        super(MessageBox, self).__init__()
        self.setGeometry(300, 300, 320, 222)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.backgroundLabel = QLabel(self)
        self.backgroundLabel.setGeometry(0, 0, 320, 222)
        self.backgroundLabel.setStyleSheet(
            "background-image : url(res/messagebox.png); background-repeat: no-repeat;")

        self.messageContent = QLabel(self)
        self.messageContent.setText(self.message)
        self.messageContent.setGeometry(34, 82, 280, 40)
        self.messageContent.setStyleSheet("color:white; font-size:16px;")
        self.saveButton = QPushButton(self)
        self.saveButton.setText("OK")
        self.saveButton.setGeometry(120, 144, 100, 40)
        self.saveButton.clicked.connect(self.OnClose)
        self.saveButton.setStyleSheet(
            "background:#21ce99; border-radius:8px;color:white; font-size:18px; ")
        self.closeBtn = QPushButton(self)
        self.closeBtn.setGeometry(295, 5, 20, 20)
        self.closeBtn.setStyleSheet(
            "background-image : url(res/close3.png);background-color: transparent; ")
        self.closeBtn.clicked.connect(self.OnClose)

    def OnClose(self):
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


class QTextEditLogger(logging.Handler, QObject):
    appendPlainText = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        QObject.__init__(self)

        self.openDialog = QFileDialog(parent)

        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.widget.setGeometry(80, 280, 480, 470)
        try:
            _date = datetime.now().date()
            f = open(f"loggers/activity-log-{_date}.log", "r")
            logs = f.read()
            f.close()
        except:
            logs = ""
        self.widget.setPlainText(logs)
        self.widget.setStyleSheet(
            "background-color: transparent; border-radius: 1px; color:white; font-size:12px;")
        self.appendPlainText.connect(self.widget.appendPlainText)
        self.widget.moveCursor(QTextCursor.End)
        self.widget.ensureCursorVisible()

        self.clearLogBtn = QPushButton(parent)
        self.clearLogBtn.setGeometry(550, 220, 30, 30)
        self.clearLogBtn.setStyleSheet(
            "background-image : url(res/delete-mini.png);background-color: transparent;width:30px;height:30px; background-repeat: no-repeat;")
        self.clearLogBtn.clicked.connect(self.clear_log)

        self.saveLogBtn = QPushButton(parent)
        self.saveLogBtn.setGeometry(510, 220, 30, 30)
        self.saveLogBtn.setStyleSheet(
            "background-image : url(res/save-mini2.png);background-color: transparent;width:30px;height:30px; background-repeat: no-repeat;")
        self.saveLogBtn.clicked.connect(self.save_log)

    def save_log(self):
        path, filter = QFileDialog.getSaveFileName()
        if not path:
            return

        self._save_log_to_path(path)

    def _save_log_to_path(self, path):
        text = self.widget.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)
            logging.getLogger().debug(
                f"The logs are saved to the file - {path}")

        except Exception as e:
            logging.getLogger().debug(e)

    def clear_log(self):
        _date = datetime.now().date()
        f = open(f"loggers/activity-log-{_date}.log", "w")
        f.write("")
        f.close()

        self.widget.setPlainText("")

    def emit(self, record):
        msg = self.format(record)
        self.appendPlainText.emit(msg)


class MainThread(QThread):
    countChanged = pyqtSignal(str)

    def __init__(self, params, parent=None):
        QThread.__init__(self, parent)
        self.params = params
        self.conn_state = False

    def run(self):
        self.conn_state = True
        state_msg = {"connection": self.conn_state}
        self.countChanged.emit(str(state_msg))
        try:
            with open("settings/app_status.txt", "w") as f:
                f.write("ON")
                f.close()
        except Exception as e:
            print(e)

        time.sleep(1)
        print("App started!")
        logging.getLogger().debug("App started!")

    def stop(self):
        self.conn_state = False
        try:
            with open("settings/app_status.txt", "w") as f:
                f.write("OFF")
                f.close()
        except Exception as e:
            print(e)

        time.sleep(1)
        print("App stopped!")
        logging.getLogger().debug("App stopped!")
        self.terminate()


class MainWindow(QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setGeometry(250, 30, 640, 820)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Trader")
        self.start_flag = 1

        try:
            with open("settings/broker", "r") as f:
                self.broker = f.readlines()[0]
        except Exception as e:
            print(e)
            self.broker = INIT_BROKER
        print(self.broker)

        try:
            with open("settings/params.json", "r") as f:
                data = json.load(f)
        except Exception as e:
            print(e)
            data = {}
        print(data)

        if data:
            self.params = data
        else:
            self.params = {
                "product": INIT_PRODUCT,
                "direction": INIT_DIRECTION,
                "init_size": INIT_ORDER_SIZE,
                "add_size": INIT_ADDITIONAL_ORDER_SIZE,
                "tp_level": INIT_TP_LEVEL,
                "num_add_order": INIT_NUM_ADD_ORDER,
                "price_down_level": INIT_PRICE_DOWN_LEVEL
            }

        self.backgroundLabel = QLabel(self)
        self.backgroundLabel.setGeometry(0, 0, 640, 820)
        self.backgroundLabel.setStyleSheet(
            "background-image : url(res/main.png); background-repeat: no-repeat;")
        font = QFont()
        font.setPointSize(20)
        self.closeBtn = QPushButton(self)
        self.closeBtn.setGeometry(580, 25, 30, 30)
        self.closeBtn.setStyleSheet(
            "background-image : url(res/close2.png);background-color: transparent;")
        self.closeBtn.clicked.connect(self.onClose)

        self.optionBtn = QPushButton(self)
        self.optionBtn.setGeometry(520, 20, 40, 40)
        self.optionBtn.setStyleSheet(
            "background-image : url(res/option.png);background-color: transparent;")
        self.optionBtn.clicked.connect(self.OpenSetting)

        self.radioIB = QRadioButton(self)
        self.radioIB.setStyleSheet(
            "QRadioButton{background-color : #24202a; font-size: 18px; color: white;}")
        if self.broker == "IBKR":
            self.radioIB.setChecked(True)
            self.radioIB.setStyleSheet(
                "QRadioButton{background-color : #24202a; font-size: 18px; color: red;}")
        self.radioIB.setText("IBKR")
        self.radioIB.broker = "IBKR"
        self.radioIB.setGeometry(60, 120, 120, 40)
        self.radioIB.clicked.connect(self.onRadioClicked)

        self.radioIG = QRadioButton(self)
        self.radioIG.setText("IG.com")
        self.radioIG.broker = "IG"
        self.radioIG.setStyleSheet(
            "QRadioButton{background-color : #24202a; font-size: 18px; color: white;}")
        if self.broker == "IG":
            self.radioIG.setChecked(True)
            self.radioIG.setStyleSheet(
                "QRadioButton{background-color : #24202a; font-size: 18px; color: red;}")
        self.radioIG.setGeometry(180, 120, 120, 40)
        self.radioIG.clicked.connect(self.onRadioClicked)

        self.startBtn = QPushButton(self)
        self.startBtn.setGeometry(415, 115, 180, 48)
        self.startBtn.setText("Start")
        self.startBtn.setStyleSheet(
            "background-color: #db1222; border-radius: 16px; color:white; font-size:20px;")
        self.startBtn.clicked.connect(self.onStart)

        self.logTextBox = QTextEditLogger(self)
        self.logTextBox.setFormatter(
            logging.Formatter(
                '\n===== %(asctime)s %(module)s =====\n\n%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
        logging.getLogger().addHandler(self.logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

        # log to file
        _date = datetime.now().date()
        fh = logging.FileHandler(f'loggers/activity-log-{_date}.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter(
                '\n===== %(asctime)s %(module)s =====\n\n%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'))
        logging.getLogger().addHandler(fh)

    def onRadioClicked(self):
        if self.start_flag == 0:
            self.msg = MessageBox("You can't edit broker when bot is on!")
            self.msg.show()
            return True

        radioButton = self.sender()
        if radioButton.isChecked():
            if radioButton.broker == "IBKR":
                self.radioIB.setStyleSheet(
                    "QRadioButton{background-color : #24202a; font-size: 18px; color: red;}")
                self.radioIG.setStyleSheet(
                    "QRadioButton{background-color : #24202a; font-size: 18px; color: white;}")
            else:
                self.radioIB.setStyleSheet(
                    "QRadioButton{background-color : #24202a; font-size: 18px; color: white;}")
                self.radioIG.setStyleSheet(
                    "QRadioButton{background-color : #24202a; font-size: 18px; color: red;}")

            self.broker = radioButton.broker
            try:
                with open("settings/broker", "w") as f:
                    f.write(self.broker)
            except Exception as e:
                print(f"{self.broker} - write to a file issue - {e}")
            print("Selected Broker is %s" % (radioButton.broker))
            logging.getLogger().debug(
                f"Selected Broker is {radioButton.broker}")

    def onStart(self):
        if self.start_flag == 1:
            try:
                self.main_thread = MainThread(params=self.params)
                self.main_thread.countChanged.connect(self.onProcess)
                self.main_thread.start()
                self.radioIB.setCheckable(False)
                self.radioIG.setCheckable(False)

            except Exception as e:
                self.msg = MessageBox(e)
                self.msg.show()
        else:
            self.startBtn.setText("Start")
            self.start_flag = 1
            self.radioIB.setCheckable(True)
            self.radioIG.setCheckable(True)
            self.main_thread.stop()

    def onClose(self):
        global app
        if self.start_flag == 0:
            self.main_thread.stop()
        app.quit()

    def onProcess(self, value):
        msg = ast.literal_eval(value)
        if not msg["connection"]:
            self.main_thread.stop()
            self.start_flag = 1
            self.radioIB.setCheckable(True)
            self.radioIG.setCheckable(True)
            self.msg = MessageBox("Connection failed!!!")
            self.msg.show()
        else:
            self.start_flag = 0
            self.radioIB.setCheckable(False)
            self.radioIG.setCheckable(False)
            self.startBtn.setText("Stop")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)

    def SettingsUpdate(self, param_string):
        params = ast.literal_eval(param_string)
        self.params = params

        print(params)

    def OpenSetting(self):
        try:
            self.SW = SettingsWindow(self.params, self.start_flag)
            self.SW.countChanged.connect(self.SettingsUpdate)
            self.SW.show()
        except Exception as e:
            print(e)


class SettingsWindow(QWidget):
    countChanged = pyqtSignal(str)

    def __init__(self, params, start_flag):

        self.params = params
        self.start_flag = start_flag

        super(SettingsWindow, self).__init__()

        self.setFixedSize(650, 820)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background:#0b0b0b;")
        setting_icon = QPushButton(self)
        setting_icon.setGeometry(20, 30, 40, 40)
        setting_icon.setStyleSheet(
            "background-image : url(res/option.png);background-color: transparent; ")
        self.titleText = QLabel(self)
        self.titleText.setText("Parameters Module")
        self.titleText.setGeometry(80, 10, 300, 80)
        self.titleText.setStyleSheet("color:white; font-size:28px;border:none; font-family: Arial, Helvetica, "
                                     "sans-serif;")

        self.productLabel = QLabel(self)
        self.productLabel.setGeometry(80, 150, 200, 40)
        self.productLabel.setText("Instrument:")
        self.productLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.productEdit = QLineEdit(self)
        self.productEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;padding-left:5px;")
        self.productEdit.setGeometry(350, 150, 200, 40)
        self.productEdit.setAlignment(Qt.AlignLeft)
        self.productEdit.setText(self.params["product"])
        self.productEdit.setReadOnly(True)

        self.directionLabel = QLabel(self)
        self.directionLabel.setGeometry(80, 210, 200, 40)
        self.directionLabel.setText("Direction:")
        self.directionLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.direction_combo = QComboBox(self)
        self.directions = ['LONG', 'SHORT']
        for direction in self.directions:
            self.direction_combo.addItem(direction)
        idx = self.directions.index(self.params["direction"])
        self.direction_combo.setCurrentIndex(idx)
        self.direction_combo.setStyleSheet(
            "background-color:#24202a;color:white;font-size:16px;border:none;padding-left:5px;")
        self.direction_combo.setGeometry(350, 210, 200, 40)

        self.currencyLabel = QLabel(self)
        self.currencyLabel.setGeometry(80, 290, 200, 40)
        self.currencyLabel.setText("Currency:")
        self.currencyLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.currencyEdit = QLineEdit(self)
        self.currencyEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;")
        self.currencyEdit.setGeometry(350, 290, 200, 40)
        self.currencyEdit.setAlignment(Qt.AlignCenter)
        self.currencyEdit.setText(self.params["currency"])
        self.currencyEdit.setReadOnly(True)

        self.sizeLabel = QLabel(self)
        self.sizeLabel.setGeometry(80, 350, 200, 40)
        self.sizeLabel.setText("Initial Order Size:")
        self.sizeLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.sizeEdit = QLineEdit(self)
        self.sizeEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;")
        self.sizeEdit.setGeometry(350, 350, 200, 40)
        self.sizeEdit.setAlignment(Qt.AlignCenter)
        self.sizeEdit.setText(self.params["init_size"])
        self.sizeEdit.setReadOnly(True)

        self.addOrderSizeLabel = QLabel(self)
        self.addOrderSizeLabel.setGeometry(80, 410, 200, 40)
        self.addOrderSizeLabel.setText("Additional Order Size:")
        self.addOrderSizeLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.addOrderSizeEdit = QLineEdit(self)
        self.addOrderSizeEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;")
        self.addOrderSizeEdit.setGeometry(350, 410, 200, 40)
        self.addOrderSizeEdit.setAlignment(Qt.AlignCenter)
        self.addOrderSizeEdit.setText(self.params["add_size"])
        self.addOrderSizeEdit.setReadOnly(True)

        self.addOrderNumLabel = QLabel(self)
        self.addOrderNumLabel.setGeometry(80, 490, 200, 40)
        self.addOrderNumLabel.setText("Number of Additional Orders:")
        self.addOrderNumLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.addOrderNumEdit = QLineEdit(self)
        self.addOrderNumEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;")
        self.addOrderNumEdit.setGeometry(350, 490, 200, 40)
        self.addOrderNumEdit.setAlignment(Qt.AlignCenter)
        self.addOrderNumEdit.setText(self.params["add_order_num"])
        self.addOrderNumEdit.setReadOnly(True)

        self.tpLabel = QLabel(self)
        self.tpLabel.setGeometry(80, 550, 200, 40)
        self.tpLabel.setText("Take Profit (%):")
        self.tpLabel.setStyleSheet("color:white; font-size:16px;border:none;")
        self.tpEdit = QLineEdit(self)
        self.tpEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;")
        self.tpEdit.setGeometry(350, 550, 200, 40)
        self.tpEdit.setAlignment(Qt.AlignCenter)
        self.tpEdit.setText(self.params["tp_level"])
        self.tpEdit.setReadOnly(True)

        self.priceDownLevelLabel = QLabel(self)
        self.priceDownLevelLabel.setGeometry(80, 610, 200, 40)
        self.priceDownLevelLabel.setText("Price Deviation (%):")
        self.priceDownLevelLabel.setStyleSheet(
            "color:white; font-size:16px;border:none;")
        self.priceDownLevelEdit = QLineEdit(self)
        self.priceDownLevelEdit.setStyleSheet(
            "background:#24202a; color:white; font-size:16px;border:none;")
        self.priceDownLevelEdit.setGeometry(350, 610, 200, 40)
        self.priceDownLevelEdit.setAlignment(Qt.AlignCenter)
        self.priceDownLevelEdit.setText(self.params["price_down_level"])
        self.priceDownLevelEdit.setReadOnly(True)

        self.editButton = QPushButton(self)
        self.editButton.setText("Edit")
        self.editButton.setGeometry(250, 740, 150, 40)
        self.editButton.clicked.connect(self.OnEditClick)
        self.editButton.setStyleSheet(
            "background:#db1222; border-radius:8px;color:white; font-size:16px;")

        self.confirmButton = QPushButton(self)
        self.confirmButton.setText("Save")
        self.confirmButton.setGeometry(450, 740, 150, 40)
        self.confirmButton.clicked.connect(self.OnShow)
        self.confirmButton.setStyleSheet(
            "background:#db1222; border-radius:8px;color:white; font-size:16px;")

        self.closeBtn = QPushButton(self)
        self.closeBtn.setGeometry(600, 30, 30, 30)
        self.closeBtn.setStyleSheet(
            "background-image : url(res/close2.png);background-color: transparent; ")
        self.closeBtn.clicked.connect(self.OnClose)

    def OnEditClick(self):
        read_only = False
        self.productEdit.setReadOnly(read_only)
        self.productEdit.setFocus()
        self.currencyEdit.setReadOnly(read_only)
        self.sizeEdit.setReadOnly(read_only)
        self.addOrderSizeEdit.setReadOnly(read_only)
        self.addOrderNumEdit.setReadOnly(read_only)
        self.tpEdit.setReadOnly(read_only)
        self.priceDownLevelEdit.setReadOnly(read_only)

    def OnShow(self):
        direction = self.directions[self.direction_combo.currentIndex()]
        params = {
            "product": self.productEdit.text(),
            "currency": self.currencyEdit.text(),
            "direction": str(direction),
            "init_size": self.sizeEdit.text(),
            "add_size": self.addOrderSizeEdit.text(),
            "add_order_num": self.addOrderNumEdit.text(),
            "tp_level": self.tpEdit.text(),
            "price_down_level": self.priceDownLevelEdit.text()
        }
        try:
            with open("settings/params.json", "w") as f:
                json.dump(params, f)
                logging.getLogger().debug(
                    f"New parameters:\n{params}\nFile path: {f.name}\n")
        except Exception as e:
            print(e)
            logging.getLogger().debug(f"Save parameters error:\n{e}\n")
        param_string = str(params)
        self.countChanged.emit(param_string)

        read_only = True
        self.productEdit.setReadOnly(read_only)
        self.productEdit.setFocus()
        self.currencyEdit.setReadOnly(read_only)
        self.sizeEdit.setReadOnly(read_only)
        self.addOrderSizeEdit.setReadOnly(read_only)
        self.addOrderNumEdit.setReadOnly(read_only)
        self.tpEdit.setReadOnly(read_only)
        self.priceDownLevelEdit.setReadOnly(read_only)
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.lightGray)
        painter.drawLine(0, 100, 650, 100)
        painter.drawLine(0, 690, 650, 690)

    def OnClose(self):
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


def main():
    import sys

    global app
    app = QApplication(sys.argv)
    MW = MainWindow()
    MW.show()
    sys.exit(app.exec_())

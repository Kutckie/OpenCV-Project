#default imports
import os
import sys
import configparser

#GUI dependencies
import PyQt5
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import (QCheckBox, QApplication, QWidget, QMainWindow, QLabel, QPushButton, QTextBrowser)

from pynput.keyboard import Key, Listener, KeyCode

#Importing script functions
from monitor_calibration import MonitorCalibration


class DBDScript(QMainWindow):
    def __ini__(self) -> None:
        super().__init__()
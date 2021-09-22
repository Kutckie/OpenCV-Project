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
from ctypes import c_bool, c_int

#GIL workaround
from threading import Thread
from multiprocessing.spawn import Process, Value, Array, freeze_support

#Importing script functions
from ASC_body import auto_skillcheck
from monitor_calibration import MonitorCalibration
from monitor_configuration import ConfigureMonitor
from target_acquisition import get_target_window_info




class DBDScript(QMainWindow):
    def __ini__(self) -> None:
        super().__init__()
        freeze_support

        #init configparser
        self.config = configparser.ConfigParser()

        #Init monitor calibration
        self.monitor_calibration = MonitorCalibration()

        #init parent gui
        self.init_gui()

        #functions toggle
        self.gti_toggle = Value(c_bool, 1)
        self.asc_toggle = Value(c_bool, 0)

        self.asc_keycode = None

        #Screen capture zones
        self.asc_monitor = None

        #Load config
        self.__load_config()

        #Sync variables, information about target window
        self.is_target_active = Value(c_bool, False) # true if target window foregrounded
        self.window_rect = Array(c_int, range(4)) # target window rect (from win32gui)

        #Starting necessary thread to get information about target window
        self.get_target_info_thread = Thread(target=get_target_window_info,
                                            args=(self.gti_toogle, self.is_target_active, 
                                            self.window_rect))
        
        self.get_target_info_thread.start()

    def init_gui(self) -> None:
        def __set_pointer_size(widget: PyQt5.QtWidgets, size: int) -> None:
            """Sets pointer size of text

            Args:
                widget (PyQt5.QtWidgets): like QCheckBox
                size (int): size of pointer (px)
            """
            font = QFont()
            font.setPointSize(size)
            widget.setFont(font)

        self.setFixedSize(520, 155)
        self.setWindowTitle("DBDasc")

        self.tabs = QTabWidget(self)
        self.tabs.resize(302, 155)
        self.asc_tab = QWidget()

        self.tabs.addTab(self.asc_tab, "Auto SkillCheck")

        #AutoSkillCheck Checkbox
        self.asc_checkbox = QCheckBox(self.asc_tab)
        __set_pointer_size(self.asc_checkbox, 10)
        self.asc_checkbox.setText("Auto SkillCheck")
        self.asc_checkbox.adjustSize()
        self.asc_checkbox.move(10, 10)

        #change Keybind
        self.asc_keybind_lbl = QLabel(self.asc_tab)
        __set_pointer_size(self.asc_keybind_lbl, 10)
        self.asc_keybind_lbl.setText("Change Keybind:")
        self.asc_keybind_lbl.adjustSize()
        self.asc_keybind_lbl.move(10, 40)
        
        self.asc_keybind_btn = QPushButton(self.asc_tab)
        self.asc_keybind_btn.resize(60, 25)
        self.asc_keybind_btn.move(115, 35)

        #calibrate monitor
        self.asc_monitor_lbl = QLabel(self.asc_tab)
        __set_pointer_size(self.asc_monitor_lbl, 10)
        self.asc_monitor_lbl.setText("Calibrate capture area: ")
        self.asc_monitor_lbl.adjustSize()
        self.asc_monitor_lbl.move(10, 70)
        
        self.asc_monitor_btn = QPushButton(self.asc_tab)
        self.asc_monitor_btn.resize(60, 25)
        self.asc_monitor_btn.move(10, 90)
        self.asc_monitor_btn.setText("Calibrate")
        
        self.asc_std_monitor_btn = QPushButton(self.asc_tab)
        self.asc_std_monitor_btn.resize(60, 25)
        self.asc_std_monitor_btn.move(75, 90)
        self.asc_std_monitor_btn.setText("Default")

        #Connecting
        self.asc_keybind_btn.clicked.connect(lambda x: self.__change_keybind_btn_handle("AutoSkillCheck", "keycode"))

        self.asc_checkbox.stateChanged.connect(lambda x: self.__checkbox_handle(self.asc_toggle, 
                                                                                Process,
                                                                                auto_skillcheck,
                                                                                self.asc_toggle, # args
                                                                                self.is_target_active,
                                                                                self.window_rect,
                                                                                self.asc_monitor,
                                                                                self.asc_ai_toggle, 
                                                                                self.asc_keycode))
        self.asc_ai_checkbox.stateChanged.connect(self.__ai_checkbox_handle)
        
        self.asc_monitor_btn.clicked.connect(lambda x: self.__change_monitor_btn_handle("AutoSkillCheck", "monitor"))
        
        self.asc_std_monitor_btn.clicked.connect(lambda x: self.update_config("AutoSkillCheck", "monitor", "default"))

    def __checkbox_handle(self, toggle: bool, launch_method: object, function: object, *args, **kwargs) -> None:
        """Accepts a function enable signal from checkboxes and (starts / disables) (processes / threads)

        Args:
            toggle (bool): On / Off toggle
            launch_method (object): Process or Thread object like `multiprocessing.Process`
            function (object): function that's need to be started / stopped
        """
        sender = self.sender()
        if sender.isChecked():
            toggle.value = 1
            launch_method(target=function, args=args, kwargs=kwargs).start()
            self.log_browser.append(f"[+] {sender.text()} -> ON")
        else:
            toggle.value = 0
            self.log_browser.append(f"[+] {sender.text()} -> OFF")

    def __change_keybind_btn_handle(self, partition:str, param:str) -> None:
        
        """Changes keybind (via updating config.ini file) when the keybind button is clicked
        NEED TO COMPLETE
        WHAT NEEDED:
        1. Add processing  - if several buttons are pressed at the same time

        Args:
            partition (str): partition of cfg
            param (str): param of selected partition
        """
        self.log_browser.append("[=] Waiting for a button...")

        sender = self.sender()
        sender.setStyleSheet("background-color: #8A2BE2; color: #FFF;")
        self.__change_btn_name(sender, "Waiting...", False)

        def on_press(key):
            try:
                self.update_config(partition, param, key)
                return False
            except:
                self.log_browser.append("[ERROR] An error occured while changing the button")
                self.update_config(partition, param, "None")
                return False

        listener = Listener(on_press=on_press)
        listener.start()

    def __change_monitor_btn_handle(self, partition: str, param: str) -> None:
        file_path = self.utility.get_file_path(self)
        
        #init child configure window
        if file_path:
            self.configure_window = MonitorCalibration(file_path, partition, param, self)
            self.configure_window.show()
        
    def __create_config(self) -> None:
        """Creates a config file
        Runs if no config.ini file was found or need to be replaced
        """
         
        self.config.add_section("AutoSkillCheck")
        self.config.set("AutoSkillCheck", "keycode", "c") # c is default keybind
        self.config.set("AutoSkillCheck", "monitor", "default")

        with open(f"{os.getcwd()}\\config.ini", "w") as config_file:
            self.config.write(config_file)


    def __load_config(self) -> None:
        """Loads settings from a configuration file
        """
        self.log_browser.append("[+] Loading config...")
        
        config_file_path = os.getcwd() + "\\config.ini"

        if not os.path.exists(config_file_path):
            self.log_browser.append("[=] Config not exists, creating new one")
            self.__create_config()
        
        self.config.read(f"{os.getcwd()}\\config.ini")

        # Here loading settings from config file 
        try:
            #Auto SkillCheck
            self.asc_keycode = self.__read_keycode(self.config.get("AutoSkillCheck", "keycode"))
            self.__change_btn_name(self.asc_keybind_btn, self.asc_keycode)
            self.asc_monitor = self.__read_monitor(self.config.get("AutoSkillCheck", "monitor")) # Make a dict() from str object

            self.log_browser.append("[+] Config loaded!")
        except:
            self.log_browser.append("[!!!] ERROR! Returning to default settings...")
            self.config = configparser.ConfigParser()
            self.__create_config()
            self.__load_config()

    def update_config(self, partition: str, param: str, value: str) -> None:
        """Updates the config file and calls the `self.__load_config()` function

        Args:
            partition (str): Partition of cfg file
            param (str): Parameter of cfg file
            value (str): The value to be written
        """
        self.config.set(partition, param, str(value).replace("'", ""))
        with open(f"{os.getcwd()}\\config.ini", "w") as config_file:
            self.config.read(f"{os.getcwd()}\\config.ini")
            self.config.write(config_file)
            self.log_browser.append(f"[+] [{param}] of [{partition}] has been set to [{value}]")
            self.__load_config()
        
    def __read_keycode(self, keycode_str: str) -> object:
        """Takes a string keycode object and returns it as an object of pynput.keyboard

        Args:
            keycode_str (str): keycode thats need to be converted in pynput.keyboard object

        Returns:
            object: pynput.keyboard object
        """
        keycode = None
        try:
            keycode = eval(keycode_str)
            # self.log_browser.append("[DEBUG] Config (keycode) has <Key> like keycode")
            return keycode
        except NameError:
            try:
                if len(keycode_str) == 1:
                    keycode = KeyCode.from_char(keycode_str)
                    # self.log_browser.append("[DEBUG] Config (keycode) has <KeyCode> like keycode")
                    return keycode
                else:
                    self.log_browser.append("[ERROR] Config (keycode) multiple characters found, delete config file and restart the program")
            except:
                self.log_browser.append("[ошибочка] не пиши гавно в конфиге")
        except:
            self.log_browser.append("[ERROR] Can't load config (keycode) - unknown type of keycode")

    def __read_monitor(self, monitor_str: str) -> dict:
        try:
            try:
                monitor = eval(monitor_str)
                return monitor
            except NameError:
                return monitor_str
        except:
            self.log_browser.append("[ERROR] Incorrect type of monitor (config.ini). Monitor has been set to default")
            return "default"

    def __change_btn_name(self, btn_object: object, name: str, use_keynames: bool=True) -> None:
        """Changes the name of the button

        Args:
            btn_object (object): The button whose name you want to change
            name (str): New name of button
            use_keynames (bool, optional): If necessary to use keynames dict(). Defaults to True.
        """
        keynames = {
            "Key.alt":"Alt",
            "Key.alt_gr":"AltGr",
            "Key.alt_l":"Left Alt",
            "Key.alt_r":"Right Alt",
            "Key.backspace":"BSPACE",
            "Key.caps_lock":"CapsLock",
            "Key.cmd":"Win",
            "Key.cmd_l":"Left Win",
            "Key.cmd_r":"Right Win",
            "Key.ctrl":"Ctrl",
            "Key.ctrl_l":"Left Ctrl",
            "Key.ctrl_r":"Right Ctrl",
            "Key.delete":"Delete",
            "Key.down":"Down",
            "Key.end":"End",
            "Key.enter":"Enter",
            "Key.esc":"Esc",
            "Key.f1":"F1",
            "Key.f2":"F2",
            "Key.f3":"F3",
            "Key.f4":"F4",
            "Key.right":"Right",
            "Key.scroll_lock":"SL",
            "Key.shift":"Shift",
            "Key.shift_l":"Left Shift",
            "Key.shift_r":"Right Shift",
            "Key.space":"Space",
            "Key.tab":"Tab",
            "Key.up":"Up"
        }
        try:
            name = str(name).replace("'", "")
            if use_keynames:
                
                btn_object.setStyleSheet("") # Set default style of btn_object
                keyname = keynames.get(name)
                
                if keyname == None:
                    keyname = name.upper()
            
                btn_object.setText(keyname)
            else:
                btn_object.setText(name)
        except:
            self.log_browser.append(f"[ERROR] Can't change name of btn ({btn_object})")
            btn_object.setText(":(")

    def __turn_off_tasks(self) -> None:
        """Turn off all tasks
        """
        self.gti_toogle.value = 0
        self.asc_toggle.value = 0

    def closeEvent(self, event) -> None:
        """Looking for a close event of PyQt
        """
        self.__turn_off_tasks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = DBDScript()
    sys.exit(app.exec_())
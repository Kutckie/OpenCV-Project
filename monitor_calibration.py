import numpy as np
from os import getcwd
from mss.windows import MSS as mss
from PyQt5.QtWidgets import QFileDialog

class MonitorCalibration:
    def __init__(self) -> None:
        pass
    
    def scrn_area_capture(self, monitor: dict()) -> np.ndarray:
        """Gets a screeshot of the selected area
        Args:
            monitor(dict): screenshot capture area -> {"top": 1, "left": 2, "width": 3, "height": 4}
        Returns:
            np.ndarray: returns an image of the selected area as numpy ndarray
        """
        with mss() as sct:
            """Context Manager
            """
            return np.array(sct.grab(monitor))

    def get_file_path(self, parent) -> str:
        file_path = QFileDialog.getOpenFileName(parent, "Open Image",  
                                                 getcwd(), "Image files (*.jpg *.png)")[0]
        return file_path
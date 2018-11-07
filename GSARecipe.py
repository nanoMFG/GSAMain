import numpy as np
import cv2, sys, time, json, copy, subprocess
from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as mp
import random

class GSARecipe(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(GSARecipe, self).__init__(parent=parent)
        self.left = 10
        self.top = 10
        self.title = 'Recipe Visualization'
        self.width = 800
        self.height = 1000
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        m = PlotCanvas(self, width=8, height=10)
        m.move(0,0)

        self.show()

class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=8, height=10, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()
        
    def plot(self):
        data = [random.random() for i in range(25)]
        ax = self.figure.add_subplot(111)
        ax.plot(data, 'r-')
        ax.set_title('Recipe Visualization')
        self.draw()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = GSARecipe()
    sys.exit(app.exec_())

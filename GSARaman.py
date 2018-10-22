from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import pandas as pd


filelist=[]

class GSARaman(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(GSARaman,self).__init__(parent=parent)
        self.spect_type=''
        self.data=[]

        self.layout=QtWidgets.QGridLayout(self)

        self.flbut=QtWidgets.QPushButton('Upload File')
        self.flbut.clicked.connect(self.openFileName)
        self.layout.addWidget(self.flbut,0,0)

        self.fitbut=QtWidgets.QPushButton('Do Fitting')
        self.fitbut.clicked.connect(self.doFitting)
        self.layout.addWidget(self.fitbut,0,1)

        self.download_but=QtWidgets.QPushButton('Download Data')
        self.layout.addWidget(self.download_but,1,1)

    def openFileName(self):
        fpath=QtWidgets.QFileDialog.getOpenFileName()
        filelist.append(fpath)

    def checkFileType(self):
        for flnm in filelist:
            self.data=pd.read_csv(flnm[0])
            cols=self.data.shape[1]
            rows=self.data.shape[0]
            if cols == 1:
                self.data=pd.DataFrame(self.data.iloc[0:rows/2,0],self.data.iloc[rows/2:rows,0])
                self.spect_type='single'
            elif cols == 2:
                self.spect_type='single'
                if type(self.data.iloc[0,0]) is str:
                    self.data=self.data.iloc[1:rows,:]
                else:
                    self.data=self.data
            else:
                self.spect_type='map'

    def doFitting(self):
        self.checkFileType()
        if self.spect_type=='single':
            self.widget=SingleSpect()
            x=self.data.iloc[:,0]
            y=self.data.iloc[:,1]
            self.widget.graphSpect(x,y)
        else:
            self.widget=MapFit()


class SingleSpect(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SingleSpect,self).__init__(parent=parent)

    def graphSpect(self,x,y):
        self.spect_plot=pg.plot(x,y)
        raman.layout.addWidget(self.spect_plot,2,0)



class MapFit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MapFit,self).__init__(parent=parent)


app=QtWidgets.QApplication([])
raman=GSARaman()
raman.show()
app.exec_()
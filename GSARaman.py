from __future__ import division
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

pg.setConfigOption('background','w')
pg.setConfigOption('foreground','k')

filelist=[]
layer1=[{'a':3.00007920e-01,'w':3.73588869e+01,'b':1.58577373e+03},{'a':1.00000000e+00,'w':3.25172389e+01,'b':2.68203383e+03}]
layer2=[{'a':1.04377489e+00,'w':3.34349819e+01,'b':1.59438802e+03},{'a':7.06298092e-01,'w':6.14683794e+01,'b':2.70286968e+03}]
layer3=[{'a':1.04128278e+00,'w':2.63152833e+01,'b':1.60154940e+03},{'a':6.50155655e-01,'w':5.73486165e+01,'b':2.72324859e+03}]
layer4=[{'a':1.01520762e+00,'w':2.79110458e+01,'b':1.61188139e+03},{'a':5.18657822e-01,'w':6.83826156e+01,'b':2.73099972e+03}]
layer5=[{'a':9.67793017e-01,'w':2.80824430e+01,'b':1.62490732e+03},{'a':4.30042148e-01,'w':6.41600512e+01,'b':2.75285511e+03}]
graphene=[{'a':9.98426340e-01,'w':2.83949973e+01,'b':1.63840546e+03},{'a':4.22730948e-01,'w':7.98338055e+01,'b':2.76274546e+03}]
cdat={'mono':layer1,'bi':layer2,'tri':layer3,'quad':layer4,'pent':layer5,'graph':graphene}

class GSARaman(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(GSARaman,self).__init__(parent=parent)
        self.resize(700,700)
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
            x=np.array(self.data.iloc[:,0])
            y=np.array(self.data.iloc[:,1])
            self.widget.plotSpect(x,y)
        else:
            self.widget=MapFit()


class SingleSpect(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SingleSpect,self).__init__(parent=parent)

    def Single_Lorentz(self, x,a,w,b):
        return a*(((w/2)**2)/(((x-b)**2)+((w/2)**2)))

    def Lfit(self,x,a1,w1,b1,a2,w2,b2,a3,w3,b3):
        LGfit=self.Single_Lorentz(x,a1,w1,b1)
        LGpfit=self.Single_Lorentz(x,a2,w2,b2)
        LDfit=self.Single_Lorentz(x,a3,w3,b3)
        Lfit=LGfit+LGpfit+LDfit
        return Lfit

    def backgroundFit(self,x,y):
        I_raw=y
        W=x

        polyx=np.array([W[0],W[int(len(W)/2)],W[len(W)-1]])
        polyy=np.array([I_raw[0],I_raw[int(len(W)/2)],I_raw[len(W)-1]])        
        bkgfit=np.polyfit(polyx,polyy,2)
        bkgpoly=(bkgfit[0]*W**2)+(bkgfit[1]*W)+bkgfit[2]
        I_raw=I_raw-bkgpoly
    
        m=(I_raw[len(W)-1]-I_raw[0])/(W[len(W)-1]-W[0])
        b=I_raw[len(W)-1]-m*W[len(W)-1]
        bkglin=m*W+b
    
        I_raw=I_raw-bkglin
    
        I=((I_raw-np.min(I_raw))/np.max(I_raw-np.min(I_raw)));
        return I

    def fitToPlot(self,x,y):
        I=self.backgroundFit(x,y)
        fit_params,fit_cov=curve_fit(self.Lfit,x,y,
            bounds=([0.3*np.max(I),33,1400,0.3*np.max(I),32,2000,0,10,1300],[1.5*np.max(I),60,2000,1.5*np.max(I),60,3000,np.max(I),50,1400]))
        
        y_fit=self.Lfit(x,fit_params[0],fit_params[1],fit_params[2],fit_params[3],fit_params[4],fit_params[5],fit_params[6],fit_params[7],fit_params[8])
        self.fit_plot=pg.plot(x,y_fit)

        self.fitting_params=QtWidgets.QLabel(
            """Fitting Parameters:
            G Peak:
                """u'\u03b1'"""="""+str(round(fit_params[0],4))+"""
                """u'\u0393'"""="""+str(round(fit_params[1],4))+"""
                """u'\u03c9'"""="""+str(round(fit_params[2],4))+"""
            G' Peak:
                """u'\u03b1'"""="""+str(round(fit_params[3],4))+"""
                """u'\u0393'"""="""+str(round(fit_params[4],4))+"""
                """u'\u03c9'"""="""+str(round(fit_params[5],4))+"""
            D Peak:
                """u'\u03b1'"""="""+str(round(fit_params[6],4))+"""
                """u'\u0393'"""="""+str(round(fit_params[7],4))+"""
                """u'\u03c9'"""="""+str(round(fit_params[8],4)))

        raman.layout.addWidget(self.fitting_params,2,2)

    def plotSpect(self,x,y):
        y_norm=[]
        for i in y:
            y_norm.append((i-np.min(y))/(np.max(y)-np.min(y)))
        self.spect_plot=pg.plot(x,y_norm)
        self.fitToPlot(x,y_norm)

        raman.layout.addWidget(self.spect_plot,2,0)
        raman.layout.addWidget(self.fit_plot,2,1)




class MapFit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MapFit,self).__init__(parent=parent)


app=QtWidgets.QApplication([])
raman=GSARaman()
raman.show()
app.exec_()
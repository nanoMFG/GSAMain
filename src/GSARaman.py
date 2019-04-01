from __future__ import division
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import pyqtgraph.exporters
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.sparse import vstack
from scipy.misc import toimage
from scipy.interpolate import griddata
from PIL.ImageQt import ImageQt
from multiprocessing import Pool
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import qimage2ndarray
import tempfile
import shutil
import os
import zipfile
from zipfile import ZipFile

filelist=[]
layer1=[{'a':3.00007920e-01,'w':3.73588869e+01,'b':1.58577373e+03},{'a':1.00000000e+00,'w':3.25172389e+01,'b':2.68203383e+03}]
layer2=[{'a':1.04377489e+00,'w':3.34349819e+01,'b':1.59438802e+03},{'a':7.06298092e-01,'w':6.14683794e+01,'b':2.70286968e+03}]
layer3=[{'a':1.04128278e+00,'w':2.63152833e+01,'b':1.60154940e+03},{'a':6.50155655e-01,'w':5.73486165e+01,'b':2.72324859e+03}]
layer4=[{'a':1.01520762e+00,'w':2.79110458e+01,'b':1.61188139e+03},{'a':5.18657822e-01,'w':6.83826156e+01,'b':2.73099972e+03}]
layer5=[{'a':9.67793017e-01,'w':2.80824430e+01,'b':1.62490732e+03},{'a':4.30042148e-01,'w':6.41600512e+01,'b':2.75285511e+03}]
graphene=[{'a':9.98426340e-01,'w':2.83949973e+01,'b':1.63840546e+03},{'a':4.22730948e-01,'w':7.98338055e+01,'b':2.76274546e+03}]
cdat={'monolayer':layer1,'bilayer':layer2,'trilayer':layer3,'four layers':layer4,'five layers':layer5,'graphene':graphene}

w=[]

class GSARaman(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(GSARaman,self).__init__(parent=parent)
        self.resize(1100,600)
        self.spect_type=''
        self.data=[]

        self.layout=QtWidgets.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.displayWidget=QtWidgets.QStackedWidget()
        self.displayWidget.addWidget(SingleSpect)
        self.displayWidget.addWidget(MapFit)
        self.layout.addWidget(self.displayWidget,2,0,1,3)

        self.flbut=QtWidgets.QPushButton('Upload File')
        self.flbut.clicked.connect(self.openFileName)
        self.flbut.setFixedSize(400,30)
        self.layout.addWidget(self.flbut,0,0)

        self.fitbut=QtWidgets.QPushButton('Do Fitting')
        self.fitbut.clicked.connect(self.doFitting)
        self.fitbut.setEnabled(False)
        self.fitbut.setFixedSize(400,30)
        self.layout.addWidget(self.fitbut,0,1)

        self.download_but=QtWidgets.QPushButton('Download Data')
        self.download_but.clicked.connect(self.downloadData)
        self.download_but.setFixedSize(400,30)
        self.download_but.setEnabled(False)
        self.layout.addWidget(self.download_but,1,1)
        self.download_list=[]

        self.statusBar=QtWidgets.QProgressBar()
        self.layout.addWidget(self.statusBar,0,2)

        self.errmsg=QtWidgets.QMessageBox()
        self.downloadMsg=QtWidgets.QMessageBox()
        self.cnfmdnld=False

        self.pathmade=False

    def openFileName(self):
        fpath=QtWidgets.QFileDialog.getOpenFileName()
        filelist.append(fpath)
        if filelist[-1][0]!=u'':
            if filelist[-1][0][-3:]!='txt' and filelist[-1][0][-3:]!='csv':
                self.errmsg.setIcon(QtWidgets.QMessageBox.Critical)
                self.errmsg.setText('Please upload a .txt or .csv')
                self.errmsg.exec_()

                del filelist[-1]
            else:
                self.fitbut.setEnabled(True)
        else:
            del filelist[-1]

        self.f_list=filelist

    def checkFileType(self, flnm):
        #for flnm in filelist:
        if flnm[0][-3:]=='csv':
            self.data=pd.read_csv(flnm[0])
        else:
            self.data=pd.read_table(flnm[0])

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
        if not self.pathmade:
                self.make_temp_dir()

        for flnm in filelist:
            self.checkFileType(flnm)
            if self.spect_type=='single':
                self.widget=SingleSpect
                self.displayWidget.setCurrentWidget(self.widget)

                x=np.array(self.data.iloc[:,0])
                y=np.array(self.data.iloc[:,1])

                self.widget.plotSpect(x,y)
                self.fitbut.setEnabled(False)
                self.download_but.setEnabled(True)
            else:
                self.widget=MapFit
                self.displayWidget.setCurrentWidget(self.widget)

                self.widget.mapLoop(self.data)
                self.fitbut.setEnabled(False)
                self.download_but.setEnabled(True)
        print 'done'

    def make_temp_dir(self):
        self.dirpath = tempfile.mkdtemp()
        self.pathmade=True

    def save_files(self, filelist):
        for flnm in filelist:
            shutil.copy2(flnm[0],self.dirpath)

    def downloadData(self):
        self.downloadMsg.setIcon(QtWidgets.QMessageBox.Question)
        self.downloadMsg.setWindowTitle('Confirm Download')
        self.downloadMsg.setText('The Raman spectrum(s) following files will be downloaded:\n'+'\n'.join('{}'.format(item[0]) for item in self.f_list))
        self.downloadMsg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        self.downloadMsg.buttonClicked.connect(self.msgbtn)
        self.downloadMsg.exec_()

        if self.cnfmdnld:
            self.save_files(self.f_list)
            self.zip_files(self.dirpath)
            shutil.rmtree(self.dirpath)
            self.pathmade=False
            print 'did it'

    def msgbtn(self, i):
        print i.text()
        if i.text() == 'OK':
            self.cnfmdnld=True
            print 'True'
        else:
            self.cnfmdnld=False
            print 'false'

    def zip_files(self,directory):
        zipname=QtWidgets.QFileDialog.getSaveFileName()
        shutil.make_archive(zipname[0],'zip',directory)

class SingleSpect(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SingleSpect,self).__init__(parent=parent)
        self.layout=QtWidgets.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

    def Single_Lorentz(self, x,a,w,b):
        return a*(((w/2)**2)/(((x-b)**2)+((w/2)**2)))

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

    def checkParams(self,G_params,Gp_params):
        x=np.array([1,2,3,4,5,6])
        diffs=[]

        PGp=np.array(Gp_params)
        PG=np.array(G_params)

        layer_keys=['monolayer','bilayer','trilayer','four layers','five layers','graphene']

        for key in layer_keys:
            LGp=np.array([cdat[key][1]['a'],cdat[key][1]['w'],cdat[key][1]['b']])
            LG=np.array([cdat[key][0]['a'],cdat[key][0]['w'],cdat[key][0]['b']])

            dfGp=np.average(np.absolute(100*(PGp-LGp)/LGp),weights=[1,1,0.5])
            dfG=np.average(np.absolute(100*(PG-LG)/LG),weights=[1,1,0.5])
            drat=np.absolute(100*(((PG[0]/PGp[0])-(LG[0]/LGp[0]))/(LG[0]/LGp[0])))
            df=np.average([dfGp,dfG,drat],weights=[0.5,0.5,1])
            diffs.append(df)

        diff_array=np.array(diffs)
        idx=diffs.index(np.min(diff_array))
        
        self.layers=layer_keys[idx]

        self.diff_plot=pg.plot(x,diff_array,pen=None,symbol='o')
        self.diff_plot.setLabel('left',u'\u0394'+'[%]')
        self.diff_plot.setLabel('bottom','# Layers')
        ticks=[list(zip(range(7),('','1','2','3','4','5','graphene')))]
        self.diff_label=self.diff_plot.getAxis('bottom')
        self.diff_label.setTicks(ticks)
        self.diff_plot.win.hide()

    def fitToPlot(self,x,y):
        I=self.backgroundFit(x,y)
        pG=[1.1*np.max(I), 50, 1581.6] #a w b
        pGp=[1.1*np.max(I), 50, 2675]
        pD=[0.1*np.max(I),15,1350]

        #fit G peak
        G_param,G_cov=curve_fit(self.Single_Lorentz,x,y,bounds=([0.3*np.max(I),33,1400],[1.5*np.max(I),60,2000]),p0=pG)
        G_fit=self.Single_Lorentz(x,G_param[0],G_param[1],G_param[2])

        #fit G' peak
        Gp_param,Gp_cov=curve_fit(self.Single_Lorentz,x,y,bounds=([0.3*np.max(I),32,2000],[1.5*np.max(I),60,3000]),p0=pGp)
        Gp_fit=self.Single_Lorentz(x,Gp_param[0],Gp_param[1],Gp_param[2])

        #fit D peak
        D_param,D_cov=curve_fit(self.Single_Lorentz,x,y,bounds=([0,10,1300],[np.max(I),50,1400]),p0=pD)
        D_fit=self.Single_Lorentz(x,D_param[0],D_param[1],D_param[2])

        y_fit=G_fit+Gp_fit+D_fit
        self.checkParams(G_param,Gp_param)

        test_params=cdat[self.layers]
        G_test=self.Single_Lorentz(x,test_params[0]['a'],test_params[0]['w'],test_params[0]['b'])
        Gp_test=self.Single_Lorentz(x,test_params[1]['a'],test_params[1]['w'],test_params[1]['b'])
        y_test=G_test+Gp_test

        self.fit_plot=pg.plot(x,y_fit,pen='w')
        self.fit_plot.setRange(yRange=[0,1])
        self.fit_plot.setLabel('left','I<sub>norm</sub>[arb]')
        self.fit_plot.setLabel('bottom',u'\u03c9'+'[cm<sup>-1</sup>]')
        self.fit_plot.win.hide()

        self.overlay_plot=pg.plot()
        self.overlay_plot.addLegend(offset=(-1,1))
        self.overlay_plot.plot(x,y,pen='g',name='Raw Data')
        self.overlay_plot.plot(x,y_fit,pen='r',name='Fitted Data')
        self.overlay_plot.plot(x,y_test,pen='b',name='Test Data')
        self.overlay_plot.setLabel('left','I<sub>norm</sub>[arb]')
        self.overlay_plot.setLabel('bottom',u'\u03c9'+'[cm<sup>-1</sup>]')
        self.overlay_plot.win.hide()
        exporter2=pg.exporters.ImageExporter(self.fit_plot.plotItem)
        exporter2.params.param('width').setValue(1024, blockSignal=exporter2.widthChanged)
        exporter2.params.param('height').setValue(860, blockSignal=exporter2.heightChanged)
        exporter2.export(raman.dirpath+'/overlayplot.png')

        self.fitting_params=QtWidgets.QLabel(
            """Fitting Parameters:
            G Peak:
                """u'\u03b1'"""="""+str(round(G_param[0],4))+"""
                """u'\u0393'"""="""+str(round(G_param[1],4))+"""
                """u'\u03c9'"""="""+str(round(G_param[2],4))+"""
            G' Peak:
                """u'\u03b1'"""="""+str(round(Gp_param[0],4))+"""
                """u'\u0393'"""="""+str(round(Gp_param[1],4))+"""
                """u'\u03c9'"""="""+str(round(Gp_param[2],4))+"""
            D Peak:
                """u'\u03b1'"""="""+str(round(D_param[0],4))+"""
                """u'\u0393'"""="""+str(round(D_param[1],4))+"""
                """u'\u03c9'"""="""+str(round(D_param[2],4))+"""
            Quality="""+str(round(1-(D_param[0]/G_param[0]),4))+"""(Ratio of D to G)
            Best Case Match: """+self.layers)

        self.fitting_params.setFixedSize(300,500)
        self.layout.addWidget(self.fitting_params,2,2)

    def plotSpect(self,x,y):
        y_norm=[]
        for i in y:
            y_norm.append((i-np.min(y))/(np.max(y)-np.min(y)))

        self.spect_plot=pg.plot(x,y_norm,pen='w')
        self.spect_plot.setFixedSize(400,500)
        self.spect_plot.setLabel('left','I<sub>norm</sub>[arb]')
        self.spect_plot.setLabel('bottom',u'\u03c9'+'[cm<sup>-1</sup>]')
        self.spect_plot.win.hide()

        self.fitToPlot(x,y_norm)

        self.TabWidget=QtWidgets.QTabWidget()
        self.TabWidget.addTab(self.fit_plot,"Fit")
        self.TabWidget.addTab(self.overlay_plot,"Overlay")
        self.TabWidget.addTab(self.diff_plot,"Diffs")
        self.TabWidget.setFixedSize(400,500)

        self.layout.addWidget(self.TabWidget,2,1)
        self.layout.addWidget(self.spect_plot,2,0)


class MapFit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MapFit,self).__init__(parent=parent)
        self.layout=QtWidgets.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.pickParam=QtWidgets.QComboBox()
        self.pickParam.setFixedSize(400,30)
        self.pickParam.addItem("G Peak")
        self.pickParam.addItem("G' Peak")
        self.pickParam.addItem("D Peak")
        self.pickParam.addItem("Quality")
        self.pickParam.activated.connect(self.changeParam)
        self.paramnum=0
        self.pickParam.setEnabled(False)

        self.mapPlot=QtWidgets.QTabWidget()
        self.mapPlot.setFixedSize(400,500)
        self.mapPlot.currentChanged.connect(self.changeHist)
        self.map_plotted=False

        self.spectPlots=QtWidgets.QTabWidget()
        self.spectPlots.setFixedSize(400,500)
        self.hist_plotted=False
        self.spect_plotted=False

        self.fitting_params=QtWidgets.QLabel()
        self.fitting_params.setFixedSize(300,500)
        self.layout.addWidget(self.fitting_params,1,2)

        self.layout.addWidget(self.pickParam,0,0)
        self.layout.addWidget(self.mapPlot,1,0)
        self.layout.addWidget(self.spectPlots,1,1)

        self.param_dict={}
        self.norm_dict={}

        self.fig1=plt.figure()
        self.canvas1=FigureCanvas(self.fig1)
        self.fig2=plt.figure()
        self.canvas2=FigureCanvas(self.fig2)
        self.fig3=plt.figure()
        self.canvas3=FigureCanvas(self.fig3)
    
    def prepareData(self,data):
        rows=data.shape[0]

        self.freqs=np.array(data.columns.values[2:],dtype=float)
        global w
        w = self.freqs
        
        self.pos=np.array(data.iloc[:,0:2])
        self.I_data=np.array(data.iloc[:,2:])

        self.data_list=[]
        for i in range(rows):
            self.data_list.append((tuple(self.pos[i]),self.I_data[i]))

    def mapLoop(self,data):
        self.prepareData(data)
        
        self.completed=0
        length=len(self.data_list)

        pool=Pool(processes=None)
        for i in pool.imap_unordered(fitting, self.data_list):
            app.processEvents()
            self.completed+=(1/length)*100+1
            raman.statusBar.setValue(self.completed)
            self.param_dict.update(i[0])
            self.norm_dict.update(i[1])
            self.make_plots(i[2])


        self.mapSpecPlot(self.param_dict)
        #self.make_plots(self.param_dict.keys())

    def mapSpecPlot(self,data_dict):

        keys=data_dict.keys()
        num=self.paramnum
        print self.paramnum

        if num<=2:
            self.data_array_a=np.append(np.array(keys[0]),[data_dict[keys[0]][num]['a']])
            self.data_array_a=np.array([self.data_array_a])
            length=len(keys)

            for i in range(length):
                new_entry=np.append(np.array(keys[i]),[data_dict[keys[i]][num]['a']])
                new_entry=np.array([new_entry])
                self.data_array_a=np.append(self.data_array_a,new_entry,axis=0)
            z_a=self.data_array_a[:,2]
            x_a=self.data_array_a[:,0]
            y_a=self.data_array_a[:,1]

            xi_a=np.linspace(min(self.data_array_a[:,0]),max(self.data_array_a[:,0]))
            xi_a=np.linspace(min(x_a),max(x_a))
            yi_a=np.linspace(min(self.data_array_a[:,1]),max(self.data_array_a[:,1]))
            yi_a=np.linspace(min(y_a),max(y_a))
            X_a,Y_a=np.meshgrid(xi_a,yi_a)
            Z_a=griddata((x_a,y_a),z_a,(X_a,Y_a),method='nearest')

            self.fig1.clear()
            ax1=self.fig1.add_subplot(111)
            C1=ax1.contourf(X_a,Y_a,Z_a)
            plt.colorbar(C1,ax=ax1)
            plt.set_cmap('inferno')
            cid1=self.fig1.canvas.mpl_connect('button_press_event', self.onclick)
            self.canvas1.draw()
        
            self.data_array_w=np.append(np.array(keys[0]),[data_dict[keys[0]][num]['w']])
            self.data_array_w=np.array([self.data_array_w])
            length=len(keys)

            for i in range(length):
                new_entry=np.append(np.array(keys[i]),[data_dict[keys[i]][num]['w']])
                new_entry=np.array([new_entry])
                self.data_array_w=np.append(self.data_array_w,new_entry,axis=0)
            z_w=self.data_array_w[:,2]

            Z_w=griddata((x_a,y_a),z_w,(X_a,Y_a),method='nearest')

            self.fig2.clear()
            ax2=self.fig2.add_subplot(111)
            C2=ax2.contourf(X_a,Y_a,Z_w)
            plt.colorbar(C2,ax=ax2)
            plt.set_cmap('inferno')
            cid2=self.fig2.canvas.mpl_connect('button_press_event', self.onclick)
            self.canvas2.draw()

            self.data_array_b=np.append(np.array(keys[0]),[data_dict[keys[0]][num]['b']])
            self.data_array_b=np.array([self.data_array_b])
            length=len(keys)

            for i in range(length):
                new_entry=np.append(np.array(keys[i]),[data_dict[keys[i]][num]['b']])
                new_entry=np.array([new_entry])
                self.data_array_b=np.append(self.data_array_b,new_entry,axis=0)
            z_b=self.data_array_b[:,2]


            Z_b=griddata((x_a,y_a),z_b,(X_a,Y_a),method='nearest')

            self.fig3.clear()
            ax3=self.fig3.add_subplot(111)
            C3=ax3.contourf(X_a,Y_a,Z_b)
            plt.colorbar(C3,ax=ax3)
            plt.set_cmap('inferno')
            cid3=self.fig3.canvas.mpl_connect('button_press_event', self.onclick)
            self.canvas3.draw()

            self.histList=[z_a,z_w,z_b]

            self.mapPlot.addTab(self.canvas1,u'\u03b1')
            self.mapPlot.addTab(self.canvas2,u'\u0393')
            self.mapPlot.addTab(self.canvas3,u'\u03c9')

        else:
            data_array_d=np.append(np.array(keys[0]),[data_dict[keys[0]][2]['a']])
            data_array_d=np.array([data_array_d])
            data_array_g=np.append(np.array(keys[0]),[data_dict[keys[0]][0]['a']])
            data_array_g=np.array([data_array_g])
            data_array_gp=np.append(np.array(keys[0]),[data_dict[keys[0]][1]['a']])
            data_array_gp=np.array([data_array_gp])
            length=len(keys)

            for i in range(length):
                new_entry1=np.append(np.array(keys[i]),[data_dict[keys[i]][2]['a']])
                new_entry1=np.array([new_entry1])
                new_entry2=np.append(np.array(keys[i]),[data_dict[keys[i]][0]['a']])
                new_entry2=np.array([new_entry2])
                new_entry3=np.append(np.array(keys[i]),[data_dict[keys[i]][1]['a']])
                new_entry3=np.array([new_entry3])

                data_array_d=np.append(data_array_d,new_entry1,axis=0)
                data_array_g=np.append(data_array_g,new_entry2,axis=0)
                data_array_gp=np.append(data_array_gp,new_entry3,axis=0)

            z_1=np.ones(data_array_d[:,2].shape)-np.divide(data_array_d[:,2],data_array_g[:,2])
            z_2=np.divide(data_array_g[:,2],data_array_gp[:,2])

            x_a=data_array_d[:,0]
            y_a=data_array_d[:,1]

            xi_a=np.linspace(min(self.data_array_a[:,0]),max(self.data_array_a[:,0]))
            xi_a=np.linspace(min(x_a),max(x_a))
            yi_a=np.linspace(min(self.data_array_a[:,1]),max(self.data_array_a[:,1]))
            yi_a=np.linspace(min(y_a),max(y_a))
            X_a,Y_a=np.meshgrid(xi_a,yi_a)
            Z_1=griddata((x_a,y_a),z_1,(X_a,Y_a),method='nearest')
            Z_2=griddata((x_a,y_a),z_2,(X_a,Y_a),method='nearest')

            self.fig1.clear()
            ax1=self.fig1.add_subplot(111)
            C1=ax1.contourf(X_a,Y_a,Z_1)
            plt.colorbar(C1,ax=ax1)
            plt.set_cmap('inferno')
            cid1=self.fig1.canvas.mpl_connect('button_press_event', self.onclick)
            self.canvas1.draw()

            self.mapPlot.addTab(self.canvas1,'D:G')

            self.fig2.clear()
            ax2=self.fig2.add_subplot(111)
            C2=ax2.contourf(X_a,Y_a,Z_2)
            plt.colorbar(C2,ax=ax2)
            plt.set_cmap('inferno')
            cid2=self.fig2.canvas.mpl_connect('button_press_event', self.onclick)
            self.canvas2.draw()

            self.mapPlot.addTab(self.canvas2,"G:G'")
            
            self.mapPlot.removeTab(0)

        self.pickParam.setEnabled(True)

            
    def Single_Lorentz(self, x,a,w,b):
        return a*(((w/2)**2)/(((x-b)**2)+((w/2)**2)))

    def changeParam(self,index):
        self.paramnum=index
        self.mapPlot.setCurrentIndex(0)
        self.mapSpecPlot(self.param_dict)

    def changeHist(self,i):
        z=self.histList[i]
        widths=[0.01,0.1,0.1]

        hist,bin_edges=np.histogram(z,bins='auto',density=False)
        hist_shift=np.ptp(z)/len(hist)
        self.hist_plot=pg.plot()
        bg1=pg.BarGraphItem(x=bin_edges[0:len(hist)-1]+hist_shift,height=hist,width=widths[i],brush='r')
        self.hist_plot.addItem(bg1)

        if self.hist_plotted==False:
            self.spectPlots.addTab(self.hist_plot,'histogram')
            self.hist_plotted=True
        else:
            self.spectPlots.removeTab(0)
            self.spectPlots.insertTab(0,self.hist_plot,'histogram')
            
        self.hist_plot.win.hide()

    def plotSpects(self,pos):
        param_list=self.param_dict[pos]
        G_fit=self.Single_Lorentz(self.freqs,param_list[0]['a'],param_list[0]['w'],param_list[0]['b'])
        Gp_fit=self.Single_Lorentz(self.freqs,param_list[1]['a'],param_list[1]['w'],param_list[1]['b'])
        D_fit=self.Single_Lorentz(self.freqs,param_list[2]['a'],param_list[2]['w'],param_list[2]['b'])
        y_fit=G_fit+Gp_fit+D_fit

        y_norm=self.norm_dict[pos]

        layers=self.checkParams([param_list[0]['a'],param_list[0]['w'],param_list[0]['b']],[param_list[1]['a'],param_list[1]['w'],param_list[1]['b']])
        G_test=self.Single_Lorentz(self.freqs,cdat[layers][0]['a'],cdat[layers][0]['w'],cdat[layers][0]['b'])
        Gp_test=self.Single_Lorentz(self.freqs,cdat[layers][1]['a'],cdat[layers][1]['w'],cdat[layers][1]['b'])
        y_test=G_test+Gp_test

        self.fit_plot=pg.plot()
        self.fit_plot.addLegend(offset=(-1,1))
        self.fit_plot.plot(self.freqs,y_norm,pen='g',name='Raw Data')
        self.fit_plot.plot(self.freqs,y_test,pen='b',name='Test Data')
        self.fit_plot.plot(self.freqs,y_fit,pen='r',name='Fitted Data')
        self.fit_plot.setLabel('left','I<sub>norm</sub>[arb]')
        self.fit_plot.setLabel('bottom',u'\u03c9'+'[cm<sup>-1</sup>]')

        if self.spect_plotted==False:
            self.spectPlots.insertTab(1,self.fit_plot,'Spect Plot')
            self.spectPlots.setCurrentIndex(1)
            self.spect_plotted=True
        else:
            self.spectPlots.removeTab(1)
            self.spectPlots.insertTab(1,self.fit_plot,'Spect Plot')
            self.spectPlots.setCurrentIndex(1)
        self.fit_plot.win.hide()

        self.fitting_params.setText(
            """Fitting Parameters:
            G Peak:
                """u'\u03b1'"""="""+str(round(param_list[0]['a'],4))+"""
                """u'\u0393'"""="""+str(round(param_list[0]['w'],4))+"""
                """u'\u03c9'"""="""+str(round(param_list[0]['b'],4))+"""
            G' Peak:
                """u'\u03b1'"""="""+str(round(param_list[1]['a'],4))+"""
                """u'\u0393'"""="""+str(round(param_list[1]['w'],4))+"""
                """u'\u03c9'"""="""+str(round(param_list[1]['b'],4))+"""
            D Peak:
                """u'\u03b1'"""="""+str(round(param_list[2]['a'],4))+"""
                """u'\u0393'"""="""+str(round(param_list[2]['w'],4))+"""
                """u'\u03c9'"""="""+str(round(param_list[2]['b'],4))+"""
            Quality="""+str(round(1-(param_list[2]['a']/param_list[0]['a']),4))+"""(Ratio of D to G)
            Best Case Match: """+layers)

        self.fitting_params.setFixedSize(300,500)
        self.layout.addWidget(self.fitting_params,1,2)

    def checkParams(self,G_params,Gp_params):
        diffs=[]

        PGp=np.array(Gp_params)
        PG=np.array(G_params)

        layer_keys=['monolayer','bilayer','trilayer','four layers','five layers','graphene']

        for key in layer_keys:
            LGp=np.array([cdat[key][1]['a'],cdat[key][1]['w'],cdat[key][1]['b']])
            LG=np.array([cdat[key][0]['a'],cdat[key][0]['w'],cdat[key][0]['b']])

            dfGp=np.average(np.absolute(100*(PGp-LGp)/LGp),weights=[1,1,0.5])
            dfG=np.average(np.absolute(100*(PG-LG)/LG),weights=[1,1,0.5])
            drat=np.absolute(100*(((PG[0]/PGp[0])-(LG[0]/LGp[0]))/(LG[0]/LGp[0])))
            df=np.average([dfGp,dfG,drat],weights=[0.5,0.5,1])
            diffs.append(df)

        diff_array=np.array(diffs)
        idx=diffs.index(np.min(diff_array))
        
        return layer_keys[idx]

    def onclick(self,event):
        x=event.xdata
        y=event.ydata
        pos_tup=(x,y)

        if None in pos_tup:
            return
        else:
            keys=self.param_dict.keys()
            length=len(keys)
            x_list=np.array([])
            y_list=np.array([])
            for i in range(length):
                x_list=np.append(x_list,keys[i][0])
                y_list=np.append(y_list,keys[i][1])

                x_list=np.unique(x_list)
                y_list=np.unique(y_list)

            x_key=self.find_nearest(x_list,x)
            y_key=self.find_nearest(y_list,y)

            self.plotSpects((x_key,y_key))

    def make_plots(self,key):
        i=key
        param_list=self.param_dict[i]
        G_fit=self.Single_Lorentz(self.freqs,param_list[0]['a'],param_list[0]['w'],param_list[0]['b'])
        Gp_fit=self.Single_Lorentz(self.freqs,param_list[1]['a'],param_list[1]['w'],param_list[1]['b'])
        D_fit=self.Single_Lorentz(self.freqs,param_list[2]['a'],param_list[2]['w'],param_list[2]['b'])
        y_fit=G_fit+Gp_fit+D_fit

        y_norm=self.norm_dict[i]

        layers=self.checkParams([param_list[0]['a'],param_list[0]['w'],param_list[0]['b']],[param_list[1]['a'],param_list[1]['w'],param_list[1]['b']])
        G_test=self.Single_Lorentz(self.freqs,cdat[layers][0]['a'],cdat[layers][0]['w'],cdat[layers][0]['b'])
        Gp_test=self.Single_Lorentz(self.freqs,cdat[layers][1]['a'],cdat[layers][1]['w'],cdat[layers][1]['b'])
        y_test=G_test+Gp_test

        fit_plot=pg.plot()
        fit_plot.addLegend(offset=(-1,1))
        fit_plot.plot(self.freqs,y_norm,pen='g',name='Raw Data')
        fit_plot.plot(self.freqs,y_test,pen='b',name='Test Data')
        fit_plot.plot(self.freqs,y_fit,pen='r',name='Fitted Data')
        fit_plot.setLabel('left','I<sub>norm</sub>[arb]')
        fit_plot.setLabel('bottom',u'\u03c9'+'[cm<sup>-1</sup>]')

        exporter=pg.exporters.ImageExporter(fit_plot.plotItem)
        exporter.params.param('width').setValue(1024, blockSignal=exporter.widthChanged)
        exporter.params.param('height').setValue(860, blockSignal=exporter.heightChanged)
        exporter.export(raman.dirpath+'/overlayplot_'+str(i)+'.png')

    def find_nearest(self,array,value):
        array=np.asarray(array)
        idx=(np.abs(array-value)).argmin()
        return array[idx]

def Single_Lorentz(x,a,w,b):
    return a*(((w/2)**2)/(((x-b)**2)+((w/2)**2)))

def backgroundFit(x,y):
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

def fitting(data_tuple):
    global w
    pos=data_tuple[0]
    x=w
    y=data_tuple[1]

    y_norm=[]
    for i in y:
            y_norm.append((i-np.min(y))/(np.max(y)-np.min(y)))

    I=backgroundFit(x,y_norm)

    pG=[1.1*np.max(I), 50, 1581.6] #a w b
    pGp=[1.1*np.max(I), 50, 2675]
    pD=[0.1*np.max(I),15,1350]

    #fit G peak
    G_param,G_cov=curve_fit(Single_Lorentz,x,y_norm,bounds=([0.3*np.max(I),33,1400],[1.5*np.max(I),60,2000]),p0=pG)
    G_fit=Single_Lorentz(x,G_param[0],G_param[1],G_param[2])

    #fit G' peak
    Gp_param,Gp_cov=curve_fit(Single_Lorentz,x,y_norm,bounds=([0.3*np.max(I),32,2000],[1.5*np.max(I),60,3000]),p0=pGp)
    Gp_fit=Single_Lorentz(x,Gp_param[0],Gp_param[1],Gp_param[2])

    #fit D peak
    D_param,D_cov=curve_fit(Single_Lorentz,x,y_norm,bounds=([0,10,1300],[np.max(I),50,1400]),p0=pD)
    D_fit=Single_Lorentz(x,D_param[0],D_param[1],D_param[2])

    Gdict={'a':G_param[0],'w':G_param[1],'b':G_param[2]}
    Gpdict={'a':Gp_param[0],'w':Gp_param[1],'b':Gp_param[2]}
    Ddict={'a':D_param[0],'w':D_param[1],'b':D_param[2]}

    return [{pos:[Gdict,Gpdict,Ddict]},{pos:y_norm},pos]

app=QtWidgets.QApplication([])
SingleSpect=SingleSpect()
MapFit=MapFit()
raman=GSARaman()
raman.show()
app.exec_()
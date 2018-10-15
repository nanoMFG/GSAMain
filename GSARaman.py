from PyQt5 import QtGui, QtCore, QtWidgets

import pandas as pd
import ipywidgets as widgets
from IPython.display import clear_output
import matplotlib
#matplotlib notebook
import matplotlib.pyplot as plt
import scipy
import numpy as np
from decimal import Decimal
import unicodedata
from unicodedata import lookup as GL
import sympy as sy
from joblib import Parallel, delayed
from lmfit import Model
import warnings
import zipfile
from zipfile import ZipFile
import os

class Spectrum(QtWidgets.QWidget):
    def __init__(self, parent=None):
    	super(Spectrum,self).__init__(parent=parent)
        self.x=0
        self.y=0
        self.I=[]
        self.W=[]
        self.If=[]
        self.PG=[]
        self.PGp=[]
        self.PD=[]
        self.IDfit=[]
        self.Q=0
        self.diffs=[]
        self.mdi=0
        self.md=0
        self.mf=[]

global Specs
Specs=[]

global filelist
filelist = []

global cfl

def mycb(w,fnames):
    global fnm
    fnm=fnames[0]
    fbase = os.path.basename(fnm)
    os.makedirs('data/' + os.path.splitext(fbase)[0])
    filelist.append(fbase)
    os.rename(fnm, 'data/raw/' + fbase)
    w.reset()
    filename = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile')
    self.myTextBox.setText(filename)
    print(filename)

def errprint(code):
    errfile=pd.read_csv('errfile.txt',sep='\t',header=None)
    with errout:
        clear_output()
        print(errfile[0][code])
        fit_but.disabled=False
        errout

def case_lookup(index):
    casefile=pd.read_csv('Case_List.txt',sep='\t',header=None)
    c=casefile[0][index]
    return c

fit_but = widgets.Button(description='Do Fitting')
    
def fit_but_cb(change):
    global cfl
    fit_but.disabled=True
    param.disabled=True
    with plist:
        clear_output()
        print('Reading data files...')
    with errout:
        clear_output()
    with diffsplot:
        clear_output()
    with datplot:
        clear_output()
    
    for flnm in filelist:
        cfl = flnm
        if flnm[-3:]=='txt':
            sp='\s+'
        elif flnm[-3:]=='csv':
            sp=','
        else:
            errprint(0)
            return
        try:
            data = pd.read_csv('data/raw/' + flnm,sep=sp,header=None)
        except:
            sp='\t'
            data = pd.read_csv('data/raw/' + flnm,sep=sp,header=None)
        with plist:
            clear_output()
            print('Data file read')

        n=int(data.size/len(data)) #n determines the size of the data file

        global Specs
        Specs.clear()

        ##Single Spectra Data File, n=2    
        if n==2:
            with plist:
                clear_output()
                print('Fitting single spectra data.')

            s=Spectrum()
            Spectra(s,data)
            Fit(s)

            dtplot(s)

            with diffsplot:
                clear_output()
                fig=plt.figure(figsize=(4,4))
                ax=fig.add_subplot(111)
                plt.plot(s.diffs,'kv')
                plt.plot(s.mdi,s.md,'gv')
                plt.annotate((round(Decimal(s.md),2)),xy=(s.mdi,1.2*s.md))
                plt.xticks(range(6),('1','2','3','4','5','Graphite'))
                plt.xlabel('# Layers')
                plt.ylabel('$\Delta$ [%]')
                plt.show()

            save_spec(s)
            zip_files('data')
            params_print(s)

        #Map files will be much larger than 2 points and need separate handling
        elif n > 2:
            Specs=[]
            Map(data)
        else:
            errprint(1)
            return
    fit_but.disabled=False

fit_but.on_click(fit_but_cb)
fit_but
import numpy as np
import cv2, sys, time, json, copy, subprocess
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import pandas as pd
import matplotlib.pyplot as mp
import matplotlib.lines as mlines
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import random

class GSARecipe(QtGui.QWidget):
    def __init__(self,parent=None):
        super(GSARecipe,self).__init__(parent=parent)
        self.df = pd.DataFrame()
        self.experiments = []

        self.layout=QtWidgets.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.file_button = QtWidgets.QPushButton('Upload File')
        self.file_button.clicked.connect(self.getFile)

        self.experiment_selection = QtGui.QComboBox(self)
        self.experiment_selection.activated[str].connect(self.plotRecipe)
        self.experiment_selection.setEnabled(False)

        self.figure = Figure()
        self.recipe_profile = FigureCanvas(self.figure)

        self.layout.addWidget(self.file_button,0,0,1,1)
        self.layout.addWidget(self.experiment_selection,0,1,1,1)
        self.layout.addWidget(self.recipe_profile,1,0,1,2)

    def getFile(self):
        filepath = QtWidgets.QFileDialog.getOpenFileName()
       
        self.df = pd.read_csv(filepath[0])
        
        self.experiment_selection.addItems(['Please Select Exeriment No'])
        ind, col = self.df.shape
        self.experiments = []
        for i in range(ind):
            self.experiments.append(str(i+1))
        
        self.experiment_selection.addItems(self.experiments)
        self.experiment_selection.setEnabled(True)

    def collapse(self, series):
        
        stamp = []

        self.df = series.to_frame()
        
        i = 0
        for n in range(6):
            stamp_component = self.df[i:i+13].transpose()

            stamp_component.columns = ['Timestamp (min)','Temp (degC)','Pressure(Torr)',
                                       'Sample Location (normalized from 0-1)','Helium Flow Rate (sccm)',
                                       'Helium Flow Rate (Torr l/s)', 'Hydrogen Flow Rate (sccm)',
                                       'Hydrogen Flow Rate (Torr l/s)','Carbon Source','Carbon Source Flow Rate (sccm)',
                                       'Carbon Source Flow Rate (Torr l/s)','Argon Flow Rate (sccm)', 'Argon Flow Rate (Torr l/s)']
            stamp.append(stamp_component)
            i += 13

        reorder = stamp[0].append([stamp[1],stamp[2],stamp[3],stamp[4],stamp[5]])
        reorder.index = [0,1,2,3,4,5]

        return reorder

    def finalize(self, frame1, frame2, frame3):
        frames = [frame1, frame2, frame3]

        for frame in frames:
            frame.rename(columns={'Timestamp (min)' : 'Time (min)'}, inplace=True)
            total = 0
            for i in range(len(frame.index)):
                total += frame.iloc[i,0]
                frame.iat[i,0] = total

        zeroA = pd.DataFrame({'Time (min)' : [0],'Temp (degC)' : [0],'Pressure(Torr)' : [frame1.iat[0,2]],
                              'Sample Location (normalized from 0-1)' : [frame1.iat[0,3]],
                              'Helium Flow Rate (sccm)' : [frame1.iat[0,4]], 'Helium Flow Rate (Torr l/s)' : [frame1.iat[0,5]], 
                              'Hydrogen Flow Rate (sccm)' : [frame1.iat[0,6]], 'Hydrogen Flow Rate (Torr l/s)' : [frame1.iat[0,7]],
                              'Carbon Source' : [frame1.iat[0,8]],'Carbon Source Flow Rate (sccm)' : [frame1.iat[0,9]],
                              'Carbon Source Flow Rate (Torr l/s)' : [frame1.iat[0,10]],
                              'Argon Flow Rate (sccm)' : [frame1.iat[0,11]], 'Argon Flow Rate (Torr l/s)' : [frame1.iat[0,12]]})
        zeroedFrame1 = zeroA.append(frame1)
        zeroedFrame1.index = [0, 1, 2, 3, 4, 5, 6]
        tmp = zeroedFrame1.dropna(axis=0, how='all')
        shrink1 = tmp.dropna(axis=1, how='all')
        Annealing = shrink1.fillna(0)

        zeroG = pd.DataFrame({'Time (min)' : [0],'Temp (degC)' : [Annealing.iat[-1,1]],'Pressure(Torr)' : [frame2.iat[0,2]],
                              'Sample Location (normalized from 0-1)' : [frame2.iat[0,3]],
                              'Helium Flow Rate (sccm)' : [frame2.iat[0,4]],'Helium Flow Rate (Torr l/s)' : [frame2.iat[0,5]], 
                              'Hydrogen Flow Rate (sccm)' : [frame2.iat[0,6]],'Hydrogen Flow Rate (Torr l/s)' : [frame2.iat[0,7]],
                              'Carbon Source' : [frame2.iat[0,8]],'Carbon Source Flow Rate (sccm)' : [frame2.iat[0,9]],
                              'Carbon Source Flow Rate (Torr l/s)' : [frame2.iat[0,10]],
                              'Argon Flow Rate (sccm)' : [frame2.iat[0,11]], 'Argon Flow Rate (Torr l/s)' : [frame2.iat[0,12]]})
        zeroedFrame2 = zeroG.append(frame2)
        zeroedFrame2.index = [0, 1, 2, 3, 4, 5, 6]
        tmp = zeroedFrame2.dropna(axis=0, how='all')
        shrink2 = tmp.dropna(axis=1, how='all')
        Growth = shrink2.fillna(0)

        zero3 = pd.DataFrame({'Time (min)' : [Growth.iat[-1,0]],'Temp (degC)' : [Growth.iat[-1,1]],
                              'Pressure(Torr)' : [frame3.iat[0,2]],'Sample Location (normalized from 0-1)' : [frame3.iat[0,3]],
                              'Helium Flow Rate (sccm)' : [frame3.iat[0,4]],'Helium Flow Rate (Torr l/s)' : [frame3.iat[0,5]],
                              'Hydrogen Flow Rate (sccm)' : [frame3.iat[0,6]],'Hydrogen Flow Rate (Torr l/s)' : [frame3.iat[0,7]],
                              'Carbon Source' : [frame3.iat[0,8]],'Carbon Source Flow Rate (sccm)' : [frame3.iat[0,9]],
                              'Carbon Source Flow Rate (Torr l/s)' : [frame3.iat[0,10]],
                              'Argon Flow Rate (sccm)' : [frame3.iat[0,11]], 'Argon Flow Rate (Torr l/s)' : [frame3.iat[0,12]]})
        zeroedFrame3 = zero3.append(frame3)
        zeroedFrame3.index = [0, 1, 2, 3, 4, 5, 6]
        total = 0
        for i in range(len(zeroedFrame3.index)):
            total += zeroedFrame3.iloc[i,0]
            zeroedFrame3.iat[i,0] = total
        tmp = zeroedFrame3.dropna(axis=0, how='all')
        shrink3 = tmp.dropna(axis=1, how='all')
        Cooling = shrink3.fillna(0)

        return Annealing, Growth, Cooling

    def plotRecipe(self):
        exp = int(self.experiment_selection.currentText())-1
        grapheneRec    = self.df.iloc[exp, 31:269]
        Anneal_series  = grapheneRec.iloc[1:79]
        Growth_series  = grapheneRec.iloc[80:159]
        Cooling_series = grapheneRec.iloc[160:269]

        mp.close('all')

        Anneal = self.collapse(Anneal_series)
        Growth = self.collapse(Growth_series)
        Cooling = self.collapse(Cooling_series)

        A, G, C = self.finalize(Anneal, Growth, Cooling)

        A = A.astype(str)
        G = G.astype(str)
        C = C.astype(str)

        self.figure, (A_temp, G_temp, C_temp) = mp.subplots(1, 3, sharey=True)

        A_temp.plot(A['Time (min)'], A['Temp (degC)'], 'b')
        A_temp.tick_params(axis='both', direction='in')
        A_gas = A_temp.twinx()
        A_gas.tick_params(axis='y', direction='in', labelright=False)

        G_temp.plot(G['Time (min)'], G['Temp (degC)'], 'b')
        G_temp.tick_params(axis='both', direction='in')
        G_gas = G_temp.twinx()   
        G_gas.tick_params(axis='y', direction='in', labelright=False)

        C_temp.plot([10,10,0], C['Temp (degC)'], 'b')
        C_temp.tick_params(axis='both', direction='in')
        C_gas = C_temp.twinx()
        C_gas.tick_params(axis='y', direction='in')

        A_gas.get_shared_y_axes().join(A_gas, G_gas, C_gas)

        hel_count = False
        hyd_count = False
        car_count = False
        arg_count = False

        for flow_rate in A[4:]:
            if flow_rate == 'Helium Flow Rate (sccm)':
                A_hel = A_gas.step(A['Time (min)'], A['Helium Flow Rate (sccm)'], 'r')
                hel_count = True
            if flow_rate == 'Hydrogen Flow Rate (sccm)':
                A_hyd = A_gas.step(A['Time (min)'], A['Hydrogen Flow Rate (sccm)'], 'm', label = 'Hydrogen Flow Rate')
                hyd_count = True
            if flow_rate == 'Carbon Source Flow Rate (sccm)':
                A_car = A_gas.step(A['Time (min)'], A['Carbon Source Flow Rate (sccm)'], 'g', label = 'Carbon Source Flow Rate')
                car_count = True
            if flow_rate == 'Argon Flow Rate (sccm)':
                A_arg = A_gas.step(A['Time (min)'], A['Argon Flow Rate (sccm)'], 'y', label = 'Argon Flow Rate')
                arg_count = True
       
        for flow_rate in G[4:]:
            if flow_rate == 'Helium Flow Rate (sccm)':
                G_hel = G_gas.step(G['Time (min)'], G['Helium Flow Rate (sccm)'], 'r', label = 'Helium Flow Rate')
                if hel_count == False:
                    hel_count = True
            if flow_rate == 'Hydrogen Flow Rate (sccm)':
                G_hyd = G_gas.step(G['Time (min)'], G['Hydrogen Flow Rate (sccm)'], 'm', label = 'Hydrogen Flow Rate')
                if hyd_count == False:
                    hyd_count = True
            if flow_rate == 'Carbon Source Flow Rate (sccm)':
                G_car = G_gas.step(G['Time (min)'], G['Carbon Source Flow Rate (sccm)'], 'g', label = 'Carbon Source Flow Rate')
                if car_count == False:
                    car_count = True
            if flow_rate == 'Argon Flow Rate (sccm)':
                G_arg = G_gas.step(G['Time (min)'], G['Argon Flow Rate (sccm)'], 'y', label = 'Argon Flow Rate')
                if arg_count == False:
                    arg_count = True
        
        for flow_rate in C[4:]:
            if flow_rate == 'Helium Flow Rate (sccm)':
                C_hel = C_gas.step(C['Time (min)'], C['Helium Flow Rate (sccm)'], 'r', label = 'Helium Flow Rate')
                if hel_count == False:
                    hel_count = True
            if flow_rate == 'Hydrogen Flow Rate (sccm)':
                C_hyd = C_gas.step(C['Time (min)'], C['Hydrogen Flow Rate (sccm)'], 'm', label = 'Hydrogen Flow Rate')
                if hyd_count == False:
                    hyd_count = True
            if flow_rate == 'Carbon Source Flow Rate (sccm)':
                C_car = C_gas.step(C['Time (min)'], C['Carbon Source Flow Rate (sccm)'], 'g', label = 'Carbon Source Flow Rate')
                if car_count == False:
                   car_count = True
            if flow_rate == 'Argon Flow Rate (sccm)':
                C_arg = C_gas.step(C['Time (min)'], C['Argon Flow Rate (sccm)'], 'y', label = 'Argon Flow Rate')
                if arg_count == False:
                    arg_count = True

        self.figure.suptitle('Graphene Growth Recipe Profile', fontsize = 20)
        A_temp.set_title('Annealing')
        G_temp.set_title('Growth')
        C_temp.set_title('Cooling')
    
        A_temp.set_ylabel('Temperature ($^\circ$C)', fontsize = 20)
        G_temp.set_xlabel('Time (min)', fontsize = 20)  
        C_gas.set_ylabel('Gas Flow Rate (sccm)', fontsize = 20)
    
        temperature = mlines.Line2D([],[],color = 'blue')
    
        recipe_handles = [temperature]
        recipe_labels = ['Temperature']

        if hel_count == True:
            helium = mlines.Line2D([],[],color = 'red')
            recipe_handles.append(helium)
            recipe_labels.append('Helium Flow Rate')
        if hyd_count == True:
            hydrogen = mlines.Line2D([],[],color = 'magenta')
            recipe_handles.append(hydrogen)
            recipe_labels.append('Hydrogen Flow Rate')        
        if car_count == True:
            carbon = mlines.Line2D([],[],color = 'green')
            recipe_handles.append(carbon)
            recipe_labels.append('Carbon Source Flow Rate')
        if arg_count == True:
            argon = mlines.Line2D([],[],color = 'yellow')
            recipe_handles.append(argon)
            recipe_labels.append('Argon Flow Rate')
    
        self.figure.legend(recipe_handles, recipe_labels, loc = 'upper right', fontsize = 12)

        self.figure.set_figheight(10)
        self.figure.set_figwidth(20)
        self.recipe_profile.draw()
        mp.show()

app=QtWidgets.QApplication([])
recipe=GSARecipe()
recipe.show()
app.exec_()

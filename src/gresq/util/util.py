from PyQt5 import QtGui, QtCore
import pandas as pd
import copy
import io
import requests
from mlxtend.frequent_patterns import apriori
from gresq.database import sample, preparation_step, dal, Base, mdf_forge, properties, recipe, raman_set, author, raman_spectrum,  sem_file , sem_analysis

class DownloadThread(QtCore.QThread):
    """
    Threading class for downloading files. Can be used to download files in parallel.

    url:                    Box download url.
    thread_id:              Thread ID that used to identify the thread.
    info:                   Dictionary for extra parameters.
    """
    downloadFinished = QtCore.pyqtSignal(object,int,object)
    def __init__(self,url,thread_id,info={}):
        super(DownloadThread,self).__init__()
        self.url = url
        self.thread_id = thread_id
        self.info = info
        self.data = None

        self.finished.connect(lambda: self.downloadFinished.emit(self.data,self.thread_id,self.info))

    def __del__(self):
        self.wait()

    def run(self):
        r = requests.get(self.url)
        self.data = r.content

class ItemsetsTableModel(QtCore.QAbstractTableModel):
    """
    Creates a PyQt TableModel that determines the support for different sets of attributes.
    If all rows contain data for a set of attributes, the support is '1' and if no rows contain
    data for a set, the support is '0'. This model is useful for conducting analyses on
    datasets where some rows are missing data. It can help determine which sets of attributes
    should be used on the basis of how much support there is for a particular set.
    """
    def __init__(self,parent=None):
        super(ItemsetsTableModel,self).__init__(parent=parent)
        self.frequent_itemsets = pd.DataFrame()
        self.items = []

    def rowCount(self, parent):
        return self.frequent_itemsets.shape[0]

    def columnCount(self, parent):
        return self.frequent_itemsets.shape[1]

    def data(self,index,role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                i,j = index.row(),index.column()
                value = self.frequent_itemsets.iloc[i,j]
                if pd.isnull(value):
                    return ''
                else:
                    return str(value)
        return QtCore.QVariant()

    def headerData(self,section,orientation,role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.frequent_itemsets.columns[section]
        return QtCore.QAbstractTableModel.headerData(self,section,orientation,role)

    def sort(self,column,order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.AscendingOrder:
            self.frequent_itemsets.sort_values(by=self.frequent_itemsets.columns[column],ascending=True,inplace=True)
        elif order == QtCore.Qt.DescendingOrder:
            self.frequent_itemsets.sort_values(by=self.frequent_itemsets.columns[column],ascending=False,inplace=True)
        self.layoutChanged.emit()

    def update_frequent_itemsets(self,df,min_support=0.5):
        self.beginResetModel()
        dfisnull = ~pd.isnull(df)
        self.items = df.columns
        self.frequent_itemsets = apriori(dfisnull,use_colnames=True,min_support=0.5)
        self.frequent_itemsets.columns = ['Support','Feature Set']
        self.frequent_itemsets['# Features'] = self.frequent_itemsets['Feature Set'].apply(lambda x: len(x))
        self.frequent_itemsets['Feature Set'] = self.frequent_itemsets['Feature Set'].apply(lambda x: tuple(x))
        self.frequent_itemsets['Support'] = self.frequent_itemsets['Support'].apply(lambda x: round(x,4))
        self.frequent_itemsets.sort_values(by='# Features',ascending=False,inplace=True)
        self.frequent_itemsets = self.frequent_itemsets[['Support','# Features','Feature Set']]
        self.endResetModel()

class ResultsTableModel(QtCore.QAbstractTableModel):
    """
    This PyQt TableModel is used for displaying data queried from a SQL query 
    in a TableView.
    """
    def __init__(self,parent=None):
        super(ResultsTableModel,self).__init__(parent=parent)
        self.df = pd.DataFrame()
        self.header_mapper = None

    def copy(self,fields=None):
        model = ResultsTableModel()
        model.df = self.df.copy()
        model.header_mapper = copy.deepcopy(self.header_mapper)

        if fields:
            for col in model.df.columns:
                if col not in fields:
                    model.df.drop(columns=col,inplace=True)
                    del model.header_mapper[col]

        return model

    def setHeaderMapper(self,models):
        self.header_mapper = {}
        for column in list(self.df.columns):
            for model in models:
                if hasattr(model,column):
                    info = getattr(model,column).info
                    value = info['verbose_name']
                    if info['std_unit']:
                        value += ' (%s)'%info['std_unit']
                    self.header_mapper[column] = value
                    break


    def read_sqlalchemy(self,statement,session,models=None):
        self.beginResetModel()
        self.df = pd.read_sql_query(statement,session.connection())
        
        if models:
            self.setHeaderMapper(models)
        else:
            self.header_mapper = None

        self.endResetModel()

    def value(self,column,row):
        if isinstance(column,str):
            item = self.df[column]
            return item.iloc[row].values[0]

    def rowCount(self, parent):
        return self.df.shape[0]

    def columnCount(self, parent):
        return self.df.shape[1]

    def data(self,index,role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                i,j = index.row(),index.column()
                value = self.df.iloc[i,j]
                if pd.isnull(value):
                    return ''
                else:
                    return str(value)
        return QtCore.QVariant()

    def headerData(self,section,orientation,role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if self.header_mapper:
                return self.header_mapper[self.df.columns[section]]
            else:
                return self.df.columns[section]

        return QtCore.QAbstractTableModel.headerData(self,section,orientation,role)

    def sort(self,column,order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.AscendingOrder:
            self.df = self.df.sort_values(by=self.df.columns[column],ascending=True)
        elif order == QtCore.Qt.DescendingOrder:
            self.df = self.df.sort_values(by=self.df.columns[column],ascending=False)
        self.layoutChanged.emit()


def downloadAllImageMasks(session,directory):
    def saveTo(data,path):
        with open(path,'wb') as f:
            f.write(data)
    for sample_model in session.query(sample).all():
        for analysis in sample_model.analyses:
            sem = analysis.sem_file_model
            mask_url = analysis.mask_url
            img_url = sem.url

            par_path = os.path.join(directory,sample_model)
            thread = DownloadThread(img_url,sample_model.id)
            thread.downloadFinished.connect(lambda x,y,z: saveTo)

def errorCheck(func):
    def wrapper(self,*args,**kwargs,success_text='Success!'):
        try:
            func(self,*args,**kwargs)
            success_dialog = QtGui.QMessageBox(self)
            success_dialog.setText(success_text)
            success_dialog.setWindowModality(QtCore.Qt.WindowModal)
            success_dialog.exec()
        except:
            error_dialog = QtGui.QMessageBox(self)
            error_dialog.setWindowModality(QtCore.Qt.WindowModal)
            error_dialog.setText("Error!")
            error_dialog.setInformativeText(str(e))
            error_dialog.exec()

    return wrapper  
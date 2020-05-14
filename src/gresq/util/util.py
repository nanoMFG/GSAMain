import os
import numpy as np
from PIL import Image
from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
import copy
import io
import operator
import requests
import traceback
import inspect
from mlxtend.frequent_patterns import apriori
import functools
import logging
from sqlalchemy import String, Integer, Float, Numeric, Date
from collections.abc import Sequence
from collections import OrderedDict, deque
import pyqtgraph as pg
from gresq.util.gwidgets import LabelMaker, SpacerMaker, BasicLabel, SubheaderLabel, HeaderLabel, MaxSpacer

logger = logging.getLogger(__name__)

sql_validator = {
    "int": lambda x: isinstance(x.property.columns[0].type, Integer),
    "float": lambda x: isinstance(x.property.columns[0].type, Float),
    "str": lambda x: isinstance(x.property.columns[0].type, String),
    "date": lambda x: isinstance(x.property.columns[0].type, Date),
}

operators = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}


def errorCheck(success_text=None, error_text="Error!",logging=True,show_traceback=False):
    """
    Decorator for class functions to catch errors and display a dialog box for a success or error.
    Checks if method is a bound method in order to properly handle parents for dialog box.

    success_text:               (str) What header to show in the dialog box when there is no error. None displays no dialog box at all.
    error_text:                 (str) What header to show in the dialog box when there is an error.
    logging:                    (bool) Whether to write error to log. True writes to log, False does not.
    show_traceback:             (bool) Whether to display full traceback in error dialog box. 
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if inspect.ismethod(func):
                self = args[0]
            else:
                self = None
            try:
                return func(*args, **kwargs)
                if success_text:
                    success_dialog = QtWidgets.QMessageBox(self)
                    success_dialog.setText(success_text)
                    success_dialog.setWindowModality(QtCore.Qt.WindowModal)
                    success_dialog.exec()
            except Exception as e:
                error_dialog = QtWidgets.QMessageBox(self)
                error_dialog.setWindowModality(QtCore.Qt.WindowModal)
                error_dialog.setText(error_text)
                if logging:
                    logger.exception(traceback.format_exc())
                if show_traceback:
                    error_dialog.setInformativeText(traceback.format_exc())
                else:
                    error_dialog.setInformativeText(str(e))
                error_dialog.exec()

        return wrapper
    return decorator


class ConfigParams:
    def __init__(self,box_config_path=None,mode='local',read=True,write=False,validate=False,test=False):
        assert mode in ['local','nanohub']
        self.box_config_path = box_config_path
        self.mode = mode
        self.read = read
        self.write = write
        self.validate = validate
        self.test = test

    def canRead(self):
        return self.read

    def canWrite(self):
        return self.write

    def canValidate(self):
        return self.validate

    def canRead(self):
        return self.read

    def setRead(self,flag):
        assert isinstance(flag,bool)
        self.read = flag

    def setWrite(self,flag):
        assert isinstance(flag,bool)
        self.write = flag

    def setValidate(self,flag):
        assert isinstance(flag,bool)
        self.validate = flag


class ResultsTableModel(QtCore.QAbstractTableModel):
    """
    This PyQt TableModel is used for displaying data queried from a SQL query 
    in a TableView.
    """

    def __init__(self, parent=None):
        super(ResultsTableModel, self).__init__(parent=parent)
        self.df = pd.DataFrame()
        self.header_mapper = None

    def copy(self, fields=None):
        model = ResultsTableModel()
        model.df = self.df.copy()
        model.header_mapper = copy.deepcopy(self.header_mapper)

        if fields:
            for col in model.df.columns:
                if col not in fields:
                    model.df.drop(columns=col, inplace=True)
                    del model.header_mapper[col]

        return model

    def setHeaderMapper(self, models):
        self.header_mapper = {}
        for column in list(self.df.columns):
            for model in models:
                if hasattr(model, column):
                    info = getattr(model, column).info
                    if "verbose_name" in info:
                        value = info["verbose_name"]
                    else:
                        logger.warning(
                            f"column: {column} in {model.__name__} has no verbose_name in info."
                        )
                        value = column
                    if "std_unit" in info:
                        if info["std_unit"]:
                            value += " (%s)" % info["std_unit"]
                    self.header_mapper[column] = value
                    break

    def read_sqlalchemy(self, statement, session, models=None):
        self.beginResetModel()
        self.df = pd.read_sql_query(statement, session.connection())

        if models:
            self.setHeaderMapper(models)
        else:
            self.header_mapper = None

        self.endResetModel()

    def value(self, column, row):
        if isinstance(column, str):
            item = self.df[column]
            return item.iloc[row].values[0]

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return self.df.shape[0]

    def columnCount(self, parent):
        if parent.isValid():
            return 0
        return self.df.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                i, j = index.row(), index.column()
                value = self.df.iloc[i, j]
                if pd.isnull(value):
                    return ""
                else:
                    return str(value)
        return QtCore.QVariant()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if self.header_mapper:
                return self.header_mapper[self.df.columns[section]]
            else:
                return self.df.columns[section]

        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.AscendingOrder:
            self.df = self.df.sort_values(by=self.df.columns[column], ascending=True)
        elif order == QtCore.Qt.DescendingOrder:
            self.df = self.df.sort_values(by=self.df.columns[column], ascending=False)
        self.layoutChanged.emit()


class ItemsetsTableModel(QtCore.QAbstractTableModel):
    """
    Creates a PyQt TableModel that determines the support for different sets of attributes.
    If all rows contain data for a set of attributes, the support is '1' and if no rows contain
    data for a set, the support is '0'. This model is useful for conducting analyses on
    datasets where some rows are missing data. It can help determine which sets of attributes
    should be used on the basis of how much support there is for a particular set.
    """

    def __init__(self, parent=None):
        super(ItemsetsTableModel, self).__init__(parent=parent)
        self.frequent_itemsets = pd.DataFrame()
        self.items = []

    def rowCount(self, parent):
        return self.frequent_itemsets.shape[0]

    def columnCount(self, parent):
        return self.frequent_itemsets.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                i, j = index.row(), index.column()
                value = self.frequent_itemsets.iloc[i, j]
                if pd.isnull(value):
                    return ""
                else:
                    return str(value)
        return QtCore.QVariant()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.frequent_itemsets.columns[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.AscendingOrder:
            self.frequent_itemsets.sort_values(
                by=self.frequent_itemsets.columns[column], ascending=True, inplace=True
            )
        elif order == QtCore.Qt.DescendingOrder:
            self.frequent_itemsets.sort_values(
                by=self.frequent_itemsets.columns[column], ascending=False, inplace=True
            )
        self.layoutChanged.emit()

    def update_frequent_itemsets(self, df, min_support=0.5):
        self.beginResetModel()
        dfisnull = ~pd.isnull(df)
        self.items = df.columns
        self.frequent_itemsets = apriori(dfisnull, use_colnames=True, min_support=0.5)
        self.frequent_itemsets.columns = ["Support", "Feature Set"]
        self.frequent_itemsets["# Features"] = self.frequent_itemsets[
            "Feature Set"
        ].apply(lambda x: len(x))
        self.frequent_itemsets["Feature Set"] = self.frequent_itemsets[
            "Feature Set"
        ].apply(lambda x: tuple(x))
        self.frequent_itemsets["Support"] = self.frequent_itemsets["Support"].apply(
            lambda x: round(x, 4)
        )
        self.frequent_itemsets.sort_values(
            by="# Features", ascending=False, inplace=True
        )
        self.frequent_itemsets = self.frequent_itemsets[
            ["Support", "# Features", "Feature Set"]
        ]
        self.endResetModel()
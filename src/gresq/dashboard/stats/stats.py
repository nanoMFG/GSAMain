import pandas as pd
import pyqtgraph as pg
import numpy as np
from pandas.api.types import is_numeric_dtype
import copy
from sklearn.manifold import TSNE
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QColor
from grdb.database.v1_1_0 import dal, Base
from grdb.database.v1_1_0.models import (
    Sample,
    Recipe,
    Properties,
    Author,
    PreparationStep,
    RamanSet,
    RamanSpectrum,
    SemFile,
    SemAnalysis,
)
from gresq.util.util import ItemsetsTableModel, ResultsTableModel, BasicLabel, HeaderLabel, SubheaderLabel


class PlotWidget(QtGui.QWidget):
    sigClicked = QtCore.pyqtSignal(object, object)

    # selectedBrush = QtGui.QBrush(QtGui.QColor(0, 255, 0))

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent=parent)
        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.model = ResultsTableModel()

        self.xaxisbox = QtGui.QComboBox()
        self.yaxisbox = QtGui.QComboBox()
        self.zaxisbox = QtGui.QComboBox()
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setMenuEnabled(False)

        # self.scatter_plot emits signal when point is clicked
        # How to catch signal?
        self.scatter_plot = pg.ScatterPlotItem()
        self.plot_widget.addItem(self.scatter_plot)
        self.selectedPt = None

        # Connect signal to slot - slot should be a function in the class defining the display below the plot
        # self.scatter_plot.sigClicked.connect(lambda plot, points: self.sigClicked.emit(plot,points))
        self.scatter_plot.sigClicked.connect(self.onClickedPoint)

        self.xaxisbox.activated.connect(self.updatePlot)
        self.yaxisbox.activated.connect(self.updatePlot)

        self.layout.addWidget(QtGui.QLabel("X Axis"), 0, 0, 1, 1)
        self.layout.addWidget(QtGui.QLabel("Y Axis"), 0, 1, 1, 1)
        self.layout.addWidget(self.xaxisbox, 1, 0, 1, 1)
        self.layout.addWidget(self.yaxisbox, 1, 1, 1, 1)
        self.layout.addWidget(self.plot_widget, 2, 0, 1, 2)

    def onClickedPoint(self, plot, points):
        newPt = points[0]
        newPt.setBrush(0, 0, 255)
        if self.selectedPt != None:
            if self.selectedPt.pos() != newPt.pos():
                self.selectedPt.setBrush(211, 211, 211)
        self.selectedPt = newPt
        self.sigClicked.emit(plot, points)

    def setModel(self, model, xfields=None, yfields=None):
        self.model = model
        self.yaxisbox.clear()
        self.xaxisbox.clear()
        for c in self.model.df.columns:
            if is_numeric_dtype(self.model.df[c]):
                if xfields:
                    if c in xfields:
                        self.xaxisbox.addItem(c)
                else:
                    self.xaxisbox.addItem(c)
                if yfields:
                    if c in yfields:
                        self.yaxisbox.addItem(c)
                else:
                    self.yaxisbox.addItem(c)
        self.scatter_plot.clear()

    def updatePlot(self):
        x = self.xaxisbox.currentText()
        y = self.yaxisbox.currentText()
        scatter_data = self.model.df.loc[:, [x, y, "id"]].dropna()

        # Find the id of each row corresponding to an (x, y) point in the plot
        defaultBrush = QtGui.QBrush(QtGui.QColor(211, 211, 211))
        if x != y:
            self.scatter_plot.setData(
                x=scatter_data[x],
                y=scatter_data[y],
                brush=defaultBrush,
                data=scatter_data["id"].tolist(),
            )
        else:
            self.scatter_plot.setData(
                x=scatter_data.iloc[:, 0],
                y=scatter_data.iloc[:, 0],
                brush=defaultBrush,
                data=scatter_data["id"].tolist(),
            )

        xbounds = self.scatter_plot.dataBounds(ax=0)
        if None not in xbounds:
            self.plot_widget.setXRange(*xbounds)
        ybounds = self.scatter_plot.dataBounds(ax=1)
        if None not in ybounds:
            self.plot_widget.setYRange(*ybounds)
        self.plot_widget.setLabel(text=x, axis="bottom")
        self.plot_widget.setLabel(text=y, axis="left")


class TSNEWidget(QtGui.QStackedWidget):
    tsneClicked = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(TSNEWidget, self).__init__(parent=parent)
        self.itemsets_model = ItemsetsTableModel()

        self.tsne = TSNEPlot()
        self.tsne.tsneClicked.connect(
            lambda plot, points: self.tsneClicked.emit(plot, points)
        )
        self.feature = FeatureSelectionItem()
        self.addWidget(self.feature)
        self.addWidget(self.tsne)

        self.tsne.run_button.clicked.connect(
            lambda: self.tsne.run(self.feature.get_selected_features())
        )
        self.feature.go_button.clicked.connect(lambda: self.setCurrentWidget(self.tsne))
        self.tsne.back_button.clicked.connect(
            lambda: self.setCurrentWidget(self.feature)
        )

    def setModel(self, model, fields=None):
        self.results_model = model.copy(fields=fields)
        self.itemsets_model.update_frequent_itemsets(
            df=self.results_model.df.select_dtypes(include=[np.number, np.bool]),
            min_support=float(self.feature.min_support_edit.text()),
        )
        self.feature.setModel(self.itemsets_model)
        self.tsne.setModel(self.results_model)


class TSNEPlot(QtGui.QWidget):
    tsneClicked = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(TSNEPlot, self).__init__(parent=parent)
        self.model = ResultsTableModel()

        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.random_seed = np.random.randint(1, 99999)
        self.perplexity = 30
        self.lr = 200.0

        self.plot_widget = pg.PlotWidget()
        self.tsne_plot = pg.ScatterPlotItem(
            symbol="o",
            size=10,
            pen=pg.mkPen(width=0.2, color="b"),
            brush=pg.mkBrush(0.7),
            antialias=True,
        )
        self.tsne_plot.sigClicked.connect(self.pointClicked)
        self.selectedPt = None
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.addItem(self.tsne_plot)

        self.random_seed_edit = QtGui.QLineEdit(str(self.random_seed))
        self.random_seed_edit.setValidator(QtGui.QIntValidator(1, 99999))
        self.random_seed_edit.setMaximumWidth(75)
        self.perplexity_edit = QtGui.QLineEdit(str(self.perplexity))
        self.perplexity_edit.setValidator(QtGui.QIntValidator(1, 50))
        self.perplexity_edit.setMaximumWidth(75)
        self.lr_edit = QtGui.QLineEdit(str(self.lr))
        self.lr_edit.setValidator(QtGui.QDoubleValidator(10, 1000, 3))
        self.lr_edit.setMaximumWidth(75)

        self.select_feature = QtGui.QComboBox()

        self.run_button = QtGui.QPushButton("Run t-SNE")
        self.back_button = QtGui.QPushButton("<<< Feature Selection")
        self.save_button = QtGui.QPushButton("Export Image")
        self.save_button.setIcon(
            self.style().standardIcon(QtGui.QStyle.SP_FileDialogStart)
        )

        self.legend = pg.GradientWidget(orientation="right")
        self.legend.setMaximumWidth(50)
        self.legend.sigGradientChangeFinished.connect(self.colorChange)
        # print(self.legend.colorMap())

        self.layout.addWidget(QtGui.QLabel("Perplexity"), 0, 0, 1, 1)
        self.layout.addWidget(self.perplexity_edit, 0, 1, 1, 1)
        self.layout.addWidget(QtGui.QLabel("Random Seed"), 1, 0, 1, 1)
        self.layout.addWidget(self.random_seed_edit, 1, 1, 1, 1)
        self.layout.addWidget(QtGui.QLabel("Learning Rate"), 2, 0, 1, 1)
        self.layout.addWidget(self.lr_edit, 2, 1, 1, 1)
        self.layout.addWidget(self.save_button, 3, 0, 1, 1)
        self.layout.addWidget(self.run_button, 3, 1, 1, 2)
        self.layout.addWidget(self.plot_widget, 4, 0, 4, 3)
        self.layout.addWidget(self.select_feature, 8, 0, 1, 3)
        self.layout.addWidget(self.back_button, 9, 0, 1, 3)
        self.layout.addWidget(self.legend, 4, 4, 4, 1)
        # self.layout.setColumnStretch(4, 1)

        self.select_feature.activated[str].connect(self.setBrushes)

    # def drawLegend(self):
    # 	qp = QtGui.QPainter(self)
    # 	color = QtGui.QColor(255, 0, 0)
    # 	qp.fillRect(2, 2, 1, 2, color)

    def colorChange(self):
        feature = self.select_feature.currentText()
        if feature:
            self.setBrushes(feature)

    def pointClicked(self, plot, points):
        # Mark clicked point - give it an extra thick border
        newPt = points[0]
        newPt.setPen(pg.mkPen(width=0.4, color="r"))
        if self.selectedPt != None:
            if self.selectedPt.pos() != newPt.pos():
                self.selectedPt.setPen(pg.mkPen(width=0.2, color="b"))
        self.selectedPt = newPt
        self.tsneClicked.emit(plot, points)

    def setModel(self, model):
        self.model = model
        self.select_feature.clear()
        self.select_feature.addItem("No Coloring")
        self.select_feature.addItems([
            self.model.headerData(h,orientation=QtCore.Qt.Horizontal) for h in range(len(self.model.df.columns)) 
            if self.model.headerData(h,orientation=QtCore.Qt.Horizontal)!='id'])
        self.tsne_plot.clear()

    def getColumnName(self,feature):
        mapper = self.model.header_mapper
        for key,value in mapper.items():
            if feature == value:
                return key

        return feature

    def setBrushes(self, feature):
        feature = self.getColumnName(feature)
        if feature in self.model.df.columns:
            brushes = []
            if is_numeric_dtype(self.model.df[feature]):
                values = self.model.df[feature][self.nonnull_indexes]
                maxVal = max(values.dropna())
                minVal = min(values.dropna())
                if pd.isnull(minVal) or pd.isnull(maxVal):
                    brushes = [pg.mkBrush(0.2)] * len(values)
                else:
                    for val in values:
                        print(type(val))
                        if not np.isnan(val):
                            if maxVal == minVal:
                                percent = 0.5
                            else:
                                percent = (val - minVal) / (maxVal - minVal)
                            # print("Percent: ", int(percent*100), " Min: ", minVal, " Max: ", maxVal, " Value: ", val)
                            brushes.append(self.makeColoredBrush(percent, val))
                        else:
                            brushes.append(pg.mkBrush(0.2))
            else:
                values = list(self.model.df[feature][self.nonnull_indexes].unique())
                for val in self.model.df[feature][self.nonnull_indexes]:

                    if (not isinstance(val, str)) and (not np.isnan(val)):
                        index = int(values.index(val) / len(values))
                        brushes.append(pg.mkBrush(pg.intColor(index)))
                    else:
                        brushes.append(pg.mkBrush(0.2))
            self.tsne_plot.setBrush(brushes)

    # Returns a QBrush based on color gradient of legend
    def makeColoredBrush(self, percent, value):
        color = self.legend.getColor(percent)
        print("Value: ", value, " Percent: ", percent, " Color: ", color.getRgb())
        return pg.mkBrush(color)
        # color1 = self.legend.getColor1()
        # color2 = self.legend.getColor2()
        # hue = int(percent*(color2.hslHue() - color1.hslHue()) + color1.hslHue())
        # color = TSNEPlot.createColor(hue, color1.hslSaturation(), color1.lightness())
        # return pg.mkBrush(color)

    @staticmethod
    def createColor(h, s, l):
        color = QColor()
        color.setHsl(h, s, l)
        return color

    def resetBounds(self):
        xbounds = self.tsne_plot.dataBounds(ax=0)
        if None not in xbounds:
            self.plot_widget.setXRange(*xbounds)
        ybounds = self.tsne_plot.dataBounds(ax=1)
        if None not in ybounds:
            self.plot_widget.setYRange(*ybounds)

    def showError(self, msg):
        error_msg = QtWidgets.QErrorMessage()
        error_msg.setWindowTitle("GrResQ: Warning")
        error_msg.showMessage(msg)
        error_msg.exec_()

    def run(self, features):
        self.features = features
        self.tsne = TSNE(random_state=self.random_seed)
        # print(self.model.df.columns)
        # TODO: self.nonnull_indexes is often undefined

        if not (pd.Series(self.features).isin(self.model.df.columns).all()):
            self.showError(
                "Features: " + self.features + " not in model: " + self.model.__name__
            )
            return

        self.nonnull_indexes = ~self.model.df[self.features].isnull().any(1)
        if self.nonnull_indexes.empty:
            self.showError(
                "Features: "
                + self.features
                + " contain null value: "
                + self.model.__name__
            )
            return

        tsne_input = self.model.df[self.features][self.nonnull_indexes]
        ids = self.model.df["id"][self.nonnull_indexes]
        if tsne_input.empty:
            self.showError("Input dataframe should not be empty.")
            return
        elif tsne_input.shape[0] < 2:
            self.showError("TSNE fit requires a minimum of 2 samples.")
            return
        self.tsne.fit(tsne_input)
        self.tsne_plot.clear()

        # if model:
        #     i = int(model.df['id'].values[index.row()])
        # else:
        #     i = index
        # s = session.query(sample).filter(sample.id==i)[0]

        self.tsne_plot.setData(
            x=self.tsne.embedding_[:, 0],
            y=self.tsne.embedding_[:, 1],
            data=ids.tolist()
        )
        self.resetBounds()


class FeatureSelectionItem(QtGui.QWidget):
    def __init__(self, parent=None):
        super(FeatureSelectionItem, self).__init__(parent=parent)
        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.feature_list = QtGui.QListWidget()
        self.feature_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.feature_list.itemSelectionChanged.connect(self.featureChange)

        self.min_support = 0.5

        self.model = ItemsetsTableModel()
        self.itemsets_view = QtGui.QTableView()
        self.itemsets_view.verticalHeader().setVisible(False)
        # self.itemsets_view.setMinimumHeight(200)
        self.itemsets_view.setMinimumWidth(300)
        self.itemsets_view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.itemsets_view.setSortingEnabled(True)
        self.itemsets_view.activated.connect(
            lambda x: self.select_features(self.model, x)
        )

        self.min_support_edit = QtGui.QLineEdit(str(self.min_support))
        self.min_support_edit.setFixedWidth(75)
        self.min_support_edit.setValidator(QtGui.QDoubleValidator(0, 1, 3))

        self.go_button = QtGui.QPushButton("Go to Plot >>>")
        self.go_button.setEnabled(False)

        itemsets_label = SubheaderLabel("Frequent Feature Sets")
        manual_label = SubheaderLabel("Manual Feature Selection")
        min_support_label = BasicLabel("Minimum Support")
        min_support_label.setAlignment(QtCore.Qt.AlignRight)

        self.layout.addWidget(itemsets_label, 0, 0)
        self.layout.addWidget(min_support_label, 1, 1, 1, 1)
        self.layout.addWidget(self.min_support_edit, 1, 2, 1, 1)
        self.layout.addWidget(self.itemsets_view, 2, 0, 1, 3)
        self.layout.addWidget(manual_label, 3, 0)
        self.layout.addWidget(self.feature_list, 4, 0, 1, 3)
        self.layout.addWidget(self.go_button, 5, 0, 1, 3)

    # Only allow plotting after features are selected
    def featureChange(self):
        if len(self.feature_list.selectedItems()) == 0:
            self.go_button.setEnabled(False)
        else:
            self.go_button.setEnabled(True)

    def setModel(self, model):
        self.model = model
        self.itemsets_view.setModel(self.model)
        header = self.itemsets_view.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        self.feature_list.clear()
        self.feature_list.addItems(self.model.items)

    def select_features(self, model, index):
        self.feature_list.clearSelection()
        for item in model.frequent_itemsets["Feature Set"].iloc[index.row()]:
            list_item = self.feature_list.findItems(item, QtCore.Qt.MatchExactly)[0]
            list_item.setSelected(True)

    def get_selected_features(self):
        return [s.text() for s in self.feature_list.selectedItems()]


class Legend(QtGui.QWidget):
    def __init__(
        self,
        color1=TSNEPlot.createColor(225, 128, 128),
        color2=TSNEPlot.createColor(45, 128, 128),
    ):
        super().__init__()
        self.initUI()
        self.color1 = color1
        self.color2 = color2
        self.color_scale = pg.GradientEditorItem()
        self.color_scale.loadPreset("thermal")
        self.color_scale.setOrientation("right")
        self.color_scale.setColorMode("hsv")

    def initUI(self):
        self.setGeometry(0, 0, 10, 100)

    def getColor1(self):
        return self.color1

    def getColor2(self):
        return self.color2

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        g = self.color_scale.getGradient()
        # g = QtGui.QLinearGradient(0.0, 0.0, 0, self.height())
        # g.setColorAt(0, self.color1)
        # g.setColorAt(1, self.color2)
        qp.fillRect(0, 0, self.width(), self.height(), g)

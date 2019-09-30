from __future__ import division
import pandas as pd
import numpy as np
import sys, operator, os
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import cv2
import io
import sip
import requests
from PIL import Image
from gresq.util.models import ResultsTableModel
from gresq.util.box_adaptor import BoxAdaptor
from gresq.dashboard.stats import TSNEWidget, PlotWidget
# from gresq.util.csv2db2 import build_db
from gresq.database import sample, preparation_step, dal, Base, mdf_forge, properties, recipe, raman_set, author, raman_spectrum
from sqlalchemy import String, Integer, Float, Numeric
from gresq.config import config
import scipy
from scipy import signal
# from statsmodels.nonparametric.smoothers_lowess import lowess

"""
Each primary field will correspond to an MDF schema. Each of these are models
(whose schema is in gresq/database.py) that are stored as separate datasets on MDF
so when a user selects a primary field, they are searching a particular group
of datasets on MDF.
	mdf_forge_fields:			mdf_forge schema. This corresponds to the raw data.
	raman_spectrum_fields:		raman_spectrum schema. This corresponds the Raman postprocessing (peaks, fwhm, etc.)
	sem_postprocess_fields		sem_postprocess schema. This corresponds to SEM postprocessing
								like coverage, orientation, etc. The raw data may contain some
								of this information as well if the user inputs it during submission.
								However, that information is stored in the mdf_forge model.
"""

preparation_fields = [
	"name",
	"duration",
	"furnace_temperature",
	"furnace_pressure",
	"sample_location",
	"helium_flow_rate",
	"hydrogen_flow_rate",
	"carbon_source",
	"carbon_source_flow_rate",
	"argon_flow_rate",
	"cooling_rate"
	]

properties_fields = [
    "growth_coverage",
    "shape",
    "average_thickness_of_growth",
    "standard_deviation_of_growth",
    "number_of_layers",
    "domain_size"
    ]

recipe_fields = [
    "catalyst",
    "tube_diameter",
    "cross_sectional_area",
    "tube_length",
    "base_pressure",
    "thickness",
    "diameter",
    "length",
    "sample_surface_area",
    "dewpoint"
    ]

hybrid_recipe_fields = [
    "maximum_temperature",
    "maximum_pressure",
    "average_carbon_flow_rate",
    "carbon_source",
    "uses_helium",
    "uses_hydrogen",
    "uses_argon"
    ]

author_fields = [
    "last_name",
    "first_name",
    "institution"
]

raman_fields = [
    "gp_to_g",
    "d_to_g"
]

spectrum_fields = [
    "percent",
    "d_peak_shift",
    "d_peak_amplitude",
    "d_fwhm",
    "g_peak_shift",
    "g_peak_amplitude",
    "g_fwhm",
    "g_prime_peak_shift",
    "g_prime_peak_amplitude",
    "g_prime_fwhm"    
]

sample_fields = [
    "id",
    "experiment_date",
    "validated"
]

results_fields = sample_fields+properties_fields+raman_fields

selection_list = {
    'Experimental Conditions':{'fields':recipe_fields,'model':recipe},
    'Preparation': {'fields':preparation_fields,'model':preparation_step},
    'Properties': {'fields':properties_fields,'model':properties},
    'Raman Analysis': {'fields':raman_fields,'model':raman_set},
    'Provenance Information': {'fields':author_fields,'model':author}
    }

sql_validator = {
    'int': lambda x: isinstance(x.property.columns[0].type,Integer),
    'float': lambda x: isinstance(x.property.columns[0].type,Float),
    'str': lambda x: isinstance(x.property.columns[0].type,String)
}

operators = {
    '==': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '>': operator.gt,
    '<=': operator.le,
    '>=': operator.ge
}

label_font = QtGui.QFont("Helvetica", 28, QtGui.QFont.Bold)

def convertScripts(text):
    if '^' in text:
        words = text.split('^')
        new_text = "%s<sup>%s</sup>"%(words[0],words[1])
    elif '_' in text:
        words = text.split('_')
        new_text = "%s<sub>%s</sub>"%(words[0],words[1])
    else:
        new_text = text

    return new_text

class GSAQuery(QtGui.QWidget):
    """
    Main query widget.
    """
    def __init__(self,privileges={'read':True,'write':False,'validate':False},parent=None):
        super(GSAQuery,self).__init__(parent=parent)
        self.privileges = privileges
        self.filters = []
        self.filter_fields = QtGui.QStackedWidget()
        self.filter_fields.setMaximumHeight(50)
        self.filter_fields.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)
        self.filters_dict = {}
        for selection in selection_list.keys():
            for field in selection_list[selection]['fields']:
                widget = self.generate_field(model=selection_list[selection]['model'],field=field)
                widget.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Preferred)
                self.filters_dict[getattr(selection_list[selection]['model'],field).info['verbose_name']] = widget
                self.filter_fields.addWidget(widget)

        self.primary_selection = QtGui.QComboBox()
        self.primary_selection.addItems(sorted(selection_list.keys()))
        self.primary_selection.activated[str].connect(self.populate_secondary)

        self.secondary_selection = QtGui.QComboBox()
        self.secondary_selection.activated[str].connect(lambda x: self.filter_fields.setCurrentWidget(self.filters_dict[x]))

        self.filter_table = QtGui.QTableWidget()
        self.filter_table.setColumnCount(4)
        self.filter_table.setHorizontalHeaderLabels(['Field','','Value',''])
        header = self.filter_table.horizontalHeader()
        header.setSectionResizeMode(0, QtGui.QHeaderView.Stretch)
        self.filter_table.setColumnWidth(1,30)
        self.filter_table.setColumnWidth(2,100)
        self.filter_table.setColumnWidth(3,25)
        self.filter_table.setWordWrap(True)
        self.filter_table.verticalHeader().setVisible(False)
        self.filter_table.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Preferred)

        self.results = ResultsWidget()
        self.results.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)

        self.preview = PreviewWidget(privileges=self.privileges)
        if self.privileges['validate'] or self.privileges['write']:
            self.preview.admin_tab.updateQuery.connect(lambda: self.query(self.filters))
            self.preview.admin_tab.queryUnvalidated.connect(lambda: self.query([sample.validated.is_(False)]))

        self.addFilterBtn = QtGui.QPushButton('Add Filter')
        self.addFilterBtn.clicked.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))

        # self.searchBtn = QtGui.QPushButton('Search')
        # self.searchBtn.clicked.connect(self.query)

        searchLabel = QtGui.QLabel('Query')
        searchLabel.setFont(label_font)

        resultsLabel = QtGui.QLabel('Results')
        resultsLabel.setFont(label_font)

        searchLayout = QtGui.QGridLayout()
        searchLayout.setAlignment(QtCore.Qt.AlignTop)
        searchLayout.addWidget(self.primary_selection,1,0)
        searchLayout.addWidget(self.secondary_selection,2,0)
        searchLayout.addWidget(self.filter_fields,3,0)
        searchLayout.addWidget(self.addFilterBtn,4,0)
        searchLayout.addWidget(self.filter_table,5,0,4,1)

        resultsLayout = QtGui.QSplitter(QtCore.Qt.Vertical)
        # resultsLayout.setAlignment(QtCore.Qt.AlignTop)
        resultsLayout.addWidget(self.results)
        resultsLayout.addWidget(self.preview)

        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.addWidget(searchLabel,0,0)
        self.layout.addLayout(searchLayout,1,0)
        self.layout.addWidget(resultsLabel,0,1)
        self.layout.addWidget(resultsLayout,1,1)

        self.primary_selection.activated[str].emit(self.primary_selection.currentText())
        self.secondary_selection.activated[str].emit(self.secondary_selection.currentText())
        self.results.plotClicked.connect(lambda plot, points: self.preview.select(index=points[0].data()))


    def generate_field(self,model,field):
        """
        Generates an input selected field of selected model.

        model:          sqlalchemy model to which the field corresponds
        field:          column within the sqlalchemy model
        """
        cla = model
        if sql_validator['int'](getattr(cla,field)) == True:
            vf = ValueFilter(model=cla,field=field,validate=int)
            vf.input.returnPressed.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))
            return vf
        elif sql_validator['float'](getattr(cla,field)) == True:
            vf = ValueFilter(model=cla,field=field,validate=int)
            vf.input.returnPressed.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))
            return vf
        elif sql_validator['str'](getattr(cla,field)) == True:
            with dal.session_scope() as session:
                classes = []
                for v in session.query(getattr(cla,field)).distinct():
                    classes.append(getattr(v,field))
            return ClassFilter(model=cla,field=field,classes=classes,validate=str)
        else:
            raise ValueError('Field %s data type (%s) not recognized.'%(field,getattr(cla,field).property.columns[0].type))

    def populate_secondary(self,selection):
        """
        Populates secondary selection combo box with fields corresponding to the primary selection model.
        """
        # selection_list = {
        #   'Sample Fields': {'fields':mdf_forge_fields,'model':mdf_forge},
        #   'Raman Analysis Fields': {'fields':raman_spectrum_fields,'model':None},
        #   'SEM Analysis Fields': {'fields':sem_postprocess_fields,'model':None}
        #   }

        self.secondary_selection.clear()
        self.secondary_selection.addItems([getattr(selection_list[selection]['model'],v).info['verbose_name'] for v in selection_list[selection]['fields']])

    def addFilter(self,widget):
        """
        Adds filter to search query. Three actions take place:
            - A row is added to filter_table
            - A sqlalchemy filter object is appended to the filters list
            - A SQL query is performed using new filters list.
        """
        if widget.valid():
            self.filters.append(widget.sqlalchemy_filter())
            row = self.filter_table.rowCount()
            self.filter_table.insertRow(row)
            self.filter_table.setItem(row,0,QtGui.QTableWidgetItem(widget.label.text()))
            self.filter_table.setItem(row,1,QtGui.QTableWidgetItem(widget.operation))
            self.filter_table.setItem(row,2,QtGui.QTableWidgetItem(str(widget.value)))
            # self.filter_table.resizeRowsToContents()

            delRowBtn = QtGui.QPushButton('X')
            delRowBtn.clicked.connect(self.deleteRow)
            self.filter_table.setCellWidget(row,3,delRowBtn)
            widget.clear()
            self.query(self.filters)

    def deleteRow(self):
        """
        Deletes filter associated with row in filter_table when delete button is activated. Three actions take place:
            - The row is deleted from filter_table
            - The corresponding sqlalchemy filter object is removed from the filters list
            - A SQL query is performed using new filters list.
        """
        row = self.filter_table.indexAt(self.sender().parent().pos()).row()
        if row >= 0:
            self.filter_table.removeRow(row)
            del self.filters[row]
            self.query(self.filters)

    def query(self,filters):
        """
        Runs query on results widget. This is a separate function so as to make the selection signal work properly.
        This is because the model must be set before selection signalling can be connected.
        """
        if self.privileges['validate']:
            self.results.query(filters)
        else:
            self.results.query(filters+[sample.validated==True])
        self.results.results_table.selectionModel().currentChanged.connect(lambda x: self.preview.select(self.results.results_model,x))

class ValueFilter(QtGui.QWidget):
    """
    Creates new filter input for numeric fields.

    model:          sqlalchemy model to which the field corresponds
    field:          column within the sqlalchemy model
    """
    def __init__(self,model,field,validate=None,parent=None):
        super(ValueFilter,self).__init__(parent=parent)
        self.field = field
        self.model = model
        self.validate = validate

        layout = QtGui.QGridLayout(self)
        self.label = QtGui.QLabel(getattr(model,field).info['verbose_name'])
        # self.label.setFixedWidth(150)
        self.label.setWordWrap(True)
        self.comparator = QtGui.QComboBox()
        self.comparator.setFixedWidth(50)
        self.comparator.addItems(sorted(list(operators)))
        self.input = QtGui.QLineEdit()
        self.input.setFixedWidth(100)

        if self.validate == int:
            self.input.setValidator(QtGui.QIntValidator())
        elif self.validate == float:
            self.input.setValidator(QtGui.QDoubleValidator())

        layout.addWidget(self.label,0,0)
        layout.addWidget(self.comparator,0,1)
        layout.addWidget(self.input,0,2)

    @property
    def operation(self):
        return self.comparator.currentText()

    @property
    def value(self):
        return self.validate(self.input.text())

    def valid(self):
        try:
            self.value
            return True
        except:
            return False

    def sqlalchemy_filter(self):
        return operators[self.comparator.currentText()](getattr(self.model,self.field),self.value)

    def clear(self):
        self.input.clear()

class ClassFilter(QtGui.QWidget):
    """
    Creates new filter input for class (string) fields.

    model:          sqlalchemy model to which the field corresponds
    field:          column within the sqlalchemy model
    """
    def __init__(self,model,field,validate=None,classes=[],parent=None):
        super(ClassFilter,self).__init__(parent=parent)
        self.field = field
        self.model = model
        self.validate = validate

        layout = QtGui.QGridLayout(self)
        self.label = QtGui.QLabel(getattr(model,field).info['verbose_name'])
        # self.label.setFixedWidth(150)
        self.label.setWordWrap(True)
        self.classes = QtGui.QComboBox()
        self.classes.addItems(classes)

        layout.addWidget(self.label,0,0)
        layout.addWidget(self.classes,0,1)

    @property
    def operation(self):
        return 'AND'

    @property
    def value(self):
        assert self.classes.count() > 0
        return self.validate(self.classes.currentText())

    def valid(self):
        try:
            self.value
            return True
        except:
            return False

    def sqlalchemy_filter(self):
        return operator.eq(getattr(self.model,self.field),self.value)

    def clear(self):
        pass

class DetailWidget(QtGui.QWidget):
    def __init__(self,parent=None):
        super(DetailWidget,self).__init__(parent=parent)
        self.properties = FieldsDisplayWidget(fields=properties_fields,model=properties)
        self.conditions = FieldsDisplayWidget(fields=recipe_fields+hybrid_recipe_fields,model=recipe)

        propertiesLabel = QtGui.QLabel('Properties')
        propertiesLabel.setFont(label_font)
        conditionsLabel = QtGui.QLabel('Conditions')
        conditionsLabel.setFont(label_font)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(propertiesLabel,0,0)
        layout.addWidget(self.properties,1,0)
        layout.addWidget(conditionsLabel,0,1)
        layout.addWidget(self.conditions,1,1)

    def update(self,properties_model,recipe_model):
        self.properties.setData(properties_model)
        self.conditions.setData(recipe_model)

class PreviewWidget(QtGui.QTabWidget):
    """
    Widget for displaying data associated with selected sample. Contains tabs for:
        -Graphene details
        -SEM data (raw and postprocessed)
        -Raman data (raw and postprocessed)
        -Recipe visualization
        -Provenance information
    """
    def __init__(self,privileges=None,parent=None):
        super(PreviewWidget,self).__init__(parent=parent)
        self.privileges = privileges
        self.detail_tab = DetailWidget()
        self.sem_tab = SEMDisplayTab()
        self.raman_tab = RamanDisplayTab()
        self.recipe_tab = RecipeDisplayTab()
        self.provenance_tab = ProvenanceDisplayTab()
        self.admin_tab = None
        self.setTabPosition(QtGui.QTabWidget.South)

        self.addTab(self.detail_tab,'Details')
        self.addTab(self.sem_tab,'SEM')
        self.addTab(self.raman_tab,'Raman')
        self.addTab(self.recipe_tab,'Recipe')
        self.addTab(self.provenance_tab,'Provenance')

        if privileges:
            if privileges['write'] or privileges['validate']:
                self.admin_tab = AdminDisplayTab(privileges=privileges)
                self.addTab(self.admin_tab,'Admin')

    def select(self,model=None,index=None):
        """
        Select sample model and update preview. Can use ResultsTableModel with corresponding index,
        standalone sample model or a sample id.

        model:              ResultsTableModel object or sample model if index=None. If None, index refers to sample id.
        index:              Index from ResultsWidget table or sample id if model=None. If None, model refers to a sample model.
        """

        with dal.session_scope() as session:
            if index:
                if model:
                    i = int(model.df['id'].values[index.row()])
                else:
                    i = index
                s = session.query(sample).filter(sample.id==i)[0]
            elif index==None and model != None:
                s = model
            self.detail_tab.update(s.properties,s.recipe)
            self.sem_tab.update(s)
            self.raman_tab.update(s)
            self.recipe_tab.update(s.recipe)
            self.provenance_tab.update(s.authors)
            if self.admin_tab:
                self.admin_tab.update(s)

class ResultsWidget(QtGui.QTabWidget):
    """
    Widget for displaying results associated with a query. Contains tabs:
        - Results:              Each row associated with a sample and column corresponding to
                                a field. Clicking a row selects that sample for the PreviewWidget.
        - t-SNE:                Allows users to conduct t-SNE visualization on queried data.
        - Plot:                 Allows users to scatter plot queried data.
    """
    plotClicked = QtCore.pyqtSignal(object, object)
    tsneClicked = QtCore.pyqtSignal(object, object)
    def __init__(self,parent=None):
        super(ResultsWidget,self).__init__(parent=parent)
        self.setTabPosition(QtGui.QTabWidget.North)
        self.results_model = ResultsTableModel()
        self.results_table = QtGui.QTableView()
        self.results_table.setMinimumWidth(400)
        self.results_table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.results_table.setSortingEnabled(True)

        self.tsne = TSNEWidget()
        self.plot = PlotWidget()

        self.addTab(self.results_table,'Query Results')
        self.addTab(self.plot,'Plotting')
        self.addTab(self.tsne,'t-SNE')

        self.plot.sigClicked.connect(lambda plot, points: self.plotClicked.emit(plot,points))

    def query(self,filters):
        """
        Queries SQL database using list of sqlalchemy filters.

        filters:                list of sqlalchemy filters
        """
        self.results_model = ResultsTableModel()
        if len(filters)>0:
            with dal.session_scope() as session:
                all_sample_fields = [c.key for c in sample.__table__.columns] #+['author_last_names']
                sample_columns = tuple([getattr(sample,s) for s in all_sample_fields])
                recipe_columns = tuple([getattr(recipe,r) for r in recipe_fields+hybrid_recipe_fields])
                properties_columns = tuple([getattr(properties,p) for p in properties_fields])
                raman_columns = tuple([getattr(raman_set,r) for r in raman_fields])

                query_columns = sample_columns+raman_columns+recipe_columns+properties_columns

                q = session.query(*query_columns).\
                    join(sample.recipe).\
                    join(sample.properties).\
                    outerjoin(recipe.preparation_steps).\
                    outerjoin(raman_set).\
                    outerjoin(author).\
                    filter(*filters).distinct()

                self.results_model.read_sqlalchemy(q.statement,session,models=[sample,recipe,properties,raman_set])

        self.results_table.setModel(self.results_model)
        for c in range(self.results_model.columnCount(parent=None)):
            if self.results_model.df.columns[c] not in results_fields:
                self.results_table.hideColumn(c)
        self.results_table.resizeColumnsToContents()
        self.plot.setModel(self.results_model,xfields=recipe_fields+hybrid_recipe_fields,yfields=raman_fields+properties_fields)
        self.tsne.setModel(self.results_model,fields=recipe_fields+hybrid_recipe_fields+raman_fields+properties_fields)

class FieldsDisplayWidget(QtGui.QScrollArea):
    """
    Generic widget that creates a display from the selected fields from a particular model.

    fields: The fields from the model to generate the form. Note: fields must exist in the model.
    model:  The model to base the display on.
    """
    def __init__(self,fields,model,elements_per_col=100,parent=None):
        super(FieldsDisplayWidget,self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.fields = {}

        for f,field in enumerate(fields):
            self.fields[field] = {}
            info = getattr(model,field).info
            if info['std_unit']:
                unit = convertScripts(info['std_unit'])
                label = "%s (%s):"%(info['verbose_name'],unit)
            else:
                label = "%s:"%(info['verbose_name'])
            self.fields[field]['label'] = QtGui.QLabel(label)
            self.fields[field]['label'].setWordWrap(True)
            # self.fields[field]['label'].setMaximumWidth(120)
            # self.fields[field]['label'].setMinimumHeight(self.fields[field]['label'].sizeHint().height())
            self.fields[field]['value'] = QtGui.QLabel()
            self.fields[field]['value'].setMinimumWidth(50)
            self.fields[field]['value'].setAlignment(QtCore.Qt.AlignCenter)
            self.layout.addWidget(self.fields[field]['label'],f%elements_per_col,2*(f//elements_per_col))
            self.layout.addWidget(self.fields[field]['value'],f%elements_per_col,2*(f//elements_per_col)+1)

        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setWidget(self.contentWidget)

    def setData(self,model,index=None):
        """
        Update data displayed in the FieldsDisplayWidget for selected index in ResultsTableModel or from a SQLAlchemy object.

        model:              ResultsTableModel or SQLAlchemy object
        index:              Index from ResultsWidget table. Ignored if SQLAlchemy object.
        """
        for field in self.fields.keys():
            if index:
                if field in model.df.columns:
                    value = model.df[field].iloc[index.row()]
                    if pd.isnull(value):
                        value = ''
            else:
                try:
                    value = getattr(model,field)
                except:
                    value = ''
            self.fields[field]['value'].setText(str(value))

class DownloadThread(QtCore.QThread):
    downloadFinished = QtCore.pyqtSignal(object,int)
    def __init__(self,url,thread_id):
        super(DownloadThread,self).__init__()
        self.url = url
        self.thread_id = thread_id
        self.data = None

        self.finished.connect(lambda: self.downloadFinished.emit(self.data,self.thread_id))

    def __del__(self):
        self.wait()

    def run(self):
        r = requests.get(self.url)
        self.data = r.content

class SEMDisplayTab(QtGui.QScrollArea):
    def __init__(self,parent=None):
        super(SEMDisplayTab,self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.progress_bar = QtGui.QProgressBar()
        self.file_list = QtGui.QListWidget()
        self.sem_info = QtGui.QStackedWidget()
        self.sample_id = None
        self.threads = []

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.file_list.setFixedWidth(100)
        self.progress_bar.setFixedWidth(100)

        self.layout.addWidget(self.file_list,0,0,1,1)
        self.layout.addWidget(self.sem_info,0,1,2,1)
        self.layout.addWidget(self.progress_bar,1,0,1,1)

        self.file_list.currentRowChanged.connect(self.sem_info.setCurrentIndex)

    def loadImage(self,data,thread_id):
        img = np.array(Image.open(io.BytesIO(data)))
        image_tab = pg.GraphicsLayoutWidget()
        wImgBox_VB = image_tab.addViewBox(row=1,col=1)
        wImgItem = pg.ImageItem()
        wImgItem.setImage(img)
        wImgBox_VB.addItem(wImgItem)
        wImgBox_VB.setAspectLocked(True)


        sem_tabs = QtGui.QTabWidget()
        sem_tabs.addTab(image_tab,"Raw Data")

        if self.sample_id == thread_id:
            self.file_list.addItem("SEM Image %s"%str(self.file_list.count()+1))
            self.sem_info.addWidget(sem_tabs)
            self.progress_bar.setValue(100*sum([t.isFinished() for t in self.threads])/len(self.threads))

    def update(self,sample_model=None):
        if sample_model != None:
            if sample_model.id != self.sample_id:
                self.file_list.clear()
                self.progress_bar.reset()

                for w in [self.sem_info.widget(i) for i in range(self.sem_info.count())]:
                    self.sem_info.removeWidget(w)

                self.threads = []
                self.sample_id = sample_model.id
                if len(sample_model.sem_files) > 0:
                    self.progress_bar.setValue(1)
                    for sem in sample_model.sem_files:
                        thread = DownloadThread(url=sem.url,thread_id=sem.sample_id)
                        thread.downloadFinished.connect(self.loadImage)
                        thread.start()
                        print('Thread started.')
                        self.threads.append(thread)
                else:
                    self.progress_bar.setValue(100)

class ProvenanceDisplayTab(QtGui.QScrollArea):
    def __init__(self,parent=None):
        super(ProvenanceDisplayTab,self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.author_widgets = []

    def update(self,author_models=[]):
        for widget in self.author_widgets:
            self.layout.removeWidget(widget)
            sip.delete(widget)
        self.author_widgets = []

        for a,auth in enumerate(author_models):
            self.author_widgets.append(FieldsDisplayWidget(fields=["full_name_and_institution"],model=author))
            self.author_widgets[-1].setData(auth)
            self.layout.addWidget(self.author_widgets[-1],a,0)

class RamanDisplayTab(QtGui.QScrollArea):
    def __init__(self,parent=None):
        super(RamanDisplayTab,self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.progress_bar = QtGui.QProgressBar()
        self.file_list = QtGui.QListWidget()
        self.raman_info = QtGui.QStackedWidget()
        self.weighted_values = FieldsDisplayWidget(fields=raman_fields,model=raman_set,elements_per_col=1)
        self.sample_id = None
        self.threads = []

        self.file_list.setFixedWidth(130)
        self.progress_bar.setFixedWidth(130)

        self.layout.addWidget(self.file_list,0,0,1,1)
        self.layout.addWidget(self.raman_info,0,1,1,1)
        self.layout.addWidget(self.weighted_values,1,1,1,1)
        self.layout.addWidget(self.progress_bar,1,0,1,1)

    def loadSpectrum(self,data,thread_id,spectrum_model):
        raman_tabs = QtGui.QTabWidget()
        spectrum_plot_tab = QtGui.QWidget()
        spectrum_properties_tab = FieldsDisplayWidget(fields=spectrum_fields,model=raman_spectrum)
        spectrum_properties_tab.setData(spectrum_model)
        raman_tabs.addTab(spectrum_plot_tab,"Spectrum")
        raman_tabs.addTab(spectrum_properties_tab,"Properties")

        if self.sample_id == thread_id:
            self.file_list.addItem("Spectrum %s (%s%%)"%(str(self.file_list.count()+1),round(spectrum_model.percent,2)))
            self.raman_info.addWidget(raman_tabs)
            self.progress_bar.setValue(100*sum([t.isFinished() for t in self.threads])/len(self.threads))

    def update(self,sample_model=None):
        if sample_model != None:
            if sample_model.id != self.sample_id:
                self.file_list.clear()
                self.progress_bar.reset()

                for w in [self.raman_info.widget(i) for i in range(self.raman_info.count())]:
                    self.raman_info.removeWidget(w)

                self.threads = []
                self.sample_id = sample_model.id
                raman_analysis = sample_model.raman_analysis
                self.weighted_values.setData(raman_analysis)
                if len(raman_analysis.raman_spectra) > 0:
                    self.progress_bar.setValue(1)
                    for spectrum in raman_analysis.raman_spectra:
                        thread = DownloadThread(url=spectrum.raman_file.url,thread_id=raman_analysis.sample_id)
                        thread.downloadFinished.connect(lambda x,y: self.loadSpectrum(x,y,spectrum))
                        thread.start()
                        print('Thread started.')
                        self.threads.append(thread)
                else:
                    self.progress_bar.setValue(100)

class RecipeDisplayTab(QtGui.QScrollArea):
    def __init__(self,parent=None):
        super(RecipeDisplayTab,self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.primary_axis = QtGui.QComboBox()
        self.recipe_model = None

        self.recipe_plot = pg.PlotWidget()
        # self.recipe_plot.setMouseEnabled(x=True, y=False)

        self.layout.addWidget(self.recipe_plot,0,0,1,2)
        self.layout.addWidget(QtGui.QLabel("Primary Axis:"),1,0)
        self.layout.addWidget(self.primary_axis,1,1)

    def update(self,recipe_model):
        try:
            self.primary_axis.activated[str].disconnect()
        except:
            pass
        self.primary_axis.clear()
        self.recipe_plot.clear()
        self.recipe_model = recipe_model
        if self.recipe_model:
            step_list = sorted(self.recipe_model.preparation_steps, key = lambda x: getattr(x,'step'))
            self.data = {
                'furnace_pressure': [],
                'furnace_temperature': [],
                'argon_flow_rate': [],
                'hydrogen_flow_rate': [],
                'helium_flow_rate': [],
                'carbon_source_flow_rate': [],
                'duration': [],
                'cooling_rate': [],
                'name': []
            }
            for step in step_list:
                for field in self.data.keys():
                    value = getattr(step,field)
                    if value:
                        self.data[field].append(value)
                    else:
                        self.data[field].append(np.nan)
            axis_fields = {
                'Furnace Temperature': 'furnace_temperature',
                'Furnace Pressure': 'furnace_pressure',
                'Helium Flow Rate': "helium_flow_rate",
                'Hydrogen Flow Rate': "hydrogen_flow_rate",
                'Carbon Source Flow Rate': "carbon_source_flow_rate",
                'Argon Flow Rate': "argon_flow_rate"
                }
            for field in list(axis_fields.keys()):
                if np.isnan(self.data[axis_fields[field]]).all():
                    del axis_fields[field]
            self.primary_axis.addItems(sorted(axis_fields.keys()))
            self.primary_axis.activated[str].connect(lambda x: self.plot(plot_field=axis_fields[x]))
            if self.primary_axis.count() > 0:
                self.primary_axis.setCurrentIndex(0)
                self.primary_axis.activated[str].emit(self.primary_axis.currentText())

    def plot(self,plot_field=None):
        self.recipe_plot.clear()
        if self.recipe_model and plot_field:
            if all(self.data['duration']):

                timestamp = [0]+[sum(self.data['duration'][:i]) for i in range(1,len(self.data['duration'])+1)]

                x = np.linspace(0,sum(self.data['duration']),1000)
                condlist = [np.logical_and(x>=timestamp[i], x<timestamp[i+1]) for i in range(0,len(timestamp)-1)]
                y = np.piecewise(x,condlist,self.data[plot_field])
                if np.isfinite(y).sum()>25:
                    win = signal.hann(25)
                    win /= win.sum()
                    y = scipy.convolve(y,win,mode='same')
                self.recipe_plot.plot(x=x,y=y,pen=pg.mkPen('r',width=8))
                self.recipe_plot.setXRange(min(x),max(x),padding=0)

                # print(self.data['duration'],timestamp,self.data[plot_field])

                colors = {'Annealing':'y','Growing':'g','Cooling':'b'}
                for n,name in enumerate(self.data['name']):
                    if name in colors.keys():
                        x1 = sum(self.data['duration'][:n])
                        x2 = sum(self.data['duration'][:n+1])

                        brush = pg.mkBrush(colors[name])
                        c = brush.color()
                        c.setAlphaF(0.2)
                        brush.setColor(c)
                        fb = pg.LinearRegionItem(values=(x1,x2),movable=False,brush=brush)
                        self.recipe_plot.addItem(fb)

                ay = self.recipe_plot.getAxis('left')
                yticks = np.unique(self.data[plot_field])
                # ay.setTicks([[(v, str(v)) for v in yticks]])


                ax = self.recipe_plot.getAxis('bottom')
                xticks = [0]+timestamp
                ax.setTicks([[(v, str(v)) for v in xticks]])

                self.recipe_plot.setLabel(text='Time (min)',axis='bottom')
                info = getattr(preparation_step,plot_field).info
                ylabel = info['verbose_name']
                if info['std_unit']:
                    ylabel += ' (%s)'%info['std_unit']
                self.recipe_plot.setLabel(text=ylabel,axis='left')

                self.recipe_plot.enableAutoRange()


class AdminDisplayTab(QtGui.QScrollArea):
    updateQuery = QtCore.pyqtSignal()
    queryUnvalidated = QtCore.pyqtSignal()
    def __init__(self,privileges, parent=None):
        super(AdminDisplayTab,self).__init__(parent=parent)
        self.sample_id = None
        self.privileges = privileges

        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.validate_button = QtGui.QPushButton('Validate/Unvalidate')
        self.validate_button.clicked.connect(self.toggle_validate_model)
        self.validate_status_label = QtGui.QLabel('')

        self.delete_button = QtGui.QPushButton('Delete Selected Entry')
        self.delete_button.clicked.connect(self.delete_model)
        self.delete_button.setStyleSheet("background-color: rgb(255,100,100)")

        self.query_unvalidated_button = QtGui.QPushButton('Query All Unvalidated')
        self.query_unvalidated_button.clicked.connect(lambda: self.queryUnvalidated.emit())

        if self.privileges['validate']==False:
            self.validate_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.layout.addWidget(self.query_unvalidated_button,0,0,1,3)
        self.layout.addWidget(QtGui.QLabel('Validation Status:'),1,0)
        self.layout.addWidget(self.validate_status_label,1,1)
        self.layout.addWidget(self.validate_button,1,2)
        self.layout.addWidget(self.delete_button,2,0,1,3)


    def update(self,sample_model):
        self.sample_id = sample_model.id
        self.validate_status_label.setText(str(sample_model.validated))

        if self.privileges['write'] or self.privileges['validate']:
            if self.privileges['validate']:
                self.delete_button.setEnabled(True)
            elif self.privileges['write'] and sample_model.nanohub_userid and sample_model.nanohub_userid == os.getuid():
                self.delete_button.setEnabled(True)
            else:
                self.delete_button.setEnabled(False)
        else:
            self.delete_button.setEnabled(False)


    def delete_model(self):
            confirmation_dialog = QtGui.QMessageBox(self)
            confirmation_dialog.setText("Are you sure you want to delete this recipe?")
            confirmation_dialog.setInformativeText("Note: you will not be able to undo this submission.")
            confirmation_dialog.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            confirmation_dialog.setWindowModality(QtCore.Qt.WindowModal)

            def upload_wrapper(btn):
                if btn.text() == "OK":
                    try:
                        with dal.session_scope() as session:
                            model = session.query(sample).get(self.sample_id)
                            session.delete(model)
                            session.commit()

                            success_dialog = QtGui.QMessageBox(self)
                            success_dialog.setText("Recipe successfully deleted.")
                            success_dialog.setWindowModality(QtCore.Qt.WindowModal)
                            success_dialog.exec()

                    except Exception as e:
                        error_dialog = QtGui.QMessageBox(self)
                        error_dialog.setWindowModality(QtCore.Qt.WindowModal)
                        error_dialog.setText("Submission Error!")
                        error_dialog.setInformativeText(str(e))
                        error_dialog.exec()
                        return

            confirmation_dialog.buttonClicked.connect(upload_wrapper)
            confirmation_dialog.exec()

    def toggle_validate_model(self):
        if self.sample_id:
            with dal.session_scope() as session:
                model = session.query(sample).get(self.sample_id)
                model.validated = not model.validated
                session.commit()
                self.validate_status_label.setText(str(model.validated))


if __name__ == '__main__':
    dal.init_db(config['development'])
    app = QtGui.QApplication([])
    query = GSAQuery()
    query.show()
    sys.exit(app.exec_())

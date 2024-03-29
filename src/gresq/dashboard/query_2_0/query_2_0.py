from __future__ import division
from ctypes import sizeof
import pandas as pd
import numpy as np
import sys, operator, os
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import cv2
import io
import sip
import requests
import uuid
import json
from PIL import Image
from gresq.util.io import DownloadThread, DownloadPool, DownloadRunner
from gresq.util.util import ConfigParams, sql_validator, operators, ResultsTableModel, errorCheck, BasicLabel, HeaderLabel
from gresq.util.box_adaptor import BoxAdaptor
from gresq.dashboard.stats import TSNEWidget, PlotWidget
from grdb.database import dal, Base
from grdb.database.models import (
    Experiment,
    Substrate,
    EnvironmentConditions,
    Furnace,
    Recipe,
    Properties,
    Author,
    PreparationStep,
    RamanFile,
    RamanAnalysis,
    SemFile,
    SemAnalysis,
)
from sqlalchemy import String, Integer, Float, Numeric, or_
from gresq.config import config
from gsaimage import ImageEditor
import scipy
from scipy import signal
from gsaraman.raw_plotter import RamanQueryWidget

"""
Each primary field will correspond to a SQLAlchemy model. Each of these are models
(whose schema is in grdb.database.v1_1_0.py). Secondary fields are attributes of these
models and the fields that will be displayed are controlled via the field lists
below.
"""
# made changes here - Mitisha
preparation_fields = [
    "name",
    "duration",
    "furnace_temperature",
    "furnace_pressure",
    "sample_location",
    "helium_flow_rate",
    "hydrogen_flow_rate",
    "carbon_source_flow_rate",
    "argon_flow_rate",
    "cooling_rate",
]

properties_fields = [
    "growth_coverage",
    "shape",
    "average_thickness_of_growth",
    "standard_deviation_of_growth",
    "number_of_layers",
    "domain_size",
]

substrate_fields = [
    "catalyst",
    "thickness",
    "diameter",
    "length",
    "surface_area",
]

furnace_fields = [
    "tube_diameter",
    "cross_sectional_area",
    "tube_length",
    "length_of_heated_region",
]

environment_conditions_fields = [
    "dew_point",
    "ambient_temperature",
]

recipe_fields = [
    "base_pressure",
    # "carbon_source",
]

hybrid_recipe_fields = [
    "maximum_temperature",
    "maximum_pressure",
    "average_carbon_flow_rate",
    "uses_helium",
    "uses_hydrogen",
    "uses_argon",
]

author_fields = ["last_name", "first_name", "institution"]

raman_fields = ["gp_to_g", "d_to_g"]

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
    "g_prime_fwhm",
]

experiment_fields = ["id", "experiment_date", "validated"]

results_fields = experiment_fields + properties_fields + raman_fields

selection_list = {
    "Furnace": {"fields": furnace_fields, "model": Furnace},
    "Substrate": {"fields": substrate_fields, "model": Substrate},
    "Environment Conditions": {"fields": environment_conditions_fields, "model": EnvironmentConditions},
    "Recipe": {"fields": recipe_fields , "model": Recipe},
    "Preparation": {"fields": preparation_fields, "model": PreparationStep},
    "Properties": {"fields": properties_fields, "model": Properties},
    "Raman Analysis": {"fields": raman_fields, "model": RamanAnalysis},
    "Provenance Information": {"fields": author_fields, "model": Author},
}


def convertScripts(text):
    if "^" in text:
        words = text.split("^")
        new_text = "%s<sup>%s</sup>" % (words[0], words[1])
    elif "_" in text:
        words = text.split("_")
        new_text = "%s<sub>%s</sub>" % (words[0], words[1])
    else:
        new_text = text

    return new_text


class GSAQuery(QtGui.QWidget):
    """
    Main query widget.
    """

    def __init__(
        self, 
        config,
        parent=None
    ):
        super(GSAQuery, self).__init__(parent=parent)
        self.config = config
        self.filters = [] # list of filters to apply to query
        self.filter_fields = QtGui.QStackedWidget() # display for filter inputs
        # self.filter_fields.setMaximumHeight(50)
        self.filter_fields.setSizePolicy(
            QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum
        )
        self.filters_dict = {} # dictionary of filter inputs
        for selection in selection_list.keys():
            for field in selection_list[selection]["fields"]:
                widget = self.generate_field(
                    model=selection_list[selection]["model"], field=field
                )
                widget.setSizePolicy(
                    QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred
                )
                self.filters_dict[
                    getattr(selection_list[selection]["model"], field).info[
                        "verbose_name"
                    ]
                ] = widget
                self.filter_fields.addWidget(widget)

        self.primary_selection = QtGui.QComboBox()
        self.primary_selection.addItems(sorted(selection_list.keys()))
        self.primary_selection.activated[str].connect(self.populate_secondary)

        self.secondary_selection = QtGui.QComboBox()
        self.secondary_selection.activated[str].connect(
            lambda x: self.filter_fields.setCurrentWidget(self.filters_dict[x])
        )

        self.primary_selection.activated[str].connect(
            lambda x: self.secondary_selection.activated[str].emit(
                self.secondary_selection.currentText()
            )
        )

        self.filter_table = QtGui.QTableWidget()
        self.filter_table.setColumnCount(4)
        self.filter_table.setHorizontalHeaderLabels(["Field", "", "Value", ""])
        header = self.filter_table.horizontalHeader()
        header.setSectionResizeMode(0, QtGui.QHeaderView.Stretch)
        self.filter_table.setColumnWidth(1, 40)
        self.filter_table.setColumnWidth(2, 100)
        self.filter_table.setColumnWidth(3, 30)
        self.filter_table.setWordWrap(True)
        self.filter_table.verticalHeader().setVisible(False)
        self.filter_table.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding
        )

        self.results = ResultsWidget()
        self.results.setSizePolicy(
            QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred
        )

        self.preview = PreviewWidget(config=self.config)
        if self.config.canWrite() or self.config.canValidate():
            self.preview.admin_tab.updateQuery.connect(lambda: self.query(self.filters))
            self.preview.admin_tab.queryUnvalidated.connect(
                lambda: self.query([Experiment.validated.is_(False)])
            )

        self.addFilterBtn = QtGui.QPushButton("Add Filter")
        self.addFilterBtn.clicked.connect(
            lambda: self.addFilter(self.filter_fields.currentWidget())
        )

        searchLayout = QtGui.QGridLayout()
        searchLayout.setAlignment(QtCore.Qt.AlignTop)
        searchLayout.addWidget(HeaderLabel("Query"),0,0)
        searchLayout.addWidget(self.primary_selection, 2, 0)
        searchLayout.addWidget(self.secondary_selection, 3, 0)
        searchLayout.addWidget(self.filter_fields, 4, 0)
        searchLayout.addWidget(self.addFilterBtn, 5, 0)
        dummyLayout = QtGui.QGridLayout()
        dummyLayout.addWidget(self.filter_table)
        searchLayout.addLayout(dummyLayout,6,0)

        resultsLayout = QtGui.QGridLayout()
        resultsLayout.setAlignment(QtCore.Qt.AlignTop)
        resultsLayout.addWidget(HeaderLabel("Results"),0,0)
        resultsLayout.addWidget(self.results,1,0)

        vsplitLayout = QtGui.QSplitter(QtCore.Qt.Vertical)
        vsplitLayout.addWidget(self.results)
        vsplitLayout.addWidget(self.preview)
        vsplitLayout.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred
        )

        hsplitLayout = QtGui.QSplitter(QtCore.Qt.Horizontal)
        dummy = QtWidgets.QWidget()
        dummy.setLayout(searchLayout)
        dummy.setSizePolicy(
            QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred
        )
        hsplitLayout.addWidget(dummy)
        hsplitLayout.addWidget(vsplitLayout)

        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(hsplitLayout)

        self.primary_selection.activated[str].emit(self.primary_selection.currentText())
        self.secondary_selection.activated[str].emit(
            self.secondary_selection.currentText()
        )
        self.results.plotClicked.connect(
            lambda plot, points: self.preview.select(index=points[0].data())
        )
        self.results.tsneClicked.connect(
            lambda plot, points: self.preview.select(index=points[0].data())
        )

    def generate_field(self, model, field):
        """
        Generates an input selected field of selected model.

        model:          SQLAlchemy model to which the field corresponds
        field:          Column within the sqlalchemy model
        """
        cla = model
        if sql_validator["int"](getattr(cla, field)) == True:
            vf = ValueFilter(model=cla, field=field, validate=int)
            vf.input.returnPressed.connect(
                lambda: self.addFilter(self.filter_fields.currentWidget())
            )
            return vf
        elif sql_validator["float"](getattr(cla, field)) == True:
            vf = ValueFilter(model=cla, field=field, validate=int)
            vf.input.returnPressed.connect(
                lambda: self.addFilter(self.filter_fields.currentWidget())
            )
            return vf
        elif sql_validator["str"](getattr(cla, field)) == True:
            with dal.session_scope() as session:
                classes = []
                for v in session.query(getattr(cla, field)).distinct():
                    classes.append(getattr(v, field))
            return ClassFilter(model=cla, field=field, classes=classes, validate=str)
        else:
            raise ValueError(
                "Field %s data type (%s) not recognized."
                % (field, getattr(cla, field).property.columns[0].type)
            )

    def populate_secondary(self, selection):
        """
        Populates secondary selection combo box with fields corresponding to the primary selection model.
        """
        self.secondary_selection.clear()
        self.secondary_selection.addItems(
            [
                getattr(selection_list[selection]["model"], v).info["verbose_name"]
                for v in selection_list[selection]["fields"]
            ]
        )

    def addFilter(self, widget):
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
            self.filter_table.setItem(
                row, 0, QtGui.QTableWidgetItem(widget.label.text())
            )
            self.filter_table.setItem(row, 1, QtGui.QTableWidgetItem(widget.operation))
            self.filter_table.setItem(row, 2, QtGui.QTableWidgetItem(str(widget.value)))
            # self.filter_table.resizeRowsToContents()

            delRowBtn = QtGui.QPushButton("X")
            delRowBtn.clicked.connect(self.deleteRow)
            self.filter_table.setCellWidget(row, 3, delRowBtn)
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

    def query(self, filters):
        """
        Runs query on results widget. This is a separate function so as to make the selection signal work properly.
        This is because the model must be set before selection signalling can be connected.
        """
        if self.config.canValidate():
            self.results.query(filters)
        else:
            self.results.query(filters + [or_(Experiment.validated == True, Experiment.nanohub_userid == os.getuid())])
        self.results.results_table.selectionModel().currentChanged.connect(
            lambda x: self.preview.select(self.results.results_model, x) if self.results.rowCount() > 0 else None
        )


class ValueFilter(QtGui.QWidget):
    """
    Creates new filter input for numeric fields.

    model:          sqlalchemy model to which the field corresponds
    field:          column within the sqlalchemy model
    """

    def __init__(self, model, field, validate=None, parent=None):
        super(ValueFilter, self).__init__(parent=parent)
        self.field = field
        self.model = model
        self.validate = validate

        layout = QtGui.QGridLayout(self)
        info = getattr(model, field).info

        label = "%s"%info["verbose_name"]
        if 'std_unit' in info.keys() and info['std_unit'] != None:
            label += " (%s)"%info['std_unit']
        self.label = BasicLabel(label)
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

        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.comparator, 0, 1)
        layout.addWidget(self.input, 0, 2)

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
        return operators[self.comparator.currentText()](
            getattr(self.model, self.field), self.value
        )

    def clear(self):
        self.input.clear()


class ClassFilter(QtGui.QWidget):
    """
    Creates new filter input for class (string) fields.

    model:          sqlalchemy model to which the field corresponds
    field:          column within the sqlalchemy model
    """

    def __init__(self, model, field, validate=None, classes=[], parent=None):
        super(ClassFilter, self).__init__(parent=parent)
        self.field = field
        self.model = model
        self.validate = validate

        layout = QtGui.QGridLayout(self)
        self.label = BasicLabel(getattr(model, field).info["verbose_name"])
        # self.label.setFixedWidth(150)
        self.label.setWordWrap(True)
        self.classes = QtGui.QComboBox()
        self.classes.addItems(classes)

        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.classes, 0, 1)

    @property
    def operation(self):
        return "AND"

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
        return operator.eq(getattr(self.model, self.field), self.value)

    def clear(self):
        pass


class DetailWidget(QtGui.QWidget):
    """
    Widget that displays information pertaining to the properties and conditions of the entry.
    """
    # made changes here - Mitisha
    def __init__(self, parent=None):
        super(DetailWidget, self).__init__(parent=parent)
        self.properties = FieldsDisplayWidget(
            fields=properties_fields, model=Properties
        )
        selection_list_for_conditions = ["Recipe","Substrate", "Furnace"]
        self.conditions = MultipleFieldsDisplayWidget(condition_list=selection_list_for_conditions
            )
            
        propertiesLabel = HeaderLabel("Properties")
        conditionsLabel = HeaderLabel("Conditions")

        layout = QtGui.QGridLayout(self)
        layout.addWidget(propertiesLabel, 0, 0)
        layout.addWidget(self.properties, 1, 0)
        layout.addWidget(conditionsLabel, 0, 1)
        layout.addWidget(self.conditions, 1, 1)

    def update(self, properties_model, recipe_model, substrate_model, furnace_model):
        self.properties.setData(properties_model)
        self.conditions.setData(recipe_model)
        self.conditions.setData(substrate_model)
        self.conditions.setData(furnace_model)


class PreviewWidget(QtGui.QTabWidget):
    """
    Widget for displaying data associated with selected Experiment. Contains tabs for:
        -Graphene details
        -SEM data (raw and postprocessed)
        -Raman data (raw and postprocessed)
        -Recipe visualization
        -Provenance information
    """

    def __init__(self, config, parent=None):
        super(PreviewWidget, self).__init__(parent=parent)
        self.config = config
        self.detail_tab = DetailWidget()
        self.sem_tab = SEMDisplayTab(config=config)
        self.raman_tab = RamanDisplayTab(config=config)
        self.recipe_tab = RecipeDisplayTab(config=config)
        self.provenance_tab = ProvenanceDisplayTab()
        self.admin_tab = None
        self.setTabPosition(QtGui.QTabWidget.South)
        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred
        )

        self.addTab(self.detail_tab, "Details")
        self.addTab(self.sem_tab, "SEM")
        self.addTab(self.raman_tab, "Raman")
        self.addTab(self.recipe_tab, "Recipe")
        self.addTab(self.provenance_tab, "Provenance")

        if config.canWrite() or config.canRead:
            self.admin_tab = AdminDisplayTab(config=config)
            self.addTab(self.admin_tab, "Admin")

    @errorCheck(error_text='Error selecting entry!')
    def select(self, model=None, index=None):
        """
        Select Experiment model and update preview. Can use ResultsTableModel with corresponding index,
        standalone Experiment model or a Experiment id.

        model:              ResultsTableModel object or Experiment model if index=None. If None, index refers to Experiment id.
        index:              Index from ResultsWidget table or Experiment id if model=None. If None, model refers to a Experiment model.
        """

        session = dal.Session()
        #with dal.session_scope() as session:
        if index:
            if model:
                i = int(model.df["id"].values[index.row()])
            else:
                i = index
            s = session.query(Experiment).filter(Experiment.id == i)[0]
        elif index == None and model != None:
            s = model
        else:
            # index == None and model == none
            error_msg = QtWidgets.QErrorMessage()
            error_msg.showMessage("Both model and index are unable to be found.")
            error_msg.exec_()
            return

        self.detail_tab.update(s.properties, s.recipe,s.substrate, s.furnace)
        self.provenance_tab.update(s.authors)
        self.recipe_tab.update(s.recipe)
        if self.admin_tab:
            self.admin_tab.update(s)
        self.sem_tab.update(s)
        self.raman_tab.update(s)

        session.close()


class ResultsWidget(QtGui.QTabWidget):
    """
    Widget for displaying results associated with a query. Contains tabs:
        - Results:              Each row associated with an  experiment and column corresponding to
                                a field. Clicking a row selects that experiment for the PreviewWidget.
        - t-SNE:                Allows users to conduct t-SNE visualization on queried data.
        - Plot:                 Allows users to scatter plot queried data.
    """

    plotClicked = QtCore.pyqtSignal(object, object)
    tsneClicked = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(ResultsWidget, self).__init__(parent=parent)
        self.setTabPosition(QtGui.QTabWidget.North)
        self.results_model = ResultsTableModel()
        self.results_table = QtGui.QTableView()
        self.results_table.setMinimumWidth(400)
        self.results_table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.results_table.setSortingEnabled(True)

        self.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred
        )

        self.tsne = TSNEWidget()
        self.plot = PlotWidget()

        self.addTab(self.results_table, "Query Results")
        self.addTab(self.plot, "Plotting")
        self.addTab(self.tsne, "t-SNE")

        self.plot.sigClicked.connect(
            lambda plot, points: self.plotClicked.emit(plot, points)
        )
        self.tsne.tsneClicked.connect(
            lambda plot, points: self.plotClicked.emit(plot, points)
        )

    def rowCount(self):
        return self.results_model.rowCount(parent=None)

    @errorCheck(error_text="Error querying database!")
    def query(self, filters):
        """
        Queries SQL database using list of sqlalchemy filters.

        filters:                list of sqlalchemy filters
        """
        # made changes here - Mitisha
        
        self.results_model = ResultsTableModel()
        if len(filters) > 0:
            with dal.session_scope() as session:
                all_experiment_fields = [
                    c.key for c in Experiment.__table__.columns
                ]  # +['author_last_names']
                experiment_columns = tuple([getattr(Experiment, e) for e in all_experiment_fields])
                recipe_columns = tuple(
                    [getattr(Recipe, r) for r in recipe_fields]# + hybrid_recipe_fields]
                )
                substrate_columns = tuple(
                    [getattr(Substrate, sb) for sb in substrate_fields]
                )
                furnace_columns = tuple(
                    [getattr(Furnace, f) for f in furnace_fields]
                )
                environment_conditions_columns = tuple(
                    [getattr(EnvironmentConditions, e) for e in environment_conditions_fields]
                )
                
                properties_columns = tuple(
                    [getattr(Properties, p) for p in properties_fields]
                )
                raman_columns = tuple([getattr(RamanAnalysis, r) for r in raman_fields])

                query_columns = (
                    furnace_columns + experiment_columns + recipe_columns + raman_columns + properties_columns + substrate_columns + environment_conditions_columns  
                ) 
                #What we want is - one-to-many - "some join"(Parent, )
                #parent.child_id doesnt exist, Child.parent_id exists
                #Parent.id and Child.id exist

                #
                q = (
                    session.query(*query_columns)
                    #Experiment linked to all by many-to-one
                    .join(Recipe, Recipe.id == Experiment.recipe_id)
                    .join(Substrate, Substrate.id == Experiment.substrate_id)
                    .join(Furnace, Furnace.id == Experiment.furnace_id)
                    # #Linked to experiment by one-to-one
                    .outerjoin(EnvironmentConditions, EnvironmentConditions.id == Experiment.environment_conditions_id)
                    .outerjoin(Properties, Experiment.id == Properties.experiment_id)
                    # #Linked to experiment by one-to-many
                    .outerjoin(RamanFile, Experiment.id == RamanFile.experiment_id)
                    # #Linked to parent by one-to-many
                    .outerjoin(RamanAnalysis, RamanAnalysis.raman_file_id == RamanFile.id)
                    .outerjoin(PreparationStep, PreparationStep.recipe_id == Recipe.id) 
                    # #Linked to Experiment by many-to-many
                    # ses3.query(Experiment,Recipe).filter(Experiment.recipe_id==Recipe.id)
                    .outerjoin(Author, Author.id == Experiment.submitted_by) #check: why is it called this? why not author
                    .filter(*filters)
                    .distinct()
                )

                # result = session.query(Recipe)\
                # .options(contains_eager(Recipe.experiments))\
                # .join(Row)\
                # .filter(Table.name == 'abc', Row.status == True).one()

                self.results_model.read_sqlalchemy(
                    q.statement, session, models=[Furnace, Experiment, Recipe, PreparationStep, Properties, RamanAnalysis, Substrate, EnvironmentConditions]
                ) 
                
        self.results_table.setModel(self.results_model)

        for c in range(self.results_model.columnCount(parent=None)):
            if self.results_model.df.columns[c] not in results_fields:
                self.results_table.hideColumn(c)
        self.results_table.resizeColumnsToContents()
        self.plot.setModel(
            self.results_model,
            xfields= recipe_fields + hybrid_recipe_fields,
            yfields= raman_fields + properties_fields,
        )

        self.tsne.setModel(
            self.results_model,
            fields=['id']
            + recipe_fields
            + hybrid_recipe_fields
            + raman_fields
            + properties_fields,
        )


class FieldsDisplayWidget(QtGui.QScrollArea):
    """
    Generic widget that creates a display from the selected fields from a particular model.

    fields:             (list of str) The fields from the model to generate the form. Note: fields must exist in the model.
    model:              (SQLAlchemy model) The model to base the display on.
    """

    def __init__(self, fields, model, elements_per_col=100, parent=None):
        super(FieldsDisplayWidget, self).__init__(parent=parent)
        self.base_model = model
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.fields = {}

        for f, field in enumerate(fields):
            self.fields[field] = {}
            info = getattr(model, field).info
            if "std_unit" in info:
                if info["std_unit"]:
                    unit = convertScripts(info["std_unit"])
                    label = "%s (%s):" % (info["verbose_name"], unit)
                else:
                    label = "%s:" % (info["verbose_name"])
            else:
                label = "%s:" % (info["verbose_name"])
            tooltip = info['tooltip'] if 'tooltip' in info.keys() else None
            self.fields[field]["label"] = BasicLabel(label,tooltip=tooltip)
            self.fields[field]["label"].setWordWrap(True)
            # self.fields[field]['label'].setMaximumWidth(120)
            # self.fields[field]['label'].setMinimumHeight(self.fields[field]['label'].sizeHint().height())
            self.fields[field]["value"] = BasicLabel()
            self.fields[field]["value"].setMinimumWidth(50)
            self.fields[field]["value"].setAlignment(QtCore.Qt.AlignCenter)
            self.layout.addWidget(
                self.fields[field]["label"],
                f % elements_per_col,
                2 * (f // elements_per_col),
            )
            self.layout.addWidget(
                self.fields[field]["value"],
                f % elements_per_col,
                2 * (f // elements_per_col) + 1,
            )

        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setWidget(self.contentWidget)

    def setData(self, model, index=None, ndecimal=3):
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
                        value = ""
                    elif value != None and isinstance(value, float):
                        value = round(value, ndecimal)
            else:
                try:
                    value = getattr(model, field)
                    if value != None and isinstance(value, float):
                        value = round(value, ndecimal)
                except Exception as e:
                    #print(type(value), e)
                    print(e)
                    value = ""
            self.fields[field]["value"].setText(str(value))

# made changes here - Mitisha - added new class 
class MultipleFieldsDisplayWidget(QtGui.QScrollArea):
    """
    Generic widget that creates a display from the selected fields from a particular model.

    fields:             (list of str) The fields from the model to generate the form. Note: fields must exist in the model.
    model:              (SQLAlchemy model) The model to base the display on.
    """

    def __init__(self, condition_list, elements_per_col=100, parent=None):
        
       #fields= selection_list[selection]["fields"], model=selection_list[selection]["model"]
        super(MultipleFieldsDisplayWidget, self).__init__(parent=parent)
        #self.base_model = model
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.fields = {}
        f=0

        for condition in condition_list:
            model=selection_list[condition]["model"]
            fields=selection_list[condition]["fields"]
            for field in fields:
                self.fields[field] = {}
                info = getattr(model, field).info
                if "std_unit" in info:
                    if info["std_unit"]:
                        unit = convertScripts(info["std_unit"])
                        label = "%s (%s):" % (info["verbose_name"], unit)
                    else:
                        label = "%s:" % (info["verbose_name"])
                else:
                    label = "%s:" % (info["verbose_name"])
                tooltip = info['tooltip'] if 'tooltip' in info.keys() else None
                self.fields[field]["label"] = BasicLabel(label,tooltip=tooltip)
                self.fields[field]["label"].setWordWrap(True)
                # self.fields[field]['label'].setMaximumWidth(120)
                # self.fields[field]['label'].setMinimumHeight(self.fields[field]['label'].sizeHint().height())
                self.fields[field]["value"] = BasicLabel()
                self.fields[field]["value"].setMinimumWidth(50)
                self.fields[field]["value"].setAlignment(QtCore.Qt.AlignCenter)
                self.layout.addWidget(
                    self.fields[field]["label"],
                    f % elements_per_col,
                    2 * (f // elements_per_col),
                )
                self.layout.addWidget(
                    self.fields[field]["value"],
                    f % elements_per_col,
                    2 * (f // elements_per_col) + 1,
                )
                f+=1

        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setWidget(self.contentWidget)

    def setData(self, model, index=None, ndecimal=3):
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
                        value = ""
                    elif value != None and isinstance(value, float):
                        value = round(value, ndecimal)
            else:
                try:
                    value = getattr(model, field)
                    if value != None and isinstance(value, float):
                        value = round(value, ndecimal)
                except Exception as e:
                    continue
                    # value = ""
                    # print(type(value), e)
                    
            self.fields[field]["value"].setText(str(value))



class RawImageTab(pg.GraphicsLayoutWidget):
    """
    Widget to display an image. Useful for connecting threaded downloads to image display.
    """
    def __init__(self, parent=None):
        super(RawImageTab, self).__init__(parent=parent)
        self._id = None
        self.viewbox = self.addViewBox(row=1, col=1)
        self.img_item = pg.ImageItem()
        self.viewbox.addItem(self.img_item)
        self.viewbox.setAspectLocked(True)

    def loadImage(self, data, thread_id, info):
        """
        Loads image. Good for slotting into a downloadFinished signal from a DownloadThread object.

        data:           Bytes object to be decoded into image.
        thread_id:      Thread ID. Useful for keeping track of threads.
        info:           (dict) Dictionary of ancillary parameters from DownloadThread.
        """
        self._id = thread_id
        img = np.array(Image.open(io.BytesIO(data)))
        self.img_item.setImage(img, levels=(0, 255))


class SEMAdminTab(QtGui.QScrollArea):
    """
    Widget for handling admin functionality in the SEM display tab.

    sem_id:             (int) sem_file model ID
    experiment_id:          (int) experiment model ID
    """
    def __init__(self, sem_id, experiment_id, parent=None):
        super(SEMAdminTab, self).__init__(parent=parent)
        self.sem_id = sem_id
        self.experiment_id = experiment_id

        self.set_default_button = QtGui.QPushButton("Set Default Analysis")
        self.set_primary_button = QtGui.QPushButton("Set Primary Analysis")
        self.default_label = BasicLabel("")
        self.primary_label = BasicLabel("")
        self.sem_list = QtGui.QListWidget()
        self.sem_list.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum
        )
        self.mask_stack = QtGui.QStackedWidget()

        with dal.session_scope() as session:
            sem = session.query(SemFile).filter(SemFile.id == self.sem_id).first()

            for a, analysis in enumerate(sem.sem_analyses):
                mask_widget = RawImageTab()

                self.sem_list.addItem(str(analysis.id))
                self.mask_stack.addWidget(mask_widget)

                thread = DownloadThread(
                    url=analysis.mask_url,
                    thread_id=self.sem_id,
                    info={"analysis_id": analysis.id},
                )
                thread.downloadFinished.connect(mask_widget.loadImage)
                thread.start()

        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.set_primary_button, 0, 0, 1, 1)
        self.layout.addWidget(self.primary_label, 0, 1, 1, 1)
        self.layout.addWidget(self.sem_list, 1, 0, 1, 1)
        self.layout.addWidget(self.mask_stack, 1, 1, 1, 1)
        self.layout.addWidget(self.set_default_button, 3, 0, 1, 1)
        self.layout.addWidget(self.default_label, 3, 1, 1, 1)

        self.set_primary_button.clicked.connect(self.setPrimary)
        self.sem_list.currentRowChanged.connect(self.mask_stack.setCurrentIndex)
        self.sem_list.currentItemChanged.connect(
            lambda curr, prev: self.setDefaultStatus(int(curr.text()))
        )
        self.set_default_button.clicked.connect(self.setDefault)

    def setDefaultStatus(self, analysis_id):
        with dal.session_scope() as session:
            sem_file_model = (
                session.query(SemFile).filter(SemFile.id == self.sem_id).first()
            )

            self.default_label.setText(
                str(sem_file_model.default_analysis_id == analysis_id)
            )

    @errorCheck(error_text="Error setting as default SEM!")
    def setDefault(self):
        analysis_id = int(self.sem_list.currentItem().text())
        with dal.session_scope() as session:
            sem_file_model = (
                session.query(SemFile).filter(SemFile.id == self.sem_id).first()
            )

            sem_file_model.default_analysis_id = analysis_id
            session.commit()

        self.setDefaultStatus(analysis_id)

    @errorCheck(error_text="Error setting as primary SEM!")
    def setPrimary(self):
        with dal.session_scope() as session:
            experiment_model = (
                session.query(Experiment).filter(Experiment.id == self.experiment_id).first()
            )
            experiment_model.primary_sem_file_id = self.sem_id
            session.commit()

        self.setPrimaryStatus()

    def setPrimaryStatus(self):
        with dal.session_scope() as session:
            experiment_model = (
                session.query(Experiment).filter(Experiment.id == self.experiment_id).first()
            )
            self.primary_label.setText(str(experiment_model.primary_sem_file_id == self.sem_id))        


class SEMDisplayTab(QtGui.QScrollArea):
    def __init__(self, config, parent=None):
        super(SEMDisplayTab, self).__init__(parent=parent)
        self.config = config

        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.progress_bar = QtGui.QProgressBar()
        self.file_list = QtGui.QListWidget()
        self.sem_info = QtGui.QStackedWidget()
        self.experiment_id = None
        self.threadpool = DownloadPool(2)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.file_list.setFixedWidth(100)
        self.progress_bar.setFixedWidth(100)

        self.layout.addWidget(self.file_list, 0, 0, 1, 1)
        self.layout.addWidget(self.sem_info, 0, 1, 2, 1)
        self.layout.addWidget(self.progress_bar, 1, 0, 1, 1)

        self.file_list.currentRowChanged.connect(self.sem_info.setCurrentIndex)

    def upload_file(self, file_path, folder_name=None):
        box_adaptor = BoxAdaptor(self.config.box_config_path)
        upload_folder = box_adaptor.create_upload_folder(folder_name=folder_name)
        box_file = box_adaptor.upload_file(upload_folder, file_path, str(uuid.uuid4()))

        return box_file.get_shared_link_download_url(access="open")

    @errorCheck(success_text="Successfully submitted mask to database!",error_text='Error submitting mask!')
    def submitMask(self, sem_id, px_per_um, mask):
        assert isinstance(mask,np.ndarray)
        assert isinstance(px_per_um,int)
        mask_img = 255 * (1 - mask.astype(np.uint8))
        with dal.session_scope() as session:
            analysis = SemAnalysis()
            analysis.sem_file_id = sem_id
            experiment_model = (
                session.query(Experiment).filter(Experiment.id == self.experiment_id).first()
            )
            analysis.automated = False
            analysis.growth_coverage = float(np.mean(mask.astype(int)))
            analysis.px_per_um = int(px_per_um)

            fname = os.path.join(os.getcwd(), "%s_mask.png" % sem_id)
            cv2.imwrite(fname, mask_img)
            analysis.mask_url = self.upload_file(fname)
            os.remove(fname)

            print({i.name: getattr(analysis, i.name) for i in analysis.__table__.columns})

            session.add(analysis)
            session.commit()

            self.update(experiment_model, force_refresh=True)

    def update_progress_bar(self, *args, **kwargs):
        self.progress_bar.setValue(100 * self.threadpool.doneCount() / self.threadpool.count())

    def createSEMTabs(self, sem):
        sem_tabs = QtGui.QTabWidget()

        image_tab = RawImageTab()
        mask_tab = RawImageTab()

        sem_tabs.addTab(image_tab, "Raw Data")
        sem_tabs.addTab(mask_tab, "Mask")

        edit_tab = None
        admin_tab = None
        if self.config.canValidate():
            edit_tab = ImageEditor(sem_id=sem.id, config=self.config)
            edit_tab.submitClicked.connect(lambda x,y,z: self.submitMask(x,y,z))
            admin_tab = SEMAdminTab(sem_id=sem.id, experiment_id=self.experiment_id)

            sem_tabs.addTab(edit_tab, "Mask Editor")
            sem_tabs.addTab(admin_tab, "Admin")

        thread = DownloadThread(url=sem.url, thread_id=sem.experiment_id, info={"sem_id": sem.id})
        runner = self.threadpool.addThread(thread)
        runner.finished[object, int, object].connect(image_tab.loadImage)
        runner.finished.connect(self.update_progress_bar)
        if edit_tab is not None:
            runner.finished[object, int, object].connect(edit_tab.loadImage)

        if sem.default_analysis:
            thread = DownloadThread(url=sem.default_analysis.mask_url, thread_id=sem.id)
            runner = self.threadpool.addRunner(thread)
            runner.finished[object, int, object].connect(mask_tab.loadImage)

        return sem_tabs

    @errorCheck(error_text="Error updating SEM display!")
    def update(self, experiment_model=None, force_refresh=False):
        if experiment_model != None:
            if experiment_model.id != self.experiment_id or force_refresh:
                self.file_list.clear()
                self.progress_bar.reset()

                while self.sem_info.count()>0:
                    self.sem_info.removeWidget(self.sem_info.widget(0))

                self.threadpool.terminate()
                self.experiment_id = experiment_model.id
                if experiment_model.sem_files is not None:
                    if len(experiment_model.sem_files) > 0:
                        self.progress_bar.setValue(1)
                        for sem in experiment_model.sem_files:
                            self.file_list.addItem("SEM ID: %s" % sem.id)
                            self.sem_info.addWidget(self.createSEMTabs(sem))
                        self.threadpool.run()
                    else:
                        self.progress_bar.setValue(100)


class ProvenanceDisplayTab(QtGui.QScrollArea):
    def __init__(self, parent=None):
        super(ProvenanceDisplayTab, self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.author_widgets = []

    @errorCheck(error_text="Error updating provenance display!")
    def update(self, author_models=[]):
        for widget in self.author_widgets:
            self.layout.removeWidget(widget)
            sip.delete(widget)
        self.author_widgets = []

        for a, auth in enumerate(author_models):
            self.author_widgets.append(
                FieldsDisplayWidget(fields=["full_name_and_institution"], model=Author)
            )
            self.author_widgets[-1].setData(auth)
            self.layout.addWidget(self.author_widgets[-1], a, 0)


class RamanDisplayTab(QtGui.QScrollArea):
    def __init__(self, config, parent=None):
        super(RamanDisplayTab, self).__init__(parent=parent)
        self.config = config
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.progress_bar = QtGui.QProgressBar()
        self.file_list = QtGui.QListWidget()
        self.raman_info = QtGui.QStackedWidget()
        self.weighted_values = FieldsDisplayWidget(
            fields=raman_fields, model=RamanAnalysis, elements_per_col=1
        )
        self.experiment_id = None
        self.threads = []

        self.file_list.setFixedWidth(130)
        self.progress_bar.setFixedWidth(130)

        self.layout.addWidget(self.file_list, 0, 0, 1, 1)
        self.layout.addWidget(self.raman_info, 0, 1, 1, 1)
        self.layout.addWidget(self.weighted_values, 1, 1, 1, 1)
        self.layout.addWidget(self.progress_bar, 1, 0, 1, 1)

    def loadSpectrum(self, data, thread_id, spectrum_model):
        raman_tabs = QtGui.QTabWidget()
        byte_table = io.BytesIO()
        byte_table.write((io.BytesIO(data)).getvalue())
        byte_table.seek(0)
        data_table = pd.read_table(byte_table, index_col=False, error_bad_lines=False, encoding='utf-8')
        spectrum_plot_tab = RamanQueryWidget(data_table) # Replace QtGui.QWidget() with raman display, should use data to load spectrum. 
                                            # Note: may have to use io.BytesIO(data) to convert to bytes object to read from.
        spectrum_properties_tab = FieldsDisplayWidget(
            fields=spectrum_fields, model=RamanAnalysis
        )
        spectrum_properties_tab.setData(spectrum_model)
        raman_tabs.addTab(spectrum_plot_tab, "Spectrum")
        raman_tabs.addTab(spectrum_properties_tab, "Properties")

        if self.experiment_id == thread_id:
            self.file_list.addItem(
                "Spectrum %s (%s%%)"
                % (str(self.file_list.count() + 1), round(spectrum_model.percent, 2))
            )
            self.raman_info.addWidget(raman_tabs)
            self.progress_bar.setValue(
                100 * sum([t.isFinished() for t in self.threads]) / len(self.threads)
            )

    @errorCheck(error_text="Error updating Raman display!")
    # def update(self, raman_file_model=None):
    #     # print("\n SELF is:", self, "\n Model is:", raman_file_model, "\n trying to print id", raman_file_model.id)
    #     if raman_file_model != None:
    #         if raman_file_model.id != self.experiment_id:
    #             self.file_list.clear()
    #             self.progress_bar.reset()

    #             for w in [
    #                 self.raman_info.widget(i) for i in range(self.raman_info.count())
    #             ]:
    #                 self.raman_info.removeWidget(w)

    #             self.threads = []
    #             # self.experiment_id = raman_file_model.id
    #             raman_analysis = raman_file_model.raman_analyses
    #             self.weighted_values.setData(raman_analysis)
    #             if len(raman_analysis) > 0:
    #                 self.progress_bar.setValue(1)
    #                 for spectrum in raman_analysis:
    #                     thread = DownloadThread(
    #                         url=spectrum.raman_file.url,
    #                         thread_id=raman_analysis.raman_file.experiment_id,
    #                         info={"spectrum": spectrum},
    #                     )
    #                     thread.downloadFinished.connect(
    #                         lambda data, thread_id, info: self.loadSpectrum(data, thread_id, info['spectrum'])
    #                     )
    #                     thread.start()
    #                     print("Thread started.")
    #                     self.threads.append(thread)
    #             else:
    #                 self.progress_bar.setValue(100)
    def update(self, experiment_model=None):
        #print("\n SELF is:", self, "\n Model is:", experiment_model, "\n trying to print id", experiment_model.id)
        if experiment_model != None:
            if experiment_model.id != self.experiment_id:
                self.file_list.clear()
                self.progress_bar.reset()

                for w in [
                    self.raman_info.widget(i) for i in range(self.raman_info.count())
                ]:
                    self.raman_info.removeWidget(w)

                self.threads = []
                raman_files=experiment_model.raman_files
                raman_file = None
                #print(f"raman_files ar {raman_files}")
                if raman_files:
                    raman_file = raman_files[0]
                experiment_id = experiment_model.id
                if raman_file:
                    #this may have problems when multiple raman files are present - need to check
                    session = dal.Session()
                    raman_analyses = session.query(RamanAnalysis).filter(RamanAnalysis.raman_file_id == raman_file.id).all()
                    if raman_analyses:
                        self.weighted_values.setData(raman_analyses)
                        if len(raman_analyses) > 0:
                            self.progress_bar.setValue(1)
                            for spectrum in raman_analyses:
                                thread = DownloadThread(
                                    url=spectrum.raman_file.url,
                                    thread_id=experiment_id,
                                    info={"spectrum": spectrum},
                                )
                                thread.downloadFinished.connect(
                                    lambda data, thread_id, info: self.loadSpectrum(data, thread_id, info['spectrum'])
                                )
                                thread.start()
                                self.threads.append(thread)
                        else:
                            self.progress_bar.setValue(100)


class RecipeDisplayTab(QtGui.QScrollArea):
    def __init__(self, config, parent=None):
        super(RecipeDisplayTab, self).__init__(parent=parent)
        self.config = config
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.primary_axis = QtGui.QComboBox()
        self.recipe_model = None

        self.recipe_plot = pg.PlotWidget()
        self.recipe_plot.setMenuEnabled(False)
        # self.recipe_plot.setMouseEnabled(x=True, y=False)

        self.layout.addWidget(self.recipe_plot, 0, 0, 1, 2)
        self.layout.addWidget(BasicLabel("Primary Axis:"), 1, 0)
        self.layout.addWidget(self.primary_axis, 1, 1)

    @errorCheck(error_text="Error exporting recipe!")
    def exportRecipe(self):
        if self.config.mode == 'local':
            name = QtWidgets.QFileDialog.getSaveFileName(None, "Export Image", '', "JSON File (*.json)")[0]
            if name != '':
                with open(name,'w') as f:
                    json.dump(self.recipe_model.json_encodable(),f)
        elif self.config.mode == 'nanohub':
            name = 'recipe_%s.json'%self.recipe_model.id
            with open(name,'w') as f:
                json.dump(self.recipe_model.json_encodable(),f)
            subprocess.check_output('exportfile %s'%name,shell=True)
            os.remove(name)
        else:
            return        

    @errorCheck(error_text="Error updating recipe display!")
    def update(self, recipe_model):
        try:
            self.primary_axis.activated[str].disconnect()
        except:
            pass
        self.primary_axis.clear()
        self.recipe_plot.clear()
        self.recipe_model = recipe_model
        if self.recipe_model:
            session = dal.Session()
            steps = session.query(PreparationStep).filter(PreparationStep.recipe_id == recipe_model.id).all()
            step_list = sorted(
                steps, key=lambda x: getattr(x, "step")
            )
            self.data = {
                "furnace_pressure": [],
                "furnace_temperature": [],
                "argon_flow_rate": [],
                "hydrogen_flow_rate": [],
                "helium_flow_rate": [],
                "carbon_source_flow_rate": [],
                "duration": [],
                "cooling_rate": [],
                "name": [],
            }
            for step in step_list:
                for field in self.data.keys():
                    value = getattr(step, field)
                    if value:
                        self.data[field].append(value)
                    else:
                        self.data[field].append(np.nan)
            axis_fields = {
                "Furnace Temperature": "furnace_temperature",
                "Furnace Pressure": "furnace_pressure",
                "Helium Flow Rate": "helium_flow_rate",
                "Hydrogen Flow Rate": "hydrogen_flow_rate",
                "Carbon Source Flow Rate": "carbon_source_flow_rate",
                "Argon Flow Rate": "argon_flow_rate",
            }
            for field in list(axis_fields.keys()):
                if np.isnan(self.data[axis_fields[field]]).all():
                    del axis_fields[field]
            self.primary_axis.addItems(sorted(axis_fields.keys()))
            self.primary_axis.activated[str].connect(
                lambda x: self.plot(plot_field=axis_fields[x])
            )
            if self.primary_axis.count() > 0:
                self.primary_axis.setCurrentIndex(0)
                self.primary_axis.activated[str].emit(self.primary_axis.currentText())

    def plot(self, plot_field=None):
        self.recipe_plot.clear()
        if self.recipe_model and plot_field:
            if all(self.data["duration"]):

                timestamp = [0] + [
                    sum(self.data["duration"][:i])
                    for i in range(1, len(self.data["duration"]) + 1)
                ]

                x = np.linspace(0, sum(self.data["duration"]), 1000)
                condlist = [
                    np.logical_and(x >= timestamp[i], x < timestamp[i + 1])
                    for i in range(0, len(timestamp) - 1)
                ]
                y = np.piecewise(x, condlist, self.data[plot_field])
                if np.isfinite(y).sum() > 25:
                    win = signal.hann(25)
                    win /= win.sum()
                    y = scipy.convolve(y, win, mode="same")
                self.recipe_plot.plot(x=x, y=y, pen=pg.mkPen("r", width=8))
                self.recipe_plot.setXRange(min(x), max(x), padding=0)

                # print(self.data['duration'],timestamp,self.data[plot_field])

                colors = {"Annealing": "y", "Growing": "g", "Cooling": "b"}
                for n, name in enumerate(self.data["name"]):
                    if name in colors.keys():
                        x1 = sum(self.data["duration"][:n])
                        x2 = sum(self.data["duration"][: n + 1])

                        brush = pg.mkBrush(colors[name])
                        c = brush.color()
                        c.setAlphaF(0.2)
                        brush.setColor(c)
                        fb = pg.LinearRegionItem(
                            values=(x1, x2), movable=False, brush=brush
                        )
                        self.recipe_plot.addItem(fb)

                ay = self.recipe_plot.getAxis("left")
                yticks = np.unique(self.data[plot_field])
                # ay.setTicks([[(v, str(v)) for v in yticks]])

                ax = self.recipe_plot.getAxis("bottom")
                xticks = [0] + timestamp
                # ax.setTicks([[(v, str(v)) for v in xticks]])

                self.recipe_plot.setLabel(text="Time (min)", axis="bottom")
                info = getattr(PreparationStep, plot_field).info
                ylabel = info["verbose_name"]
                if "std_unit" in info:
                    if info["std_unit"]:
                        ylabel += " (%s)" % info["std_unit"]
                self.recipe_plot.setLabel(text=ylabel, axis="left")

                self.recipe_plot.enableAutoRange()


class AdminDisplayTab(QtGui.QScrollArea):
    updateQuery = QtCore.pyqtSignal()
    queryUnvalidated = QtCore.pyqtSignal()

    def __init__(self, config, parent=None):
        super(AdminDisplayTab, self).__init__(parent=parent)
        self.experiment_id = None
        self.config = config

        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

        self.validate_button = QtGui.QPushButton("Validate/Unvalidate")
        self.validate_button.clicked.connect(self.toggle_validate_model)
        self.validate_status_label = BasicLabel("")

        self.delete_button = QtGui.QPushButton("Delete Selected Entry")
        self.delete_button.clicked.connect(self.delete_model)
        self.delete_button.setStyleSheet("background-color: rgb(255,100,100)")

        self.query_unvalidated_button = QtGui.QPushButton("Query All Unvalidated")
        self.query_unvalidated_button.clicked.connect(
            lambda: self.queryUnvalidated.emit()
        )

        if self.config.canValidate() == False:
            self.validate_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.layout.addWidget(self.query_unvalidated_button, 0, 0, 1, 3)
        self.layout.addWidget(BasicLabel("Validation Status:"), 1, 0)
        self.layout.addWidget(self.validate_status_label, 1, 1)
        self.layout.addWidget(self.validate_button, 1, 2)
        self.layout.addWidget(self.delete_button, 2, 0, 1, 3)

    @errorCheck(error_text="Error updating admin display!")
    def update(self, experiment_model):
        self.experiment_id = experiment_model.id
        self.validate_status_label.setText(str(experiment_model.validated))

        if self.config.canWrite() or self.config.canValidate():
            if self.config.canValidate():
                self.delete_button.setEnabled(True)
            elif (
                self.config.canWrite()
                and experiment_model.nanohub_userid
                and experiment_model.nanohub_userid == os.getuid()
                and experiment_model.validate == False
            ):
                self.delete_button.setEnabled(True)
            else:
                self.delete_button.setEnabled(False)
        else:
            self.delete_button.setEnabled(False)

    def delete_model(self):
        confirmation_dialog = QtGui.QMessageBox(self)
        confirmation_dialog.setText("Are you sure you want to delete this recipe?")
        confirmation_dialog.setInformativeText(
            "Note: you will not be able to undo this submission."
        )
        confirmation_dialog.setStandardButtons(
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel
        )
        confirmation_dialog.setWindowModality(QtCore.Qt.WindowModal)

        def upload_wrapper(btn):
            if btn.text() == "OK":
                try:
                    with dal.session_scope() as session:
                        model = session.query(experiment).get(self.experiment_id)
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
        if self.experiment_id:
            with dal.session_scope() as session:
                model = session.query(Experiment).get(self.experiment_id)
                model.validated = not model.validated
                session.commit()
                self.validate_status_label.setText(str(model.validated))


if __name__ == "__main__":
    dal.init_db(config["development"])
    app = QtGui.QApplication([])
    query = GSAQuery()
    query.show()
    sys.exit(app.exec_())

from __future__ import division
import numpy as np
import cv2, sys, time, json, copy, subprocess, os
from PyQt5 import QtGui, QtCore
import uuid
from gresq.util.box_adaptor import BoxAdaptor
from gresq.util.gwidgets import GStackedWidget, ImageWidget
from gresq.util.util import BasicLabel, HeaderLabel, SubheaderLabel, sql_validator, ConfigParams, MaxSpacer
from gresq.database import dal, Base
from gresq import __version__ as GRESQ_VERSION
from gsaraman import __version__ as GSARAMAN_VERSION
from gsaimage import __version__ as GSAIMAGE_VERSION
from .util import get_or_add_software_row
from gresq.database.models import (
    Sample,
    Recipe,
    Author,
    Properties,
    PreparationStep,
    Properties,
    RamanFile,
    SemFile,
    RamanSet,
    RamanSpectrum,
    Software,
)
from sqlalchemy import String, Integer, Float, Numeric, Date
from gresq.config import config
from gresq.util.csv2db import build_db
#from gsaraman import GSARaman
from gresq.recipe import Recipe as RecipeMDF
from gresq.util.mdf_adaptor import MDFAdaptor, MDFException
from gresq.dashboard.query import convertScripts
from gsaraman.raw_plotter import RamanWidget


SOFTWARE_NAME = "gresq"

sample_fields = ["material_name", "experiment_date"]

preparation_fields = [
    "name",
    "duration",
    "furnace_temperature",
    "furnace_pressure",
    "sample_location",
    "helium_flow_rate",
    "hydrogen_flow_rate",
    "argon_flow_rate",
    "carbon_source",
    "carbon_source_flow_rate",
    "cooling_rate",
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
    "dewpoint",
]

properties_fields = [
    "average_thickness_of_growth",
    "standard_deviation_of_growth",
    "number_of_layers",
    "growth_coverage",
    "domain_size",
    "shape",
]

author_fields = ["first_name", "last_name", "institution"]


def convertValue(value, field):
    if sql_validator["int"](field):
        value = int(value)
    elif sql_validator["float"](field):
        value = float(value)
    else:
        value = str(value)
    return value


class GSASubmit(QtGui.QTabWidget):
    """
    Main submission widget
    """

    def __init__(
        self,
        config,
        parent=None
    ):
        super(GSASubmit, self).__init__(parent=parent)
        self.config = config
        self.properties = PropertiesTab(config=self.config)
        self.preparation = PreparationTab(config=self.config)
        self.provenance = ProvenanceTab(config=self.config)
        self.file_upload = FileUploadTab(config=self.config)
        self.review = ReviewTab(config=self.config)

        self.setTabPosition(QtGui.QTabWidget.South)
        self.addTab(self.preparation, "Preparation")
        if self.config.canWrite():
            self.addTab(self.properties, "Properties")
            self.addTab(self.file_upload, "File Upload")
            self.addTab(self.provenance, "Provenance")
            self.addTab(self.review, "Review")

        self.currentChanged.connect(
            lambda x: self.review.refresh(
                properties_response=self.properties.getResponse(),
                preparation_response=self.preparation.getResponse(),
                files_response=self.file_upload.getResponse(),
                provenance_response=self.provenance.getResponse(),
            )
            if x == self.indexOf(self.review)
            else None
        )

        self.review.submitButton.clicked.connect(
            lambda: self.review.submit(
                properties_response=self.properties.getResponse(),
                preparation_response=self.preparation.getResponse(),
                files_response=self.file_upload.getResponse(),
                provenance_response=self.provenance.getResponse(),
                validator_response=self.properties.validate()
                + self.preparation.validate()
                + self.file_upload.validate()
                + self.provenance.validate(),
            )
        )

        self.provenance.nextButton.clicked.connect(
            lambda: self.setCurrentWidget(self.review)
        )
        self.preparation.nextButton.clicked.connect(
            lambda: self.setCurrentWidget(self.properties)
        )
        self.properties.nextButton.clicked.connect(
            lambda: self.setCurrentWidget(self.file_upload)
        )
        self.file_upload.nextButton.clicked.connect(
            lambda: self.setCurrentWidget(self.provenance)
        )

        if config.test:
            self.test()

    def test(self):
        self.properties.testFill()
        self.provenance.testFill()
        self.preparation.testFill()


class FieldsFormWidget(QtGui.QScrollArea):
    """
    Generic widget that creates a form from the selected fields from a particular model. Automatically
    determines whether to use a combo box or line edit widget. Applies appropriate validators and
    allows users to select the appropriate unit as defined in the model. If the field is a String
    field and 'choices' is not in the model 'info' dictionary, a line edit is used instead of combo box.

    fields:         (list of str) The fields from the model to generate the form. NOTE: fields must exist in the model!
    model:          (SQLAlchemy model) The model to base the form on. The model is used to determine data type of each field
                    and appropriate ancillary information found in the field's 'info' dictionary.
    """

    def __init__(self, fields, model, parent=None):
        super(FieldsFormWidget, self).__init__(parent=parent)
        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.fields = fields
        self.model = model

        self.input_widgets = {}
        self.other_input = {}
        self.units_input = {}

        for f, field in enumerate(fields):
            row = f % 9
            col = f // 9
            info = getattr(model, field).info
            tooltip = info['tooltip'] if 'tooltip' in info.keys() else None
            self.layout.addWidget(BasicLabel(info["verbose_name"],tooltip=tooltip), row, 3 * col)
            if sql_validator["str"](getattr(model, field)):
                input_set = []
                if "choices" in info.keys():
                    input_set.extend(info["choices"])
                    with dal.session_scope() as session:
                        if hasattr(self.model, field):
                            for v in session.query(
                                getattr(self.model, field)
                            ).distinct():
                                if getattr(v, field) not in input_set:
                                    input_set.append(getattr(v, field))

                    self.input_widgets[field] = QtGui.QComboBox()
                    self.input_widgets[field].addItems(input_set)
                    self.input_widgets[field].addItem("Other")

                    self.other_input[field] = QtGui.QLineEdit()
                    self.other_input[field].setPlaceholderText(
                        "Enter other input here."
                    )
                    self.other_input[field].setFixedHeight(
                        self.other_input[field].sizeHint().height()
                    )
                    self.other_input[field].hide()

                    self.input_widgets[field].activated[str].connect(
                        lambda x, other_input=self.other_input[
                            field
                        ]: other_input.show()
                        if x == "Other"
                        else other_input.hide()
                    )
                    self.layout.addWidget(self.other_input[field], row, 3 * col + 2)
                    self.input_widgets[field].activated[str].emit(
                        self.input_widgets[field].currentText()
                    )

                else:
                    self.input_widgets[field] = QtGui.QLineEdit()
                    with dal.session_scope() as session:
                        if hasattr(self.model, field):
                            entries = [
                                v[0]
                                for v in session.query(
                                    getattr(self.model, field)
                                ).distinct()
                            ]
                            completer = QtGui.QCompleter(entries)
                            self.input_widgets[field].setCompleter(completer)
                self.layout.addWidget(self.input_widgets[field], row, 3 * col + 1)

            elif sql_validator["date"](getattr(model, field)):
                self.input_widgets[field] = QtGui.QDateEdit()
                self.input_widgets[field].setCalendarPopup(True)
                self.input_widgets[field].setDate(QtCore.QDate.currentDate())
                self.layout.addWidget(self.input_widgets[field], row, 3 * col + 1)

            else:
                self.input_widgets[field] = QtGui.QLineEdit()
                if sql_validator["int"](getattr(model, field)):
                    self.input_widgets[field].setValidator(QtGui.QIntValidator())
                elif sql_validator["float"](getattr(model, field)):
                    validator = QtGui.QDoubleValidator()
                    validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
                    self.input_widgets[field].setValidator(validator)

                if "conversions" in info.keys():
                    self.units_input[field] = QtGui.QComboBox()
                    self.units_input[field].addItems(info["conversions"].keys())
                    if "std_unit" in info.keys():
                        self.units_input[field].setCurrentIndex(
                            self.units_input[field].findText(info["std_unit"])
                        )

                self.layout.addWidget(self.input_widgets[field], row, 3 * col + 1)
                if field in self.units_input.keys():
                    self.layout.addWidget(self.units_input[field], row, 3 * col + 2)

        self.setWidgetResizable(True)
        self.setWidget(self.contentWidget)

    def validate(self):
        # Future implementations should use 'required' boolean field in info dict instead of a list.
        states = []
        for field in self.fields:
            input_widget = self.input_widgets[field]
            if isinstance(input_widget,QtGui.QLineEdit):
                validator = input_widget.validator()
                if validator != 0:
                    val = validator.validate(input_widget.text(),0)[0]
                    if val != QtGui.QValidator.Acceptable:
                        states.append("Field '%s' of model '%s' has input with validation state '%s'."%(field,self.model.__class__.__name__,val))
        return states


    def getModel(self):
        form_model = self.model()
        for field in self.fields:
            column = getattr(self.model, field)
            info = column.info
            if isinstance(self.input_widgets[field], QtGui.QComboBox):
                if self.input_widgets[field].currentText() == "Other":
                    value = self.other_input[field].text()
                else:
                    value = self.input_widgets[field].currentText()
                setattr(form_model, field, value)
            elif isinstance(self.input_widgets[field], QtGui.QDateTimeEdit):
                setattr(form_model, field, self.input_widgets[field].date().toPyDate())
            else:
                value = self.input_widgets[field].text()
                if value != "":
                    if field in self.units_input.keys():
                        unit = self.units_input[field].currentText()
                        conv = info["conversions"][unit]
                        value *= conv
                    setattr(form_model, field, convertValue(value, column))

        return form_model

    def getResponse(self):
        """
        Returns a dictionary response of the form fields. Dictionary, D, is defined as:
            D[field] = {
                'value':    output of the input widget for 'field'. If empty, it is None.
                'unit':     output of the units widget for 'field'. If empty or nonexistent, it is None.
            }
        """
        response = {}
        for field in self.fields:
            info = getattr(self.model, field).info
            response[field] = {}
            if isinstance(self.input_widgets[field], QtGui.QComboBox):
                if self.input_widgets[field].currentText() == "Other":
                    response[field]["value"] = self.other_input[field].text()
                else:
                    response[field]["value"] = self.input_widgets[field].currentText()
                response[field]["unit"] = ""
            elif isinstance(self.input_widgets[field], QtGui.QDateTimeEdit):
                response[field]["value"] = self.input_widgets[field].date().toPyDate()
            else:
                response[field]["value"] = (
                    self.input_widgets[field].text()
                    if self.input_widgets[field].text() != ""
                    else None
                )
                if field in self.units_input.keys():
                    response[field]["unit"] = self.units_input[field].currentText()
                else:
                    response[field]["unit"] = ""

        return response

    def fillResponse(self, response_dict):
        for field in self.fields:
            if response_dict[field]["value"]:
                value = response_dict[field]["value"]
                unit = response_dict[field]["unit"]
                input_widget = self.input_widgets[field]
                if isinstance(self.input_widgets[field], QtGui.QComboBox):
                    item_list = [
                        input_widget.itemText(i) for i in range(input_widget.count())
                    ]
                    if value in item_list:
                        input_widget.setCurrentIndex(item_list.index(value))
                    else:
                        input_widget.setCurrentIndex(item_list.index("Other"))
                        self.other_input[field].setText(value)
                elif isinstance(self.input_widgets[field], QtGui.QDateTimeEdit):
                    date = QtCore.QDate(value[0], value[1], value[2])
                    self.input_widgets[field].setDate(date)
                else:
                    input_widget.setText(str(value))
                    if field in self.units_input.keys():
                        units_widget = self.units_input[field]
                        units_list = [
                            units_widget.itemText(i)
                            for i in range(units_widget.count())
                        ]
                        units_widget.setCurrentIndex(units_list.index(unit))

    def testFill(self, fields=None):
        response_dict = {}
        if fields == None:
            fields = self.fields
        for field in fields:
            response_dict[field] = {}
            response_dict[field]["value"] = random_fill(field, self.model)
            if "std_unit" in getattr(self.model, field).info.keys():
                response_dict[field]["unit"] = getattr(self.model, field).info[
                    "std_unit"
                ]
            else:
                response_dict[field]["unit"] = None

        self.fillResponse(response_dict)

    def clear(self):
        for widget in list(self.input_widgets.values()) + list(
            self.other_input.values()
        ):
            if isinstance(widget, QtGui.QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QtGui.QLineEdit):
                widget.setText("")
            elif isinstance(widget, QtGui.QDateTimeEdit):
                widget.setDate(QtCore.QDate.currentDate())


class ProvenanceTab(QtGui.QWidget):
    """
    Provenance information tab. Users input author information.
    """

    def __init__(self, config, parent=None):
        super(ProvenanceTab, self).__init__(parent=parent)
        self.config = config
        self.mainLayout = QtGui.QGridLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

        # self.authors = GStackedWidget(border=True)
        # self.author_list = self.authors.createListWidget()

        self.stackedFormWidget = QtGui.QStackedWidget()
        self.stackedFormWidget.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.sample_input = FieldsFormWidget(fields=sample_fields, model=Sample)
        self.author_list = QtGui.QListWidget()
        self.author_list.currentRowChanged.connect(
            self.stackedFormWidget.setCurrentIndex
        )
        self.add_author_btn = QtGui.QPushButton("New Author")
        self.remove_author_btn = QtGui.QPushButton("Remove Author")
        self.nextButton = QtGui.QPushButton("Next >>>")
        self.clearButton = QtGui.QPushButton("Clear Fields")
        # spacer = QtGui.QSpacerItem(
        #     self.nextButton.sizeHint().width(),
        #     self.nextButton.sizeHint().height(),
        #     vPolicy=QtGui.QSizePolicy.Expanding,
        # )
        # hspacer = QtGui.QSpacerItem(
        #     self.nextButton.sizeHint().width(),
        #     self.nextButton.sizeHint().height(),
        #     vPolicy=QtGui.QSizePolicy.Expanding,
        #     hPolicy=QtGui.QSizePolicy.Expanding,
        # )

        self.layout = QtGui.QGridLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.addWidget(self.sample_input, 0, 0, 1, 2)
        self.layout.addWidget(self.stackedFormWidget, 1, 0, 1, 2)
        self.layout.addWidget(self.add_author_btn, 2, 0, 1, 1)
        self.layout.addWidget(self.remove_author_btn, 2, 1, 1, 1)
        self.layout.addWidget(self.author_list, 3, 0, 1, 2)
        self.layout.addItem(MaxSpacer(), 5, 0)
        self.layout.addWidget(self.clearButton, 4, 0, 1, 2)
        self.mainLayout.addLayout(self.layout, 0, 0)
        self.mainLayout.addItem(MaxSpacer(), 0, 1)
        self.mainLayout.addWidget(self.nextButton, 1, 0, 1, 2)

        self.add_author_btn.clicked.connect(self.addAuthor)
        self.remove_author_btn.clicked.connect(self.removeAuthor)
        self.clearButton.clicked.connect(self.clear)

    def validate_authors(self, provenance_response):
        if len(provenance_response["author"]) == 0:
            return "You must have at least one author."
        for a, auth in enumerate(provenance_response["author"]):
            if (
                auth["last_name"]["value"] == None
                or auth["first_name"]["value"] == None
            ):
                return (
                    "Author %s (input: %s, %s) must have a valid first and last name"
                    % (a, auth["last_name"]["value"], auth["first_name"]["value"])
                )
            if auth["institution"]["value"] == None:
                return "Author [%s, %s] must have a valid institution" % (
                    auth["last_name"]["value"],
                    auth["first_name"]["value"],
                )
        return True

    def validate(self):
        response = self.getResponse()
        return [self.validate_authors(response)]

    def addAuthor(self):
        """
        Add another author. Adds new entry to author list and creates new author input widget.
        """
        w = FieldsFormWidget(
            fields=["first_name", "last_name", "institution"], model=Author
        )
        idx = self.stackedFormWidget.addWidget(w)
        self.stackedFormWidget.setCurrentIndex(idx)
        self.author_list.addItem(
            "%s, %s"
            % (
                w.input_widgets["last_name"].text(),
                w.input_widgets["first_name"].text(),
            )
        )
        item = self.author_list.item(idx)
        w.input_widgets["last_name"].textChanged.connect(
            lambda txt: item.setText(
                "%s, %s"
                % (
                    w.input_widgets["last_name"].text(),
                    w.input_widgets["first_name"].text(),
                )
            )
        )
        w.input_widgets["first_name"].textChanged.connect(
            lambda txt: item.setText(
                "%s, %s"
                % (
                    w.input_widgets["last_name"].text(),
                    w.input_widgets["first_name"].text(),
                )
            )
        )

    def removeAuthor(self):
        """
        Removes author as selected from author list widget.
        """
        x = self.author_list.currentRow()
        self.stackedFormWidget.removeWidget(self.stackedFormWidget.widget(x))
        self.author_list.takeItem(x)

    def getResponse(self):
        """
        Returns a list of dictionary responses, as defined in FieldsFormWidget.getResponse() for each step.
        """
        response = []
        for i in range(self.stackedFormWidget.count()):
            response.append(self.stackedFormWidget.widget(i).getResponse())
        return {"author": response, "sample": self.sample_input.getResponse()}

    def clear(self):
        while self.author_list.count() > 0:
            self.author_list.setCurrentRow(0)
            self.removeAuthor()
        self.sample_input.clear()

    def testFill(self):
        for _ in range(3):
            self.addAuthor()
            self.stackedFormWidget.currentWidget().testFill()


class PropertiesTab(QtGui.QWidget):
    """
    Properties tab widget. Users input graphene properties and experimental parameters.
    """

    def __init__(self, config, parent=None):
        super(PropertiesTab, self).__init__(parent=parent)
        self.config = config
        self.mainLayout = QtGui.QGridLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

        self.properties_form = FieldsFormWidget(properties_fields, Properties)
        self.nextButton = QtGui.QPushButton("Next >>>")
        self.clearButton = QtGui.QPushButton("Clear Fields")
        spacer = QtGui.QSpacerItem(
            self.nextButton.sizeHint().width(),
            self.nextButton.sizeHint().height(),
            vPolicy=QtGui.QSizePolicy.Expanding,
        )
        hspacer = QtGui.QSpacerItem(
            self.nextButton.sizeHint().width(),
            self.nextButton.sizeHint().height(),
            vPolicy=QtGui.QSizePolicy.Expanding,
            hPolicy=QtGui.QSizePolicy.Expanding,
        )

        self.layout = QtGui.QGridLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.addWidget(self.properties_form, 0, 0)
        self.layout.addWidget(
            BasicLabel(
                "NOTE:\nThis section optional. Please input any properties data you may have."
            ),
            2,
            0,
        )
        self.layout.addWidget(self.clearButton, 1, 0)
        self.layout.addItem(spacer, 3, 0)

        self.mainLayout.addLayout(self.layout, 0, 0)
        self.mainLayout.addItem(hspacer, 0, 1)
        self.mainLayout.addWidget(self.nextButton, 1, 0, 1, 2)

        self.clearButton.clicked.connect(self.clear)

    def validate(self):
        return []

    def getResponse(self):
        return self.properties_form.getResponse()

    def clear(self):
        self.properties_form.clear()

    def testFill(self):
        self.properties_form.testFill()


class PreparationTab(QtGui.QWidget):
    """
    Preparation tab widget. Users input the recipe preparation steps.
    """

    oscm_signal = QtCore.pyqtSignal()

    def __init__(self, config, parent=None):
        super(PreparationTab, self).__init__(parent=parent)
        self.config = config
        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setAlignment(QtCore.Qt.AlignRight)

        self.stackedFormWidget = QtGui.QStackedWidget()
        self.stackedFormWidget.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.steps_list = QtGui.QListWidget()
        self.steps_list.setMaximumWidth(150)
        self.steps_list.currentRowChanged.connect(
            self.stackedFormWidget.setCurrentIndex
        )

        self.oscm_button = QtGui.QPushButton("Submit to OSCM")
        self.addStepButton = QtGui.QPushButton("Add Step")
        self.removeStepButton = QtGui.QPushButton("Remove Step")
        self.addStepButton.clicked.connect(self.addStep)
        self.removeStepButton.clicked.connect(self.removeStep)
        self.nextButton = QtGui.QPushButton("Next >>>")
        self.clearButton = QtGui.QPushButton("Clear Fields")
        self.clearButton.clicked.connect(self.clear)
        self.oscm_button.clicked.connect(self.handle_send_to_oscm)

        spacer = QtGui.QSpacerItem(
            self.nextButton.sizeHint().width(),
            self.nextButton.sizeHint().height(),
            vPolicy=QtGui.QSizePolicy.Expanding,
            hPolicy=QtGui.QSizePolicy.Expanding,
        )

        self.miniLayout = QtGui.QGridLayout()
        self.miniLayout.addWidget(self.addStepButton, 0, 0)
        self.miniLayout.addWidget(self.steps_list, 1, 0)
        self.miniLayout.addWidget(self.removeStepButton, 2, 0)
        self.recipeParams = FieldsFormWidget(fields=recipe_fields, model=Recipe)
        self.layout.addLayout(self.miniLayout, 0, 0, 3, 1)
        self.layout.addWidget(self.recipeParams, 0, 1, 1, 1)
        self.layout.addItem(spacer, 0, 1, 1, 2)
        self.layout.addWidget(self.stackedFormWidget, 1, 1, 1, 2)
        self.layout.addWidget(self.clearButton, 2, 1, 1, 1)
        self.layout.addWidget(self.oscm_button, 2, 2, 1, 1)
        self.layout.addWidget(self.nextButton, 3, 0, 1, 3)

    def testFill(self):
        self.recipeParams.testFill()
        for step in range(3):
            self.addStep()
            self.stackedFormWidget.currentWidget().testFill()
            name_widget = self.stackedFormWidget.currentWidget().input_widgets["name"]
            name_widget.setCurrentIndex(step)
            name_widget.activated[str].emit(name_widget.currentText())

    def validate(self):
        response = self.getResponse()
        return [
            self.validate_preparation(response),
            self.validate_temperature(response),
            self.validate_pressure(response),
            self.validate_base_pressure(response),
            self.validate_duration(response),
            self.validate_carbon_source(response),
        ]

    def validate_preparation(self, preparation_response):
        if len(preparation_response["preparation_step"]) == 0:
            return "Missing preparation steps."
        else:
            return True

    def validate_temperature(self, preparation_response):
        for s, step in enumerate(preparation_response["preparation_step"]):
            if step["furnace_temperature"]["value"] == None:
                return "Missing input for field '%s' for Preparation Step %s (%s)." % (
                    PreparationStep.furnace_temperature.info["verbose_name"],
                    s,
                    step["name"]["value"],
                )
        return True

    def validate_pressure(self, preparation_response):
        for s, step in enumerate(preparation_response["preparation_step"]):
            if step["furnace_pressure"]["value"] == None:
                return "Missing input for field '%s' for Preparation Step %s (%s)." % (
                    PreparationStep.furnace_pressure.info["verbose_name"],
                    s,
                    step["name"]["value"],
                )
        return True

    def validate_base_pressure(self, preparation_response):
        if preparation_response["recipe"]["base_pressure"]["value"] == None:
            return "Missing input for field '%s' in Preparation." % (
                Recipe.base_pressure.info["verbose_name"]
            )
        else:
            return True

    def validate_duration(self, preparation_response):
        for s, step in enumerate(preparation_response["preparation_step"]):
            if step["duration"]["value"] == None:
                return "Missing input for field '%s' for preparation Step %s (%s)." % (
                    PreparationStep.duration.info["verbose_name"],
                    s,
                    step["name"]["value"],
                )
        return True

    def validate_carbon_source(self, preparation_response):
        list_of_sources = [
            step["carbon_source"]["value"]
            for step in preparation_response["preparation_step"]
            if step["carbon_source"]["value"] and step["name"]["value"] == "Growing"
        ]
        list_of_flows = [
            step["carbon_source_flow_rate"]["value"]
            for step in preparation_response["preparation_step"]
            if step["carbon_source_flow_rate"]["value"]
            and step["name"]["value"] == "Growing"
        ]
        if len(list_of_sources) == 0:
            return "You must have at least one carbon source."
        if len(list_of_flows) != len(list_of_sources):
            return "You must have a flow rate for each carbon source."
        return True

    def addStep(self):
        """
        Add another step. Adds new entry to step list and creates new step input widget.
        """
        w = FieldsFormWidget(fields=preparation_fields, model=PreparationStep)
        idx = self.stackedFormWidget.addWidget(w)
        self.stackedFormWidget.setCurrentIndex(idx)
        self.steps_list.addItem(w.input_widgets["name"].currentText())
        item = self.steps_list.item(idx)
        w.input_widgets["name"].activated[str].connect(item.setText)
        # w.input_widgets['name'].activated[str].connect(
        #     lambda x: w.input_widgets['carbon_source'].hide() if x not in ['Growing','Cooling'] else w.input_widgets['carbon_source'].show())
        # w.input_widgets['name'].activated[str].connect(
        #     lambda x: w.input_widgets['carbon_source_flow_rate'].hide() if x not in ['Growing','Cooling'] else w.input_widgets['carbon_source_flow_rate'].show())
        # w.input_widgets['name'].activated[str].connect(
        #     lambda x: w.units_input['carbon_source_flow_rate'].hide() if x not in ['Growing','Cooling'] else w.units_input['carbon_source_flow_rate'].show())
        # w.input_widgets['name'].activated[str].emit(w.input_widgets['name'].currentText())

    def removeStep(self):
        """
        Removes step as selected from step list widget.
        """
        x = self.steps_list.currentRow()
        self.stackedFormWidget.removeWidget(self.stackedFormWidget.widget(x))
        self.steps_list.takeItem(x)

    def getResponse(self):
        """
        Returns a response dictionary containing:

        reparation_step:        A list of dictionary responses, as defined in FieldsFormWidget.getResponse() for each step.
        recipe:                 A dictionary containing response from recipe input widget.
        """
        prep_response = []
        for i in range(self.stackedFormWidget.count()):
            prep_response.append(self.stackedFormWidget.widget(i).getResponse())
        recipe_response = self.recipeParams.getResponse()

        return {"preparation_step": prep_response, "recipe": recipe_response}

    def clear(self):
        while self.steps_list.count() > 0:
            self.steps_list.setCurrentRow(0)
            self.removeStep()
        self.recipeParams.clear()

    def getRecipeDict(self, preparation_response):
        with dal.session_scope() as session:
            c = Recipe()
            for field, item in preparation_response["recipe"].items():
                value = item["value"]
                unit = item["unit"]
                if value != None:
                    if sql_validator["str"](getattr(Recipe, field)) or sql_validator[
                        "int"
                    ](getattr(Recipe, field)):
                        setattr(c, field, value)
                    elif sql_validator["float"](getattr(Recipe, field)):
                        value = float(value)
                        setattr(
                            c,
                            field,
                            value * getattr(Recipe, field).info["conversions"][unit],
                        )
                    else:
                        value = int(value)
                        setattr(c, field, value)
            session.add(c)
            session.flush()

            for step_idx, step in enumerate(preparation_response["preparation_step"]):
                p = PreparationStep()
                p.recipe_id = c.id
                p.step = step_idx
                for field, item in step.items():
                    value = item["value"]
                    unit = item["unit"]
                    if value != None:
                        if sql_validator["str"](
                            getattr(PreparationStep, field)
                        ) or sql_validator["int"](getattr(PreparationStep, field)):
                            setattr(p, field, value)
                        elif sql_validator["float"](getattr(PreparationStep, field)):
                            value = float(value)
                            setattr(
                                p,
                                field,
                                value
                                * getattr(PreparationStep, field).info["conversions"][
                                    unit
                                ],
                            )
                        else:
                            value = int(value)
                            setattr(p, field, value)
                session.add(p)
                session.flush()

            return c.json_encodable()

    def handle_send_to_oscm(self):
        preparation_response = self.getResponse()

        validator_response = self.validate()

        if any([v != True for v in validator_response]):
            error_dialog = QtGui.QMessageBox(self)
            error_dialog.setWindowModality(QtCore.Qt.WindowModal)
            error_dialog.setText("Input Error!")
            error_dialog.setInformativeText(
                "\n\n".join([v for v in validator_response if v != True])
            )
            error_dialog.exec()
            return

        # build oscm path
        oscm_dir = "oscm_files"
        oscm_path = os.path.abspath(oscm_dir)

        # define filename
        filename = "recipe.json"

        # preparation data. Here I just have JSON data for the example
        recipe_dict = self.getRecipeDict(preparation_response)

        # create file
        dump_file = open(os.path.join(oscm_path, filename), "w")
        json.dump(recipe_dict, dump_file)
        dump_file.close()

        # Stop preparing recipe and go to oscm widget (not sure if this work!!!)
        self.oscm_signal.emit()

class RamanFileWidget(QtGui.QWidget):
    def __init__(self,file_path=None,parent=None):
        super(RamanFileWidget,self).__init__(parent=parent)
        self.file_path = file_path
        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        self.characteristic = QtGui.QLineEdit()
        self.characteristic.setValidator(QtGui.QDoubleValidator(0.0, 100.0, 2))

        self.raman_display = RamanWidget(file_path) # replace QtGui.QWidget() with raman display, should use file_path to load spectrum

        self.layout.addWidget(BasicLabel("Characteristic Percentage:",tooltip="Percent of sample this spectrum represents."),0,0)
        self.layout.addWidget(self.characteristic,0,1)
        self.layout.addWidget(self.raman_display,1,0,1,2)

    def percent(self):
        return float("0"+self.characteristic.text())

class FileUploadTab(QtGui.QWidget):
    """
    File upload widget tab. Users upload SEM and Raman files as well as associated input.

    mode:   Upload method (local or nanohub)
    """

    def __init__(self, config, parent=None):
        super(FileUploadTab, self).__init__(parent=parent)
        self.layout = QtGui.QGridLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.config = config

        self.images = GStackedWidget(border=True)
        self.images.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.spectra = GStackedWidget(border=True)
        self.spectra.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.raman_list = self.spectra.createListWidget()
        self.sem_list = self.images.createListWidget()

        self.upload_sem = QtGui.QPushButton("Import")
        self.upload_raman = QtGui.QPushButton("Import")
        self.remove_sem = QtGui.QPushButton("Remove")
        self.remove_raman = QtGui.QPushButton("Remove")
        self.clearButton = QtGui.QPushButton("Clear Fields")
        self.wavelength_input = FieldsFormWidget(fields=["wavelength"], model=RamanFile)

        self.nextButton = QtGui.QPushButton("Next >>>")

        
        sem_layout = QtGui.QGridLayout()
        sem_layout.setAlignment(QtCore.Qt.AlignTop)
        sem_layout.addWidget(HeaderLabel("Upload SEM"),0,0,1,2)
        sem_layout.addWidget(self.sem_list,1,0,1,2)
        sem_layout.addWidget(self.upload_sem,2,0,1,1)
        sem_layout.addWidget(self.remove_sem,2,1,1,1)
        sem_dummy = QtGui.QWidget()
        sem_dummy.setLayout(sem_layout)
        sem_dummy.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)

        raman_layout = QtGui.QGridLayout()
        raman_layout.setAlignment(QtCore.Qt.AlignTop)
        raman_layout.addWidget(HeaderLabel("Upload Raman"),0,0,1,2)
        raman_layout.addWidget(self.wavelength_input,1,0,1,2)
        raman_layout.addWidget(self.raman_list,2,0,1,2)
        raman_layout.addWidget(self.upload_raman,3,0,1,1)
        raman_layout.addWidget(self.remove_raman,3,1,1,1)
        raman_dummy = QtGui.QWidget()
        raman_dummy.setLayout(raman_layout)
        raman_dummy.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)

        self.layout.addWidget(sem_dummy,0,0)
        self.layout.addWidget(self.images,0,1)
        self.layout.addWidget(raman_dummy,1,0)
        self.layout.addWidget(self.spectra,1,1)
        self.layout.addWidget(self.clearButton, 2, 0)
        self.layout.addWidget(self.nextButton, 2, 1)

        self.upload_sem.clicked.connect(self.importSEM)
        self.upload_raman.clicked.connect(self.importRaman)
        self.remove_sem.clicked.connect(self.removeSEM)
        self.remove_raman.clicked.connect(self.removeRaman)
        self.clearButton.clicked.connect(self.clear)

    def setWavelength(self, wavelength):
        self.wavelength_input.setText(str(wavelength))

    def removeSEM(self):
        self.images.removeCurrentWidget()

    def removeRaman(self):
        self.spectra.removeCurrentWidget()

    def importSEM(self, file_path=None):
        if file_path:
            sem_file_path = file_path
        else:
            sem_file_path = self.importFile()
        if isinstance(sem_file_path, str) and os.path.isfile(sem_file_path):
            image = ImageWidget(sem_file_path)
            self.images.addWidget(image,name=sem_file_path)

    def importRaman(self, file_path=None, pct=None):
        if file_path:
            raman_file_path = file_path
        else:
            raman_file_path = self.importFile()

        if isinstance(raman_file_path, str) and os.path.isfile(raman_file_path):
            self.spectra.addWidget(RamanFileWidget(raman_file_path),name=raman_file_path) # RamanFileWidget claass should be modified to display spectrum

    def importFile(self):
        if self.config.mode == "local":
            try:
                file_path = QtGui.QFileDialog.getOpenFileName()
                if isinstance(file_path, tuple):
                    file_path = file_path[0]
                else:
                    return
                return file_path
            except Exception as e:
                print(e)
                return
        elif self.config.mode == "nanohub":
            try:
                file_path = (
                    subprocess.check_output("importfile", shell=True)
                    .strip()
                    .decode("utf-8")
                )
                return file_path
            except Exception as e:
                print(e)
                return
        else:
            return

    def validate_percentages(self, files_response):
        if len(files_response["Raman Files"]) > 0:
            try:
                sm = []
                for i in files_response["Characteristic Percentage"]:
                    if i.strip() != "":
                        sm.append(float("0"+i))
                sm = sum(sm)
            except:
                return "Please make sure you have input a characteristic percentage for all Raman spectra."
            if sm != 100:
                return (
                    "Characteristic percentages must sum to 100%. They currently sum to %s."
                    % sm
                )
            return True
        else:
            return True

    def validate_raman_files(self, files_response):
        for ri, ram in enumerate(files_response["Raman Files"]):
            try:
                params = GSARaman.auto_fitting(ram)
            except:
                return "File formatting issue with file: %s" % ram
        return True

    def validate(self):
        response = self.getResponse()
        return [
            self.validate_percentages(response),
            #self.validate_raman_files(response),
        ]

    def getResponse(self):
        """
        Returns a response dictionary containing:
            SEM Image File:             The path to the SEM file.
            Raman Files:                A list of paths to the Raman files.
            Characteristic Percentage:  A list of percentages, where each entry represents the fraction of
                                        the sample that each Raman file represents.
            Raman Wavelength:           The wavelength of the Raman spectroscopy.
        """
        r = {
            "SEM Image Files": list(self.images.getMetanames()),
            "Raman Files": list(self.spectra.getMetanames()),
            "Characteristic Percentage": [spec.percent() for spec in self.spectra],
            "Raman Wavelength": self.wavelength_input.getResponse()["wavelength"][
                "value"
            ],
        }
        return r

    def clear(self):
        self.images.clear()
        self.spectra.clear()
        self.wavelength_input.clear()


class ReviewTab(QtGui.QScrollArea):
    """
    Review tab widget. Allows users to look over input and submit. Validates data and then uploads to MDF.
    """

    def __init__(self, config, parent=None):
        super(ReviewTab, self).__init__(parent=parent)
        self.config = config
        self.properties_response = None
        self.preparation_response = None
        self.files_response = None
        self.submitButton = QtGui.QPushButton("Submit")

    def zipdir(self, path, ziph):
        """
        Create a zipfile from a nested directory. Make the paths in the zip file
        relative to the root directory
        :param path: Path to the root directory
        :param ziph: zipfile handler
        :return:
        """
        for root, dirs, files in os.walk(path):
            for file in files:
                ziph.write(
                    os.path.join(root, file),
                    arcname=os.path.join(os.path.relpath(root, path), file),
                )

    def stage_upload(self, response_dict, response_files=[], json_name="mdf"):
        import zipfile, time, shutil

        mdf_dir = "mdf_%s" % time.time()
        os.mkdir(mdf_dir)
        mdf_path = os.path.abspath(mdf_dir)
        for f in response_files:
            if os.path.isfile(f):
                shutil.move(f, mdf_path)

        dump_file = open(os.path.join(mdf_path, "%s.json" % json_name), "w")
        json.dump(response_dict, dump_file)
        dump_file.close()

        box_adaptor = BoxAdaptor(self.config.box_config_path)
        upload_folder = box_adaptor.create_upload_folder()

        zip_path = mdf_path + ".zip"
        zipf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
        self.zipdir(mdf_path, zipf)
        zipf.close()
        print("Uploading ", zip_path, " to box")

        box_file = box_adaptor.upload_file(upload_folder, zip_path, mdf_dir + ".zip")

        return box_file

    def upload_recipe(self, response_dict=None, box_file=None, session=None):
        if session:
            session.commit()
        else:
            mdf = MDFAdaptor()
            return mdf.upload_recipe(Recipe(response_dict), box_file)

    def upload_raman(
        self,
        response_dict=None,
        raman_dict=None,
        box_file=None,
        dataset_id=None,
        session=None,
    ):
        if session:
            session.commit()
        else:
            mdf = MDFAdaptor()
            return mdf.upload_raman_analysis(
                Recipe(response_dict), dataset_id, raman_dict, box_file
            )

    def upload_file(self, file_path, folder_name=None):
        box_adaptor = BoxAdaptor(self.config.box_config_path)
        upload_folder = box_adaptor.create_upload_folder(folder_name=folder_name)
        box_file = box_adaptor.upload_file(upload_folder, file_path, str(uuid.uuid4()))

        return box_file.get_shared_link_download_url(access="open")

    def refresh(
        self,
        properties_response,
        preparation_response,
        files_response,
        provenance_response,
    ):
        """
        Refreshes the review fields.

        properties_response:        Response from PropertiesTab.getResponse().
        preparation_response:       Response from PreparationTab.getResponse().
        files_response:             Response from FileUploadTab.getResponse().
        provenance_response:        Response from ProvenanceTab.getResponse().
        """
        self.properties_response = properties_response
        self.preparation_response = preparation_response
        self.files_response = files_response

        self.contentWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.contentWidget)
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        propertiesLabel = HeaderLabel("Properties")
        preparationLabel = HeaderLabel("Recipe")
        filesLabel = HeaderLabel("Files")
        authorsLabel = HeaderLabel("Authors")

        # Author response
        self.layout.addWidget(
            authorsLabel, self.layout.rowCount(), 0, QtCore.Qt.AlignLeft
        )
        for a, auth in enumerate(provenance_response["author"]):
            row = self.layout.rowCount()
            self.layout.addWidget(
                BasicLabel(
                    "%s, %s   [%s]"
                    % (
                        auth["last_name"]["value"],
                        auth["first_name"]["value"],
                        auth["institution"]["value"],
                    )
                )
            )

        # Properties response
        self.layout.addWidget(
            propertiesLabel, self.layout.rowCount(), 0, QtCore.Qt.AlignLeft
        )
        label = BasicLabel()
        for field in properties_response.keys():
            info = getattr(Properties, field).info
            row = self.layout.rowCount()
            value = properties_response[field]["value"]
            unit = convertScripts(properties_response[field]["unit"])

            label = BasicLabel(info["verbose_name"])
            self.layout.addWidget(
                label, row, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter
            )
            self.layout.addWidget(
                BasicLabel(str(value)),
                row,
                1,
                QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter,
            )
            self.layout.addWidget(
                BasicLabel(str(unit)),
                row,
                2,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter,
            )
            self.layout.addItem(
                QtGui.QSpacerItem(
                    label.sizeHint().width(),
                    label.sizeHint().height(),
                    hPolicy=QtGui.QSizePolicy.Expanding,
                ),
                row,
                3,
            )

        # Preparation response
        self.layout.addItem(
            QtGui.QSpacerItem(
                label.sizeHint().width(),
                label.sizeHint().height(),
                vPolicy=QtGui.QSizePolicy.Fixed,
            ),
            self.layout.rowCount(),
            0,
        )
        self.layout.addWidget(
            preparationLabel, self.layout.rowCount(), 0, QtCore.Qt.AlignLeft
        )
        recipe_response = preparation_response["recipe"]
        for field in recipe_response.keys():
            info = getattr(Recipe, field).info
            row = self.layout.rowCount()
            value = recipe_response[field]["value"]
            unit = convertScripts(recipe_response[field]["unit"])
            label = BasicLabel(info["verbose_name"])
            self.layout.addWidget(
                label, row, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter
            )
            self.layout.addWidget(
                BasicLabel(str(value)),
                row,
                1,
                QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter,
            )
            self.layout.addWidget(
                BasicLabel(str(unit)),
                row,
                2,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter,
            )
            self.layout.addItem(
                QtGui.QSpacerItem(
                    label.sizeHint().width(),
                    label.sizeHint().height(),
                    hPolicy=QtGui.QSizePolicy.Expanding,
                ),
                row,
                3,
            )

        self.layout.addWidget(
            BasicLabel("Preparation Steps:"),
            self.layout.rowCount(),
            0,
            QtCore.Qt.AlignLeft,
        )
        for step, step_response in enumerate(preparation_response["preparation_step"]):
            stepLabel = SubheaderLabel("Step %s" % step)
            self.layout.addWidget(
                stepLabel, self.layout.rowCount(), 0, QtCore.Qt.AlignLeft
            )
            for field in step_response.keys():
                info = getattr(PreparationStep, field).info
                row = self.layout.rowCount()
                value = step_response[field]["value"]
                unit = convertScripts(step_response[field]["unit"])
                label = BasicLabel(info["verbose_name"])
                self.layout.addWidget(
                    label, row, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter
                )
                self.layout.addWidget(
                    BasicLabel(str(value)),
                    row,
                    1,
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter,
                )
                self.layout.addWidget(
                    BasicLabel(str(unit)),
                    row,
                    2,
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter,
                )
                self.layout.addItem(
                    QtGui.QSpacerItem(
                        label.sizeHint().width(),
                        label.sizeHint().height(),
                        hPolicy=QtGui.QSizePolicy.Expanding,
                    ),
                    row,
                    3,
                )

        # File upload response
        self.layout.addItem(
            QtGui.QSpacerItem(
                label.sizeHint().width(),
                label.sizeHint().height(),
                vPolicy=QtGui.QSizePolicy.Fixed,
            ),
            self.layout.rowCount(),
            0,
        )
        self.layout.addWidget(
            filesLabel, self.layout.rowCount(), 0, QtCore.Qt.AlignLeft
        )
        self.layout.addWidget(
            BasicLabel("SEM Image Files:"), self.layout.rowCount(), 0
        )
        for k in range(len(files_response["SEM Image Files"])):
            row = self.layout.rowCount()
            name = files_response["SEM Image Files"][k]
            label = BasicLabel("%s" % (name))
            self.layout.addWidget(
                label, row, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter
            )

        self.layout.addWidget(
            BasicLabel("Raman Wavelength"), self.layout.rowCount(), 0
        )
        self.layout.addWidget(
            BasicLabel(files_response["Raman Wavelength"]), self.layout.rowCount(), 1
        )
        self.layout.addWidget(
            BasicLabel("Raman Spectroscopy Files:"), self.layout.rowCount(), 0
        )
        for k in range(len(files_response["Raman Files"])):
            row = self.layout.rowCount()
            name = files_response["Raman Files"][k]
            pct = files_response["Characteristic Percentage"][k]
            label = BasicLabel("[%s]  %s" % (pct, name))
            self.layout.addWidget(
                label, row, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter
            )

        self.layout.addWidget(self.submitButton, self.layout.rowCount(), 0)

        self.setWidget(self.contentWidget)
        self.setWidgetResizable(True)

    def submit(
        self,
        properties_response,
        preparation_response,
        files_response,
        provenance_response,
        validator_response=[],
    ):
        """
        Checks and validates responses. If invalid, displays message box with problems.
        Otherwise, it submits the full, validated response and returns the output response dictionary.

        properties_response:        Response from PropertiesTab.getResponse().
        preparation_response:       Response from PreparationTab.getResponse().
        files_response:             Response from FileUploadTab.getResponse().
        provenance_response:        Response from ProvenanceTab.getResponse().

        Validations performed:
            Ensures temperature input for each preparation step.
            Ensures pressure input for each preparation step.
            Ensures timestep input for each preparation step.
            Ensures base pressure input in properties.
            Ensures total characteristic percentages add up to 100.
            Ensures at least one author.
            Ensures there is a carbon source.
            Ensures Raman files are formatted correctly.

        Returns dictionary containing:
        json:           json encodable dictionary of 'sample' model.
        **kwargs:       All entries from files_response

        """

        if any([v != True for v in validator_response]):
            error_dialog = QtGui.QMessageBox(self)
            error_dialog.setWindowModality(QtCore.Qt.WindowModal)
            error_dialog.setText("Input Error!")
            error_dialog.setInformativeText(
                "\n\n".join([v for v in validator_response if v != True])
            )
            error_dialog.exec()
            return

        with dal.session_scope() as session:
            ### SAMPLE DATASET ###
            gresq_soft = get_or_add_software_row(session, "gresq", GSAIMAGE_VERSION)
            gsaimage_soft = get_or_add_software_row(
                session, "gsaimage", GSAIMAGE_VERSION
            )
            gsaraman_soft = get_or_add_software_row(
                session, "gsaraman", GSARAMAN_VERSION
            )

            s = Sample(
                software_name=gresq_soft.name, software_version=gresq_soft.version
            )

            if self.config.mode == "nanohub":
                s.nanohub_userid = os.getuid()
            for field, item in provenance_response["sample"].items():
                value = item["value"]
                if value != None:
                    if sql_validator["str"](getattr(Sample, field)) or sql_validator[
                        "int"
                    ](getattr(Sample, field)):
                        setattr(s, field, value)
                    elif sql_validator["date"](getattr(Sample, field)):
                        setattr(s, field, value)
            session.add(s)
            session.flush()

            for f in files_response["SEM Image Files"]:
                print(f)
                sf = SemFile()
                sf.sample_id = s.id
                sf.filename = os.path.basename(f)
                sf.url = self.upload_file(f)
                session.add(sf)
                session.flush()

            ### RAMAN IS A SEPARATE DATASET FROM SAMPLE ###
            rs = RamanSet()
            rs.sample_id = s.id
            rs.experiment_date = provenance_response["sample"]["experiment_date"][
                "value"
            ]
            session.add(rs)
            session.flush()
            for ri, ram in enumerate(files_response["Raman Files"]):
                rf = RamanFile()
                rf.filename = os.path.basename(ram)
                rf.sample_id = s.id
                rf.url = self.upload_file(ram)
                if files_response["Raman Wavelength"] != None:
                    rf.wavelength = files_response["Raman Wavelength"]
                session.add(rf)
                session.flush()

                params = GSARaman.auto_fitting(ram)
                r = RamanSpectrum(
                    software_name=gsaraman_soft.name,
                    software_version=gsaraman_soft.version,
                )
                r.raman_file_id = rf.id
                r.set_id = rs.id
                if files_response["Characteristic Percentage"] != None:
                    r.percent = float(files_response["Characteristic Percentage"][ri])
                else:
                    r.percent = 0.0
                for peak in params.keys():
                    for v in params[peak].keys():
                        key = "%s_%s" % (peak, v)
                        setattr(r, key, float(params[peak][v]))
                session.add(r)
                session.flush()

            rs_fields = [
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
            for field in rs_fields:
                setattr(
                    rs,
                    field,
                    sum(
                        [
                            getattr(spect, field) * getattr(spect, "percent") / 100.0
                            for spect in rs.raman_spectra
                        ]
                    ),
                )
            rs.d_to_g = sum(
                [
                    getattr(spect, "d_peak_amplitude")
                    / getattr(spect, "g_peak_amplitude")
                    * getattr(spect, "percent")
                    / 100.0
                    for spect in rs.raman_spectra
                ]
            )
            rs.gp_to_g = sum(
                [
                    getattr(spect, "g_prime_peak_amplitude")
                    / getattr(spect, "g_peak_amplitude")
                    * getattr(spect, "percent")
                    / 100.0
                    for spect in rs.raman_spectra
                ]
            )
            session.flush()

            # Recipe
            c = Recipe()
            c.sample_id = s.id
            for field, item in preparation_response["recipe"].items():
                value = item["value"]
                unit = item["unit"]
                if value != None:
                    if sql_validator["str"](getattr(Recipe, field)) or sql_validator[
                        "int"
                    ](getattr(Recipe, field)):
                        setattr(c, field, value)
                    elif sql_validator["float"](getattr(Recipe, field)):
                        value = float(value)
                        setattr(
                            c,
                            field,
                            value * getattr(Recipe, field).info["conversions"][unit],
                        )
                    else:
                        value = int(value)
                        setattr(c, field, value)
            session.add(c)
            session.flush()

            # Properties
            pr = Properties()
            pr.sample_id = s.id
            for field, item in properties_response.items():
                value = item["value"]
                unit = item["unit"]
                if value != None:
                    if sql_validator["str"](
                        getattr(Properties, field)
                    ) or sql_validator["int"](getattr(Properties, field)):
                        setattr(pr, field, value)
                    elif sql_validator["float"](getattr(Properties, field)):
                        value = float(value)
                        setattr(
                            pr,
                            field,
                            value
                            * getattr(Properties, field).info["conversions"][unit],
                        )
                    else:
                        value = int(value)
                        setattr(pr, field, value)
            session.add(pr)
            session.flush()

            # Preparation Step
            for step_idx, step in enumerate(preparation_response["preparation_step"]):
                p = PreparationStep()
                p.recipe_id = c.id
                p.step = step_idx
                for field, item in step.items():
                    value = item["value"]
                    unit = item["unit"]
                    if value != None:
                        if sql_validator["str"](
                            getattr(PreparationStep, field)
                        ) or sql_validator["int"](getattr(PreparationStep, field)):
                            setattr(p, field, value)
                        elif sql_validator["float"](getattr(PreparationStep, field)):
                            value = float(value)
                            setattr(
                                p,
                                field,
                                value
                                * getattr(PreparationStep, field).info["conversions"][
                                    unit
                                ],
                            )
                        else:
                            value = int(value)
                            setattr(p, field, value)
                session.add(p)
                session.flush()

            for auth in provenance_response["author"]:
                a = Author()
                a.sample_id = s.id
                for field, item in auth.items():
                    value = item["value"]
                    if value != None:
                        setattr(a, field, value)
                session.add(a)
                session.flush()

            confirmation_dialog = QtGui.QMessageBox(self)
            confirmation_dialog.setText("Are you sure you want to submit this recipe?")
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
                        # response_dict = full_response['json']
                        # box_file = self.stage_upload(
                        #   response_dict,
                        #   response_files=full_response['Raman Files']+full_response['SEM Image Files'],
                        #   json_name='recipe'
                        #   )
                        # dataset_id = self.upload_recipe(response_dict,box_file)

                        # raman_dict = full_response['raman']
                        # box_file = self.stage_upload(
                        #   raman_dict,
                        #   json_name='raman'
                        #   )
                        # dataset_id = self.upload_raman(response_dict,raman_dict,box_file,dataset_id)
                        session.commit()
                        if config.mode == 'nanohub':
                            for ram in files_response["Raman Files"]:
                                os.remove(ram)
                            for sem in files_response["SEM Image Files"]:
                                os.remove(sem)

                        success_dialog = QtGui.QMessageBox(self)
                        success_dialog.setText("Recipe successfully submitted.")
                        success_dialog.setWindowModality(QtCore.Qt.WindowModal)
                        success_dialog.exec()

                    except MDFException as e:
                        error_dialog = QtGui.QMessageBox(self)
                        error_dialog.setWindowModality(QtCore.Qt.WindowModal)
                        error_dialog.setText("Submission Error!")
                        error_dialog.setInformativeText(str(e))
                        error_dialog.exec()
                        return

            confirmation_dialog.buttonClicked.connect(upload_wrapper)
            confirmation_dialog.exec()


def random_fill(field_name, model):
    import random, string, datetime

    field = getattr(model, field_name)
    if sql_validator["str"](field):
        return "".join(random.choice(string.ascii_uppercase) for _ in range(10))
    elif sql_validator["int"](field):
        return np.random.randint(10)
    elif sql_validator["float"](field):
        return round(np.random.randn() * 5 + 50, 3)
    elif sql_validator["date"](field):
        return datetime.datetime.today()
    else:
        return None


def make_test_dict(test_sem_file=None, test_raman_file=None):
    dal.init_db(config["development"])
    Base.metadata.drop_all(bind=dal.engine)
    Base.metadata.create_all(bind=dal.engine)

    with dal.session_scope() as session:
        s = Sample()
        for field in sample_fields:
            setattr(s, field, random_fill(field, Sample))
        session.add(s)
        session.flush()

        if test_sem_file:
            sf = SemFile()
            sf.sample_id = s.id
            sf.filename = os.path.basename(test_sem_file)
            session.add(sf)
            session.flush()

        c = Recipe()
        c.sample_id = s.id
        for field in recipe_fields:
            setattr(c, field, random_fill(field, Recipe))
        session.add(c)
        session.flush()

        for n, name in enumerate(["Annealing", "Growing", "Cooling"]):
            p = PreparationStep()
            p.recipe_id = c.id
            p.step = n
            p.name = name
            for field in preparation_fields:
                if field != "name":
                    setattr(p, field, random_fill(field, PreparationStep))
            session.add(p)
            session.flush()

        pr = Properties()
        pr.sample_id = s.id
        for field in properties_fields:
            setattr(pr, field, random_fill(field, Properties))
        session.add(pr)
        session.flush()

        for _ in range(3):
            a = Author()
            a.sample_id = s.id
            for field in author_fields:
                setattr(a, field, random_fill(field, Author))
            session.add(a)
            session.flush()

        if test_raman_file:
            rs = RamanSet()
            session.add(rs)
            session.flush()
            for ri, ram in enumerate([test_raman_file]):
                rf = RamanFile()
                rf.filename = os.path.basename(ram)
                rf.sample_id = s.id
                if files_response["Raman Wavelength"] != None:
                    rf.wavelength = 800
                session.add(rf)
                session.flush()

                params = GSARaman.auto_fitting(ram)
                r = RamanSpectrum()
                r.raman_file_id = rf.id
                r.set_id = rs.id
                r.percent = 100.0
                for peak in params.keys():
                    for v in params[peak].keys():
                        key = "%s_%s" % (peak, v)
                        setattr(r, key, params[peak][v])
                session.add(r)
                session.flush()

            rs_fields = [
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
            for field in rs_fields:
                setattr(
                    rs,
                    field,
                    sum(
                        [
                            getattr(spect, field) * getattr(spect, "percent") / 100.0
                            for spect in rs.raman_spectra
                        ]
                    ),
                )
            rs.d_to_g = sum(
                [
                    getattr(spect, "d_peak_amplitude")
                    / getattr(spect, "g_peak_amplitude")
                    * getattr(spect, "percent")
                    / 100.0
                    for spect in rs.raman_spectra
                ]
            )
            rs.gp_to_g = sum(
                [
                    getattr(spect, "g_prime_peak_amplitude")
                    / getattr(spect, "g_peak_amplitude")
                    * getattr(spect, "percent")
                    / 100.0
                    for spect in rs.raman_spectra
                ]
            )
            session.flush()

        if test_raman_file:
            return s.json_encodable, rs.json_encodable()
        else:
            return s.json_encodable(), None


if __name__ == "__main__":
    os.system("source gresq/sql_source.sh")
    dal.init_db(
        config["development"],
        privileges={"read": True, "write": True, "validate": False},
    )

    app = QtGui.QApplication([])
    submit = GSASubmit(
        box_config_path="box_config.json",
        privileges={"read": True, "write": True, "validate": False},
    )
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        submit.test()
    submit.show()
    sys.exit(app.exec_())

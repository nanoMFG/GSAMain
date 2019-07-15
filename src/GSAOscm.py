"""
Author: Ricardo Toro
Last update: 07/15/2019
"""

import os, sys, json, re
from PyQt5 import QtGui, QtCore, QtWidgets
from oscm_adapter import OSCMAdapter

label_bold = QtGui.QFont("Times", 7, QtGui.QFont.Bold)

class GSAOscm(QtWidgets.QTabWidget):
    '''
    Main oscm widget
    '''
    def __init__(self, server_instance='dev', parent=None):
        super(GSAOscm,self).__init__(parent=parent)

        # instantiate OSCM adapter
        self.session = OSCMAdapter(server_instance = server_instance)
        
        # set tab positions
        self.setTabPosition(QtWidgets.QTabWidget.North)

        # instantiate tabs
        self.login = LoginTab(self, self.session)
        self.oscm_register = OscmRegister(self, self.session)

        # add log in tab
        self.addTab(self.login,'Log in')

        # ---------------------------------------------------
        # Set general layout:
        # ---------------------------------------------------

        # get widget dimension
        frameGm = self.frameGeometry()
        # find centerPoint of the screen
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        # center widget
        frameGm.moveCenter(centerPoint)
        # Set final dimensions to the widget (x_screen_pos, x_screen_pos, width, height)
        self.setGeometry(frameGm)

    def handle_fatal_error(self, msg):

        # Enable log in Tab
        self.setTabEnabled(0, True)

        # Go to log in Tab
        self.setCurrentWidget(self.login)

        # remove all Tabs, but login
        for i in range(1, self.count()):
            self.removeTab(1)

        # pop up fatal error msg
        QtWidgets.QMessageBox.warning(self, 'Error', msg)
                           
class LoginTab(QtWidgets.QWidget):
    '''
	Login tab widget. Users input oscm credentials to get authentication token.
    '''

    def __init__(self, main_widget, session, parent=None):
        super(LoginTab, self).__init__(parent=parent)

        self.mw = main_widget
        
        self.session = session
        self.auth = {
            'success': False,
            'msg': None
        }

        # form fields
        max_width = 200
        self.username = QtWidgets.QLineEdit(self)
        self.username.setMaximumWidth(max_width)
        self.password = QtWidgets.QLineEdit(self)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setMaximumWidth(max_width)

        # login button
        buttonLogin = QtWidgets.QPushButton('Login', self)
        buttonLogin.setMaximumWidth(max_width)
        buttonLogin.clicked.connect(self.handle_login)

        # Register button
        buttonRegister = QtWidgets.QPushButton('Register', self)
        buttonRegister.setMaximumWidth(max_width)
        buttonRegister.clicked.connect(self.handle_register)

        # ---------------------------------------------------
        # layout:
        # ---------------------------------------------------
        # main layout
        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignCenter)

        # set layout
        layout = QtWidgets.QFormLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)

        layout.addRow('Username', self.username)
        layout.addRow('Password', self.password)
        layout.addRow('', buttonLogin)
        layout.addRow('', buttonRegister)

        spacer = QtWidgets.QSpacerItem(325, 0, hPolicy = QtWidgets.QSizePolicy.Fixed)

        mainLayout.addItem(spacer, 0, 0)
        mainLayout.addLayout(layout, 1, 1)

        self.setLayout(mainLayout)

    def handle_login(self):

        # Try to authenticate user
        self.auth = self.session.authenticate(self.username.text(), self.password.text())

        if self.auth['success']:
            # Pops up msg with success msg
            QtWidgets.QMessageBox.information(
                self, 'Success', 'User successfully authenticated !!!')

            # add OSCM Dashboard Tab
            self.createTransaction = CreateTransaction(self.mw, self.session)
            self.getTransaction = GetTransaction(self.mw, self.session)

            self.mw.addTab(self.createTransaction,'Create Transaction')
            self.mw.addTab(self.getTransaction,'Get Transaction')

            # Go to OSCM Dashboard Tab
            self.mw.setCurrentWidget(self.createTransaction)
            # Disable log in Tab
            self.mw.setTabEnabled(0, False)
            # Confirm programer that user is authenticated
            print('User successfully authenticated!')
            # clear input fields
            self.clear()

        else:
            # Pops up msg with Autentication error
            QtWidgets.QMessageBox.warning(
                self, 'Error', self.auth['msg'])
            self.clear()

    def handle_register(self):
        # add OSCM Register Tab
        self.mw.addTab(self.mw.oscm_register,'Register')
        # Go to OSCM Register Tab
        self.mw.setCurrentWidget(self.mw.oscm_register)
        # Disable log in Tab
        self.mw.setTabEnabled(0, False)

    def clear(self):
        # find all QLineEdit objectes and clear them 
        for attr, value in self.__dict__.items():
            if isinstance(value, QtWidgets.QLineEdit):
                value.setText('')

class CreateTransaction(QtWidgets.QWidget):
    '''
	Create Transaction tab widget. This Tab allows OSCM users to create transactions 
    in OSCM from Gr-ResQ tool. User authentication token is required.
    It is required that the user has access to create transaction in the facility.
    If user wants to attach a file (recipe.json), the file must exit in oscm_files directory.
    '''

    def __init__(self, main_widget, session, parent=None):
        super(CreateTransaction, self).__init__(parent=parent)

        # ---------------------------------------------------
        # layout:
        # ---------------------------------------------------
        # main layout
        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignCenter)

        # init layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setSpacing(10)

        self.mw = main_widget
        self.session = session

        # build oscm path
        oscm_dir = 'oscm_files'
        self.oscm_path = os.path.abspath(oscm_dir)

        # create list of files available
        self.myfiles = [QtWidgets.QCheckBox(f) for f in os.listdir(self.oscm_path) if os.path.isfile(os.path.join(self.oscm_path, f))]

        # get facilities
        self.get_facilities()
        
        if len(self.facilities) == 0:
            self.layout.addWidget(QtWidgets.QLabel("You do not have access to submit any transaction to a facility!!!"), 0, 0)
            self.layout.addWidget(QtWidgets.QLabel("Please contact a facility to be able to submit transactions."), 1, 0)
        else:

            # ---------------------------------------------------
            # transaction form fields:
            # ---------------------------------------------------
            max_width = 300

            # transaction name
            self.transaction_name = QtWidgets.QLineEdit(self)
            self.transaction_name.setMaximumWidth(max_width)

            # qty
            self.quantity = QtWidgets.QLineEdit(self)
            self.quantity.setMaximumWidth(60)
            self.quantity.setValidator(QtGui.QIntValidator(0,2147483647))

            # instructions
            self.instructions = QtWidgets.QTextEdit(self)

            # define dropdonwns
            self.facility_selection = QtWidgets.QComboBox() # facilities
            self.facility_selection.setMaximumWidth(max_width)
            self.queue_selection = QtWidgets.QComboBox()    # queues
            self.queue_selection.setMaximumWidth(max_width)

            # init description
            self.queue_decription = QtWidgets.QLabel('', self) # set default values

            # facility:
            self.facility_selection.addItems([item['facility_name'] for item in self.facilities])
            self.facility_selection.activated.connect(self.selected_facility)
            
            # queue:
            self.queues = []
            self.selected_facility(0)   # set default values
            self.queue_selection.activated.connect(self.selected_queue)

            # Submit Transaction button
            self.buttonSubmit = QtWidgets.QPushButton('Submit', self)
            self.buttonSubmit.clicked.connect(self.handle_submit)
            self.buttonSubmit.setMaximumWidth(100)

            # loading gif
            self.gif_path = os.path.abspath('img\loader.gif')
            self.gif = QtWidgets.QLabel()
            self.gif.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.gif.setAlignment(QtCore.Qt.AlignCenter)
            self.movie = QtGui.QMovie(self.gif_path)

            # set layout
            hspacer = QtWidgets.QSpacerItem(0, 0, hPolicy = QtWidgets.QSizePolicy.Expanding)
            vspacer = QtWidgets.QSpacerItem(0, 50, vPolicy = QtWidgets.QSizePolicy.Minimum)

            self.layout.addWidget(QtWidgets.QLabel("Transaction Name:"), 0, 0)
            self.layout.addWidget(self.transaction_name, 1, 0 )

            self.layout.addWidget(QtWidgets.QLabel("Quantity:"), 0, 1)
            self.layout.addWidget(self.quantity, 1, 1 )

            self.layout.addItem(hspacer, 1, 2 )

            self.layout.addWidget(QtWidgets.QLabel("Select Facility:"), 2, 0)
            self.layout.addWidget(self.facility_selection, 3, 0)
            self.layout.addItem(hspacer, 3, 1 )

            self.layout.addWidget(QtWidgets.QLabel("Select Queue:"), 4, 0)
            self.layout.addWidget(self.queue_selection, 5, 0)
            self.layout.addItem(hspacer, 5, 1 )

            self.layout.addWidget(QtWidgets.QLabel("Queue Description: "), 6, 0)
            self.layout.addWidget(self.queue_decription, 7, 0, 1, 3)

            self.layout.addWidget(QtWidgets.QLabel("Instructions:"), 8, 0)
            self.layout.addWidget(self.instructions, 9, 0, 1, 3 )

            row = 10

            if self.myfiles:
                self.layout.addWidget(QtWidgets.QLabel("Please select files to attach:"), row, 0)
                
                for file in self.myfiles:
                    row += 1
                    self.layout.addWidget(file, row, 0 )

            row += 1
            self.layout.addItem(vspacer, row , 0)
            row += 1
            self.layout.addWidget(self.buttonSubmit, row , 0)
            row += 1
            self.layout.addWidget(self.gif, row, 0 )

        mainLayout.addLayout(self.layout, 0, 0)
        self.setLayout(mainLayout)

    def handle_submit(self):

        # start laoding gif
        self.gif.setMovie(self.movie)
        self.movie.start()

        # create new transaction

        job_data = {
            'type': 'facility',
            'queue': self.queue,
            'start': None,
            'end': None,
            'processing': None,
            'quantity': self.quantity.text(),
            'instructions': self.instructions.text() if self.instructions.text() else 'no special instructions for this job'
        }

        # validate form. If validation does no pass, show msg with corresponding warning
        validate = self.validate_fields(self.transaction_name.text(), self.facility_id, job_data)
        if not validate['success']:
            # stop loading gif
            self.stop_loader()

            # Pops up msg with warning msg
            QtWidgets.QMessageBox.warning(
                self, 'New Transaction form', validate['msg'])
            return False
            
        response_new_transaction = self.session.submit_transaction(self.transaction_name.text(), self.facility_id, job_data)
        
        if response_new_transaction['success']:

            # submit files
            transaction_id = response_new_transaction['data']['_id']

            is_partial_success = False

            for file in self.myfiles:
                
                if file.isChecked():

                    # uncheck check box
                    file.setChecked(False)

                    # submit file
                    submitted_file = self.session.submit_file(transaction_id, self.oscm_path, file.text())

                    # check if file was sent successfully, otherwise pops an warning msg
                    if not submitted_file['success']:
                        is_partial_success = True
                        # Pops up msg with warning msg
                        QtWidgets.QMessageBox.warning(
                            self, 'Warning', 'Transaction submitted successfully, but failed to submit the file: ' + file.text())

            # success_submission
            self.success_submission(is_partial_success)
            
        else:
            # stop loading gif
            self.stop_loader()

            if response_new_transaction['msg'] == 'OSCM Server is currently down':
                self.mw.handle_fatal_error(response_new_transaction['msg'])
            else:
                # Pops up msg with warning msg
                QtWidgets.QMessageBox.warning(
                    self, 'Warning', response_new_transaction['msg'])
 
    def selected_facility(self, i):

        # get facility id
        self.facility_id = self.facilities[i]['_id'] if len(self.facilities) > 0 else None

        # get facility
        self.get_facility(self.facility_id)

        # get queues
        self.get_queues()

        # update queues dropdown
        self.queue_selection.clear()
        self.queue_selection.addItems([item['name'] for item in self.queues])

        # default queue is the first element of the dropdown  
        self.selected_queue(0)
        
    def selected_queue(self, i):

        # set queue value
        self.queue = self.queues[i]['_id']

        # update decription of the queue
        self.queue_decription.setText(self.queues[i]['description'])
           
    def get_facility(self, _id):

        # get facility
        facility_response = self.session.get_facility(_id)

        # save facility or handle fatal error
        if facility_response['success']:
            self.facility = facility_response['data']
        else:
            self.mw.handle_fatal_error(facility_response['msg'])

    def get_queues(self):

        self.queues.clear()
           
        queues_response = self.session.get_queues(self.facility)

        # save queues or handle fatal error
        if queues_response['success']:
            self.queues = queues_response['data']
        else:
            self.mw.handle_fatal_error(queues_response['msg'])

    def get_facilities(self):

        # get facilities
        facilities_response = self.session.get_user_facilities()

        # save facilities or handle fatal error
        if facilities_response['success']:
            self.facilities = facilities_response['data']
        else:
            self.facilities = []
            self.mw.handle_fatal_error(facilities_response['msg'])
        
    def validate_fields(self, transaction_name, facility_id, job_data):
           
        # validate all filled in        
        if not all(value != '' for value in job_data.values()) or  transaction_name == '' or facility_id == '':
            return {'success':False, 'msg': 'Plase fill in all entries'}

        return {'success': True}

    def success_submission(self, is_partial_success):

        # stop laoding gif
        self.stop_loader()

        # find all QLineEdit objectes and clear them 
        for attr, value in self.__dict__.items():
            if isinstance(value, QtWidgets.QLineEdit):
                value.setText('')

        if not is_partial_success:
            # Pops up msg with success msg
            QtWidgets.QMessageBox.information(
                self, 'Success', 'Transaction successfully submitted !!!')

    def stop_loader(self):
        # stop loading gif
        self.movie.stop()
        self.gif.clear()

class GetTransaction(QtWidgets.QWidget):
    '''
	Get Transaction tab widget. This Tab allows OSCM users to get transactions 
    from OSCM. User authentication token is required.
    All files downloaded go temporarily to oscm_files directory. Once, the Gr-resQ tool
    is closed, all files are removed.
    '''
    
    def __init__(self, main_widget, session, parent=None):
        super(GetTransaction, self).__init__(parent=parent)

        # ---------------------------------------------------
        # layout:
        # ---------------------------------------------------

        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)

        review_layout = QtWidgets.QVBoxLayout()
        review_layout.setAlignment(QtCore.Qt.AlignTop)

        self.files_layout = QtWidgets.QVBoxLayout()
        self.files_layout.setAlignment(QtCore.Qt.AlignTop)

        #---------------------------------------------------
        # Init widget
        #---------------------------------------------------

        self.mw = main_widget
        self.session = session

        # get transactions
        self.get_transactions()

        # define dropdonwns
        self.type_transaction = QtWidgets.QComboBox() # type transaction
        self.type_transaction.setMaximumWidth(150)

        self.transactions_available = QtWidgets.QComboBox() # list of transactios available for user
        self.transactions_available.setMaximumWidth(150)
        self.transactions_available.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.transactions_available.view().setMaximumHeight(200)

        # type of transaction:
        types_transaction = ['Requested by me', 'Requested on my facility'] 
        self.type_transaction.addItems(types_transaction)
        self.type_transaction.activated.connect(self.selected_type_transaction)

        # for review transaction:
        self.list_transactions = []
        facility_label = QtWidgets.QLabel('Facility:')
        facility_label.setFont(label_bold)
        self.facility_text = QtWidgets.QLabel('')

        submitted_label = QtWidgets.QLabel('Submitted:')
        submitted_label.setFont(label_bold)
        self.submitted_text = QtWidgets.QLabel('')

        status_label = QtWidgets.QLabel('Status:')
        status_label.setFont(label_bold)
        self.status_text = QtWidgets.QLabel('')

        qty_label = QtWidgets.QLabel('Quantity:')
        qty_label.setFont(label_bold)
        self.qty_text = QtWidgets.QLabel('')

        instructions_label = QtWidgets.QLabel('Instructions:')
        instructions_label.setFont(label_bold)
        self.instructions_text = QtWidgets.QLabel('')

        # for files:
        files_title_label = QtWidgets.QLabel('Files:')
        files_title_label.setFont(label_bold)

        # Download all files button
        self.buttondownload = QtWidgets.QPushButton('Download Files', self)
        self.buttondownload.clicked.connect(self.handle_download_all)
        
        # default transaction to the first in the list
        self.list_files = []
        self.selected_type_transaction(0)
        self.transactions_available.activated.connect(self.get_transaction)

        # list of two options of type of transaction (on my facility or requested by me)
        self.layout.addWidget(QtWidgets.QLabel("Select Type of Transaction:"), 0, 0)
        self.layout.addWidget(self.type_transaction, 1, 0)

        # list of transacions available for user to select
        self.layout.addWidget(QtWidgets.QLabel("Select Transaction:"), 2, 0)
        self.layout.addWidget(self.transactions_available, 3, 0)

        # set review layout data
        if self.transaction:
            review_layout.addWidget(facility_label)
            review_layout.addWidget(self.facility_text)           

            review_layout.addWidget(submitted_label)
            review_layout.addWidget(self.submitted_text)

            review_layout.addWidget(status_label)
            review_layout.addWidget(self.status_text)

            review_layout.addWidget(qty_label)
            review_layout.addWidget(self.qty_text)

            review_layout.addWidget(instructions_label)
            review_layout.addWidget(self.instructions_text)

        # create main box
        hbox = QtWidgets.QHBoxLayout()
        
        # Top lelf frame
        left = QtWidgets.QFrame()
        left.setFrameShape(QtWidgets.QFrame.StyledPanel)
        left.setLayout(self.layout)
        
        # Top right frame
        right = QtWidgets.QFrame()
        right.setFrameShape(QtWidgets.QFrame.StyledPanel)
        right.setLayout(review_layout)

        # Bottom frame
        bottom = QtWidgets.QFrame()
        bottom.setFrameShape(QtWidgets.QFrame.StyledPanel)
        bottom.setLayout(self.files_layout)

        # split top screen into two parts and add top left and top right frames 
        splitter1 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(left)
        splitter1.addWidget(right)
        splitter1.setSizes([200,300])

        # split vertically 
        splitter2 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(files_title_label)
        splitter2.addWidget(bottom)
        splitter2.addWidget(self.buttondownload)
        splitter2.setSizes([300, 10, 200, 20])
		
        # add box to main layout
        hbox.addWidget(splitter2)
        mainLayout.addLayout(hbox, 0, 0)

        self.setLayout(mainLayout)

    def get_transactions(self):
    
        # get transactions
        transactions_response = self.session.get_user_transactions()

        # save transactions or handle fatal error
        if transactions_response['success']:
            self.transactions_customer = sorted(transactions_response['data']['customer'], key=lambda k: k['submitted'], reverse=True) if 'customer' in transactions_response['data'].keys() else []
            self.transactions_provider = sorted(transactions_response['data']['provider'], key=lambda k: k['submitted'], reverse=True) if 'provider' in transactions_response['data'].keys() else []
        else:
            self.transactions_customer = []
            self.transactions_provider = []
            self.mw.handle_fatal_error(transactions_response['msg'])

    def selected_type_transaction(self, i):

        self.list_transactions.clear()

        self.list_transactions = self.transactions_customer[:] if i == 0 else self.transactions_provider[:]

        # list of available transactions. Depends on the transaction type
        self.transactions_available.clear()        

        if len(self.list_transactions) == 0:
            # pop up fatal error msg
             QtWidgets.QMessageBox.warning(self, 'Error', 'There are no transactions for the selected transaction type!!!')
        else:
            self.transactions_available.addItems([transaction['name'] for transaction in self.list_transactions])
            self.get_transaction(0)
    
        ''' # get facility id
        self.facility_id = self.facilities[i]['_id'] if len(self.facilities) > 0 else None

        # get facility
        self.get_facility(self.facility_id) '''

    def get_transaction(self, i):

        # get transaction id
        response_transaction_id = self.session.get_transaction_id(self.list_transactions[i])
    
        # get transaction if transaction exists
        if response_transaction_id['success']:

            # get transaction by id
            transaction_response = self.session.get_transaction(response_transaction_id['data'])

            # save transaction or handle fatal error
            if transaction_response['success']:

                # set transaction
                self.transaction = transaction_response['data']

                # updated review layout
                self.facility_text.setText(self.transaction['profile']['resource_locator']['name'])
                self.submitted_text.setText(self.transaction['job']['dates']['submitted'])
                self.status_text.setText(self.transaction['profile']['properties']['status'])
                self.qty_text.setText(str(self.transaction['job']['quantity']))
                self.instructions_text.setText(self.transaction['job']['instructions'])

                # remove current files if any:
                if self.files_layout.count() > 0:
                    self.list_files.clear()
                    for i in reversed(range(self.files_layout.count())): 
                        self.files_layout.itemAt(i).widget().setParent(None)

                # get files names for transaction
                file_names_response = self.session.get_files(response_transaction_id['data'])

                if file_names_response['success']:
                    # Show file names:
                    for item in file_names_response['data']:
                        file_name = item['filename']
                        self.files_layout.addWidget(QtWidgets.QLabel(file_name))
                        self.list_files.append(item['id'])

                    self.buttondownload.setEnabled(True)
                        
                else:
                    # let user know there are no files attached to this transaction
                    self.files_layout.addWidget(QtWidgets.QLabel('There are no files!'))
                    self.buttondownload.setEnabled(False)
                
            else:
                self.mw.handle_fatal_error(transaction_response['msg'])

    def handle_download_all(self):
        
        is_all = True   # if at any time is_all = False, means at least one file failed to download

        for file in self.list_files:
            
            try:
                download_file_response = self.session.session.get_file(file)
            except:
                self.mw.handle_fatal_error('OSCM Server is currently down')
                return False

            if not download_file_response['success']:
                is_all = False                 

        if is_all:
            QtWidgets.QMessageBox.information(self, 'Files', 'All files successfully downloaded!!!')
            self.buttondownload.setEnabled(False)

        else:
            # pop up fatal error msg
            QtWidgets.QMessageBox.warning(self, 'Error', 'At least one file failed to download')

class OscmRegister(QtWidgets.QWidget):

    '''
	Register OSCM tab widget. This Tab allows OSCM users to register
    in OSCM. The user must provide all inputs.
    '''
    
    def __init__(self, main_widget, session, parent=None):
        super(OscmRegister, self).__init__(parent=parent)

        self.session = session
        self.mw = main_widget

        # ---------------------------------------------------
        # register form fields:
        # ---------------------------------------------------
        self.name = QtWidgets.QLineEdit(self)
        self.username = QtWidgets.QLineEdit(self)
        self.email = QtWidgets.QLineEdit(self)
        self.phone = QtWidgets.QLineEdit(self)

        # address:
        self.street_address = QtWidgets.QLineEdit(self)
        self.city = QtWidgets.QLineEdit(self)
        
        self.postal_code = QtWidgets.QLineEdit(self)
        self.country = QtWidgets.QLineEdit(self)

        # state:
        #self.state = QtWidgets.QLineEdit(self)
        self.state = QtWidgets.QComboBox()
        states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL',
         'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE',
         'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD',
         'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'AA', 'AE', 'AP']

        self.state.addItems(states)

        self.password = QtWidgets.QLineEdit(self)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_confirmed = QtWidgets.QLineEdit(self)
        self.password_confirmed.setEchoMode(QtWidgets.QLineEdit.Password)

        # ---------------------------------------------------
        # Buttons form fields:
        # ---------------------------------------------------

        # Register button (submit)
        self.buttonSubmit = QtWidgets.QPushButton('Submit', self)
        self.buttonSubmit.clicked.connect(self.handle_submit)

        # Back button
        self.buttonBack = QtWidgets.QPushButton('Back to Login', self)
        self.buttonBack.clicked.connect(self.handle_back)

        # ---------------------------------------------------
        # layout:
        # ---------------------------------------------------
        # main layout
        mainLayout = QtWidgets.QGridLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)

        # set layout
        layout = QtWidgets.QGridLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setSpacing(10)

        layout2 = QtWidgets.QGridLayout()
        layout2.setAlignment(QtCore.Qt.AlignBottom)

        verticalSpacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        layout.addWidget(QtWidgets.QLabel("Name"), 0, 0)
        layout.addWidget(self.name, 1, 0 )
        layout.addWidget(QtWidgets.QLabel("Username"), 0, 1)
        layout.addWidget(self.username, 1, 1)
        layout.addWidget(QtWidgets.QLabel("Email"), 0, 2)
        layout.addWidget(self.email, 1, 2)
        layout.addWidget(QtWidgets.QLabel("Phone"), 0, 3)
        layout.addWidget(self.phone, 1, 3)

        layout.addWidget(QtWidgets.QLabel("Street Address"), 2, 0, 1, 3)
        layout.addWidget(self.street_address, 3, 0, 1, 3 )
        layout.addWidget(QtWidgets.QLabel("State"), 2, 3)
        layout.addWidget(self.state, 3, 3)
        layout.addWidget(QtWidgets.QLabel("Zip Code"), 4, 0)
        layout.addWidget(self.postal_code, 5, 0)
        layout.addWidget(QtWidgets.QLabel("City"), 4, 1)
        layout.addWidget(self.city, 5, 1)
        layout.addWidget(QtWidgets.QLabel("Country"), 4, 2)
        layout.addWidget(self.country, 5, 2)

        layout.addWidget(QtWidgets.QLabel("Password"), 6, 0)
        layout.addWidget(self.password, 7, 0)
        layout.addWidget(QtWidgets.QLabel("Confirm Password"), 6, 1)
        layout.addWidget(self.password_confirmed, 7, 1)

        layout.addWidget(self.buttonSubmit, 8, 3)
        
        layout2.addItem(verticalSpacer, 0, 0)
        layout2.addWidget(self.buttonBack, 1, 0)

        mainLayout.addLayout(layout, 0, 0)
        mainLayout.addLayout(layout2, 1, 2)

        self.setLayout(mainLayout)

    def handle_submit(self):

        # create new user
        new_user = {
            'name': self.name.text(),
            'email': self.email.text(),
            'username': self.username.text(),
            'phone': self.phone.text(),
            'password': self.password.text(),
            'address': {
                'street_address': self.street_address.text(),
                'city': self.city.text(),
                'state': self.state.currentText(),
                'postal_code': self.postal_code.text(),
                'country': self.country.text()
            }
        }

        # validate form. If validation does no pass, show msg with corresponding warning
        validate = self.validate_fields(new_user)
        if not validate['success']:
            # Pops up msg with warning msg
            QtWidgets.QMessageBox.warning(
                self, 'Register user form', validate['msg'])
            return False
            
        response_new_user = self.session.register_user(new_user)

        if response_new_user['success']:
            # Pops up msg with success msg
            QtWidgets.QMessageBox.information(
                self, 'Success', 'User successfully registered. Please check your email to confirm your account!!!')
            # clear form
            self.clear()
            self.handle_back()
            
        else:
            # Pops up msg with warning msg
            QtWidgets.QMessageBox.warning(
                self, 'Warning', response_new_user['msg'])
        
    def handle_back(self):
        # clear form
        self.clear()
        # get current tab index
        idx = self.mw.currentIndex()
        # Enable log in Tab
        self.mw.setTabEnabled(0, True)
        # Go to log in Tab
        self.mw.setCurrentWidget(self.mw.login)
        # remove OSCM Register Tab
        self.mw.removeTab(idx)
        
    def validate_fields(self, user):
       
        # validate all filled in
        if not all(value != '' for value in user.values()):
            return {'success':False, 'msg': 'Plase fill in all entries'}

        # valiedate email
        _re = r'[^@]+@[^@]+\.[^@]+'
        if not re.fullmatch(_re, user['email']):
            return {'success': False, 'msg': 'Please use a valid email'} 

        # valiedate phone num
        _re = r'^([0-9]( |-)?)?(\(?[0-9]{3}\)?|[0-9]{3})( |-)?([0-9]{3}( |-)?[0-9]{4}|[a-zA-Z0-9]{7})$'
        if not re.fullmatch(_re, user['phone']):
            return {'success': False, 'msg': 'Please use a valid phone number!'}

        # validate zip code
        _re =r'^[0-9]{5}([- /]?[0-9]{4})?$'
        if not re.fullmatch(_re, user['address']['postal_code']):
            return {'success': False, 'msg': 'Please use a valid zip code'}

        # valiedate password Strength
        _re = r'^(?=.*[A-Z,])(?=.*[!@#$&*,]).{8,}$'
        if not re.fullmatch(_re, user['password']):
            return {'success': False, 'msg': 'Please use a stronger password !'}

        # validate both passwords match
        if not user['password'] == self.password_confirmed.text():
            return {'success': False, 'msg': 'Password does not match the confirmed password !'}

        return {'success': True}

    def clear(self):
        # find all QLineEdit objectes and clear them 
        for attr, value in self.__dict__.items():
            if isinstance(value, QtWidgets.QLineEdit):
                value.setText('')
         
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    oscm = GSAOscm()
    oscm.show()
    sys.exit(app.exec_())

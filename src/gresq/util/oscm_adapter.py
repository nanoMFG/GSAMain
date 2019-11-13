from oscm_client import OSCMClient


class OSCMAdapter:
    # tested!
    def __init__(self, server_instance="prod", username=None, password=None):

        if server_instance is not "prod" or server_instance is not "dev":

            self.session = OSCMClient(server_instance)

            # Init public members
            self.token = None
            self.user = {}
            self.is_auth = False
            self.customer_locator = {}

            # if there are credentials, then authenticate
            if username is not None and password is not None:
                self.authenticate(username, password)

    # ---------------------------------------------------
    # Authenticate:
    # ---------------------------------------------------

    # tested!
    def authenticate(self, username=None, password=None):

        out = {"success": False, "msg": None}

        if username is None and password is None:
            out["msg"] = "Provide both arguments"
            return out

        else:
            try:
                response = self.session.authenticate(username, password)

            except ValueError:
                out["msg"] = "Failed to authenticate user in OSCM"
                return out

            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                # always check that we have token
                if self.session.is_auth:

                    # is auth:
                    self.is_auth = True

                    # user:
                    self.user = self.session.user

                    # get user phone num
                    phone = self.session.get_profile("profile.phone")["field"]

                    # customer locator:
                    self.customer_locator = {
                        "_id": self.user["profile"]["id"],
                        "name": self.user["profile"]["name"],
                        "email": self.user["profile"]["email"],
                        "phone": phone,
                    }

                    out["success"] = True
                    return out
                else:
                    out["msg"] = "Failed to authenticate user in OSCM"
                    return out
            else:
                out["msg"] = "Failed to authenticate user in OSCM"
                return out

    # ---------------------------------------------------
    # private:
    # ---------------------------------------------------

    # tested!
    def _send_confirmation_email(self, transaction_name=None, resource_name=None):

        out = {"success": False, "msg": None, "data": None}

        # Verify all parameters are given
        if transaction_name is None or resource_name is None:
            out[
                "msg"
            ] = "Please provide the transaction name and the resource name as the arguments"
            return out

        # always check that we have token
        if self.session.is_auth:

            user = self.get_user_profile()["data"]

            receiver = user["email"]
            subject = "New OSCM transaction"
            body = "<p> Dear " + user["name"] + ", </p>"
            body += (
                "<p> A new transaction: <strong><i>"
                + transaction_name
                + "</i></strong> has been sent to the resource <strong>"
                + resource_name
                + "</strong>. </p>"
            )
            body += '<p> For more details visit your transactions at <a href="https://oscm.mechse.illinois.edu"> https://oscm.mechse.illinois.edu</a> </p>'
            body += "<p> Best regards, </p>"
            body += "<p> OSCM Team </p>"

            try:
                response = self.session.send_email(receiver, subject, body)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                out["success"] = True
                return out
            else:
                out["msg"] = "Failed to send confirmation email"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # ---------------------------------------------------
    # Getters:
    # ---------------------------------------------------

    # tested!
    def get_user_profile(self):

        out = {"success": False, "msg": None, "data": None}

        if bool(self.user):
            out["success"] = True
            out["data"] = self.user["profile"]
            return out
        else:
            out["msg"] = "Failed to get user profile"
            return out

    # tested!
    def get_provider(self, _id=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have _id
        if _id is None:
            out["msg"] = "Please provide the provider id in the argument"
            return out

        # always check that we have token
        if self.session.is_auth:

            try:
                response = self.session.get_user_by_id(_id)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                out["success"] = True
                out["data"] = response["user"]
                return out
            else:
                out["msg"] = "Failed to get provider"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_user_resources(self):

        out = {"success": False, "msg": None, "data": None}

        # always check that we have token
        if self.session.is_auth:
            try:
                response = self.session.get_profile("resources")
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                out["success"] = True
                out["data"] = response["field"]
                return out
            else:
                out["msg"] = "Failed to get resources"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_user_facilities(self):

        out = {"success": False, "msg": None, "data": None}

        # always check that we have token
        if self.session.is_auth:
            try:
                response = self.session.get_profile("facilities")
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                out["success"] = True
                out["data"] = response["field"]
                return out
            else:
                out["msg"] = "Failed to get facilities"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_resource_id(self, resource=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have resource
        if resource is None or "_id" not in resource.keys():
            out[
                "msg"
            ] = "Please provide the resource data in the argument. Resource must have an _id key"
            return out

        # always check that we have token
        if self.session.is_auth:
            out["success"] = True
            out["data"] = resource["_id"]
            return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_facility_id(self, facility=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have facility
        if facility is None or "_id" not in facility.keys():
            out[
                "msg"
            ] = "Please provide the facility data in the argument. Facility must have an _id key"
            return out

        # always check that we have token
        if self.session.is_auth:
            out["success"] = True
            out["data"] = facility["_id"]
            return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_resource(self, _id=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have _id
        if _id is None:
            out["msg"] = "Please provide the resource id in the argument"
            return out

        # always check that we have token
        if self.session.is_auth:
            try:
                response = self.session.get_resource(_id)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                out["success"] = True
                out["data"] = response["resource"]
                return out
            else:
                out["msg"] = "Failed to get resource"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_facility(self, _id=None, path="_doc"):

        out = {"success": False, "msg": None, "data": None}

        # check that you have _id and path
        if _id is None or path is None:
            out["msg"] = "Please provide the facility id in the argument"
            return out

        # always check that we have token
        if self.session.is_auth:
            try:
                response = self.session.get_facility(_id, path)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                out["success"] = True
                out["data"] = response["facility"]
                return out
            else:
                out["msg"] = "Failed to get facility"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_queues(self, facility=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have facility
        if facility is None or "configuration" not in facility.keys():
            out[
                "msg"
            ] = "Please provide the facility data in the argument. Facility must have a configuration key"
            return out

        # always check that we have token
        if self.session.is_auth:
            out["success"] = True
            out["data"] = facility["configuration"]["queues"]
            return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_user_transactions(self, version="light"):

        out = {"success": False, "msg": None, "data": None}

        # always check that we have token
        if self.session.is_auth:

            # assume user is a customer
            try:
                response_customer = self.session.get_transactions("customer", version)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            # assume user is a provider
            try:
                response_provider = self.session.get_transactions("provider", version)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            # create user transactions output
            user_transactions = dict()

            # check if current user has transactions as a customer. If it does, append to dict
            if response_customer["success"] and response_customer["transactions"]:
                user_transactions["customer"] = response_customer["transactions"]

            # check if current user has transactions as a provider. If it does, append to dict
            if response_provider["success"] and response_provider["transactions"]:
                user_transactions["provider"] = response_provider["transactions"]

            out["success"] = True
            out["data"] = user_transactions
            return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_transaction_id(self, transaction=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have transaction
        if transaction is None or "id" not in transaction.keys():
            out[
                "msg"
            ] = "Please provide the transaction data in the argument. Transaction must have an id key"
            return out

        # always check that we have token
        if self.session.is_auth:
            out["success"] = True
            out["data"] = transaction["id"]
            return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_transaction(self, _id=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have _id
        if _id is None:
            out["msg"] = "Please provide the transaction id in the argument"
            return out

        # always check that we have token
        if self.session.is_auth:
            try:
                response = self.session.get_transaction(_id)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:
                user_transaction = dict()
                # The transaction comes decopled into profile and job
                user_transaction["profile"] = response["transaction"]
                user_transaction["job"] = response["job"]

                out["success"] = True
                out["data"] = user_transaction
                return out

            else:
                out["msg"] = "Failed to get transaction"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_files(self, _id=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have _id
        if _id is None:
            out["msg"] = "Please provide the transaction id in the argument"
            return out

        # always check that we have token
        if self.session.is_auth:
            try:
                files = self.session.get_files_metadata(_id)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if files["success"]:
                out["success"] = True
                out["data"] = files["files"]
                return out
            else:
                out["msg"] = "Failed to get files"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def get_file(self, _id=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have _id
        if _id is None:
            out["msg"] = "Please provide the file id in the argument"
            return out

        # always check that we have token
        if self.session.is_auth:
            try:
                file = self.session.get_file(_id)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if file["success"]:
                out["success"] = True
                out["data"] = file["filename"]
                return out
            else:
                out["msg"] = "Failed to get the file"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # ---------------------------------------------------
    # Setters:
    # ---------------------------------------------------

    # tested!
    def submit_transaction(
        self, transaction_name=None, resource_id=None, job_data=None
    ):

        out = {"success": False, "msg": None, "data": None}

        if transaction_name is None or resource_id is None or job_data is None:
            out[
                "msg"
            ] = "Please provide the transaction name, resource id and job id as arguments"
            return out

        # always check that we have token
        if self.session.is_auth:

            try:
                # get resource info depending on the resource type
                resource_response = (
                    self.get_resource(resource_id)
                    if job_data["type"] is "resource"
                    else self.get_facility(resource_id, path="_doc")
                )

                if resource_response["data"]:
                    resource = resource_response["data"]
                else:
                    out["msg"] = resource_response["msg"]
                    return out

            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            # get provider info and set provider info for future use
            provider_id = (
                resource["owner"]["_id"]
                if job_data["type"] is "resource"
                else resource["owner_locator"]["_id"]
            )
            if self.customer_locator["_id"] is provider_id:
                status = "approved"
                provider_locator = {
                    "_id": self.customer_locator["_id"],
                    "name": self.customer_locator["name"],
                    "email": self.customer_locator["email"],
                }
            else:
                status = "requested"
                provider = self.get_provider(provider_id)["data"]
                provider_locator = {
                    "_id": provider["_id"],
                    "name": provider["profile"]["name"],
                    "email": provider["profile"]["email"],
                }

            # ------------
            # Job:
            # ------------

            # set calendar id
            calendar_locator = {"_id": resource["configuration"]["calendar"]}

            # set user_locator
            users_locator = {
                "customer_id": self.customer_locator["_id"],
                "resource_id": resource_id,
            }

            # set properties (for now we are assumed to be manual mode)
            job_properties = {
                "status": status,
                "type": "single",
                "mode": "manual" if job_data["type"] is "resource" else "queue",
                "locked": True if job_data["type"] is "resource" else False,
            }

            # set dates
            start = job_data["start"]
            end = job_data["end"]

            dates = {"start": [start], "end": [end], "duedate": end, "readytime": start}

            # set times
            times = {
                "processing": job_data["processing"],
                "setuptime": 0,
                "cleaning": 0,
            }

            # set quantity
            quantity = job_data["quantity"]

            # set instructions
            instructions = (
                job_data["instructions"]
                if job_data["instructions"]
                else "no special instructions for this job"
            )

            # set other (we are assuming you have a cvd registered with no other)
            other = None

            # build job
            job = {
                "calendar_locator": calendar_locator,
                "users_locator": users_locator,
                "properties": job_properties,
                "dates": dates,
                "times": times,
                "quantity": quantity,
                "instructions": instructions,
                "other": other,
            }

            # ------------
            # Transaction:
            # ------------

            # set provider locator
            # Already computed above

            # set customer locator
            # Already computed when init OSCMAdaptor

            # set resource locator
            resource_locator = {
                "_id": resource_id,
                "name": resource["configuration"]["profile"]["resourcename"]
                if job_data["type"] is "resource"
                else resource["configuration"]["profile"]["facility_name"],
                "type": job_data["type"],
            }

            # Need to check if we need to add queue item to facility resource locator (ONLY IF FACILITY!!)
            if job_data["type"] is "facility":
                resource_locator["queue"] = job_data["queue"]

            # set job locator (for now we assumed to be None)
            job_locator = {"_id": None}

            # set transaction properties
            transaction_properties = {"name": transaction_name, "status": status}

            # messages (please empty list)
            messages = []

            # build transaction profile
            transaction = {
                "provider_locator": provider_locator,
                "customer_locator": self.customer_locator,
                "resource_locator": resource_locator,
                "job_locator": job_locator,
                "properties": transaction_properties,
                "messages": messages,
            }

            # ------------
            # Set transaction:
            # ------------
            try:
                response = self.session.submit_transaction(job, transaction)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response["success"]:

                user_transaction = response["transaction"]

                # Send confirmation email
                condirmation_email = self._send_confirmation_email(
                    transaction_name=transaction_name,
                    resource_name=resource_locator["name"],
                )

                if condirmation_email["success"] == False:
                    out["msg"] = condirmation_email["msg"]
                    return out

                out["success"] = True
                out["data"] = user_transaction
                return out

            else:
                out["msg"] = "Failed to set the transaction"
                return out
        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested!
    def submit_file(self, transaction_id=None, my_path=None, my_filename=None):

        out = {"success": False, "msg": None, "data": None}

        if transaction_id is None or my_path is None or my_filename is None:
            out[
                "msg"
            ] = "Please provide the transaction id, the path and the filename as arguments"
            return out

        # always check that we have token
        if self.session.is_auth:

            try:
                # Get basic info from the transaction that we need to submit file
                transaction_response = self.session.get_transaction(transaction_id)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if transaction_response["success"]:
                # Build metadata
                current_transaction = transaction_response["transaction"]

                transaction_data = {
                    "user_id": current_transaction["customer_locator"]["_id"],
                    "transaction_id": current_transaction["_id"],
                    "provider_id": current_transaction["provider_locator"]["_id"],
                }

                # Submit file with metadata
                try:
                    response = self.session.submit_file(
                        transaction_data, my_path, my_filename
                    )
                except:
                    out["msg"] = "OSCM Server is currently down"
                    return out

                if response["success"]:
                    out["success"] = True
                    out["data"] = response["file_id"]
                    return out
                else:
                    out["msg"] = "Failed to submit file"
                    return out

            else:
                out["msg"] = "Failed to get the transaction"
                return out

        else:
            out["msg"] = "Failed to authenticate user in OSCM"
            return out

    # tested
    def register_user(self, user=None):

        out = {"success": False, "msg": None, "data": None}

        # check that you have user
        if user is None:
            out["msg"] = "Please provide the user in the argument"
            return out
        else:
            user["accounts"] = [{"number": None, "type": "banner"}]

        # register new user
        try:
            response_new_user = self.session.register_new_user(user)
        except:
            out["msg"] = "OSCM Server is currently down"
            return out

        if response_new_user["success"]:

            current_event = {
                "event_type": "activate-account",
                "user": response_new_user["user"],
                "user_email": user["email"],
            }

            # add event into oscm
            try:
                response_event = self.session.add_event(current_event)
            except:
                out["msg"] = "OSCM Server is currently down"
                return out

            if response_event["success"]:
                # send confirmation email
                is_email = self.session.send_confirmation_email(
                    response_event["event"]["_id"], user["email"]
                )["success"]

                if is_email:
                    out["success"] = True
                    out["data"] = response_new_user["user"]
                    return out
                else:
                    out["msg"] = "Failed to send confirmation email"
                    return out
            else:
                out["msg"] = "Failed to add event"
                return out

        else:
            out["msg"] = "The user is already registered in OSCM"
            return out

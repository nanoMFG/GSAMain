# nanoMFG Software Planning Document
<!-- Replace text below with long title of project:short-name -->
## OSCM client for Gr-resQ tool: OSCM client
### Target Release: 1.0.0 : August 31, 2019

## Development Team
<!-- Complete table for all team members 
 roles: PI, developer, validation
 status: active, inactive
-->
Name | Role | github user | nanohub user | email | status
---|---|---|---|---|---
Placid Ferreira | PI | --- | --- |  pferreir@illinois.edu | active
Ricardo Toro | developer | torosant | --- | torosant@illinois.edu | active
Jorge E. Correa | developer | --- | --- | jcorre20@illinois.edu | active

**nanoMFG Github Team(s):** @gsa-dev
**nanoHUB Group(s):** Gr-resQ

## 1. Introduction
<!-- A  concise description of the current iteration of work. -->
OSCM is a full stack, operating system to manage manufacturing hardware (machines), manufacturing data (data bases),
and manufacturing  software  (applications),  in  networks  of  cloud  manufacturing. The operating system for cyber manufacturing (OSCM) aims to make manufacturing transactions automated, safe  and  verifiable  across  frictionless  and  scalable  networks. It  has  all  the  software  components  for machine  owners  and  customers  to  register, administrate  and  access  manufacturing  capacity  in  the network  through several  end-user  applications. 
The client in the Gr-resQ tool is just a user interface with the OSCM main server. It allows users to create and interact with transactions and resources.

### 1.1 Purpose and Vision Statement
<!--Why are we building this tool? What is the key benefit? How does it relate to existing tools and existing software? How does it fit into the overall objectives for the nanoMFG node? Who will use it?-->

The OSCM client for the Gr-resQ tool will allow nanoHUB users to create accounts in OSCM. In addition, they will be able to attach CDV experiment recipes to existing or new OSCM transactions. However, the most important feature of the client is to allow nanoHUB users to import process data of an experiment, such as temperatures, pressures, flows, etc. Then, all the data captured by the transaction (execution data and process data) will be available for nanoHUB users to analyze them or push them to MDF. 

### 1.2 References
<!--List any documents or background material that are relevant.  Links are useful. For instance, a link to a wiki or readme page in the project repository, or link to a uploaded file (doc, pdf, ppt, etc.).-->
Official OSCM url: (https://oscm-il.mechse.illinois.edu)

## 2 Overview and Major Planned Features
<!--Provide and overview characterising this proposed release.  Describe how users will interact with each proposed feature.-->

The OSCM client for Gr-resQ tool is divided into 3 parts: OSCM Client python package, OSCM adaptor and OSCM GUI.

* **OSCM Client python package**: Set of basic http requests (get, post, put, delete) to OSCM server. Software that is generic. 
* **OSCM adaptor**: Set of functions that use OSCM Client python package. It also, contains set of functions to interact with MDF. The software is particular to Gr-resQ tool.
* **OSCM GUI***: Graphical user interface embedded in Gr-resQ tool. It uses the OSCM adaptor functions.

### 2.1 Product Background and Strategic Fit
<!--Provide context for the proposed product.  Is this a completely new projects, or next version of an existing project? This can include a description of any contextual research, or the status of any existing prototype application.  If this SPD describes a component, describe its relationship to larger system. Can include diagrams.-->

The OSCM client for Gr-resQ is just one component of OSCM stack. This component is not essential for the OSCM platform, but it provides an alternative front end tool to OSCM. The current OSCM front end is web-based (https://oscm-il.mechse.illinois.edu). The idea is that this new client will provide an alternative front end to OSCM, while allowing nanoHUB users to get process data from different graphene experiments. The following figure provides details of the current and proposed implementation.    

Figure goes here ... ![Image of implementation](https://github.com/nanoMFG/GSA-Image/blob/planning/doc/OSCM_implementation.png)

### 2.2 Scope and Limitations for Current Release
<!--List the all planned goals/features for this release.  These should be links to issues.  Add a new subsection for each release.  Equally important, document feature you explicity are not doing at this time-->

As mentioned before, this component is divided into 3 software parts. The first release will consist of the first 2 components listed below.  

#### Release Notes v1.0.0
##### Planned Features
1. OSCM Client python package (90%) => HTTP request: Authentication, Users, Resources, Facilities, Transactions (jobs and files)
2. OSCM adaptor (70%) => python functions: Authentication, Users, Resources, Facilities, Transactions, jobs, mdf
3. OSCM GUI (0%)

##### Not Done
1. OSCM adaptor
2. OSCM GUI

### 2.3 Scope and Limitations for Subsequent Releases
<!--Short summary of  future envisioned roadmap for subsequent efforts.-->

1. Deploy OSCM Client python package and OSCM adaptor.
2. Integrate OSCM GUI into Gr-resQ tool.
3. Test with real experiments.

### 2.3 Operating Environment
<!--Describe the target environment.  Identify components or application that are needed.  Describe technical infrastructure need to support the application.-->

Same as Gr-resQ tool.

### 2.4 Design and Implementation Constraints
<!--This could include pre-existing code that needs to be incorporated ,a certain programming language or toolkit and software dependencies.  Describe the origin and rationale for each constraint.-->

The current OSCM platform is implemented as a MEAN stack. All the current code is written in Javascript. The OSCM client for the Gr-resQ is implemented in python. There should not be any issue between implementations since the OSCM API is transparent and language agnostic.

## 3 User Interaction and Design

### 3.1 Classes of Users
<!--Identify classes (types) of users that you anticipate will use the product.  Provide any relevant context about each class that may influence how the product is used: 
The tasks the class of users will perform
Access and privilege level
Features used
Experience level
Type of interaction
Provide links to any user surveys, questionnaires, interviews, feedback or other relevant information.-->

OSCM users are different from nanoHUB users. Therefore, if a nanoHUB user does not have an OSCM account, he/she will need to create one from the Gr-resQ tool or OSCM website.

OSCM users have different roles when interacting with resources (machines or facilities) and data. The roles are:
 * Owner: It is the provider or the owner of the resource or facility.
 * Administrator: It is the administrator of the resource or facility.
 * Operator: It is the operator of a machine or device.
 * Guest: It is the customer or person willing to use machine capacity. 
 
 For more information, please visit: (https://oscm-il.mechse.illinois.edu)

### 3.2 User Requirements
<!-- Provide a list of issue links to document the main set of user requirements to be satisfied by this release.  Use the user requirement template to draft thense issues.  A well written user requirement should be easy to justify (Rational) and should be testable.  List in order of priority as must have, should have or nice to have for each use case. -->

Although OSCM users have 4 different roles, we are going to assume only 2 main roles for the client implementation:
* Provider: (owner, administrator or operator)
* Customer: guest 

### 3.3 Proposed User Interface
<!--Could include drawn mockups, screenshots of prototypes, comparison to existing software and other descriptions.-->

Not available yet.

## 4. Data And Quality Attributes

### 4.1 Data Dictionary
<!--Summarize inputs and outputs for the application.-->
Inputs:
* OSCM username and password
* Experiment recipe (json)

Outputs:
* New transaction
* Process data file

### 4.2 Usability and Performance
<!--Summarize usability requirements such as easy of adoption for new users (eg example data),  inline documentation, avoiding errors, efficient interaction, etc.  Describe performance expectations  and/or document challenges.  Note you can reference user requirements from above if needed. -->
N.A

### 4.3 Testing, Verification and Validation
<!--Describe What data is necessary to verify the basic functionality of the application.  Provide a testing plan that includes a list of issues for each planned activity.  Describe data sets that are needed to test validation.-->

Each of the 3 components of the software are to tested individually. The python package and the adaptor are tested using pytest. The GUI will be tested with user cases, where a user:
1. Create an account in OSCM
2. Request a transaction in OSCM
3. Attach a recipe to the transaction
4. Request process data from transaction
5. Push and pull OSCM data to MDF

### 4.4 Uncertainty Quantification
<!--Identify and document possible sources of uncertainty. Categorize with standard labels, such as parametric, structural, algorithmic, experimental, interpolation.

N.A

Develop a plan for measuring and documenting uncertainty, e.g., using forward propagation or inverse UQ, and showing it in the application, if applicable.-->

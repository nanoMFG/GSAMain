# nanoMFG Software Planning Document
<!-- Replace text below with long title of project:short-name -->
## Graphene Recipe Profile Visualization: nanocool
### Target Release: 1.0.0 : June 30, 2019

## Development Team
<!-- Complete table for all team members 
 roles: PI, developer, validation
 status: active, inactive
-->
Name | Role | github user | nanohub user | email | status
---|---|---|---|---|---
Elif Ertekin | PI | elifleaf | Elif Ertekin | ertekin@illinois.edu | active
Sameh Tawfick | PI | -- | -- | tawfick@illinois.edu | active
Joshua Schiller | developer | jaschil2 | -- | jaschil2@illinois.edu | active
Darren Adams | developer | dadamsncsa | -- | dadams@illinois.edu | active
Kevin Cruse | developer | kevcruse96 | kcruse2  | kevcruse96@gmail.com  | inactive

**nanoMFG Github Team(s):** @GSAMain
**nanoHUB Group(s):** Gr-ResQ

## 1. Introduction
<!-- A  concise description of the current iteration of work. -->
The Gr-ResQ tool provides a platform for users to submit their recipes and associated output data, query/analyze existing recipe data and directly connect to the OSCM platform.

### 1.1 Purpose and Vision Statement
<!--Why are we building this tool? What is the key benefit? How does it relate to existing tools and existing software? How does it fit into the overall objectives for the nanoMFG node? Who will use it?-->
Chemical vapor deposition (CVD) synthesis of graphene depends on numerous input parameters, which can each have a significant effect on the outcome yield. Moreover, the results of most experiments are diffusely scattered in the literature and often times presented in a non-standardized form. Consequently, it can be difficult for researchers to learn and improve on the results of prior work. In order to expedite the process, Gr-ResQ provides a platform for researchers to pool the results of their experiments into a centralized database, whose data can then be analyzed to determine best practices or recipes.

### 1.2 References
<!--List any documents or background material that are relevant.  Links are useful. For instance, a link to a wiki or readme page in the project repository, or link to a uploaded file (doc, pdf, ppt, etc.).-->
- https://en.wikipedia.org/wiki/Graphene
- https://en.wikipedia.org/wiki/Chemical_vapor_deposition

## 2 Overview and Major Planned Features
<!--Provide and overview characterising this proposed release.  Describe how users will interact with each proposed feature. Include a schematic/diagram to illustrate an overview of proposed software and achitecture componets for the project-->

<img width="743" alt="Screen Shot 2019-10-10 at 6 46 21 PM" src="https://user-images.githubusercontent.com/12614221/66614426-a5bcad80-eb8e-11e9-81b8-48cf18cfffb4.png">

The work in this repository involves the construction of a submission tool to collect graphene recipe data, a query tool to search for and visualize the data and associated analysis tools. The analyses allow for SEM segmentation to determine graphene coverage of a substrate, automatic processing of Raman spectroscopy data to extract graphene characteristics as well as statistical tools to view the recipes. In addition, Gr-ResQ is connected to OSCM to facilitate the creation of new experiments directly from the platform. The data on the platform is then stored in the Materials Data Facility (MDF) for greater open source access to other researchers.

<!--### 2.1 Product Background and Strategic Fit -->
<!--Provide context for the proposed product.  Is this a completely new projects, or next version of an existing project? This can include a description of any contextual research, or the status of any existing prototype application.  If this SPD describes a component, describe its relationship to larger system. Can include diagrams.-->

### 2.2 Scope and Limitations for Current Release
<!--List the all planned goals/features for this release.  These should be links to issues.  Add a new subsection for each release.  Equally important, document feature you explicity are not doing at this time-->
- [Image segmentation of SEM images](https://github.com/nanoMFG/GSAMain/issues/77)
- [Submit graphene recipe and associated data](https://github.com/nanoMFG/GSAMain/issues/78)
- [Query graphene data](https://github.com/nanoMFG/GSAMain/issues/79)
- [Visualize recipe data in database](https://github.com/nanoMFG/GSAMain/issues/80)
- [Analysis on graphene data](https://github.com/nanoMFG/GSAMain/issues/81)

<!-- ##### 2.2.1 Planned Features -->

#### 2.2.2 Release Notes 
##### v0.9.0

### 2.3 Scope and Limitations for Subsequent Releases
<!--Short summary of  future envisioned roadmap for subsequent efforts.-->
This release will be constrained to primary functionality: submission, query and validation. Future releases will allow image segmentation (both manual and automatic) as well as possible machine learning integration.

### 2.3 Operating Environment
<!--Describe the target environment.  Identify components or application that are needed.  Describe technical infrastructure need to support the application.-->
python environment utilizing the pyqt framework. Database utilizes MySQL backend with a SQLAlchemy ORM. Other requirements are listed in the requirements.txt file. Designed to work locally or on nanohub.org.

<!-- ### 2.4 Design and Implementation Constraints -->
<!--This could include pre-existing code that needs to be incorporated ,a certain programming language or toolkit and software dependencies.  Describe the origin and rationale for each constraint.-->

## 3 User Interaction and Design

### 3.1 Classes of Users
<!--Identify classes (types) of users that you anticipate will use the product.  Provide any relevant context about each class that may influence how the product is used: 
The tasks the class of users will perform
Access and privilege level
Features used
Experience level
Type of interaction
Provide links to any user surveys, questionnaires, interviews, feedback or other relevant information.-->
|          | Tasks          | Access        | Features Used |
Submitter  | Submits graphene recipes and associate SEM/Raman data | Read and write | Uses submit tool / query tool
Querier    | Uses tool primarily for search and analysis | Read only | Uses query tool
Validator  | Verifies submissions and performs post processing on inputted data | Read / Write / Validate | Uses admin tools
OSCM User  | Submits recipes to OSCM | Read or write | Uses submit tool along with OSCM interface

<!-- ### 3.2 User Requirements -->
<!-- Provide a list of issue links to document the main set of user requirements to be satisfied by this release.  Use the user requirement template to draft thense issues.  A well written user requirement should be easy to justify (Rational) and should be testable.  List in order of priority as must have, should have or nice to have for each use case. -->

### 3.3 Proposed User Interface
<!--Could include drawn mockups, screenshots of prototypes, comparison to existing software and other descriptions.-->

<img width="1259" alt="Screen Shot 2019-09-13 at 1 04 14 PM" src="https://user-images.githubusercontent.com/12614221/66623029-8bdf9280-ebaf-11e9-98d1-5730c79d8b52.png">

<img width="1259" alt="Screen Shot 2019-09-13 at 1 05 48 PM" src="https://user-images.githubusercontent.com/12614221/66623058-b29dc900-ebaf-11e9-9d20-30fb013e27d2.png">

<!-- ### 3.4 Documentation Plan -->
<!-- List planned documentation activities -->

<!-- ### 3.5 User Outreach Plan -->
<!-- List upcoming activities designed to elicit user feedback and/or engage new users.  Use issues for activities that will be completed this iteration-->

## 4. Data And Quality Attributes

### 4.1 Data Dictionary
<!--Summarize inputs and outputs for the application.-->

### 4.2 Usability and Performance
<!--Summarize usability requirements such as easy of adoption for new users (eg example data),  inline documentation, avoiding errors, efficient interaction, etc.  Describe performance expectations  and/or document challenges.  Note you can reference user requirements from above if needed. -->

### 4.3 Testing, Verification and Validation
<!--Describe What data is necessary to verify the basic functionality of the application.  Provide a testing plan that includes a list of issues for each planned activity.  Describe data sets that are needed to test validation.-->

<!-- ### 4.4 Uncertainty Quantification -->
<!--Identify and document possible sources of uncertainty. Categorize with standard labels, such as parametric, structural, algorithmic, experimental, interpolation.

<!-- Develop a plan for measuring and documenting uncertainty, e.g., using forward propagation or inverse UQ, and showing it in the application, if applicable.-->

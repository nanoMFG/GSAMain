<!--[![Build Status](https://travis-ci.com/nanoMFG/GSAMain.svg?token=N4nkhb241rGHotEqsu3q&branch=master)](https://travis-ci.com/nanoMFG/GSAMain) -->

[![Dev Status](https://img.shields.io/endpoint?url=https://salty-headland-67572.herokuapp.com/badges/phase?repo=GSAMain)](https://img.shields.io/endpoint?url=https://salty-headland-67572.herokuapp.com/badges/phase?repo=GSAMain)
### For Developers

#### Software Planning Documents

 * [gresq_SPD_1.1.0.md](https://github.com/nanoMFG/GSAMain/blob/planning_1.1.0/doc/SPD/gresq_SPD_1.1.0.md) \*
 * Draft SPD \*\* <br>


# Graphene-Synthesis-Analysis

<!-- One Paragraph of project description goes here. -->

## Getting Started

The latest production version of this application is hosted **on nanoHUB** for public use:<br/>
[https://nanohub.org/tools/gresq](https://nanohub.org/tools/gresq)

### Installing Locally
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment notes (below) for info on how to deploy the project on nanoHUB.

##### Cloning From GitHub:
The code in the repository uses submoded fro mthe GSAImage and GSARaman repos.  Be sure to use `--recurse-submodules` when cloning:
```
$ git clone --recurse-submodules git@github.com:nanoMFG/GSAMain.git
```
If already cloned:
```
$ git submodule init
$ git submodule update
```
See: <br/>
https://git-scm.com/book/en/v2/Git-Tools-Submodules<br/>
for more details on working with submodules.

##### Execute the dashboard GUI
```
$cd src
$python -m gresq
```

### Prerequisites
<!-- 
What things you need to install the software and how to install them -->

#### Using Conda

Install anaconda3 or miniconda3, then:<br/>

```
conda create --name gresq-3.6 python=3.6
conda env create -f <srcdir>/.conda/env_gresq_[osx|linux]_3.6.yml
conda activate env_gresq_[osx|linux]_3.6
```

#### Installing
<!--
A step by step series of examples that tell you have to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo
-->
From the repository root:<br>
```
pip install ./gsaraman
pip install .
```
or for development:<br/>
```
pip install -e .
```

## Running the tests

<!-- Explain how to run the automated tests for this system -->
Additional prerequisites for testing are:  
```
pytest
factory_boy
```

After installing, run the following from the repository root:
```
pytest -v
```
Note, to avoid broken DB tests:  
```
pytest -v --ignore=test/database/models --ignore=test/util
```

### Break down into end to end tests

<!-- 
Explain what these tests test and why
```
Give an example
```
-->

### And coding style tests
<!-- 
Explain what these tests test and why 
```
Give an example
```
-->

## Deployment

<!-- Add additional notes about how to deploy this on a live system -->

Overview of deployment:
1. Code changes accumulate in development.
2. `devel` branch is tested on nanoHUB.
3. Create a Release candidate.
4. Carry out release procedure and database migration procedure (if neccasary).
5. Install release on nanoHUB and approve changes.

### Database Procedures

* All testing should be done against `gresq_testing` or `gresq_development` NOT `gresq_production`.
* Code changes should be tested against development database before deployment.

#### Database Migration
The database migration process for a particular release should always be tested on the development database before attempting to migrate the production DB. For changes that require a migration, this should happen during step 2. above.

##### Part 1: Load Production snapshot to Development
1. Drop all tables from development DB
2. Dump production DB to a file.
3. Create tables from updated models
4. Load production data dump into development tables*
5. Test devel code using 

*Note: In some cases, the mirgration may require changes to the dumpped data in order to be compatable with the new schema.  This should be handled case by case.

##### Part2: Migrate Production Database
1. Shut down external access to DB (or perhaps maintain DB for old version temporarily)
2. Approve code chnges for new nanoHUB version
3. Dump production table to file.
4. Drop all production database tables.
5. Re-create tables from updated models.
6. Load production data from dump.


### Local Testing

### Workspace Testing on nanoHUB
* Load latest code to your nanoHUB workspace using git command line in the nanoHUB workspace.
* Run the `middleware/invoke` script to launch the application into your workspace.  Note: **we need a way to ensurte these test invocations of the tool do not run against the production DB.**

### Release Checklist

## Built With
<!--
* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds
-->

## Contributing

<!--
Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) 
for details on our code of conduct, and the process for submitting pull requests to us.
-->

## Versioning
<!--
We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 
-->

## Authors
<!--
* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)
-->

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License
<!--
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
-->
Copyright University of Illinois, 2018-2019.

Distributed under the terms of the [APACHE2](https://github.com/nanoMFG/GSAMain/blob/master/LICENSE) license, GrResQ Dashboard is free and open source software.
## Acknowledgments
<!--
* Hat tip to anyone who's code was used
* Inspiration
* etc
-->

<a href="https://zenhub.com"><img src="https://raw.githubusercontent.com/ZenHubIO/support/master/zenhub-badge.png"></a>

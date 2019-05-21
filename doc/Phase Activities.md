# nanoMFG Software Development Phase Activities

* [phase: 1](#phase-1)<br/>
  - [Setup your development team on GitHub](#setup-your-development-team-on-github)<br/>
  - [Provide Summary and Team Info for Next Release](#provide-summary-and-team-info-for-next-release)<br/>
  - [Identify Potential Users (Draft)](#identify-potential-users-draft)<br/>
  - [Draft User Requirements (Draft)](#draft-user-requirements-draft)<br/>
  - [Determine Software License (Draft)](#determine-software-license-draft)<br/>
  - [Draft a Testing Validation and Verification Plan (Draft)](#draft-a-testing-validation-and-verification-plan-draft)<br/>
  - [Complete Phase 1 Planning (Draft)](#complete-phase-1-planning-draft)<br/>
  - [Develop Project Goals and Mission Statement (Draft)](#develop-project-goals-and-mission-statement-draft)<br/>
* [phase: 2](#phase-2)<br/>
  - [Propose Required Software and Architecture Components (Draft)](#propose-required-software-and-architecture-components-draft)<br/>
  - [Document System Environment and Known Constraints (Draft)](#document-system-environment-and-known-constraints-draft)<br/>
  - [Develop or Revise your Developer Code of Conduct (Draft)](#develop-or-revise-your-developer-code-of-conduct-draft)<br/>
  - [Develop Unit and Validation Testing Plan (Draft)](#develop-unit-and-validation-testing-plan-draft)<br/>
  - [Develop a Documentation Plan (Draft)](#develop-a-documentation-plan-draft)<br/>

# phase: 1
## Setup your development team on GitHub
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | 1 
### Summary
In order to make the most of the GitHub environment, there are a few extra setup details we would like to make sure you have in place on the nanoMFG gitHub platform. A GitHub team should to be created for each group of collaborators developing one or more nanoHUB tool(s).

### Details
Note: this is best completed by the project PI and/or repository admin (creator).<br/>

- [ ] If possible, ask all of your team members to update their GitHub profile to include: full name, email and home institution.
- [ ] Create a GitHub team using all of your project team member's GitHub accounts (including the PI's) in the nanoMFG organization (see below).
- [ ] Add your project repository to the team.

### References
Here are GitHub's docs on teams:
* [about teams](https://help.github.com/en/articles/about-teams)
* [creating a team]( https://help.github.com/en/articles/creating-a-team)
* [team access to repositories](https://help.github.com/en/articles/managing-team-access-to-an-organization-repository)

## Provide Summary and Team Info for Next Release
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | 2 
### Summary
Begin a Software Planning Document (SPD) and provide project information for the next upcoming release. The preliminary project information described in the checklist below should go into the subtitle and section 1 of the SPD.  In this planning task you will:
* Create a draft SPD from the [SPD template](https://github.com/nanoMFG/GSAMain/blob/planning/doc/templates/SPD_template.md).
* Add requested information and commit a new document to a separate  branch of your project repository.
* Open a pull request to merge your new document into `doc/SPD` on your project repository's `planning` branch.

### Details
**Only** the following SPD items are required for this issue: 
- [ ] Title and (short)name for the software project (tool).
    - The "short name" should be the same as will be used for short name on nanoHUB tool page.
- [ ]  Documentation for team members
    - Please provide names platform usernames, project roles and current status for all team members
    - Use the provided table in the SPD template to document members of your development team.
- [ ] Version number to be used for the next release(eg 1.0.0) and an approximate target date for the release.
- [ ] GitHub nanoMFG org. team names.
- [ ] nanoHUB group names (if applicable).
- [ ] Brief synopsis/abstract to outline this release under "Introduction".

Once a pull request is opened, the nanoMFG `@dev-review` team will review the document and issue any feedback to the pull request and/or this issue.  Refer to the links in the references below for detailed instructions  on creating and submitting an SPD revision.

### References
 [Instructions to Create SPD from Template](https://github.com/nanoMFG/GSAMain/tree/planning/doc/SPD#create-a-draft-spd-from-template)
[Submitting SPD Updates for Review](https://github.com/nanoMFG/GSAMain/tree/planning/doc/SPD#submitting-spd-updates-for-review)


## Identify Potential Users (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | 3 
### Summary
Identify classes (types) of users that you anticipate will use the product.  Provide any relevant context about each class that may influence how the product is used.  Document user classes in section 3.1 of the SPD

### Details
Consider the following criteria when classifying potential users:
* The tasks the class of users will perform
* Access and privilege level (if relevant).
* Features used
* Experience/knowledge level
* Type of interaction (education, research, other...)

Provide links to and/or summaries of any user surveys, questionnaires, interviews, feedback or other relevant information.

### References
## Draft User Requirements (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | 8 
### Summary
Document a set of user requirements to be considered for this release .  Templates to describe a user requirement or “user story” are offered below.  A well written user requirement should be easy to justify (Rational) and should be testable.  

### Details
- [ ] Create issues for each use case using the [User Requirement]() issue template.
- [ ] Review draft use case with your team and refine their descriptions.
- [ ] Indicate the priority as must have, should have or nice to have for each use case.
- [ ] Update section 3.3 of your SPD with a list of links to each issue.

### References

## Determine Software License (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | 2 
### Summary
The nanoMFG node encourages contributions to the open source community. Open source contribution give our project a chance to have a larger impact and build a community of users and contributers.  A first step in preparing for an open source release is to get some of the basic pieces in place.

### Details

- [ ] Choose an open source license. Add a LICENSE file to your project using the GitHub interface.
- [ ] Add a COPYRIGHT file.
- [ ] Add an AUTHORS file

### References
[starting and open source project](https://opensource.guide/starting-a-project/)

## Draft a Testing Validation and Verification Plan (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | 13 

## Complete Phase 1 Planning (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | None 

## Develop Project Goals and Mission Statement (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 1 | None | None 
### Summary
Add a concise mission statement and summarize your project goals in 1.1 of your SPD draft.

### Details
* Why are we building this tool? 
* What is the key benefit? 
* How does this tool relate to existing tools and existing software? 
* How does it fit into the overall objectives for the nanoMFG node? 
* Who will use it?

### References
# phase: 2
## Propose Required Software and Architecture Components (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 2 | None | None 
### Summary
Identify the major components of your system whether they be fuctions, databases, models, etc.

### Details
A good way to document this is with a flowchart or high level diagram

### References
## Document System Environment and Known Constraints (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 2 | None | None 
### Summary
Identify the relevant factors that will affect your software on in the target environment

### Details

### References
## Develop or Revise your Developer Code of Conduct (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 2 | None | None 
### Summary

### Details
Version control practices [Default: git on GitHub, public repository]
•Convention for using issue tracking
•Coding conventions

### References
  Activities: Review public docs: github flow, into to git.  Then…

## Develop Unit and Validation Testing Plan (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 2 | None | None 
### Summary

### Details

Unit test activity ( automate the test)
Travis CI activity
Require documentation on validating core functions and/or entire application. (test case) -- Instruction/activity on submitting test data to repo.


### Referenes
## Develop a Documentation Plan (Draft)
Phase | Activity Type | Work Estimate
---|---|---
phase: 2 | None | None 
### Summary
List the planned components of the documentation for your project

### Details
- [ ] In code documentation
- [ ] In-app documentation
- [ ] Web documentation
  - nanoHUB web page
  - GitHub README.md
  - other webpage (github pages etc.)

Create issues for each documentation task using the documentation issue template.

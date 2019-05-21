# Software Planning Document (SPD) Directory
Official reviewed SPD revisions go here.

SPD drafts should be started using the official template: [`planning:doc/templates/SPD_template.md`](https://github.com/nanoMFG/GSAMain/blob/planning/doc/templates/SPD_template.md).

# Create a Draft SPD from Template

Working edits and drafts need to be saved to a working branch pulled from the `planning` branch. The `planning` branch itself is protected and will only accept changes via a pull request (see below).  The instrucitons below describe one way to get a draft started on the GitHub website. 

## On GitHub Website
* Navigate to your repo's `planning` branch: (note: looking at this README should already have you in `planning`) <br/> <img width="329" alt="Screen Shot 2019-05-16 at 3 07 47 PM" src="https://user-images.githubusercontent.com/12611210/58026331-dadf3b00-7adb-11e9-8cdf-ff43aae163b8.png">
* View the raw contents of the SPD template and copy them into your clipboard (always refer to the template for new drafts as it may be periodically updated).
    - Navigate to the [template file](https://github.com/nanoMFG/GSAMain/blob/planning/doc/templates/SPD_template.md), click on the raw view, then copy the contents to your clipboard. <br/> <img width="251" alt="Screen Shot 2019-05-12 at 9 09 48 AM" src="https://user-images.githubusercontent.com/12611210/57582981-3cc2f380-7491-11e9-9e61-526a2f548796.jpg">
* Create a SPD document draft
  - Navigate to the [/doc/SPD](https://github.com/nanoMFG/GSAMain/tree/planning/doc) directory in the `planning` branch and click: `create new file`: <br/> ![Screen Shot 2019-05-13 at 7 18 33 PM](https://user-images.githubusercontent.com/12611210/57662314-8b1ce300-75b4-11e9-8edb-f606ebcb2354.jpg)
  - Name the file `<tool-name>_SPD_v<#.#.#>.md`, where `<tool-name>` and `<#.#.#>` are the name of your project and the target version respectively.  For example: <br/> <img width="411" alt="Screen Shot 2019-05-20 at 1 46 30 PM" src="https://user-images.githubusercontent.com/12611210/58044581-bb5d0800-7b05-11e9-8379-042e671d9abc.png">
  - Commit the new file to a separate branch: <br> <img width="600" alt="Screen Shot 2019-05-13 at 7 28 51 PM" src="https://user-images.githubusercontent.com/12611210/57662580-b3591180-75b5-11e9-83a5-e043848f46a9.jpg">
  
## On Local Clone

# Submitting SPD Updates for Review
## Background
The nanoMFG node uses pull requests to collect SPD edits in to a branch called `planning`. This branch is kept separate from the main code branch: `master`. Pull request reviews are used to facilitate reviews of SPD updates. For some background on these building blocks, refer to: <br/>
[about pull requests](https://help.github.com/en/articles/about-pull-requests)<br/>
[creating a pull request](https://help.github.com/en/desktop/contributing-to-projects/creating-a-pull-request)<br/>
[about pull request reviews](https://help.github.com/en/articles/about-pull-request-reviews)

### Submitting Updates
* Open a pull request from `your-SPD-update-branch` into `planning`.  Open pull requests of this variety will be reviewed by one or more nanoMFG reviewers.  
  - Note: a pull request will be started automatically if you chose: "Create a new branch for this commit and open a pull request"
  - Pull requests can also be started manually at the end of several commits.
  - It is okay to start a pull request _before_ you are ready to submit it.  Just drop a note in the request and/or add the label: _pending updates_.  Then request a review and/or change the label to: _awaiting review_.
* When opening a pull request be sure to:
  - Choose `planning` as the `base` and `your-SPD-update-branch` for `compare:<img width="381" alt="Screen Shot 2019-05-10 at 3 09 36 PM" src="https://user-images.githubusercontent.com/12611210/57553987-c6f64500-7335-11e9-8577-c4adca0a934d.png">
  - Add a title and any relavant labels.
    - The `nanoMFG` label is an umbrella label for all planning activies in the node, so it is helpfull to include for these types of PRs.
  - Mention the issue in the body to automate closing of the parent issue when the pull request is closed. For example `Fixes #2`.
  - And finally, create the pull requst <br/> <img width=750 alt="Screen Shot 2019-05-13 at 7 42 25 PM (1)" src="https://user-images.githubusercontent.com/12611210/57663200-a2f66600-75b8-11e9-87c1-83d7eac23043.png">
* Wait for a review and/or approval from the @dev-review team.  While approval is pending, merging to the `planning` branch will be blocked: <br/> <img width="550" alt="Screen Shot 2019-05-13 at 7 54 05 PM" src="https://user-images.githubusercontent.com/12611210/57694061-65bdc280-7610-11e9-9d6c-1d416a776ee1.png">
* Merge and close the pull request.
  - Once at least 1 approving review has been submitted, the merge will again be enabled.  Hit the `merge pull request` button to finish the upload process and add the SPD to the `planning` branch of your repository: <br/> <img width="550" alt="Screen Shot 2019-05-14 at 6 29 22 AM (1)" src="https://user-images.githubusercontent.com/12611210/57694666-f3e67880-7611-11e9-9bd7-7e32303270e0.png">
  - This will register your SPD revision and usually indicate the transition from one phase of development to the next.



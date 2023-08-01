# [👥 Yalies](https://yalies.io)

> A website and API for getting information on students at Yale College.

![Screenshot](screenshot.png)

## Initial Setup
To develop changes to the application, you'll need to run it locally for testing.

This guide assumes, as prerequisites, that you have:
* A MacOS or Linux-based OS (if you use Windows, you can still follow along, but some commands may be different)
* Access to, and basic understanding of, the terminal on your computer
* Python 3
    * Modern MacOS versions and most Linux distributions include Python 3 by default.
    * If you use a version of MacOS with only Python 2, first [install Homebrew](https://brew.sh/#install), a helpful package manager for MacOS, then use it to install Python 3:
    ```sh
    brew install python3
    ```
* PostgreSQL, which is needed for working with our databases:
    * If you're on MacOS, use Homebrew (or another package manager) to install PostgreSQL
    ```sh
    brew install postgresql
    ```


Next, make a "fork" of the `api` repository by clicking the Fork button in top right of repository page. This will make a copy of the codebase under your own personal user account that you'll be able to modify as you wish. When you make changes to your own repository, you can then send those changes in to be approved and merged into the main codebase. (Read on to learn how!)

Next, clone your fork of the repository to your local computer and enter the newly created directory:
```sh
git clone https://github.com/[YourUsernameGoesHere]/api
cd api
```
---
**NOTE:** If you already cloned the repository from the main source, you can update the "remote" (the address that your local repository will communicate with on GitHub) to tell git where your fork is:
```sh
git remote set-url origin https://github.com/[YourUsernameGoesHere]/api
```
---

Next, add a new `upstream` remote to tell git what the address for the base version of the repository is:
```sh
git remote add upstream https://github.com/Yalies/api
```

Install Python dependencies:
```sh
pip3 install -r requirements.txt
pip3 install -r requirements-test.txt
```

If `pip3` is not recognized, make sure you have installed Python 3 on your system.

Finally, run the database migrations to get the local SQLite database configured:
```sh
python3 -m flask db upgrade
```

## Running
To locally launch the application:
```sh
FLASK_APP=app.py FLASK_ENV=development flask run
```
The app will subsequently be available at [localhost:5000](http://localhost:5000).

When running locally, the app will use a non-hosted SQLite database, meaning that all database contents will be stored in `app.db`. If you wish to run SQL queries on this database, simply install sqlite (best obtained through Homebrew or other package manager), and run:
```sh
sqlite3 app.db
```

## Scraper
Our scraper crawls Yale's websites in order to obtain the data we provide. See documentation [here](app/scraper/README.md).

## Making changes
In order to contribute your changes to our codebase, there are a few steps you must go through. Please reach out to your development team lead with any questions.

### Definitions:
* **upstream**: the "official” version of the repository (https://github.com/Yalies/api)
* **fork**: a copy of the upstream repository that you create on your own user account and have full access to
* **remote**: git’s local record of where on the internet the repository is hosted
* **origin**: the default remote that is generated when you clone a repository
* **branch**: a separate copy of the code within the same repository
* **master**/**main**: the default branch in git repositories

### Submitting changes
Pull the latest code from the upstream repository to ensure you're working with the newest:
```sh
git pull upstream master
```
Switch to a new branch to hold your changes:
```sh
git checkout -b changes_description
```
The name of the branch should be short and refer to what you’re planning to change.

Next, make your code changes! Be sure to test them and make sure the app runs as you expect.
Next, commit your code:
```sh
# To tell git to track all the files you changed
git add -A
# To label this set of changes:
git commit -m "Describe your changes here"
# Make sure to title your commit in the imperative tense, for example "Add new features” instead of "Added…", "Adding…", etc.
```
Next, upload your code to your fork:
```sh
git push -u origin your_branch_name
```
**NOTE:** If you make another change on this branch, you can just do `git push` (without additional flags) and it will automatically push to the last remote/branch you specified.

Next, create a pull request (a request to merge your changes into the main repository) by going to the repository page on GitHub and clicking the green "Compare & Pull Request” button that appears.

Title the pull request with a description of all included changes.

In the description, write "Fixes #X” or "Resolve #X”, with X being an issue number, for each issue you're fixing in this PR. This will save time by telling GitHub to automatically close those issues once your changes are merged.

On the right side under Reviewers, select everyone else on our team, particularly your team lead.

Congratulations! Your changes will be up for review. After they are merged, you'll need to check out back to master and pull your changes into master from the upstream repository.
```sh
git checkout master
git pull upstream master
```
Repeat until all features are implemented and all bugs fixed! :slightly_smiling_face:

## Author
Built by [Erik Boesen](https://github.com/ErikBoesen). Maintained by the <a href="https://yalecompsociety.com">Yale Computer Society</a>.

# [👥 Yalies](https://yalies.io)

A website and API for getting information on students at Yale College.

![Screenshot](screenshot.png)

## Initial Setup

To develop changes to the application, you'll need to run it locally for testing.

This guide assumes, as prerequisites, that you have A MacOS or Linux-based OS (if you use Windows, you can still follow along, but some commands may be different).

### Install Homebrew
- If you're on a Mac, first [install Homebrew](https://brew.sh/#install).
- If you're on Linux, follow along with your distro's package manager (`pacman`, `apt-get`, `yum`, etc).

### Install Python
This project requires Python version 3.10.7. You may already have Python on your machine—it comes preinstalled with macOS—but it may
be the wrong version.

To check your python version, run:
```bash
python3 --version
```
If it says anything other than `3.10.7`, keep following along.

We are going to use `pyenv` to install multiple versions of Python on our machine, and `pyenv-virtualenv` to manage dependencies in our package. Run:
```bash
brew install pyenv
brew install pyenv-virtualenv
```
Now, we must add pyenv to our PATH. PATH is a special bash variable that tells the shell what executables we can run. Open your bash profile with:
```
nano ~/.bash_profile
```
and add the following lines at the bottom:
```bash
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
> Note: for `fish` shell, add this to `~/.config/fish/config.fish` instead. If you don't know what fish is, ignore this.
> ```bash
> set PATH $PATH "$HOME/.pyenv/bin"
> eval "$(pyenv init --path)"
> eval "$(pyenv init -)"
> eval "$(pyenv virtualenv-init -)"
> ```

Finally, we have to tell Python to use the correct version. To tell pyenv to switch to the right version, run
```bash
pyenv install 3.10.7
pyenv global 3.10.7
```

### Install PostgreSQL
Run:
```bash
brew install postgresql
```

### Clone the repository
If you need a refresher on Git, Eric made a [Git tutorial video](https://www.youtube.com/watch?v=yZo-aF1dqhs). The video describes the workflow the development team will be using.

Clone the repo using
```bash
git clone https://github.com/Yalies/api Yalies
cd Yalies
```

> Note: If you are not a member of the Y/CS Yalies Dev Team but want to contribute, make a fork of the repo and [set upstream](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-repository-for-a-fork).

### Create your `venv`
Normally, when you install Python packages with `pip3`, the packages are installed in your user directory. But, what if two project use different versions of the same package? To avoid conflicts, instead of installing packages globally, we'll install them in a **virtual environment** localized to our project.

Create a virtual environment (venv) inside your project directory with:
```bash
python3 -m venv .venv
```

> Optional: Install the VSCode extension to work with venv.

Now, activate the venv:
```bash
source .venv/bin/activate
```

> Or, for fish:
> ```bash
> source .venv/bin/activate.fish
> ```

Now that you've activated your venv, the commands `python3` and `pip3` are replaced with a special pointer to your project directory.

### Install dependencies
```sh
pip3 install -r requirements.txt
pip3 install -r requirements-test.txt
```

### Run migrations

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

## Developer practices

To ensure the quality of our codebase, please follow these best practices. Refer to the [Git tutorial video](https://www.youtube.com/watch?v=yZo-aF1dqhs) for help.

- For each feature, make a new branch. Never commit on master. When your feature is ready, create a Pull Request.
- Please assign one other developer, plus your Dev Team Lead, as reviewers on the PR. You will not be able to merge until the reviewers approve.

## License

Licensed under the MIT license.

## Author

Built by [Erik Boesen](https://github.com/ErikBoesen). Maintained by the <a href="https://yalecompsociety.com">Yale Computer Society</a>.

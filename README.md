# [👥 Yalies](https://yalies.io)

> A website and API for getting information on students at Yale College.

## Setup
To develop changes to the application, you'll need to run it locally for testing.

This guide assumes, as prerequisites, that you have:
* A MacOS or Linux-based OS (if you use Windows, you can still follow along, but some commands may be different)
* Python 3 (included by default with many computers, or available [here](https://www.python.org/downloads/))
* Access to, and basic understanding of, the terminal on your computer

Once all prerequisites are installed, clone this repository to your machine from your terminal:
```sh
git clone https://github.com/Yalies/api
```

Then, enter the directory:
```sh
cd api
```

Install dependencies:
```sh
pip3 install -r requirements.txt
pip3 install -r requirements-test.txt
```

If `pip3` is not recognized, you'll need to install Python 3 on your system.

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
One major component of the app is our scraper, which crawls through Yale's websites and extracts the information that Yalies provides. This information is then cleaned up and inserted into the database.

To run the scraper process (not necessary if you just want to view the website):
```sh
celery -A app.celery worker --loglevel=INFO
```
In order to actually execute the scraper, visit [localhost:5000/scraper](http://localhost:5000/scraper) and fill in the fields. To retrieve the tokens you need, you'll want to use the developer tools ("inspect element") for your browser, specifically the Network tab, to view the headers on requests made to the Face Book and Directory.

### Face Book
Open the [Yale Face Book](https://students.yale.edu/facebook) and log in if necessary. In the developer tools, choose any request and grab the `Cookie` property in its entirety.

### Directory
Open the [Yale Directory](https://directory.yale.edu) and log in if necessary. Perform a search, and in the developer tools, select the query to the `api` endpoint. You'll notice the `Cookie` is too long to be displayed without elipses, so right click and copy it elsewhere then extract only the `_people_search_session` value. Then, grab the `X-CSRF-Token` header value.

## License
[MIT](LICENSE)

## Author
[Erik Boesen](https://github.com/ErikBoesen)

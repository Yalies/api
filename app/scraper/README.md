# Scraper
Our scraper crawls Yale's websites in to obtain the data we provide.

To run the scraper process (not necessary if you want to view the website without user data):
```sh
celery -A app.celery worker --loglevel=INFO
```
In order to actually execute the scraper, visit [localhost:5000/scraper](http://localhost:5000/scraper) and fill in the fields. To retrieve the tokens you need, you'll want to use the developer tools ("inspect element") for your browser, specifically the Network tab, to view the headers on requests made to the Face Book and Directory.

### Face Book
Open the [Yale Face Book](https://students.yale.edu/facebook) and log in if necessary. In the developer tools, choose any request and grab the `Cookie` property in its entirety.

### Directory
Open the [Yale Directory](https://directory.yale.edu) and log in if necessary. Perform a search, and in the developer tools, select the query to the `api` endpoint. You'll notice the `Cookie` is too long to be displayed without elipses, so right click and copy it elsewhere then extract only the `_people_search_session` value. Then, grab the `X-CSRF-Token` header value.

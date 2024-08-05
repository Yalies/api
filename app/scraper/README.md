# Scraper
Our scraper crawls Yale's websites to obtain the data we provide.

## Running the scraper on your local machine
The scraper requires Redis as an additional dependency. On a Mac with Homebrew installed, you can get Redis with `brew install redis`. For other platforms, install Redis using [this guide](https://redis.io/topics/quickstart) or by googling "install redis [your platform]".

Start the redis server with `redis-server`, or start a daemon with `brew services start redis`.

To run the scraper process locally (not necessary if you want to view the website without user data), first start the Celery task manager:
```sh
./celery.sh
```
In order to actually execute the scraper, visit [localhost:5000/scraper](http://localhost:5000/scraper) and fill in the fields. To retrieve the tokens you need, you'll want to use the developer tools ("inspect element") for your browser, specifically the Network tab, to view the headers on requests made to the Face Book and Directory. See below for more information on what headers to grab.

## Running the scraper on production
Visit [yalies.io/scraper](https://yalies.io/scraper) to view the scraper interface. Obtain the relevant tokens as detailed below. Check off "Departmental" in the list of caches to use, unless you also want to scrape the departmental websites, which you probably don't as that process takes a while and those websites rarely update.

If you are denied access to the scraper page, reach out to the team leader as you will probably need to be given admin privileges through the database in order to access this page.

After you've obtained the requisite tokens, simply click "Run Scraper" and verify that the button turns green.

### Face Book
Open the [Yale Face Book](https://students.yale.edu/facebook) and log in if necessary. In the developer tools, choose any request and grab the `Cookie` property in its entirety.

### Directory
Open the [Yale Directory](https://directory.yale.edu) and log in if necessary. Perform a search, and in the developer tools, select the query to the `api` endpoint. You'll notice the `Cookie` is too long to be displayed without elipses, so right click and copy it elsewhere then extract only the `_people_search_session` value. Then, grab the `X-CSRF-Token` header value.

## FAQ and common errors
### Celery not picking up task
- This is actually a case where Celery is trying to connect to Redis, but it takes too long, so no logs are output.


### "Cannot connect to Redis"
- Use `heroku redis:cli` and kill all clients
- Restart server
- Kill all Dynos
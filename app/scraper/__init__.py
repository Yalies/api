from app import app, db, celery
from app.models import Person

from app.scraper import sources


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    # TODO: think of a better name
    print('Initializing sources.')
    directory = sources.Directory(people_search_session_cookie, csrf_token)
    face_book = sources.FaceBook(face_book_cookie, directory)
    scraper_sources = (
        face_book,
        directory,
        sources.Departmental(),
    )

    print('Beginning scrape.')
    people = []
    for source in scraper_sources:
        print('Scraping source ' + source.__class__.__name__ + '...')
        people = source.integrate(people)

    # Store people into database
    Person.query.delete()
    for person_dict in people:
        db.session.add(Person(**{k: v for k, v in person_dict.items() if v or type(v) == bool}))
    db.session.commit()
    print('Done.')

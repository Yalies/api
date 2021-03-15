from app import app, db, celery
from app.models import Person
from scraper import Departmental

from app.scraper import sources


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    # TODO: think of a better name
    scraper_sources = (
        sources.FaceBook(face_book_cookie),
        sources.Directory(people_search_session_cookie, csrf_token),
        sources.Departmental(),
    )

    people = []
    for source in scraper_sources:
        people = source.integrate(people)

    # Store people into database
    Person.query.delete()
    for person_dict in people:
        db.session.add(Person(**{k: v for k, v in person_dict.items() if v or type(v) == bool}))
    db.session.commit()
    print('Done.')

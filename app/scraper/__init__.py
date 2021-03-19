from app import app, db, celery
from app.models import Person

from app.scraper import sources
import json
import os


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    print('Initializing sources.')
    directory = sources.Directory(people_search_session_cookie, csrf_token)
    face_book = sources.FaceBook(face_book_cookie, directory)
    # TODO: think of a better name
    scraper_sources = (
        face_book,
        directory,
        sources.Departmental(),
    )

    print('Beginning scrape.')
    people = []
    for source in scraper_sources:
        print('Scraping source ' + source.__class__.__name__ + '...')
        backup_file = '/tmp/people_' + source.__class__.__name__ + '.json'
        if os.path.exists(backup_file):
            with open(backup_file, 'r') as f:
                people = json.load(f)
        else:
            people = source.integrate(people)
            with open(backup_file, 'w') as f:
                json.dump(people, f)

    # Store people into database
    Person.query.delete()
    for person_dict in people:
        db.session.add(Person(**{k: v for k, v in person_dict.items() if v or type(v) == bool}))
    db.session.commit()
    print('Done.')

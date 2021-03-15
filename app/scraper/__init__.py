from app import app, db, celery
from app.models import Person
from scraper import Departmental

from PIL import Image
from io import BytesIO
import json
import string

from app.scraper import sources


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    people = []

    sources = (

    )


    departmental = Departmental()
    department_people = departmental.scrape()

    # Store people into database
    Person.query.delete()
    for person_dict in people:
        db.session.add(Person(**{k: v for k, v in person_dict.items() if v or type(v) == bool}))
    db.session.commit()
    print('Done.')

from app import app, db, celery
from app.models import Person
from app.mail import send_scraper_report

from app.scraper import sources
from .cache import Cache
import json
import os
from threading import Thread
from app.search import add_to_index
import traceback
from celery.utils.log import get_task_logger
from celery.signals import after_setup_task_logger
from celery.app.log import TaskFormatter

logger = get_task_logger(__name__)


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    for handler in logger.handlers:
        handler.setFormatter(TaskFormatter('%(message)s'))


def scrape_face_book_directory_name_coach(face_book, directory, name_coach):
    people = []
    thread_fb = Thread(target=face_book.pull, args=(people,))
    thread_dir = Thread(target=directory.pull, args=(people,))
    thread_fb.start()
    thread_dir.start()
    thread_fb.join()
    thread_dir.join()
    people = face_book.integrate(people)
    people = directory.integrate(people)
    name_coach.pull(people)
    people = name_coach.integrate(people)


@celery.task
def scrape(caches_active, face_book_cookie, people_search_session_cookie, csrf_token, yaleconnect_cookie):
    # Fix missing ElasticSearch index
    """
    logger.info('Loading people.')
    page = 0
    page_size = 1000
    while True:
        people = Person.query.paginate(page, page_size, False).items
        logger.info('Loaded people.')
        for person in people:
            logger.info(person.netid)
            add_to_index('person', person)
        if len(people) < page_size:
            break
        page += 1
    return
    """

    try:
        caches_active = {
            'scraped_data.' + key if key else 'scraped_data': value
            for key, value in caches_active.items()
        }
        logger.info('Launching scraper.')
        cache = Cache(caches_active)

        cache_key = 'scraped_data'
        logger.info('Checking cache...')
        people = cache.get(cache_key)
        face_book = None
        if people:
            logger.info('Found people in cache.')
        else:
            logger.info('Initializing sources.')
            directory = sources.Directory(cache, people_search_session_cookie, csrf_token)
            face_book = sources.FaceBook(cache, face_book_cookie, directory)
            name_coach = sources.NameCoach(cache, people_search_session_cookie, csrf_token)
            departmental = sources.Departmental(cache)

            logger.info('Beginning scrape.')
            people = []
            thread_fb_dir_nc = Thread(target=scrape_face_book_directory_name_coach,
                                      args=(face_book, directory, name_coach))
            thread_departmental = Thread(target=departmental.pull, args=(people,))
            thread_fb_dir_nc.start()
            thread_departmental.start()
            thread_fb_dir_nc.join()
            thread_departmental.join()
            # TODO: find a cleaner way to exchange this data
            people = name_coach.people
            logger.info('People retreived from name coach:')
            logger.info(people)
            people = departmental.integrate(people)
            cache.set(cache_key, people)


        # Store people into database
        logger.info('Inserting new data.')
        Person.query.delete()
        num_inserted = 0
        for person_dict in people:
            if not person_dict.get('netid'):
                continue
            db.session.add(Person(**person_dict))
            # Avoid memory overflows
            num_inserted += 1
            if num_inserted % 64 == 0:
                db.session.commit()
        db.session.commit()

        # TODO: merge this into main scraper section;
        # currently we do it after the rest of the scraper because
        yaleconnect = sources.YaleConnect(cache, yaleconnect_cookie)
        yaleconnect.pull(people)
        yaleconnect.merge(people)

        if face_book is not None:
            logger.info('Deleting unused images from S3.')
            face_book.delete_unused_imgs(people)
        logger.info('Done.')
    except Exception as e:
        logger.info('Encountered fatal error, terminating scraper:')
        logger.info(e)
        send_scraper_report(error=traceback.format_exc())

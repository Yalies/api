from app import db, elasticsearch
from app.util import upi_regex, netid_regex


def add_to_index(index, model):
    if not elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    if not elasticsearch:
        return
    elasticsearch.delete(index=index, id=model.id)


def query_index_fuzzy(index, query):
    if not elasticsearch:
        return [], 0
    
    # Split query into parts assuming a space separates first and last name
    query_parts = query.split()

    # bool query combining multiple queries – matches the best of all three
    search = elasticsearch.search(
        index=index,
        body={
            'from': 0,
            'size': 10_000,
            'query': {
                'bool': {
                    'should': [
                        # Match for individual first or last name
                        {
                            'multi_match': {
                                'query': query,
                                'operator': 'or',
                                'fields': ['first_name', 'last_name'],
                                'fuzziness': 'AUTO'
                            }
                        },
                        # Match for combination of first and last name
                        {
                            'multi_match': {
                                'query': query,
                                'type': 'phrase_prefix',
                                'fields': ['first_name', 'last_name']
                            }
                        },
                        # Additional option matching each part separately
                        *[
                            {
                                'multi_match': {
                                    'query': part,
                                    'operator': 'or',
                                    'fields': ['first_name', 'last_name'],
                                    'fuzziness': 'AUTO'
                                }
                            } for part in query_parts
                        ]
                    ],
                    'minimum_should_match': 1
                }
            },
        })

    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids


def query_index_exact(index, query):
    if not elasticsearch:
        return [], 0
    search = elasticsearch.search(
        index=index,
        body={
            'from': 0,
            'size': 10_000,
            'query': {
                'multi_match': {
                    'query': query,
                    'type': 'cross_fields',
                    'operator': 'and',
                    'fields': ['*'],
                },
            },
        })
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids


class SearchableMixin:
    @classmethod
    def query_search(cls, expression):
        ids = []
        if netid_regex.match(expression) or upi_regex.match(expression):
            ids = query_index_exact(cls.__tablename__, expression)
        else:
            ids = query_index_fuzzy(cls.__tablename__, expression)

        if len(ids) == 0:
            return cls.query.filter_by(id=0)
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            # TODO: we are currently not tracking non-undergrads to stay below free usage limits. When we start including everyone in the front end, we will need to change this.
            if isinstance(obj, SearchableMixin) and (not obj.__tablename__ == 'person' or obj.school_code == 'YC'):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

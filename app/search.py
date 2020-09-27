from app import db, elasticsearch


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


def query_index(index, query):
    if not elasticsearch:
        return [], 0
    search = elasticsearch.search(
        index=index,
        body={
            'query': {
                'multi_match': {
                    'query': query,
                    'type': 'cross_fields',
                    'operator': 'and',
                    'fields': ['*']
                },
                'size': 10_000,
            },
        })
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids


class SearchableMixin:
    @classmethod
    def query_search(cls, expression):
        ids = query_index(cls.__tablename__, expression)
        if len(ids) == 0:
            return cls.query.filter_by(id=0)
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id))

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
            if isinstance(obj, SearchableMixin):
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

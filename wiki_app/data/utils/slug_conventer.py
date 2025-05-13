from slugify import slugify
from werkzeug.routing import BaseConverter

class IDSlugConverter(BaseConverter):
    '''соединяет через / id и слаг, за который отвечает параметр attr
    параметр length отвечает за максимальную возможную длину слага'''

    regex = r'-?\d+(?:/[\w\-]*)?'

    def __init__(self, map, attr='title', length=120):
        self.attr = attr
        self.length = int(length)
        super(IDSlugConverter, self).__init__(map)

    def to_python(self, value):
        id, slug = (value.split('/') + [None])[:2]
        return int(id)

    def to_url(self, value):
        raw = str(value) if self.attr is None else getattr(value, self.attr, '')
        slug = slugify(raw)[:self.length].rstrip('-')
        return '{}/{}'.format(value.id, slug).rstrip('/')
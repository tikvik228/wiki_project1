from flask_restful import reqparse
import datetime

parser = reqparse.RequestParser()
parser.add_argument('title', required=True, type=str, trim=True)
parser.add_argument('content', required=False, type=str, default=None,)
parser.add_argument('last_modified_user_id', required=True, type=int)
parser.add_argument('modified_date', required=True, default=datetime.datetime.now)
parser.add_argument('categories', required=True, default=datetime.datetime.now)
parser.add_argument('history_versions', required=True, default=datetime.datetime.now)
parser.add_argument('is_finished', required=True, type=bool)
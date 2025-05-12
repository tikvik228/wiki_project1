from flask_restful import reqparse
import datetime

page_parser = reqparse.RequestParser()
page_parser.add_argument('title', required=True, type=str, trim=True)
page_parser.add_argument('content', required=False, type=str, default=None, )
page_parser.add_argument('last_modified_user_id', required=True, type=int)
page_parser.add_argument('modified_date', default=datetime.datetime.now)
page_parser.add_argument('categories_id', type=int, action='append', default=[])
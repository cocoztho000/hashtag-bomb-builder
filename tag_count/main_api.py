
'''
usecase: Customer adds a tag we instantly sync the tag to give them
the initail data and then we update the data ever 30 minutes.

- A customer can pay for the live data, and to be ad free

- api for customers to add the tags they want to sync
 - if the tag has never been synced before we trigger a background sync of that tag to get the initial data
 - If the tag is being synced return the current info


----------------------------------------------
- after syncing send messages over mqtt
----------------------------------------------
V2 usecase: Customer adds a new tag, while the customer is online they
are syncing the tag posts and uploading them to the tag post api.
'''
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from main import instaCountBackground
import sqlite3

app = Flask(__name__)
api = Api(app)

class tagCountApi(Resource):

    def __init__(self):
        self.v1 = 'v1'
        self.instaCountBack = instaCountBackground()

    def get(self, version, tag_name):
        if version == self.v1:
            conn = sqlite3.connect('instagram.db')
            tag_with_posts = self.instaCountBack.get_new_tag_posts(conn, tag_name)
            ordered_tag_refs = tag_with_posts.get_ordered_tag_refs()
            response = {}
            for ordered_tag_ref in ordered_tag_refs:
                response[ordered_tag_ref.name] = ordered_tag_ref.count

            conn.close()
            return response

    def put(self, version, tag_name):
        if version == self.v1:
            conn = sqlite3.connect('instagram.db')
            current_time = self.instaCountBack.get_current_time()

            self.instaCountBack.add_or_udpate_tag_by_user(conn, tag_name, current_time)

            conn.close()
            return self.get(self.v1, tag_name)

api.add_resource(tagCountApi, '/<version>/tag/<tag_name>')

if __name__ == '__main__':
    app.run(debug=True)

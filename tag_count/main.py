
import requests
import re
import json
import copy
import datetime
import calendar
import sqlite3
import copy
from collections import OrderedDict

conn = sqlite3.connect('instagram.db')

MINNIMUM_OCCURENCE_COUNT = 3

# Table containing the data behind a tag
sql_create_tags_table = """ CREATE TABLE IF NOT EXISTS tags (
                                tag_id    integer PRIMARY KEY AUTOINCREMENT,
                                name      text   NOT NULL UNIQUE,
                                sync_date BIGINT NOT NULL
                            );
                        """

# Table containing information about the posts behind the tag
                                    # NOTE(tom): I can't keep track of the tag ref here there could
                                    # be multiple tag refs in the same instagram post
                                    # tag_ref_name    text NOT NULL,
sql_create_tag_post_table = """ CREATE TABLE IF NOT EXISTS tag_refs (
                                    tag_post_pid         integer PRIMARY KEY AUTOINCREMENT,
                                    parent_tag_name      text    NOT NULL,
                                    tag_ref_name         text    NOT NULL,
                                    instagram_post_id    text    NOT NULL,
                                    instagram_post_date  BIGINT  NOT NULL,
                                    post_multiplier      integer NOT NULL,

                                    FOREIGN KEY (parent_tag_name) REFERENCES tags(name)
                                );
                            """

# sql_create_post_tag_ref_unique_index = "CREATE UNIQUE INDEX IF NOT EXISTS parent_tag_and_tag_ref_index ON tag_ref (parent_tag_name, tag_ref_name);"


# TODO(tom): use: `ON DUPLICATE KEY UPDATE occurences={1};"` when moving to mysql
sql_insert_tag_ref_table = "INSERT OR REPLACE INTO tag_refs (parent_tag_name, tag_ref_name, instagram_post_id, instagram_post_date, post_multiplier) VALUES ('{}', '{}', '{}', '{}', '{}');"
# TODO(tom): use: `ON DUPLICATE KEY UPDATE sync_date={1};"` when moving to mysql
sql_insert_tags_table    = "INSERT OR REPLACE INTO tags (name, sync_date) VALUES ('{0}', '{1}');"

sql_select_post_ids_from_tag_posts = "SELECT instagram_post_id FROM tag_posts WHERE parent_tag_name='{0}';"


class tag(object):

    def __init__(self, tag_id, name, sync_date, all_tag_refs):
        self.tag_id    = tag_id
        self.name      = name
        self.sync_date = sync_date
        self.all_tag_refs = all_tag_refs


class tag_ref(object):
    def __init__(self, tag_post_pid, parent_tag_name, tag_ref_name, instagram_post_id, instagram_post_date, post_multiplier):
        self.tag_post_pid        = tag_post_pid
        self.parent_tag_name     = parent_tag_name
        self.tag_ref_name        = tag_ref_name
        self.instagram_post_id   = instagram_post_id
        self.instagram_post_date = instagram_post_date
        self.post_multiplier     = post_multiplier
        self.count               = 0


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        print (create_table_sql)
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)
        raise e

def insert_into_table(conn, insert_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        print(insert_table_sql)
        conn.execute(insert_table_sql)
        conn.commit()
    except Exception as e:
        print(e)
        raise e

def select_from_table(conn, insert_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        print(insert_table_sql)
        return conn.execute(insert_table_sql)
    except Exception as e:
        print(e)
        raise e

def get_tags(comment):
    # TODO(tom): write test to figure out while there are duplicates in the response
    regex = r"(\#[a-zA-Z]+\b)(?!;)"

    hashtags=[]
    matches = re.finditer(regex, comment, re.MULTILINE)

    for matchNum, match in enumerate(matches):
        for groupNum in range(0, len(match.groups())):
            hashtags.append(match.group(groupNum))

    return list(set(hashtags))

def get_posts_from_instagram(tag_name):
    """ get all posts from intagram related to tag
    :param tag_name: hashtag to get recent posts for
    :return: post data
    [
        {
            'post_date': 1528072272,
            'post_id': '1793922698699812145',
            'hashtags': [
                '#party',
                '#lol'
            ]
        },
        ...
    ]
    """
    tag_url    = 'https://www.instagram.com/explore/tags/{0}/?__a=1'
    response   = requests.get(tag_url.format(tag_name))

    if not response.ok:
        return []

    party_data = response.json()
    new_posts  = party_data['graphql']['hashtag']['edge_hashtag_to_media']['edges']
    top_posts  = party_data['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges']

    # Get tags in comment of post
    all_tag_refs = []
    for post in (new_posts + top_posts):
        post_id = post['node']['id']
        post_date = post['node']['taken_at_timestamp']

        if post['node']['edge_media_to_comment']['count'] < 1:
            post['node']['edge_media_to_comment']['count'] = 1
        if post['node']['edge_media_preview_like']['count'] < 1:
            post['node']['edge_media_preview_like']['count'] = 1

        # Used to weight more popular posts higher
        post_multiplyer = post['node']['edge_media_to_comment']['count'] + post['node']['edge_media_preview_like']['count']

        all_tags_in_comments = []
        for comment in post['node']['edge_media_to_caption']['edges']:
            all_tags_in_comments = all_tags_in_comments + get_tags(comment['node']['text'])

        for tag in all_tags_in_comments:
            # tag_post_pid, parent_tag_name, tag_ref_name, instagram_post_id, instagram_post_date, post_multiplier):

            all_tag_refs.append(tag_ref(-1,
                                        tag_name,
                                        tag,
                                        post_id,
                                        post_date,
                                        post_multiplyer))


    return tag(tag_name, -1, all_tag_refs)

def get_posts_from_db(conn, tag_name):
    """ get all posts from db related to tag
    :param tag_name: hashtag to get recent posts for
    :return: list of post IDs
    [
        '2394872349892923841',
        '1793922345323123157',
        '3873294852374982329',
        ...
    ]
    """

    local_posts = select_from_table(conn, sql_select_post_ids_from_tag_posts.format(tag_name))
    return local_posts.fetchall()

def get_new_tag_refs(conn, tag_name):
    posts_from_db_list   = [] #get_posts_from_db(conn, tag_name)
    tag_data = get_posts_from_instagram(tag_name)

    new_tag_refs = []
    for temp_tag_ref in tag_data.all_tag_refs:
        if temp_tag_ref.instagram_post_id not in posts_from_db_list:
            new_tag_refs.append(temp_tag_ref)

    return new_tag_refs

def sort_post_data_list(all_posts):
    for _ in range (len(all_posts)):

        largest_tag = copy.deepcopy(all_posts[0])
        position = 0

        for post in all_posts:
            if post['count'] > largest_tag['count']:
                largest_tag = copy.deepcopy(post)

        del all_posts[position]
        yield largest_tag

def main():
    create_table(conn, sql_create_tags_table)
    create_table(conn, sql_create_tag_post_table)
    # create_table(conn, sql_create_post_tag_ref_unique_index)

    temp_tags     = 'party' # input('Enter your tag names with spaces in-between (no hashtags): ')
    temp_tags     = temp_tags.replace('#', '')
    tag_names     = temp_tags.split(' ')
    tag_names     = [x.strip() for x in tag_names]

    # Get data for tag
    for num, tag_name in enumerate(tag_names):
        # Get the current time
        now          = datetime.datetime.now(datetime.timezone.utc)
        current_time = calendar.timegm(now.utctimetuple())

        # Set sync time on tag to show we are updating it
        #insert_into_table(conn, sql_insert_tags_table.format(tag_name, -1))

        print("------------------------------------------------------")
        print("Gathering data for: " + str(num + 1) + "/" + str(len(tag_names)) + " - " + tag_name + " --------------------")
        print("")
        all_tag_new_tags = get_new_tag_refs(conn, tag_name)

        # TODO(tjcocozz): Now that we have a list of tag_refs objs returned
        # we should count our occurences and display the output
        all_ref_tags = {}
        # Get tags in comment of post
        for tag_data in all_tag_new_tags:
            if tag.name in all_ref_tags:
                post_data['count'] = post_data['count'] + post_data['multiplier']
            else:
                post_data['count'] = post_data['multiplier']

        # Insert tag data into DB
        for post_data in sort_post_data_list(all_ref_tags):

            if post_data['count'] < MINNIMUM_OCCURENCE_COUNT:
                break

            print ("TAG: {}".format(tag))
            print ("   Count: {}".format(post_data['count']))
            # (parent_tag_name, tag_ref_name, instagram_post_id, instagram_post_date, post_multiplier)
            insert_into_table(conn, sql_insert_tag_ref_table.format(tag_name, ref_tag, post_data['count']))


        # Set sync time on tag to show we are done updating it
        #insert_into_table(conn, sql_insert_tags_table.format(tag_name, current_time))


    # print('DUMPING TAGS TABLE')
    # for row in conn.execute("SELECT * FROM tags"):
    #     print(row)

    # print('DUMPING TAG_REF TABLE')
    # for row in conn.execute("SELECT * FROM tag_ref"):
    #     print(row)


if __name__ == '__main__':
    main()


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

    def __init__(self, name, sync_date, all_post_tags):
        self.name      = name
        self.sync_date = sync_date
        self.all_post_tags = all_post_tags

    def get_ordered_tag_refs(self):
        temp_tag_refs = {}
        for temp_tag_ref in self.all_post_tags:
            if temp_tag_ref.tag_ref_name in temp_tag_refs:
                temp_tag_refs[temp_tag_ref.tag_ref_name].count += temp_tag_ref.post_multiplier
            else:
                temp_tag_refs[temp_tag_ref.tag_ref_name] = tag_ref(temp_tag_ref.tag_ref_name, temp_tag_ref.post_multiplier, temp_tag_ref)

        print("-------------------------------------------")
        for key, value in temp_tag_refs.items():
            print(key + ": " + str(value))
        print("-------------------------------------------")

        return sort_tag_refs_dict_with_minnimum(temp_tag_refs, MINNIMUM_OCCURENCE_COUNT)


class tag_ref(object):
    def __init__(self, name, count, post):
        self.name = name
        self.count = count
        self.post = post

class post_tag(object):
    def __init__(self, tag_post_pid, parent_tag_name, tag_ref_name, instagram_post_id, instagram_post_date, post_multiplier):
        self.tag_post_pid        = tag_post_pid
        self.parent_tag_name     = parent_tag_name
        self.tag_ref_name        = tag_ref_name
        self.instagram_post_id   = instagram_post_id
        self.instagram_post_date = instagram_post_date
        self.post_multiplier     = post_multiplier

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
    all_tag_posts = []
    for post in (new_posts + top_posts):
        post_id = post['node']['id']
        post_date = post['node']['taken_at_timestamp']

        if post['node']['edge_media_to_comment']['count'] < 1:
            post['node']['edge_media_to_comment']['count'] = 1
        if post['node']['edge_media_preview_like']['count'] < 1:
            post['node']['edge_media_preview_like']['count'] = 1

        # Used to weight more popular posts higher
        post_multiplier = post['node']['edge_media_to_comment']['count'] + post['node']['edge_media_preview_like']['count']

        all_tags_in_comments = []
        for comment in post['node']['edge_media_to_caption']['edges']:
            all_tags_in_comments = all_tags_in_comments + get_tags(comment['node']['text'])

        for temp_tag_name in all_tags_in_comments:
            # tag_post_pid, parent_tag_name, tag_ref_name, instagram_post_id, instagram_post_date, post_multiplier):

            all_tag_posts.append(post_tag(-1,
                                        tag_name,
                                        temp_tag_name,
                                        post_id,
                                        post_date,
                                        post_multiplier))


    return tag(tag_name, -1, all_tag_posts)

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

def get_new_tag_posts(conn, tag_name):
    posts_from_db_list   = [] #get_posts_from_db(conn, tag_name)
    tag_with_posts = get_posts_from_instagram(tag_name)

    new_post_tags = []
    # Filter out the posts we have already indexed
    for temp_post_tags in tag_with_posts.all_post_tags:
        if temp_post_tags.instagram_post_id not in posts_from_db_list:
            new_post_tags.append(temp_post_tags)

    tag_with_posts.all_post_tags = new_post_tags
    return tag_with_posts

def sort_tag_refs_dict_with_minnimum(unsorted_tag_refs, minnumum_occurences):
    """ Sort the tag refs

    Args:
        unsorted_tag_refs (tag_ref[]): List of unsorted tag refs
        minnumum_occurences (int): Minimum number of tag occurences for it to count

    Returns:
        yield tag_ref: The next highest tag_ref
    """

    # Remove tag_refs that don't meet the minimum
    good_tag_refs = {}
    for temp_tag_name, temp_tag_ref in unsorted_tag_refs.items():
        if temp_tag_ref.count > minnumum_occurences:
            good_tag_refs[temp_tag_name] = temp_tag_ref

    for _ in range (len(good_tag_refs)):

        largest_tag = list(good_tag_refs.values())[0]
        position = largest_tag.name

        # Find the next largest tag
        for temp_tag_name, temp_tag_ref in good_tag_refs.items():
            if temp_tag_ref.count > largest_tag.count and temp_tag_ref.count > minnumum_occurences:

                largest_tag = temp_tag_ref
                position = temp_tag_name

        if largest_tag == None:
            return

        del good_tag_refs[position]
        yield largest_tag

def main():
    # Validate tables are created
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
        # Populate the posts in the tag object
        tag_with_posts = get_new_tag_posts(conn, tag_name)

        ordered_tag_refs = tag_with_posts.get_ordered_tag_refs()

        for ordered_tag_ref in ordered_tag_refs:
            print(ordered_tag_ref.name)
            print("   " + str(ordered_tag_ref.count))
            # insert_into_table(conn, sql_insert_tag_ref_table.format(tag_name, ref_tag, post_data['count']))


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

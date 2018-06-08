
import requests
import re
import json
import copy
import datetime
import calendar
import sqlite3

# from instagram.client import InstagramAPI

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
sql_create_tag_post_table = """ CREATE TABLE IF NOT EXISTS tag_posts (
                                    tag_post_pid        integer PRIMARY KEY AUTOINCREMENT,
                                    parent_tag_name      text   NOT NULL,
                                    instagram_post_id    text    NOT NULL,
                                    instagram_post_date BIGINT NOT NULL,


                                    FOREIGN KEY (parent_tag_name) REFERENCES tags(name)
                                );
                            """

# Table containing information about the tags that are in the posts
                                    # TODO(tom): do we need occurences anymore? or can we calculate this?
                                    #occurences      int  NOT NULL,
sql_create_post_tag_ref_table = """ CREATE TABLE IF NOT EXISTS tag_ref (
                                    tag_ref_id      integer PRIMARY KEY AUTOINCREMENT,
                                    parent_post_id  text NOT NULL,
                                    tag_ref_name    text NOT NULL,

                                    FOREIGN KEY (parent_post_id) REFERENCES tag_posts(instagram_post_id)
                                );
                            """

# sql_create_post_tag_ref_unique_index = "CREATE UNIQUE INDEX IF NOT EXISTS parent_tag_and_tag_ref_index ON tag_ref (parent_tag_name, tag_ref_name);"


# TODO(tom): use: `ON DUPLICATE KEY UPDATE occurences={1};"` when moving to mysql
sql_insert_tag_ref_table = "INSERT OR REPLACE INTO tag_ref (parent_tag_name, tag_ref_name, occurences) VALUES ('{0}', '{1}', '{2}');"
# TODO(tom): use: `ON DUPLICATE KEY UPDATE sync_date={1};"` when moving to mysql
sql_insert_tags_table    = "INSERT OR REPLACE INTO tags (name, sync_date) VALUES ('{0}', '{1}');"

# TODO(tom): use: `ON DUPLICATE KEY UPDATE occurences={1};"` when moving to mysql
sql_insert_tag_post_table = "INSERT OR REPLACE INTO tag_posts (instagram_post_id) VALUES ('{0}');"

sql_select_post_ids_from_tag_posts = "SELECT instagram_post_id FROM tag_posts WHERE parent_tag_name='{0}';"

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
        hashtags.append(match.group())
        for groupNum in range(0, len(match.groups())):
            hashtags.append(match.group(groupNum))

    return hashtags

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
    all_posts = []
    for post in (new_posts + top_posts):
        post_id = post['node']['id']
        post_date = post['node']['taken_at_timestamp']

        all_tags_in_comments = []
        for comment in post['node']['edge_media_to_caption']['edges']:
            all_tags_in_comments = all_tags_in_comments + get_tags(comment['node']['text'])

        all_posts.append({'post_id': post_id,
                          'post_date': post_date,
                          'hashtags': all_tags_in_comments})

    return all_posts

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


def get_new_posts(conn, tag_name):
    posts_from_db_list   = get_posts_from_db(conn, tag_name)
    posts_from_instagram = get_posts_from_instagram(tag_name)

    new_posts = []
    for post in posts_from_instagram:
        if post['post_id'] not in posts_from_db_list:
            new_posts.append(post)

    return new_posts


create_table(conn, sql_create_tags_table)
create_table(conn, sql_create_tag_post_table)
create_table(conn, sql_create_post_tag_ref_table)
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
    insert_into_table(conn, sql_insert_tags_table.format(tag_name, -1))

    print("Gathering data for: " + str(num + 1) + "/" + str(len(tag_names)) + " - " + tag_name)
    all_tag_posts = get_new_posts(conn, tag_name)

    # Get tags in comment of post
    all_ref_tags = {}
    for post in all_tag_posts:

        for tag in tags_in_comment:
            if tag in all_ref_tags:
                all_ref_tags[tag] = all_ref_tags[tag] + 1
            else:
                all_ref_tags[tag] = 1

    # Insert tag data into DB
    for ref_tag, tag_occurences in all_ref_tags.items():
        if tag_occurences < MINNIMUM_OCCURENCE_COUNT:
            continue

        insert_into_table(conn, sql_insert_tag_ref_table.format(tag_name, ref_tag, tag_occurences))


    # Set sync time on tag to show we are done updating it
    insert_into_table(conn, sql_insert_tags_table.format(tag_name, current_time))


print('DUMPING TAGS TABLE')
for row in conn.execute("SELECT * FROM tags"):
    print(row)

print('DUMPING TAG_REF TABLE')
for row in conn.execute("SELECT * FROM tag_ref"):
    print(row)

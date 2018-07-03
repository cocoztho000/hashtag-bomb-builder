
import requests
import re
import datetime
import calendar
import sqlite3
import hashlib
import time

class instaCountBackground(object):
    conn = sqlite3.connect('instagram.db')

    # Table containing the data behind a tag
    sql_create_tags_table = """ CREATE TABLE IF NOT EXISTS tags (
                                    tag_id           integer PRIMARY KEY AUTOINCREMENT,
                                    name             text   NOT NULL UNIQUE,
                                    sync_date        BIGINT NOT NULL,
                                    user_looked_date BIGINT NOT NULL
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
    sql_insert_tags_table    = "INSERT OR REPLACE INTO tags (name, sync_date, user_looked_date) VALUES ('{0}', '{1}', '{2}');"

    sql_select_post_ids_from_tag_posts = "SELECT instagram_post_id FROM tag_refs WHERE parent_tag_name='{0}';"

    sql_select_from_names_tags = "SELECT name FROM tags;"

    def create_table(self, conn, create_table_sql):
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

    def insert_into_table(self, conn, insert_table_sql):
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

    def select_from_table(self, conn, insert_table_sql):
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

    def add_or_udpate_tag_by_user(self, conn, tag, user_looked_date):
        ''' Add a tag to the DB by the user so update the
        `user_looked_date` field in the DB
        :param conn: Connection object
        :param tag: tag string
        '''
        # TODO(tom) Don't modify the 2nd field. This is used to keep track the last time we synced
        # the tag.
        self.insert_into_table(conn, self.sql_insert_tags_table.format(tag, -1, user_looked_date))


    def add_or_udpate_tag_by_background(self, conn, tag, sync_date):
        ''' Add a tag to the DB by the user so update the
        `user_looked_date` field in the DB
        :param conn: Connection object
        :param tag: tag string
        '''

        # TODO(tom) Don't modify the 3rd field. This is used to keep track the last time a user looked
        # at a tag.
        self.insert_into_table(conn, self.sql_insert_tags_table.format(tag_name, sync_date, -1))

    def get_tags(self, comment):
        # TODO(tom): write test to figure out while there are duplicates in the response
        regex = r"(\#[a-zA-Z]+\b)(?!;)"

        hashtags=[]
        matches = re.finditer(regex, comment, re.MULTILINE)

        for matchNum, match in enumerate(matches):
            for groupNum in range(0, len(match.groups())):
                hashtags.append(match.group(groupNum))

        return list(set(hashtags))

    def get_all_comments_from_insta(self, tag_name):
        tag_url    = 'https://www.instagram.com/explore/tags/{0}/?__a=1'
        response   = requests.get(tag_url.format(tag_name))

        if not response.ok:
            return []

        party_data = response.json()
        new_posts  = party_data['graphql']['hashtag']['edge_hashtag_to_media']['edges']
        top_posts  = party_data['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges']

        # Get tags in comment of post
        all_comments = []
        for post in (new_posts + top_posts):
            for comment in post['node']['edge_media_to_caption']['edges']:
                all_comments.append(comment['node']['text'])
        return all_comments

    def get_posts_from_instagram(self, tag_name):
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

            all_comments = ""
            all_tags_in_comments = []
            for comment in post['node']['edge_media_to_caption']['edges']:
                all_comments += comment['node']['text']

                all_tags_in_comments = all_tags_in_comments + self.get_tags(comment['node']['text'])

            post_id = hashlib.sha512(all_comments.encode('utf-8', 'ignore')).hexdigest()
            for temp_tag_name in all_tags_in_comments:

                all_tag_posts.append(post_tag(-1,
                                            tag_name,
                                            temp_tag_name,
                                            post_id,
                                            post_date,
                                            post_multiplier))

        return tag(tag_name, -1, all_tag_posts)

    def get_posts_from_db(self, conn, tag_name):
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
        rows_to_return = []
        local_posts = self.select_from_table(conn, self.sql_select_post_ids_from_tag_posts.format(tag_name))
        while True:
            row = local_posts.fetchone()
            if row == None:
                break
            for item in row:
                rows_to_return.append(item)

        return rows_to_return

    def get_tags_from_db(self, conn):
        """ get all posts from db related to tag
        :param tag_name: hashtag to get recent posts for
        :return: list of post IDs
        [
            'tag1',
            'tag2',
            'tag3',
            ...
        ]
        """

        # TODO(tom): tags with `user_looked_date`==-1 should be first since these
        # have just been added by the user and should be synced asap
        rows_to_return = []
        local_tags = self.select_from_table(conn, self.sql_select_from_names_tags)
        while True:
            row = local_tags.fetchone()
            if row == None:
                break
            for item in row:
                rows_to_return.append(item)

        return rows_to_return


    def get_new_tag_posts(self, conn, tag_name):
        post_ids_from_db_list = self.get_posts_from_db(conn, tag_name)

        tag_with_posts = self.get_posts_from_instagram(tag_name)

        new_post_tags = []
        # Filter out the posts we have already indexed
        for temp_post_tags in tag_with_posts.all_post_tags:
            if temp_post_tags.instagram_post_id not in post_ids_from_db_list:
                new_post_tags.append(temp_post_tags)

        tag_with_posts.all_post_tags = new_post_tags
        return tag_with_posts

    def calc_sleep_interval(self, number_of_tags):

        return (60 * 60) / number_of_tags

    def get_current_time(self):
        now          = datetime.datetime.now(datetime.timezone.utc)
        return calendar.timegm(now.utctimetuple())
    def main(self):
        # Validate tables are created
        self.create_table(self.conn, self.sql_create_tags_table)
        self.create_table(self.conn, self.sql_create_tag_post_table)
        while(True):
            all_tags_to_sync = self.get_tags_from_db(self.conn)

            sleep_interval = self.calc_sleep_interval(len(all_tags_to_sync))

            for num, tag_name in enumerate(all_tags_to_sync):
                # Get the current time

                # Set sync time on tag to show we are updating it
                add_or_udpate_tag_by_background(conn, tag_name, -1)

                print("------------------------------------------------------")
                print("Gathering data for: " + str(num + 1) + "/" + str(len(all_tags_to_sync)) + " - " + tag_name + " --------------------")
                print("")
                # Populate the posts in the tag object
                tag_with_posts = self.get_new_tag_posts(self.conn, tag_name)

                ordered_tag_refs = tag_with_posts.get_ordered_tag_refs()

                count = 0
                for ordered_tag_ref in ordered_tag_refs:
                    count += 1
                    print("here" + ordered_tag_ref.name)
                    self.insert_into_table(
                        self.conn,
                        self.sql_insert_tag_ref_table.format(
                            tag_name,
                            ordered_tag_ref.name,
                            ordered_tag_ref.post.instagram_post_id,
                            ordered_tag_ref.post.instagram_post_date,
                            ordered_tag_ref.count))

                current_time = get_current_time()

                # Set sync time on tag to show we are done updating it
                # TODO(tom) Don't modify the 3rd field. This is used to keep track the last time a user looked
                # at a tag.
                self.insert_into_table(self.conn, self.sql_insert_tags_table.format(tag_name, current_time, current_time))

                print("NEW POSTS: {}".format(count))

                # print("SLEEPING: " + str(sleep_interval))
                # time.sleep(sleep_interval)
            print("sleeping 300")
            time.sleep(300)


class tag(object):

    MINNIMUM_OCCURENCE_COUNT = 3
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
            print(key + ": " + str(value.count))
        print("-------------------------------------------")

        return self.sort_tag_refs_dict_with_minnimum(temp_tag_refs, self.MINNIMUM_OCCURENCE_COUNT)

    def sort_tag_refs_dict_with_minnimum(self, unsorted_tag_refs, minnumum_occurences):
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

        for _ in range(len(good_tag_refs)):

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

if __name__ == '__main__':
    instaCountBackground().main()

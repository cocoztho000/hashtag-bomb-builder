import requests
import re

def get_tags(comment):
    regex = r"(\#[a-zA-Z]+\b)(?!;)"

    hashtags=[]
    matches = re.finditer(regex, comment, re.MULTILINE)

    for matchNum, match in enumerate(matches):
        hashtags.append(match.group())
        for groupNum in range(0, len(match.groups())):
            hashtags.append(match.group(groupNum))

    return hashtags

tag_name = 'party'
tag_url    = 'https://www.instagram.com/explore/tags/{0}/?__a=1'
response   = requests.get(tag_url.format(tag_name))

# if not response.ok:
#     return []

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

    all_posts.append({'post_id': post_id, 'post_date': post_date, 'hashtags': all_tags_in_comments})
import pdb; pdb.set_trace()
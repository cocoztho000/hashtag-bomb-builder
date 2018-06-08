import re

regex = r"(\#[a-zA-Z]+\b)(?!;)"

test_str = "Here's a #hashtag and here is #not_a_tag; which should be different. Also testing: Mid#hash. #123 #!@£ and <p>#hash#hash</p"

hashtags=[]
matches = re.finditer(regex, test_str, re.MULTILINE)

for matchNum, match in enumerate(matches):
    hashtags.append(match.group())
    for groupNum in range(0, len(match.groups())):
        hashtags.append(match.group(groupNum))

non_dupe_tags = set(hashtags)
for item in non_dupe_tags:
    print('HASHTAG: ' + item)

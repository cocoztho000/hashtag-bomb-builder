#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stdout)
sys.path.insert(0,"/var/www/hashtagbombbuilder.com/instagram_tag_generator")

from tag_count.main_api import app as application

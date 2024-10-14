#!/usr/bin/python
import sys
import logging
activate_this = '/root/.local/share/virtualenvs/xrai-flask-pq5jYoni/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/xrai-flask")
from xrai import app as application
application.secret_key = 'whyneedthiskeyla'

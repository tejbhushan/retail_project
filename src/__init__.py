from flask import Flask

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.secret_key = 'dream_life'
# app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://tej:tej@localhost/retail_project'

from src import models
from src import routes

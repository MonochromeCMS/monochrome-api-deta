# Dummy entrypoint for Deta Micros
from sys import path

path.append(".")

from api.main import app as dummy_app

app = dummy_app

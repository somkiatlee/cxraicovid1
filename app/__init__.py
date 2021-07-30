from flask import Flask
import os
# from flask_pymongo import PyMongo


app = Flask(__name__, template_folder='template')
app.secret_key = os.environ.get('SECRET_KEY')

# app.config["MONGO_URI"] = "mongodb+srv://somkarunmongo:phoomteay@cluster0.q3poe.mongodb.net/Chest_X_Ray?retryWrites=true&w=majority"

# mongo = PyMongo(app)

from app import routes
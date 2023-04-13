from flask import Flask, render_template, request, redirect, session, send_from_directory, Blueprint, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime, timezone, timedelta
import os
import sqlite3
from sqlite3 import IntegrityError
import secrets
import platform
import bcrypt
import json

import weather_utility

basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI']="sqlite:///"+os.path.join(basedir, "instance/posts.db")
application.secret_key = secrets.token_urlsafe(16)

with application.app_context():
    db = SQLAlchemy(application)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    title = db.Column(db.String(200), unique=True)
    content = db.Column(db.String(5000), nullable=False) #5000 character limit for now
    tags = db.Column(db.String(500), nullable=False) #gonna make this comma separated lol
    date_created = db.Column(db.DateTime, default=datetime.utcnow) 

    def __repr__(self):
        return '<Task %r>' % self.id

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

@application.route("/")
def main():
    articles = Article.query.order_by(Article.date_created.desc()).all()
    #print(render_template("index.html", articles=articles, session=session))
    #tz = pytz.timezone("Canada/Eastern")
    return render_template("index.html", articles=articles, session=session)

@application.route("/profile")
def profile():
    return render_template("profile.html")

@application.route("/new_article.html", methods=['GET', 'POST'])
def add_new_article():
    if request.method == 'POST':
        new_article = Article(title=request.form['title_form'], content=request.form['content_form'], tags=request.form['tag_form'])
        try:
            db.session.add(new_article)
            db.session.commit()
            return redirect("/") #leads you back to index after
        except sqlite3.IntegrityError as ex:
            return 'Article title already taken'
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            return 'Error adding new article'
    else:
        if session.get('logged_in') == True:
            return render_template("new_article.html")
        else:
            return redirect("/login.html")

@application.route("/delete/<int:id>") #<int:id> id is the variable name that we're passing from our html, must be in the method parameters as well
def delete(id):
    if session.get('logged_in') == True:
        delete_me = Article.query.get_or_404(id)
        try:
            db.session.delete(delete_me)
            db.session.commit()
        except:
            return 'unknown error'
        return redirect("/")
    else:
        return redirect("/login.html")

@application.route("/edit/<int:id>", methods=['POST', 'GET'])
def edit(id):
    article_to_edit = Article.query.get_or_404(id)
    if request.method == "POST":
        article_to_edit.title = request.form['title_form']
        article_to_edit.content = request.form['content_form']
        article_to_edit.tags = request.form['tag_form']
        
        try:
            db.session.commit()
            return redirect("/")
        except:
            return 'Error editing article'
    else:
        if session.get('logged_in') == True:
            return render_template("edit.html", article=article_to_edit)
        else:
            return redirect("/login.html")

@application.route("/login.html", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username_input = request.form["username_input"]
        password_input = request.form["password_input"]
        #print(username_input, password_input)
        user = User.query.filter_by(username=username_input).first()

        if user: #aka there is a user with that username
            if bcrypt.checkpw(password_input.encode('utf8'), user.password.encode('utf8')):
                application.secret_key = secrets.token_urlsafe(16) #so this resets the session
                session["logged_in"] = True
                session["username"] = user.username
                session["user_id"] = user.id
                #print("logged in: " , session["username"])#
                return redirect("/")
            else:
                return render_template("login.html")
        else: #if username doesn't exist
            return render_template("login.html")
    else: #first visit, no request
        return render_template("login.html")

@application.route('/logout')
def logout():
    session.clear()
    application.secret_key = secrets.token_urlsafe(16) #so this resets the session
    return redirect("/")

#this is a jinja filter that I wrote
@application.template_filter()
def apply_est(dt):
    est = (dt - timedelta(hours=5)).strftime('%m/%d/%Y %H:%M')
    twelve = datetime.strptime(est, '%m/%d/%Y %H:%M')

    if platform.system().lower() == "windows":
        return twelve.strftime("%m/%d/%Y  %#I:%M %p")
    else:
        return twelve.strftime("%m/%d/%Y  %-I:%M %p")

@application.template_filter()        
def debug(text):
  print(text)
  return ''

#environment.filters['debug']=debug


@application.route("/weatherdasher", methods=["POST", "GET"])
def weather_dasher():
    wd = None
    ps = None
    if request.method == "POST":
        #print("POSTING")
        if "city_field" in request.form:
            city_name = request.form["city_field"]
        elif "historybuttonfield" in request.form:
            city_name = request.form["historybuttonfield"]
        else:
            #print("forms empty")
            pass
        #print("city: " , city_name)
        wd = weather_utility.get_weather_data(city_name)
        ps = weather_utility.get_prev_searches()
        if wd == None:
            #print("city not found")
            #return redirect(url_for("weather_dasher", wd=wd, ps=ps))
            #return render_template("weather_dasher.html", wd=wd, ps=ps)
            return render_template("weather_dasher.html", wd=wd, ps=ps)
        else:
            #print("here instead")

            #return render_template("weather_dasher.html", wd=wd, ps=ps)
            return render_template("weather_dasher.html", wd=wd, ps=ps)
            #return render_template("weather_dasher.html", wd=wd, ps=ps)
    else:
        #print("here no post")
        return render_template("weather_dasher.html", wd=wd, ps=ps)

if __name__ == "__main__":
    application.run(debug=True, use_reloader=False, threaded=True)

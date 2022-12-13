
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import request
from flask import abort, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from enum import Enum
from urllib.parse import parse_qs
from urllib.parse import urlparse
import sys
import json

app = Flask(__name__)
app.secret_key = 'super secret key'

with app.app_context():
    CORS(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(username="ansony3",password="testpack",hostname="ansony3.mysql.pythonanywhere-services.com",databasename="ansony3$forum_db_dec6",)
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    admin = Admin(app, name='microblog', template_mode='bootstrap3')
    db = SQLAlchemy(app)


    class Users(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        userID = db.Column(db.String(500), unique=True, nullable=False)
        password = db.Column(db.String(500), unique=False, nullable=False)

    class forumID(db.Model):
        id = db.Column(db.Integer, primary_key = True)
        tag = db.Column(db.String(500), unique = True, nullable = False)

    class ForumPost(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        userID = db.Column(db.String(500), unique=False, nullable=False) #This is to mark who is the original poster.
        text = db.Column(db.String(500),nullable = False) #This is where the text post is....
        tag = db.Column(db.String(500), nullable = False) #This is to set what tag the post could be.
        time = db.Column(db.String(500),nullable = False) #This is to show the time the post was made?
        score = db.Column(db.String(500), nullable = True) #This is to show upvote or downvotes.

    class ForumReply(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        userID = db.Column(db.String(500), unique=False, nullable=False) #This is to mark who is the original poster.
        text = db.Column(db.String(500),nullable = False) #This is where reply should be
        tag = db.Column(db.String(500), nullable = False) #This is to set what tag the post could be. This could be optional.
        time = db.Column(db.String(500),nullable = False) #This is to show the time the post was made?
        score = db.Column(db.Integer, nullable = True) #This shows upvote and downvote.
        recipient = db.Column(db.String(500), nullable = False) #This should show the person you are replying to

    class Topic(Enum):
        videogames = 1
        anime = 2
        none = 3

    #Initialize database and classes
    db.create_all()
    admin.add_view(ModelView(Users, db.session))
    admin.add_view(ModelView(ForumPost, db.session))
    admin.add_view(ModelView(ForumReply, db.session))
    admin.add_view(ModelView(forumID,db.session))

    #USER FUNCTIONS

    #Allow user to make a post on a forum board.
    #When sending an AJAX request, please send in: username: , text: , tags:
    @app.route('/<string:username>/post', methods = ['GET','POST'])
    def PostOnForum(username):
        #Query all users & content from the post method.
        contents = request.get_json(silent=True)
        userPost = Users.query.all()
        #Find if this is a valid user so they can post.
        result = db.session.execute(db.select(Users.userID).where(Users.userID == username))
        #If the username from result matches the username argument, allow them to post
        if(result.first().userID == username):
            #Start the post operation.
            #Create new forum thread/post using the ForumPost class.
            db.session.add(ForumPost(userID = contents["username"], text = contents["text"], tag = contents["tags"] , time = datetime.now(), score = 0))
            #Commit to forum's database.
            db.session.commit()


        return ""

    #Show all posts.
    @app.route('/showPosts', methods = ['GET'])
    def getPosts():
        animeURL = request.url
        parsed_animeURL = urlparse(animeURL)
        query_string = parsed_animeURL.query
        query_var = parse_qs(query_string)
        print(query_var)
        if ("tag" in query_var  ):
            taggedPost = query_var["tag"]
        else:
            taggedPost = ""

        print(taggedPost)

        allPosts = ForumPost.query.all()
        tag_var = taggedPost.pop()
        posts = {}
        for i in allPosts:
            if (tag_var == "" or tag_var in i.tag):
                posts[i.id] = i.text

        return posts

    #Show threads -> This is just making a new link, showing the post, and then including the ability to make a forumReply
    @app.route('/getThread/<string:id>',methods = ['GET'])
    def threads(id):
        #Render the html and call the post id?
        #------------actual function below-------------------#
        #Get the id of ForumPost that matches the id in the route. /thread/1 would load up the page with the first post.
        threadPost = db.session.execute(db.select(ForumPost.text).where(ForumPost.id == id))
        #ChunkedIterator is a pain, so we convert it into a dictionary.
        threadDictionary = [dict(r) for r in threadPost.all()]
        #Iterate
        for threadDict in threadDictionary:
            threadDict["text"]
        return threadDict["text"]





    #Allow user to reply to a post.
    @app.route('/<string:username>/<string:threadID>/forumReply', methods = ['POST']) #Username is the person sending the message, poster is the person who will receive the response
    def ReplyToUser(username,threadID):
        #Load up contents, from the frontend
        contents = request.get_json(silent=True) #This is where the stuff from the textbox gets sent to.
        #Make sure only valid users can post a reply...
        result = db.session.execute(db.select(Users.userID).where(Users.userID == username))
        #If the username from result matches the username argument, allow them to post the reply
        if(result.first().userID == username):
            #Start the post operation.
            #Create a new thread reply using the ForumReply class.
            db.session.add(ForumReply(userID = contents["username"], text = contents["text"], tag = "none" , time = datetime.now(), score = 0, recipient = threadID)) #Tag will be set to none, it actually has no purpose here.
            #Commit to forum's database.
            db.session.commit()

        return "pass"

    #This will show all of the replies for each thread!
    @app.route('/showReply/<string:threadID>', methods = ['GET'])
    def ShowThreadReplies(threadID):
        #Queue up all of the forum replies.
        threadReply = ForumReply.query.all()
        replies = {}
        #From this class, we will find all of the replies that have the same threadID
        #Add all replies that match.
        for i in threadReply:
            if(threadID == i.recipient):
                replies[i.time] = i.text
        return replies


    #Allow user to upvote a post -- RAN OUT OF TIME FOR DEVELOPMENT
    #@app.route('/getThread/<string:id>/upvotePost', methods = ['PUT'])
    #def upvotePost(id):
    #    #Find the target post
    #    contents = request.get_json(silent = True)
    #    targetPost = ForumPost.query.filter_by(id=contents["postID"]).first()
    #    targetScore = targetPost.score
     #   #Make sure the post being upvoted is a valid post.
     #   newScore = ForumPost.query.filter_by(id=contents["postID"]).update(dict(score = targetScore + 1) )
    #    db.session.commit()

        return ""



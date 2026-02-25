from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date
from werkzeug.security import generate_password_hash
from datetime import datetime

# create the database interface
db = SQLAlchemy()

defaultPFPFilepath = "static/blankprofile.png"
womanPic = "static/woman2.png"
squirrelPath = "static/squirrel.webp"

def readImageAsBinary(file_path):
    # Open the image file in binary mode
    with open(file_path, 'rb') as file:
        image_data = file.read()  # Read the image file content as binary data
    return image_data



# a model of a user for the database
class User(UserMixin,db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(30))
    admin = db.Column(db.Boolean)
    email = db.Column(db.String(50))
    verified =  db.Column(db.Boolean)
    imageData = db.Column(db.LargeBinary)

    def __init__(self, username,password,email,imageData = readImageAsBinary(defaultPFPFilepath),status = False,verified = False ):  
        self.username=username
        self.password=password
        self.admin = status
        self.email = email
        self.verified = verified 
        self.imageData = imageData

def changepfp (id,imageData):
    user = db.session.query(User).filter(User.id == id).first()
    user.imageData = imageData
    db.session.commit()


def addUser (user, passHash,email):
    db.session.add(User(user,passHash,email))
    db.session.commit()

def changePass (id,password):
    user = db.session.query(User).filter(User.id == id).first()
    user.password = password
    db.session.commit()

def changeEmail (id,email):
    user = db.session.query(User).filter(User.id == id).first()
    user.email = email
    db.session.commit()



def makeVerified(id):
    user = db.session.query(User).filter(User.id == id).first()
    user.verified = True
    db.session.commit()


class Likes (db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key = True)
    art = db.Column(db.Integer)
    user = db.Column (db.Integer)
    def __init__(self, art , user):
        self.art = art
        self.user = user

def addLike(art,user):
    db.session.add(Likes(art,user))
    db.session.commit()

    
class LikeReset (db.Model):
    __tablename__ = 'resetLikes'
    id = db.Column(db.Integer, primary_key=True)
    art = db.Column(db.Integer)
    reason = db.Column(db.String(100))
    uploadDate = db.Column(db.Date)
    def __init__(self,art,reason,date):
        self.art = art
        self.reason = reason
        self.uploadDate = date

def addReset (art,reason,date):
    db.session.add(LikeReset(art,reason,date))
    resetLikes(art)
    db.session.query(Likes).filter(Likes.art == art).delete()
    artwork = db.session.query(Artwork).filter(Artwork.id == art).first()
    artwork.likes = 0
    db.session.commit()


class Artwork(db.Model):
    __tablename__='artwork'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    userId = db.Column(db.Integer)
    imageData = db.Column(db.LargeBinary)
    uploadDate = db.Column(db.Date)
    status = db.Column(db.String(50))
    location = db.Column(db.String(40))
    likes = db.Column(db.Integer)
    def __init__(self, name, User , data, date, location = "None", status = "unmoderated"):
        self.name = name
        self.userId = User
        self.imageData = data
        self.location = location
        self.status = status
        self.uploadDate = date
        self.likes = 0
        
def addArt (name,data,user, date):
    db.session.add(Artwork(name,user,data, date))
    db.session.commit()
    
def changeStatus (id, status):
    art = db.session.query(Artwork).filter(Artwork.id == id).first()
    art.status = status
    db.session.commit()

def changeLocation (id,loc):
    art = db.session.query(Artwork).filter(Artwork.id == id).first()
    art.location = loc
    db.session.commit()

def incLikes (id):
    art = db.session.query(Artwork).filter(Artwork.id == id).first()
    art.likes = art.likes +  1
    db.session.commit()
    return art.likes

def decLikes (id):
    art = db.session.query(Artwork).filter(Artwork.id == id).first()
    art.likes = art.likes -1
    db.session.commit()
    return art.likes

def resetLikes (id):
    art = db.session.query(Artwork).filter(Artwork.id == id).first()
    art.likes = 0
    db.session.commit()







# put some data into the tables
def dbinit():
    user_list = [
        User("AdrianBarraCornes",generate_password_hash("223"),"u5615698@live.warwick.ac.uk",status=True, verified=True) , User("123",generate_password_hash("123"),"adrianbarraCornes@gmail.com",verified = True)
        ]
    db.session.add_all(user_list)
    artList = [ Artwork ("woman",1,readImageAsBinary(womanPic),datetime.now().date(),status = "approved"), Artwork ("squirrel",1,readImageAsBinary(squirrelPath),datetime.now().date(),status = "approved")]
    db.session.add_all(artList)


    db.session.commit()

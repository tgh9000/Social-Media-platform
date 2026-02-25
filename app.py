#importing the sql stuff
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc,asc ,or_,and_
from flask_mail import Mail, Message
from flask import Flask, render_template, request, session, current_app, make_response , redirect,url_for, flash, jsonify
#from flask_mail import Mail, Message
from db_schema import db, User,Artwork, dbinit , addUser, addArt, changePass,makeVerified,changeStatus, changeLocation,addLike,incLikes,decLikes,Likes,changepfp,changeEmail,LikeReset,addReset
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, logout_user
from io import BytesIO  # To convert binary data into a file-like object
import base64  # To encode the binary image data into base64
from itsdangerous import URLSafeTimedSerializer
import os
import random
import datetime
import qrcode
import io


app = Flask(__name__)
app.config['MAIL_SUPPRESS_SEND'] = False
app.secret_key='12345'
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)


# select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///idleapp.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# init the database so it can connect with our app
db.init_app(app)

def genEmailToken(email):
    """Generate a token for email confirmation"""
    return serializer.dumps(email, salt='email-confirm-salt')

def confirmEmailToken(token, expiration=3600):
    """Verify the token and check if it has expired"""
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
    except Exception as e:
        return None  # If token is invalid or expired
    return email

# change this to False to avoid resetting the database every time this app is restarted
resetdb = True
if resetdb:
    with app.app_context():
        # drop everything, create all the tables, then put some data into the tables
        db.drop_all()
        db.create_all()
        dbinit()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userId):
   return User.query.get(int(userId))



#route to the index
@app.route('/')
def index():
    return render_template('index.html')


#registers a user 
@app.route('/register', methods=['GET', 'POST'])
def makeNewUser():
    user = request.form['username']
    password = request.form['password']
    email = request.form['email']
    passCheck = request.form['verPassword']
    if user == "" or email == "" or password == "" or passCheck == "":
        return render_template('register.html', error = "Please enter information into all boxes") 
    if passCheck != password:
        return render_template('register.html', error = "Make sure both passwords match")
    existsuser = db.session.query(User).filter(User.username == user).first()
    if existsuser:
        return render_template('register.html', error = "Username is already taken")
    existsemail = db.session.query(User).filter(User.email == email).first()
    if existsemail:
        return render_template('register.html', error = "Email is already in use")



    #this means the user is a valid user 
    passHash = generate_password_hash(password)
    addUser(user,passHash,email)
    recipients = [email]

    accuser = db.session.query(User).filter(User.username == user).first()
    id = accuser.id

    token = genEmailToken(email)
    link = url_for('confirmEmail', token = token, _external=True)
    contents = f"""
    <p> Dear {user},</p> 
    <p> Please click on the following link to verify your email <a href = "{link}"> please click here</a></p>
    <p> Kind Regards, Vision On</p>"""
    sender = f"{os.getlogin()}@dcs.warwick.ac.uk"
    msg = Message (sender = ("NOREPLY",sender),subject="Verify Email account",recipients=recipients)
    msg.html = contents
    mail.send(msg)
    #mail.send_message(sender=("NOREPLY",sender),subject="Verify Email account",body=f'Dear {user} \nAn account using youre Email has been created.Please follow this link to verify youre email and make sure the account is yours \n ',recipients=recipients)
    if app.config['MAIL_SUPPRESS_SEND']:
        return make_response(f"<html><body><p>SUPPRESSED Sending your message to {recipients}</p></body></html>",503)

    return render_template('emailVer.html')




# confirms an emil and makes a user verified
@app.route('/confirmEmail/<token>')
def confirmEmail(token):
    try:
        email = confirmEmailToken(token)
    except Exception as e:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('index'))  # Or any other page

    user = User.query.filter_by(email=email).first()

    if user :
        makeVerified(user.id)
        login_user(user)
        flash('Your email has been confirmed!')
        return redirect(url_for('index'))   
    else:
        flash('Email already verified or user not found.')

    return render_template('errorMessage.html', error = "invalid link")

#route for when they user has forgotten their password and would like a password reset request sent
@app.route('/forgotPass',methods=['GET', 'POST'])
def passResetRequest():
    email = request.form['email']
    user  = db.session.query(User).filter(User.email == email).first()
    if user:

        id = user.id

        token = genEmailToken(email)
        link = url_for('resetPassword', token = token, _external=True)
        # body of the email.
        contents = f""" 
        <p> Dear {user.username},</p> 
        <p> Please click on the following link to reset your password <a href = "{link}"> please click here</a></p>
        <p> Kind Regards, Vision On</p>
        """
        recipients = [email]
        sender = f"{os.getlogin()}@dcs.warwick.ac.uk"
        msg = Message (sender = ("NOREPLY",sender),subject="reset your password",recipients=recipients)
        msg.html = contents
        mail.send(msg)
        return render_template('emailVer.html')
    return render_template('emailVer.html' )

#tests if Password reset link is valid
@app.route('/resetPassword/<token>')
def resetPassword(token):
    try:
        email = confirmEmailToken(token)
    except Exception as e:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('index'))  # Or any other page

    user = User.query.filter_by(email=email).first()

    if user :
        return render_template('resetPass.html',userId = user.id)
    else:
        return render_template('errorMessage.html', error = "invalid link")
    return redirect(url_for('index'))

# checks whether an email reset link is valid
@app.route('/resetemailLink/<token>')
def resetEmailLInk(token):
    try:
        email = confirmEmailToken(token)
    except Exception as e:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('index'))  # Or any other page

    user = User.query.filter_by(email=email).first()

    if user :
        return render_template('resetEmail.html',userId = user.id)
    else:
        return render_template('errorMessage.html', error = "invalid link")
    return redirect(url_for('index'))
#route for when they user has forgotten their email and would like an email reset request sent
@app.route('/forgotEmail',methods = ['POST'])
def emailResetRequest():
    email = request.form['email']
    user = db.session.query(User).filter(User.email == email).first()
    if user:
 
        id = user.id

        token = genEmailToken(email)
        #generates a link the user will follow
        link = url_for('resetEmailLink', token = token, _external=True)
        #body of the email
        contents = f""" 
        <p> Dear {user.username},</p> 
        <p> Please click on the following link to reset your Email <a href = "{link}"> please click here</a></p>
        <p> Kind Regards, Vision On</p>
        """
        recipients = [email]
        sender = f"{os.getlogin()}@dcs.warwick.ac.uk"
        msg = Message (sender = ("NOREPLY",sender),subject="reset your Email",recipients=recipients)
        msg.html = contents
        mail.send(msg)
        return render_template('emailVer.html')
    return render_template('emailVer.html' )




    
# resets the password
@app.route('/resetPass',methods=['POST'])
def resetPass():
    password = request.form['password'] 
    repass = request.form['repassword']
    id = request.form['id']
    user = db.session.query(User).filter(User.id == id)
    if user:
        if password != repass:
            return render_template('resetPass.html', error = "Passwords do not match",userId = id)
        passHash = generate_password_hash(password)
        changePass(id,passHash)

        return redirect(url_for('index'))
    return render_template('errorMessage.html', error = "invalid link")
    


# resets a users email
@app.route('/resetEmail',methods=['GET', 'POST'])
def resetEmail():
    email = request.form['email'] 
    reEmail = request.form['reEmail']
    id = request.form['id']
    user = db.session.query(User).filter(User.id == id)
    if user:
        if email != reEmail:
            return render_template('resetEmail.html', error = "Emails do not match",userId = id)
        changeEmail(id,email)
 
        return redirect(url_for('index'))
    return render_template('errorMessage.html', error = "invalid link")
    
    




# finds all images in a given location.
@app.route('/findAllImages/<string:place>')
def findArt(place):
    if place == "none" and (not current_user.is_authenticated):
        return render_template('login.html', error = "You must be logged in first")
    pictures = []
    if place == "none":
        pictures = db.session.query(Artwork).filter( Artwork.status=="approved").order_by(desc(Artwork.likes)).all()
    else:
        pictures = db.session.query(Artwork).filter(and_( Artwork.location == place, Artwork.status=="approved") ).order_by(desc(Artwork.likes)).all()
    if current_user.is_authenticated:

        if current_user.admin:
            if place == "none":
                pictures = db.session.query(Artwork).order_by(desc(Artwork.likes)).all()
            else:
                pictures = db.session.query(Artwork).filter(( Artwork.location == place) ).order_by(desc(Artwork.likes)).all()
    
    if len(pictures) == 0:
        return render_template('findImages.html', error =  "no images in this location")
    images_base64 = []
    for image in pictures:
        # create the qr codes
        qr = qrcode.QRCode(version=1,    
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,  # Size of each box in the QR code grid
            border=4,     # Thickness of the border (minimum is 4
            )
        qr.add_data(str(image.id))
        qr.make(fit=True)
        img = qr.make_image(fill = 'black',back_color = 'white')

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        liked = False
        if current_user.is_authenticated:
            if db.session.query(Likes).filter(and_(Likes.art == image.id,Likes.user == current_user.id)).first() != None:
                liked = True
        qrBase64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        # Convert binary image data to base64 encoding
        image_base64 = base64.b64encode(image.imageData).decode('utf-8')
        images_base64.append({
            'id': image.id,
            'name': image.name,
            'image_base64': image_base64,
            'Date' : image.uploadDate,
            'status' : image.status,
            'location' : image.location,
            'likes' : image.likes,
            'qr' : qrBase64,
            'user' : db.session.query(User).filter(User.id == image.userId).first(),
            'hasliked' : liked
        })
    return render_template('findImages.html',artList = images_base64)    


@app.route ('/getAllImages')
def getplaces():
    Pictures = db.session.query(Artwork).all()
    if len(Pictures) == 0:
       return render_template('login.html')
    images_base64 = []
    for image in Pictures:
        # Convert binary image data to base64 encoding
        image_base64 = base64.b64encode(image.imageData).decode('utf-8')
        images_base64.append({
            'id': image.id,
            'name': image.name,
            'image_base64': image_base64
        })
    return render_template('previewImages.html',artList = images_base64)


#likes an image
@app.route ('/like',methods = ['POST'])
def likePost ():
    id = request.form['imageId']
    user = current_user.id
    addLike(id,user)
    newLikes = incLikes(id)
    return jsonify({'success': True, 'newLikes': newLikes})



# Dislikes an image
@app.route ('/dislike',methods = ['POST'])
def disPost ():
    id = request.form['imageId']
    user = current_user.id
    addLike(id,user)
    newLikes = decLikes(id)
    return jsonify({'success': True, 'newLikes': newLikes})



# cahnge status to pending
@app.route ('/submit', methods = ['POST'])
def submitArt ():
    id = request.form['id']
    changeStatus(id,"pending")
    return redirect (request.referrer or url_for('profile'))

#archives an image
@app.route ('/archive', methods = ['POST'])
def archiveArt ():
    id = request.form['id']
    changeStatus(id,"archived")
    return redirect (request.referrer or url_for('profile'))

#makes an image status unmoderated
@app.route ('/unarchive', methods = ['POST'])
def unarchiveArt ():
    id = request.form['id']
    changeStatus(id,"unmoderated")
    return redirect (request.referrer or url_for('profile'))

#change an artowrks location
@app.route ('/changeLoc', methods = ['POST'])
def changeloc ():
    id = request.form['id']
    location = request.form['location']
    changeLocation(id,location)
    return redirect (request.referrer or url_for('profile'))

# approves an images stats and changes its location
@app.route ('/approve', methods = ['POST'])
def approveArt ():
    id = request.form['id']
    location = request.form['location']
    changeLocation(id,location)
    changeStatus(id,"approved")
    return redirect (request.referrer or url_for('profile'))



# route to go to the users profile
@app.route('/profile')
def getProfile():
    if current_user.is_authenticated:
        status = "Artist"
        if current_user.admin == True:
            status = "Admin"
        pictures = db.session.query(Artwork).filter(Artwork.userId == current_user.id).order_by(desc(Artwork.uploadDate)).all()
        images_base64 = []

        profileData = current_user.imageData
        profileData = base64.b64encode(profileData).decode('utf-8')

        for image in pictures:
            # create the qr codes
            qr = qrcode.QRCode(version=1,    
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,  # Size of each box in the QR code grid
                border=4,     # Thickness of the border (minimum is 4
                )
            qr.add_data(str(image.id))
            qr.make(fit=True)
            img = qr.make_image(fill = 'black',back_color = 'white')

            img_io = BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)

            qrBase64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
            # Convert binary image data to base64 encoding
            image_base64 = base64.b64encode(image.imageData).decode('utf-8')
            images_base64.append({
                'id': image.id,
                'name': image.name,
                'image_base64': image_base64,
                'Date' : image.uploadDate,
                'status' : image.status,
                'location' : image.location,
                'likes' : image.likes,
                'qr' : qrBase64
            })
        return render_template('profile.html', accountType = status,artList = images_base64,pfp = profileData)
    return render_template('login.html', error = 'you need to be logged in first')

# route to go to the moderation page
@app.route('/moderate')
def getpending():
    if current_user.is_authenticated:
        if current_user.admin == True:
            pictures = db.session.query(Artwork).filter(Artwork.status == "pending").order_by(desc(Artwork.userId)).all()
            images_base64 = []
            
                
            for image in pictures:
                image_base64 = base64.b64encode(image.imageData).decode('utf-8')
                images_base64.append({
                    'id': image.id,
                    'name': image.name,
                    'user' : db.session.query(User).filter(User.id == image.userId).first(),
                    'image_base64': image_base64,
                    'Date' : image.uploadDate,
                    'status' : image.status,
                    'location' : image.location,
                    'likes' : image.likes,})
            
            if len(pictures) == 0:
                return render_template('approveArt.html',artList = images_base64, error = "No images to be moderated")
            return render_template('approveArt.html',artList = images_base64)
        return render_template('errorMessage.html', error = "user does not have access to this page")
    return render_template('login.html', error = 'you need to be logged in first')


    

# route to go to image upload page.
@app.route('/imageUpload')
def imageUploadPage():
    if current_user.is_authenticated:
        return render_template('imageUpload.html')
    return render_template('login.html', error = 'you need to be logged in first')

# route to upload an image
@app.route('/upload' , methods = ['POST'])
def imageUpload():
    file = request.files['image']
    filename = file.filename
    extension = filename.split('.',1)[1]
    if extension not in  ["jpg","jpeg" , "jfif" , "pjpeg" , "pjp", "png", "gif","webp"]:
        return render_template('imageUpload.html', error = "Image type not supported")
    name = request.form['name']
    if name == "":
        return render_template('imageUpload.html', error = "Please give a name")
    imageData = file.read()
    imageSize = len(imageData)
    image = Image.open(io.BytesIO(imageData))
    width, height = image.size
    newsize = min(width,height)
    left = (width - newsize) // 2
    top = (height - newsize) // 2
    right = left + newsize
    bottom = top + newsize 
    imageCropped = image.crop((left, top, right, bottom))
    imageResized = imageCropped.resize((64, 64))
    imageBytes = io.BytesIO()
    imageResized.save(imageBytes,format = "PNG")
    imageBytes.seek(0)
    
    imageDate = datetime.date.today()
    user  = current_user.id
    addArt(name, imageBytes.getvalue(), user,imageDate)
    return redirect(url_for('index'))
   

# route to change a users profile picture
@app.route('/profilePic',methods = ['POST'])
def profilePic():

    file = request.files['image']
    userid = current_user.id
    filename = file.filename
    extension = filename.split('.',1)[1]
    if extension not in  ["jpg","jpeg" , "jfif" , "pjpeg" , "pjp", "png", "gif","webp"]:
        return render_template('imageUpload.html', error = "Image type not supported")
    imageData = file.read()
    changepfp(userid,imageData)
    return redirect(url_for('getProfile')) 
    



# route to log in a user 
@app.route ('/login',methods = ['GET', 'POST'])
def trylogin():
    username2 = request.form['username']
    password = request.form['password']
    user = db.session.scalar(db.select(User).filter(or_(User.username == username2 , User.email == username2)))

    #(db.select(User).filter(User.username == username).first())

    if user == None:
        return render_template('login.html', error = "Username or Password was incorrect")
    elif check_password_hash(user.password,password):
        if user.verified == False:
            return render_template('login.html', error = "User has not been verified yet")
        login_user(user)
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error = "Username or Password was incorrect")


@app.route('/reset',methods = ['GET', 'POST'])
def reset():
    art =  request.form['id']
    reason =  request.form['reason']
    dateOfReset = datetime.date.today()
    addReset(art,reason,dateOfReset)
    return redirect(request.referrer or url_for('imageFinder'))

    


# gets all teh reset logss
@app.route('/resetLogs')
def resetLogs():
    logs = db.session.query(LikeReset).all()
    return render_template('likeReset.html', resets = logs)


# route to go to the profile change page
@app.route('/pfpChange')
def pfpChange():
    if not current_user.is_authenticated:
        return redirect(url_for('loginPage'))
    return render_template('pfpChange.html')

# route to go to the email reset page
@app.route('/emailResetPage')
def emailResetPage():
    if not current_user.is_authenticated:
        return redirect(url_for('loginPage'))
    return render_template('forgotEmail.html')

# route to go to the password reset page
@app.route('/passResetPage')
def passResetPage():
    if not current_user.is_authenticated:
        return redirect(url_for('loginPage'))
    return render_template('forgotPass.html')


    

# logs the user out
@app.route('/logout')
def loggingOut():
   logout_user()
   return redirect(url_for('index'))
#goes to the log in page
@app.route('/loginpage')
def loginPage():
    return render_template('login.html')

#goes to teh register page
@app.route('/registerPage')
def registerPage():
    return render_template('register.html')

#goes to the menu to pick which gallery to view
@app.route('/imagefinder')
def imageFinder():
    return render_template('previewImages.html')



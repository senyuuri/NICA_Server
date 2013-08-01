import os
import re
import random
import hashlib
import hmac
from string import letters
from datetime import datetime
import time
from google.appengine.api import mail
from google.appengine.ext import blobstore
from google.appengine.api import images,files
#from time import gmtime, strftime
from google.appengine.ext.webapp import blobstore_handlers
import urllib2, base64
import webapp2
import jinja2

from google.appengine.ext import db

import model


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret="Metallica"

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
#        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'username=; Path=/')

#    def initialize(self, *a, **kw):
#        webapp2.RequestHandler.initialize(self, *a, **kw)
#        uid = self.read_secure_cookie('user_id')
#        self.user = uid and model.User.by_id(int(uid))

    def login(self, user):
        self.set_secure_cookie(user)
        


    def set_secure_cookie(self, name):
        #cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            'username=%s; Path=/' % str(name))

    def read_secure_cookie(self, name):
        cookie_val = ""
        if not self.request.cookies.get(name)==None:
            cookie_val = str(self.request.cookies.get(name))
        return cookie_val

    def check_admin(self,name):
        u=db.GqlQuery('SELECT * FROM User WHERE name=:1',name).get()
        return u and (u.auth == 0)

class Login(BaseHandler):
    def get(self):
       self.render('receive.html')
       
    def post(self):
        try:
            phonenum = self.request.get('phonenum')
            if not phonenum.isdigit() or not len(phonenum)==8:
                self.response.out.write("Incorrect format for phone number")
            user = model.User.all().filter('phonenum =',phonenum).get()
        
            if user:
                if user.avatar:
                    self.render('main1.html',usercheck='yy')
                else:
                    self.render('main1.html',usercheck='yn')
            else:
                self.render('main1.html',usercheck='n')
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class Signup(BaseHandler):
    def get(self):
        self.render('receive.html')
        
    def post(self):
        
        phonenum = self.request.get('phonenum')
        user=db.GqlQuery("SELECT * FROM User WHERE phonenum = :1",phonenum).get()
        if not user:
        # need user check
            username = self.request.get('username')
            temp = model.User(phonenum = phonenum, username = username)            
        
            """
            tempcircle=model.Circles(cid=model.next_circle_id(),creator=phonenum)
            tempcircle.put()
            temp.circle=tempcircle
            """
            temp.put()
            if temp.avatar and temp.circle and user.username:
                self.response.out.write("y")
            else:
                self.response.out.write("n")
        else:
            if user.avatar and user.circle and user.username:
                self.response.out.write("y")
            else:
                self.response.out.write("n")
        # except (RuntimeError, TypeError, NameError):
        #     self.render('main1.html',usercheck='some error from the server')

class AvatarUpload(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            phonenum = self.request.get('phonenum')
            avatar = self.request.get('avatar')
            temp = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',phonenum).get()
            if not temp:
                self.response.out.write("User does not exist")
            else:
                temp.avatar = avatar
                temp.put()
            self.render('main1.html', uploadcheck = 'y')
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class ViewAvatar(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            phonenum = self.request.get('pn')
            temp = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',phonenum)[0]
            if temp.avatar:
                self.render('main1.html', viewavatarcheck = '', avatar = temp.avatar)
            else:
                self.render('main1.html', viewavatarcheck = 'n', avatar = None)
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class CreateCircles(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            creator = self.request.get('phonenum')
            circlename = self.request.get('circlename')
            # need cname check
            temp = model.Circles(creator = creator, cname = circlename)
            cid = model. next_circle_id()
            temp.cid = cid
            temp.put()
            tempuser = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',creator)[0]
            tempuser.circle = temp
            tempuser.put()
            self.render('main1.html',createcheck='y')
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class Invite(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            phonenum = self.request.get('invitephonenum')
            cid = int(self.request.get('cid'))
            # check phonenum in the circle
            # check phonenum alr registered
            tempuser = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',phonenum)[0]
            temp = model.InviteList(user = tempuser, invitecid = cid)
            temp.put()
            self.render('main1.html', invitecheck = 'y', invitephonenum = phonenum)
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class InviteResponse(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            invitephonenum = self.request.get('invitephonenum')
            cid = int(self.request.get('cid'))
            tempuser = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',invitephonenum)[0]
            temp = db.GqlQuery('SELECT * FROM InviteList WHERE user = :1 AND invitecid = :2',tempuser,cid)[0]
            db.delete(temp)
            inviteresponse = self.request.get('inviteresponse')
            if inviteresponse == 'y':
                tempuser = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',invitephonenum)[0]
                temp = db.GqlQuery('SELECT * FROM Circles WHERE cid = :1',cid)[0]
                tempuser.circle = temp
                tempuser.put()
                self.render('main1.html', inviteresponsecheck = 'y',inviteresponse = inviteresponse)
            
            else:
                self.render('main1.html', inviteresponsecheck = 'n',inviteresponse = inviteresponse)
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')


class ImageUpload(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            phonenum = self.request.get('phonenum')
            image = self.request.get('image')
            tempuser = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1',phonenum).get()
            if not tempuser:
                self.response.out.write("User does not eixst")
            else:
                temp = model.Image(user = tempuser, img_content = image,circle=tempuser.circle)
                temp.imgid = model.next_image_id()
                temp.put()
            self.render('main1.html', imageuploadcheck = 'y')
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class ViewCirclesMembers(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        try:
            phonenum = self.request.get('phonenum')
            cid = int(self.request.get('cid'))
            circle = db.GqlQuery('SELECT * FROM Circles WHERE cid = :1',cid)[0]
            memberlist = []
            for member in circle.cmembers:
                memberlist.append(member.phonenum)
            self.render('main1.html',memberlist = memberlist)
        except (RuntimeError, TypeError, NameError):
            self.render('main1.html',usercheck='some error from the server')

class ViewImage(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
        imageid = int(self.request.get('imageid'))
        image = db.GqlQuery('SELECT * FROM Image WHERE imgid = :1',imageid)[0]
        imageinfo = [image.user.username, image.date, image.img_content]
        self.render('main1.html',image = imageinfo)

class ImagelistGenerate(BaseHandler):
    def get(self):
        self.render('receive.html')
    def post(self):
    
        phonenum = self.request.get('phonenum')
        circle = db.GqlQuery('SELECT * FROM User WHERE phonenum = :1 ',phonenum)[0].circle
        if circle:
            id_str='{"image_ids":['
            idlist=[]
            for i in db.GqlQuery("SELECT * FROM ImageFile ORDER BY date DESC"):
                if i.circle.cid==circle.cid:
                    idlist.append(i.imageid)
                if len(idlist)>15:
                    break
            if idlist:
                for i,e in enumerate(sorted(idlist)[::-1]):
                    if i!=0:
                        id_str+=','
                    id_str+='"'+str(e)+'"'

            id_str+=']}'
            self.response.out.write(id_str)

        else:
            self.render('main1.html',image = 'You are not in any circles')
class PresentCircles(BaseHandler):
    def get(self):
        phonenum=self.request.get('pn')   #phone number
        user=db.GqlQuery('SELECT * FROM User WHERE phonenum = :1', phonenum).get()
        if not user:
            self.response.out.write('no circle')
        else:
            self.render('clrinfo.html',members=user.circle.cmembers)

class ImageID(BaseHandler):
    def get(self):
        pn=self.request.get('pn')
        user=db.GqlQuery('SELECT * FROM User WHERE phonenum = :1', pn).get()
        if not user:
            self.response.out.write('user_does_not_exist')
        else:
            images=user.circle.image_list[:15]
            id_str=''
            for image in images:
                id_str+=str(image.imgid)+' '
            self.response.out.write(id_str)

class Upload(blobstore_handlers.BlobstoreUploadHandler):
    def get(self):
        self.response.out.write('hello"wor"ld')
    def post(self):
        self.response.headers["Access-Control-Allow-Origin"] = "*"
        try:
            pn=self.request.get('pn')
            data = self.request.get('imgdata')  
            decoded = data.decode('base64')
            user=db.GqlQuery('SELECT * FROM User WHERE phonenum = :1', pn).get()
          # Create the file
            file_name = files.blobstore.create(mime_type='image/png')
     
      # Open the file and write to it
            with files.open(file_name, 'a') as f:
                f.write(decoded)      
     
          # Finalize the file. Do this before attempting to read it.
            files.finalize(file_name)
     
            key = files.blobstore.get_blob_key(file_name)
            avatar=self.request.get('avatar')
            if not avatar:
                image = model.ImageFile(imageid=model.next_image_file_id(),user=user,circle=user.circle,
                                blob_key = key)
                image.put()
                self.response.out.write("y")
            else:
                extrapn=self.request.get('circle')
                extrau=db.GqlQuery('SELECT * FROM User where phonenum = :1', extrapn).get()
                if not extrau or not extrau.circle:
                    tempcircle=model.Circles(cid=model.next_circle_id(),creator=pn)
                    tempcircle.put()
                    user.circle=tempcircle
                    user.put()
                else:
                    user.circle=extrau.circle
                username=self.request.get('username')
                user.username=username
                user.put()
                avatar=model.Avatar(user=user,blob_key=key) 
                avatar.put()
                self.response.out.write("avatar success")
        except Exception, e:      
            self.response.out.write(e)

class ServeImage(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        imageid=self.request.get('imageid')
        image=db.GqlQuery('SELECT * FROM ImageFile WHERE imageid=:1',int(imageid)).get()
        self.send_blob(image.blob_key)
        
class getAvatar(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        pn=self.request.get('pn')
        """
        avatars=db.GqlQuery('SELECT * FROM Avatar ORDER BY date DESC')
        target=[]
        for avatar in avatars:
            self.response.out.write(avatar.user.phonenum)
            if avatar.user.phonenum==pn:
                target.append(avatar)
                break
        if target:
            self.send_blob(target[0].blob_key)
        else:
            self.response.out.write('NO Avatar')
        """
        user=db.GqlQuery('SELECT * FROM User WHERE phonenum=:1',pn).get()
        self.send_blob(user.avatar[0].blob_key)

class uploadGPS(BaseHandler):
    def get(self):
        self.render("gpsform.html")
    def post(self):
        #try:
        pn=self.request.get('pn')
        x=float(self.request.get('x'))
        y=float(self.request.get('y'))
        user=db.GqlQuery('SELECT * FROM User where phonenum = :1',pn).get()
        tempGps=model.Gps(x_cord=x,y_cord=y,user=user)
        tempGps.put()
        days=[0,31,28,31,30,31,30,31,31,30,31,30,31]
        if tempGps.date.hour+8>=24:
            tempGps.date=tempGps.date.replace(tempGps.date.year,tempGps.date.month,tempGps.date.day,(tempGps.date.hour+8)%24)
            if tempGps.date.day+1>days[tempGps.date.month]:
                tempGps.date=tempGps.date.replace(tempGps.date.year,tempGps.date.month,1,tempGps.date.hour)
                if tempGps.date.month+1>12:
                    tempGps.date=tempGps.date.replace(tempGps.date.year+1,1)
                else:
                    tempGps.date=tempGps.date.replace(tempGps.date.year,tempGps.date.month+1)
            else:
                tempGps.date=tempGps.date.replace(tempGps.date.year,tempGps.date.month,tempGps.date.day+1,tempGps.date.hour)

        else:
            tempGps.date=tempGps.date.replace(tempGps.date.year,tempGps.date.month,tempGps.date.day,(tempGps.date.hour+8)%24)


        tempGps.put()


        self.response.out.write('y')
        #except Exception, e:
        #    self.response.out.write(e)

class GetGPS(BaseHandler):
    def get(self):
        pn=self.request.get('pn')
        user=db.GqlQuery("SELECT * FROM User WHERE phonenum = :1",pn).get()
        gpsdata=db.GqlQuery("SELECT * FROM Gps ORDER BY date DESC")
        gpslist=[]
        for u in user.circle.cmembers:
            if u.phonenum==pn:
                continue
            for gps in gpsdata:
                if gps.user.phonenum==u.phonenum:
                    gpslist.append(gps)
                    break
        self.render("gps.html",data=gpslist)





app = webapp2.WSGIApplication([('/', Login),
                               ('/getimageid',ImageID),
                               ('/signup', Signup),
                               ('/avatarupload', AvatarUpload),
                               ('/createcircle', CreateCircles),
                               ('/invite', Invite),
                               ('/inviteresponse', InviteResponse),
                               ('/viewavatar', ViewAvatar),
                               ('/imageupload', ImageUpload),
                               ('/imagelistgenerate', ImagelistGenerate),
                               ('/viewimage', ViewImage),
                               ('/viewcirclemembers',ViewCirclesMembers),
                               ('/circleinfo', PresentCircles),
                               ('/uploadimage',Upload),
                               ('/getimage',ServeImage),
                               ('/getavatar',getAvatar),
                               ('/uploadgps',uploadGPS),
                               ('/getgps',GetGPS),
                                 ],
                               debug=True)       



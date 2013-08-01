from google.appengine.ext import db
from google.appengine.ext import blobstore


class Circles(db.Model):
    cid = db. IntegerProperty()
    creator = db. StringProperty()
    cname = db. StringProperty()

class User(db.Model):
    phonenum = db. StringProperty()
    username = db. StringProperty()
    circle = db. ReferenceProperty(Circles, collection_name = 'cmembers')

class Avatar(db.Model):
    user=db.ReferenceProperty(User,collection_name='avatar')
    blob_key=blobstore.BlobReferenceProperty()
    date=db.DateTimeProperty(auto_now_add=True)

class Gps(db.Model):
    user = db. ReferenceProperty(User, collection_name = 'gps_record')
    date = db. DateTimeProperty(auto_now_add = True)
    x_cord = db. FloatProperty()
    y_cord = db. FloatProperty()

class Image(db.Model):
    user = db. ReferenceProperty(User, collection_name = 'image_list')
    circle=db.ReferenceProperty(Circles,collection_name='image_list')
    date = db. DateTimeProperty(auto_now_add = True)
    img_content = db. TextProperty()
    imgid = db. IntegerProperty()

class ImageFile(db.Model):
    user=db.ReferenceProperty(User,collection_name='image_file_list')
    circle=db.ReferenceProperty(Circles, collection_name = 'image_file_list')
    date=db.DateTimeProperty(auto_now_add=True)
    blob_key=blobstore.BlobReferenceProperty()
    imageid=db.IntegerProperty()

class InviteList(db.Model):
    user = db. ReferenceProperty(User, collection_name = 'invite_list')
    invitecid = db. IntegerProperty()

def next_circle_id():
    circle=db.GqlQuery('SELECT * FROM Circles ORDER BY cid DESC')
    return 0 if circle.count() == 0 else circle[0].cid+1
def next_image_id():
    image=db.GqlQuery('SELECT * FROM Image ORDER BY imgid DESC')
    return 0 if image.count() == 0 else image[0].imgid+1
def next_image_file_id():
    image=db.GqlQuery('SELECT * FROM ImageFile ORDER BY imageid DESC')
    return 0 if image.count() == 0 else image[0].imageid+1

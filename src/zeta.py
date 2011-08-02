import cgi
import random
import re
import os
from datetime import datetime 

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

template_dir = os.path.dirname(__file__) + "\\template\\"

class dbUser(db.Model):
    user_name = db.StringProperty()
    user_mail = db.EmailProperty()
    priv_hash = db.StringProperty()
    publ_hash =  db.StringProperty()
    isRunning = db.BooleanProperty(default=False)
    
class dbEntry(db.Model):
    start_time = db.DateTimeProperty()
    end_time = db.DateTimeProperty()
    comment = db.TextProperty()
    user_id = db.ReferenceProperty(dbUser)


class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        #self.response.out.write(template_dir)
        path = os.path.join(template_dir, 'index.html')
        self.response.out.write(template.render(path, template_values))
        
        pass

class UserGenerate(webapp.RequestHandler):
    def get(self):
        template_values = {}
        path = os.path.join(template_dir, 'addUser.html')
        self.response.out.write(template.render(path, template_values))

        
    def post(self):
        userclean = re.sub("\W","", self.request.get('uname')).lower()
        
        checkUser = dbUser.all()
        checkUser.filter("user_name =", userclean)
        userLen = checkUser.fetch(10)
        
        if len(userLen) != 0:
            self.response.out.write("User already exists")
            return
        
        
        newuser = dbUser()
        
        newuser.user_name = cgi.escape( userclean )
        newuser.user_mail = cgi.escape( self.request.get('email'))
        
        random.seed()
        newuser.priv_hash = str ( "%016x" % random.getrandbits(128) )
        
        random.seed()
        newuser.publ_hash = str ( "%016x" % random.getrandbits(64) )
        
        newuser.put()

class GetPrivateKey(webapp.RequestHandler):
    def get(self):
        self.response.out.write(dir(self))
        
class TimeStart(webapp.RequestHandler):
    def get(self, privKey):
        
        privKey = re.sub("\W","", privKey)
        
        mUser = dbUser.all()
        mUser.filter("priv_hash =", privKey)
        rUser = mUser.fetch(10) 
        
        if len(rUser) != 1:
            self.response.out.write("User doesn't exists")
            return
        
        rUser = rUser[0]
        
        #Check if user is already in a session
        if rUser.isRunning:
            self.response.out.write("User is already in session")
            return
        
        newEntry = dbEntry()
        newEntry.start_time =  datetime.today()
        newEntry.user_id = rUser.key()
        newEntry.put()

        rUser.isRunning = True
        rUser.put()
        
        self.response.out.write("START")
    
    
    
class TimeEnd(webapp.RequestHandler):
    def get(self, privKey):
        
        privKey = re.sub("\W","", privKey)
        
        mUser = dbUser.all()
        mUser.filter("priv_hash =", privKey)
        rUser = mUser.fetch(10) 
        
        if len(rUser) != 1:
            self.response.out.write("User doesn't exists")
            return
        
        rUser = rUser[0]
        
        #Check if user is already in a session
        if not rUser.isRunning:
            self.response.out.write("User is not in session")
            return
        
        cEntry = dbEntry.all()
        cEntry.filter("user_id =", rUser.key())
        cEntry.filter("end_time =", None)
        
        rEntry = cEntry.fetch(10)
        
        if len(rEntry) != 1:
            self.response.out.write("Somehow we have more than one session open. THIS IS NOT GOOD")
            return
        
        rEntry = rEntry[0]
        
        rEntry.end_time = datetime.today()
        rEntry.put()
        
        rUser.isRunning = False
        rUser.put()
        
        self.response.out.write("END")    
    
class ListTimes(webapp.RequestHandler):
    def get(self, pubKey):
        pubKey = re.sub("\W","", pubKey)
        
        mUser = dbUser.all()
        mUser.filter("publ_hash =", pubKey)
        rUser = mUser.fetch(10) 
        
        if len(rUser) != 1:
            self.response.out.write("User doesn't exists")
            return
        
        rUser = rUser[0]
        
        tEntries = dbEntry.all()
        tEntries.filter("user_id =", rUser.key())
        tEntries.order("start_time")
        
        entries = tEntries.fetch(100)
        self.response.out.write("Listing : " + str(rUser.user_name) + "<br>")
        for e in entries:
            self.response.out.write(str(e.start_time) + " : " + str(e.end_time) + "<br>")
        
  
class UserStat(webapp.RequestHandler):
    def get(self, pubKey):
        
        mUser = dbUser.all()
        mUser.filter("publ_hash =", re.sub("\W","", pubKey))
        rUser = mUser.fetch(10) 
        
        if len(rUser) != 1:
            self.response.out.write("User doesn't exists")
            return
        
        if rUser[0].isRunning :
            self.response.out.write("RUNNING")
        else:
            self.response.out.write("NOT RUNNING")
  

class UserInfo(webapp.RequestHandler):
    def get(self, privKey):

        mUser = dbUser.all()
        mUser.filter("priv_hash =", re.sub("\W","", privKey))
        rUser = mUser.fetch(10) 
        
        if len(rUser) != 1:
            self.response.out.write("User doesn't exists")
            return
        
        rUser = rUser[0]
        
        self.response.out.write(
                                str(rUser.user_name) + ":" +
                                str(rUser.user_mail) + ":" +
                                str(rUser.publ_hash) + ":" +
                                str(rUser.isRunning) + ":"
                                ) 
        
              
#################################################################################
#################################################################################
#################################################################################    
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/UserGen', UserGenerate),
                                      (r'/start', GetPrivateKey),
                                      (r'/api/start/(.*)', TimeStart),
                                      (r'/api/end/(.*)', TimeEnd),
                                      (r'/list/(.*)', ListTimes),
                                      (r'/api/stat/(.*)', UserStat),
                                      (r'/api/info/(.*)', UserInfo),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
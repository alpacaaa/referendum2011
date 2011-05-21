import httplib
import os.path
import wsgiref.handlers
from cgi import parse_qs


from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

FACEBOOK_APP_ID = "129521920457417"
stream = open('fb_key', 'r')
FACEBOOK_APP_SECRET = stream.read()


class Vote(db.Model):
	uid = db.StringProperty()
	votes = db.StringProperty()


class AppHandler(webapp.RequestHandler):

	def get(self, user_id = None):
		if (user_id and self.request.headers['accept'].find('application/json') != -1):
			v = self.getVote(user_id)
			if v:
				return self.response.out.write(json.dumps(v.votes))
			
			return '{}'

		args = {
			'facebook_app_id': FACEBOOK_APP_ID,
			'user': user_id,
			'vote': None
		}
		
		if (user_id):
			args['vote'] = self.getVote(user_id)
		
		path = os.path.join(os.path.dirname(__file__), "index.html")
		self.response.out.write(template.render(path, args))
		
	def post(self, null = None):
		
		key  = 'fbs_' + FACEBOOK_APP_ID
		if (not(key in self.request.cookies)):
			return self.response.out.write('{}')
		
		if not('votes' in self.request.POST):
			return self.response.out.write('{}')
		
		votes = self.request.POST['votes']

		if votes.count(',') != 3:
			return self.response.out.write('{}')

		votes = votes.split(',')

		for v in votes:
			if (v != 'yes' and v != 'no'):
				return self.response.out.write('{}')

		parts = parse_qs(self.request.cookies[key])
		access_token = parts['"access_token'][0]
		
		c = httplib.HTTPSConnection('graph.facebook.com')
		c.request("GET", '/me?access_token=' + access_token)
		response = c.getresponse()
		data = response.read()
		data = json.loads(data)
		
		id = data['id']
		vote = self.getVote(id);
		
		
		if not(vote):
			vote = Vote()
		
		
		#vote = Vote()
		vote.uid = id
		vote.votes = ','.join(votes)
		
		vote.put()
		self.response.out.write(id)
		
	def getVote(self, id):
		return Vote.gql("WHERE uid = :1", id).get()




def main():
    util.run_wsgi_app(webapp.WSGIApplication([
    	(r"/", AppHandler),
    	(r"/(.*)", AppHandler)
    ]))


if __name__ == "__main__":
    main()


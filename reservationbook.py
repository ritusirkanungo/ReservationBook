import cgi
import urllib
import os

from google.appengine.api import users
from google.appengine.ext import ndb
from datetime import datetime,time,date

import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)
DEFAULT_RESERVATIONBOOK_NAME = 'ROOT'
def reservationbook_key(reservationbook_name=DEFAULT_RESERVATIONBOOK_NAME):
    """Constructs a Datastore key for a AddCreatedResource entity.

    We use reservationbook_name as the key.
    """
    return ndb.Key('AddCreatedResource', reservationbook_name)

class Author(ndb.Model):
	"""Sub model to represent an author"""
	identity=ndb.StringProperty(indexed=False)
	email=ndb.StringProperty(indexed=False)
	
class Resource(ndb.Model):
	"""Main model to represent individual resourcebook entry"""
	resourceName= ndb.StringProperty(indexed=True)
	startTime=ndb.DateTimeProperty(auto_now_add=False)
	endTime=ndb.DateTimeProperty(auto_now_add=False)
	author=ndb.StructuredProperty(Author)
	date=ndb.DateTimeProperty(auto_now_add=True)
	
class MainPage(webapp2.RequestHandler):
	def get(self):
		resource_query=Resource.query().order(-Resource.date)
		resources=resource_query.fetch()
		menu_name = 'see_your'
		menu_name1 = self.request.get('menu_name')
		
		if menu_name1 != '':
			menu_name=menu_name1
			
		user=users.get_current_user()
		if user:
			if user:
				url=users.create_logout_url(self.request.uri)
				url_linktext='Logout'
				url_createResource='Create New Resource'

			template_values = {
				'user': user,
				'url':url,
				'resources':resources,
				'url_linktext': url_linktext,
				'url_createResource': url_createResource,
				'menu_name': urllib.quote_plus(menu_name),
			}
			
			
			
			template = JINJA_ENVIRONMENT.get_template('index.html')
			self.response.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))		

class AddCreatedResource(webapp2.RequestHandler):
	def post(self):
		
		menu_name = 'see_all'
		
		resource_name = self.request.get('resource_name')
		user = users.get_current_user().user_id()
		reservationbook_name = resource_name + user
		
		addResource = Resource(parent=reservationbook_key(reservationbook_name))
		
		addResource.resourceName = resource_name
		
		
		currDay =datetime.now().day
		currMonth = datetime.now().month
		currYear = datetime.now().year
		
		getDay = self.request.get('Day')
		getMonth = self.request.get('Month')
		getYear = self.request.get('Year')

		getDate = getMonth+'/'+getDay+'/'+getYear
		
		getStartHours = self.request.get('startHours')
		getStartMins = self.request.get('startMins')
		getStartMeridian = self.request.get('startMeridian')
		getStartTime = getStartHours+':'+getStartMins+' '+getStartMeridian
		getStartDateTime = getDate+' '+getStartTime
		startDateTime = datetime.strptime(getStartDateTime, '%m/%d/%Y %I:%M %p')
		addResource.startTime = startDateTime

		
		getEndHours = self.request.get('endHours')
		getEndMins = self.request.get('endMins')
		getEndMeridian = self.request.get('endMeridian')
		getEndTime = getEndHours+':'+getEndMins+' '+getEndMeridian		
		getEndDateTime = getDate+' '+getEndTime
		endDateTime = datetime.strptime(getEndDateTime, '%m/%d/%Y %I:%M %p')
		addResource.endTime = endDateTime
		
		if users.get_current_user():
			addResource.author = Author(
						identity=users.get_current_user().user_id(),
						email=users.get_current_user().email())
		
		addResource.put()
		

		query_params={'menu_name':menu_name}
		self.redirect('/?'+urllib.urlencode(query_params))

class ReserveResource(webapp2.RequestHandler):
	def get(self):
		menu_name = 'show_reservations'
		menu_name1 = self.request.get('menu_name')
		
		if menu_name1 != '':
			menu_name = menu_name1
		resource_name = self.request.get('resource_name')	
		resource_author_id = self.request.get('resource_author_id')
		reservationbook_name = self.request.get('reservationbook_name')	
		if reservationbook_name == '':
			reservationbook_name = resource_name + resource_author_id
		
		resource_query = Resource.query(ancestor=reservationbook_key(reservationbook_name))
		resource = resource_query.fetch()

		user = users.get_current_user()
		
		template_values={
			'user': user,
			'resource':resource,	
			'menu_name': menu_name,
			'reservationbook_name':reservationbook_name,
		}
		template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
		self.response.write(template.render(template_values))
	
		
app = webapp2.WSGIApplication([
	('/', MainPage),
	('/sign', AddCreatedResource),
	('/reserveResource', ReserveResource)
],debug=True)
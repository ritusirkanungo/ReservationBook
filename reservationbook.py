import cgi
import urllib
import os

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import images
from datetime import datetime,time,date,timedelta
from time import sleep
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
from email import utils

import time
import webapp2
import jinja2
import uuid

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

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

	
	
class Author(ndb.Model):
	"""Sub model to represent an author"""
	identity=ndb.StringProperty(indexed=False)
	email=ndb.StringProperty(indexed=False)
	
class Resource(ndb.Model):
	"""Main model to represent individual resourcebook entry"""
	uuid = ndb.StringProperty(indexed=True)
	resourceName= ndb.StringProperty(indexed=False)
	startTime=ndb.DateTimeProperty(auto_now_add=False)
	endTime=ndb.DateTimeProperty(auto_now_add=False)
	author=ndb.StructuredProperty(Author)
	date=ndb.DateTimeProperty(auto_now_add=False)
	tags=ndb.StringProperty(repeated=True)
	pubDate=ndb.DateTimeProperty(auto_now_add=True)
	avatar = ndb.BlobProperty()
	
class Reservation(ndb.Model):
	author=ndb.StructuredProperty(Author)
	uuid = ndb.StringProperty(indexed=True)
	resourceUUID = ndb.StringProperty(indexed=True)
	resourceName = ndb.StringProperty(indexed=False)
	startTime = ndb.DateTimeProperty(auto_now_add=False)
	endTime = ndb.DateTimeProperty(auto_now_add=False)	
	duration = ndb.StringProperty(indexed=False)
	pubDate = ndb.DateTimeProperty(auto_now_add=True)
	
	
class MainPage(webapp2.RequestHandler):
	def get(self):
		resource_query=Resource.query().order(-Resource.date)
		resources=resource_query.fetch()
		
		
		reservation_query=Reservation.query()
		reservations = reservation_query.fetch()
		
		menu_name = 'see_your'


		deleteReservationID = ''
		deleteReservationID1 = self.request.get('deleteReservation') 
		if deleteReservationID1 != '':
			deleteReservationID = deleteReservationID1
			reservation_query_delete = Reservation.query(Reservation.uuid == deleteReservationID)
			reservation_delete_key = reservation_query_delete.fetch()
			reservation_delete_key[0].key.delete()
			sleep(2)
			query_params = {'menu_name': menu_name}
			self.redirect('/?'+urllib.urlencode(query_params))
			
		menu_name1 = self.request.get('menu_name')
		
		checkOwnerResources = 'false'
		checkOwnerResources1 = self.request.get('checkOwnerResources') 
		if checkOwnerResources1 != '' :
			checkOwnerResources = checkOwnerResources1

		getOwner = ''
		
		getOwner1 = self.request.get('getOwner')
		if getOwner1 != '':
			checkOwnerResources = 'true'
			getOwner = getOwner1
		
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
				'reservations':reservations,
				'url_linktext': url_linktext,
				'url_createResource': url_createResource,
				'menu_name': urllib.quote_plus(menu_name),
				'getOwner': getOwner,
				'checkOwnerResources': checkOwnerResources,

			}
			
			
			
			template = JINJA_ENVIRONMENT.get_template('index.html')
			self.response.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))		

class AddCreatedResource(webapp2.RequestHandler):
	def post(self):
		old_resource_uuid = self.request.get('resource_uuid');
		if old_resource_uuid!="":
			resource_query = Resource.query(Resource.uuid == old_resource_uuid)
			resource_temp_key = resource_query.fetch()
			resource_temp_key[0].key.delete()
		
		menu_name = 'see_all'
		
		resource_name = self.request.get('resource_name')
		user = users.get_current_user().user_id()
		reservationbook_name = resource_name + user
		
		addResource = Resource()
		
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
		
		getTags = self.request.get('resource_Tag')
		getTagsList = getTags.split(';')
		addResource.tags = getTagsList
		
		if users.get_current_user():
			addResource.author = Author(
						identity=users.get_current_user().user_id(),
						email=users.get_current_user().email())
		
		addResource.uuid = str(uuid.uuid4())
		
		avatar = self.request.get('img')
		
		addResource.avatar = str(avatar)
		
		addResource.put()
		sleep(2)

		query_params={'menu_name':menu_name}
		self.redirect('/?'+urllib.urlencode(query_params))

class ReserveResource(webapp2.RequestHandler):
	def get(self):
		menu_name = 'show_reservations'
		menu_name1 = self.request.get('menu_name')
		flag = self.request.get('flag')
		
		if menu_name1 != '':
			menu_name = menu_name1
		resource_uuid = self.request.get('resource_uuid')	
		
		resource_query = Resource.query(Resource.uuid == resource_uuid)
		resource = resource_query.fetch()
		resource_date = datetime.strftime(resource[0].startTime,'%m/%d/%Y')

		reservation_query = Reservation.query(Reservation.resourceUUID == resource_uuid)
		reservations = reservation_query.fetch()
		
		user = users.get_current_user()
		currDateTime = datetime
		template_values={
			'user': user,
			'resource':resource[0],	
			'menu_name': menu_name,
			'resource_date': resource_date,
			'reservations': reservations,
			'flag': flag,
			'currDateTime': 'currDateTime',
		}
		template = JINJA_ENVIRONMENT.get_template('reserveResource.html')
		self.response.write(template.render(template_values))
	
class AddReservation(webapp2.RequestHandler):
	def post(self):
		
		menu_name = 'see_your'
		
		resource_name = self.request.get('resource_name')
		resource_uuid = self.request.get('resource_uuid')
		resource_startDate = self.request.get('resource_startDate')
		
		user = users.get_current_user()
		
		resource_query = Resource.query(Resource.uuid == resource_uuid)
		resource = resource_query.fetch()
		resource = resource[0]
		resource.date= datetime.now()
		
		resource.put()
		sleep(1)
		
		reservation_query = Reservation.query(Reservation.resourceUUID == resource_uuid)
		reservations = reservation_query.fetch()
		
		getStartHours = self.request.get('startHours')
		getStartMins = self.request.get('startMins')
		getStartMeridian = self.request.get('startMeridian')
		getStartTime = getStartHours+':'+getStartMins+' '+getStartMeridian
		getStartDateTime = resource_startDate+' '+getStartTime
		startDateTime = datetime.strptime(getStartDateTime, '%m/%d/%Y %I:%M %p')

		getEndHours = self.request.get('endHours')
		getEndMins = self.request.get('endMins')
		getEndTime = getEndHours+':'+getEndMins		
		endTime = datetime.strptime(getEndTime, '%H:%M')
		delta = timedelta(hours=endTime.hour,minutes=endTime.minute)		
		endDateTime = startDateTime + delta
		flag = 'true'
		currentDate = datetime.now()
		
		if resource.startTime <= startDateTime:
			if resource.endTime >= endDateTime:
				for reservation in reservations:
					if reservation.startTime > startDateTime and reservation.startTime >= endDateTime:
						flag = 'true'
					else:
						if startDateTime >= reservation.endTime and endDateTime > reservation.endTime:
							flag = 'true'
						else:
							flag = 'false'
			else :
				flag = 'false'
		else :
			flag = 'false'
		
			
		if flag == 'true':
			addReservation = Reservation()
			addReservation.resourceName = resource_name
			addReservation.resourceUUID = resource_uuid
			addReservation.startTime = startDateTime
			addReservation.endTime = endDateTime		
			addReservation.duration = getEndTime
			
			if users.get_current_user():
				addReservation.author = Author(
							identity=users.get_current_user().user_id(),
							email=users.get_current_user().email())
			
			addReservation.uuid = str(uuid.uuid4())
			
			addReservation.put()
			
			
			
			sleep(2)
			query_params={'menu_name':menu_name}
			self.redirect('/?'+urllib.urlencode(query_params))		
		else :
			menu_name = 'add_new_reservation'
			query_params={'menu_name':menu_name,'flag':flag,'resource_uuid':resource_uuid}
			self.redirect('/reserveResource?'+urllib.urlencode(query_params))		

class ListTagResources(webapp2.RequestHandler):
	def get(self):
		get_Tag = self.request.get('get_Tag')
		resource_query = Resource.query(Resource.tags == get_Tag)
		resources = resource_query.fetch()
			
		user=users.get_current_user()
		
		if user:
			url=users.create_logout_url(self.request.uri)
			url_linktext='Logout'
			
			template_values = {
				'resources':resources,
				'user':user,
			}
			template = JINJA_ENVIRONMENT.get_template('seeTaggedResource.html')
			self.response.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))

class RSSResource(webapp2.RequestHandler):
	def get(self):
		resource_uuid = self.request.get('get_ResourceID')
		
		reservation_query = Reservation.query(Reservation.resourceUUID == resource_uuid)
		reservations = reservation_query.fetch()
		user = users.get_current_user()
		resource_query = Resource.query(Resource.uuid == resource_uuid)
		resource = resource_query.fetch()
		weburl = self.request.url
		urlstringsplit = weburl.split("/")
		urlstringsplit.remove(urlstringsplit[len(urlstringsplit)-1])
		strjoin = "/".join(urlstringsplit)
		
		strjoin = strjoin + "/reserveResource?resource_uuid="+resource_uuid
		
		
		
		top = Element('rss')
		top.set('version', '2.0')

		channel = SubElement(top, 'channel')
		title = SubElement(channel, 'title')
		title.text = resource[0].resourceName
		description = SubElement(channel, 'description')
		description.text = "This resource is owned by "+ resource[0].author.email
		link = SubElement(channel, 'link')
		link.text = strjoin
		lastBuildDate = SubElement(channel, 'lastBuildDate')
		
		resourcepubdate = resource[0].pubDate.timetuple()
		pubtimestamp = time.mktime(resourcepubdate)

		

		if resource[0].date is None:
			lastBuildDate.text = utils.formatdate(pubtimestamp)
		else:
			resourcelastdate = resource[0].date.timetuple()
			lasttimestamp = time.mktime(resourcelastdate)
			lastBuildDate.text = utils.formatdate(lasttimestamp)
		
		pubDate = SubElement(channel, 'pubDate')
		pubDate.text = utils.formatdate(pubtimestamp)
		count = 1
		if len(reservations) > 0:
			for reservation in reservations:
				reservationpubdate = reservation.pubDate.timetuple()
				reservepubtimestamp = time.mktime(reservationpubdate)

				item = SubElement(channel, 'item')
				title = SubElement(item, 'title')
				title.text = "Reservation"+str(count)
				description = SubElement(item, 'description')
				description.text = "This reservation is done by:"+reservation.author.email+"with start time:"+str(reservation.startTime)+" for duration:"+ str(reservation.duration)
				link = SubElement(item, 'link')
				link.text = strjoin
				guid = SubElement(item, 'guid')
				guid.set('isPermaLink','false')
				guid.text = reservation.uuid
				pubDate = SubElement(item, 'pubDate')
				pubDate.text = utils.formatdate(reservepubtimestamp)

				count = count + 1
		
		xmlFile = prettify(top)
		
		if user:
			url=users.create_logout_url(self.request.uri)
			url_linktext='Logout'
			
			template_values = {
				'reservations':reservations,
				'user':user,
				'xmlFile':xmlFile,
			}
			template = JINJA_ENVIRONMENT.get_template('seeRSS.html')
			self.response.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))

class Image:
	def get(self):
		resource_key = ndb.Key(urlsafe=self.request.get('img_id'))
		resource = resource_key.get()
		menu_name = 'see_all'
		if resource.avatar:
			query_params={'menu_name':menu_name,'resource_avatar':resource.avatar}
			self.redirect('/?'+urllib.urlencode(query_params))				
		else:
			menu_name = 'see_your'
			query_params={'menu_name':menu_name}
			self.redirect('/?'+urllib.urlencode(query_params))				
		
		
app = webapp2.WSGIApplication([
	('/', MainPage),
	('/sign', AddCreatedResource),
	('/reserveResource', ReserveResource),
	('/addReservation', AddReservation),
	('/listTagResources', ListTagResources),
	('/resourceRSS', RSSResource),
	('/img', Image),
],debug=True)
#!/usr/bin/env python
from fancyhands import FancyhandsClient
from google.appengine.ext import db
from datetime import datetime, timedelta

import webapp2
import os
import jinja2
import logging
import urlparse
import json

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
	def get(self):
		prank = PrankModel.all().order('-date_updated').get()
		template_values = {'prank':prank}

		template = JINJA_ENVIRONMENT.get_template('main.html')
		self.response.write(template.render(template_values))

	def post(self):
		# Get the data from the HTML POST
		phone_number = self.request.get('phone-number')
		prank_text = self.request.get('prank-text')

		# Set your Fancy Hands API Key and Secret here
		api_key = '<API KEY>'
		secret = '<API SECRET>'

		# Setup the Fancy Hands Client
		client = FancyhandsClient(api_key, secret)

		title = 'Prank Call - %s' % phone_number
		description = prank_text
		bid = 4.0
		expiration_date = datetime.now() + timedelta(1).strftime('%Y-%m-%dT10:09:08Z')

		# Build custom form data
		custom_fields = []
		custom_field = {
			'label':'Reaction',
			'type':'textarea',
			'description':'What was their reaction?',
			'order':1,
			'required':True,
		}
		custom_fields.append(custom_field)

		# Make call to Fancy Hands
		prank_request = client.custom_create(title, description, bid, expiration_date, custom_fields)

		# Save return object to PrankModel
		prank = PrankModel.create_from_callback(prank_request)

		# Render new data
		template_values = {'prank':prank}
		template = JINJA_ENVIRONMENT.get_template('main.html')
		self.response.write(template.render(template_values))

class PrankModel(db.Model):
    date_created = db.DateTimeProperty(auto_now_add=True)
    date_updated = db.DateTimeProperty(auto_now=True)
    title = db.StringProperty()
    content = db.TextProperty()
    status = db.StringProperty()
    bid = db.FloatProperty()
    fh_key = db.StringProperty()

    @classmethod
    def create_from_callback(self, callback):
		prank = PrankModel.all().filter('fh_key =', callback['key']).get()

		if prank:
			prank.status = callback['status']
			prank.numeric_status = callback['numeric_status']
		else:
			prank = PrankModel()
			prank.status = callback['status']
			prank.title = callback['title']
			prank.content = callback['content']
			prank.status = callback['status']
			prank.bid = float(callback['api_bid'])
			prank.fh_key = callback['key']

		prank.put()
		return prank

class CallbackHandler(webapp2.RequestHandler):
    def post(self):
      callback = dict(urlparse.parse_qsl(self.request.body))
      PrankModel.create_from_callback(callback)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/callback/?', CallbackHandler),
], debug=True)
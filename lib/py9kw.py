#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    py9kw.py - A API for the Captcha-solvingservice 9kw.eu
#
#    Copyright (C) 2014 by Jan Helbling <jan.helbling@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import urllib.request,binascii
from urllib.parse import urlencode
from os import getenv
from base64 import b64encode,b64decode
from time import sleep
from locale import getdefaultlocale

webservice_url	=	'https://www.9kw.eu/index.cgi'

locale		=	getdefaultlocale()[0]

if 'de' in locale.lower():
	error_codes	=	{
		1  : 'Kein API Key vorhanden.',
		2  : 'Kein API Key gefunden.',
		3  : 'Keinen aktiven API Key gefunden.',
		4  : 'API Key wurde vom Betreiber deaktiviert.',
		5  : 'Kein User gefunden.',
		6  : 'Keine Daten gefunden.',
		7  : 'Keine ID gefunden.',
		8  : 'Kein Captcha gefunden.',
		9  : 'Kein Bild gefunden.',
		10 : 'Bildgrösse nicht erlaubt.',
		11 : 'Guthaben ist nicht ausreichend.',
		12 : 'Bereits erledigt.',
		13 : 'Keine Antwort enthalten.',
		14 : 'Captcha bereits beantwortet.',
		15 : 'Captcha zu schnell eingereicht.',
		16 : 'JD Check aktiv.',
		17 : 'Unbekanntes Problem.',
		18 : 'Keine ID gefunden.',
		19 : 'Fehlerhafte Antwort.',
		20 : 'Nicht rechtzeitig eingereicht (Falsche UserID).',
		21 : 'Link nicht erlaubt.',
		22 : 'Einreichen verboten.',
		23 : 'Eingeben verboten.',
		24 : 'Zu wenig Guthaben.',
		25 : 'Keine Eingabe gefunden.',
		26 : 'Keine AGB akzeptiert.',
		27 : 'Keinen Gutscheincode in der Datenbank gefunden.',
		28 : 'Bereits genutzter Gutscheincode.',
		29 : 'Maxtimeout unter 60 Sekunden.',
		30 : 'User nicht gefunden.'
	}
else:
	error_codes = {
		1: 'No API Key available.' ,
		2: 'No API key found.',
		3: 'No active API key found.',
		4: 'API Key has been disabled by the operator. ',
		5: 'No user found.',
		6: 'No data found.',
		7: 'Found No ID.',
		8: 'found No captcha.',
		9: 'No image found.',
		10: 'Image size not allowed.',
		11: 'credit is not sufficient.',
		12: 'what was done.',
		13: 'No answer contain.',
		14: 'Captcha already been answered.',
		15: 'Captcha to quickly filed.',
		16: 'JD check active.',
		17: 'Unknown problem.',
		18: 'Found No ID.',
		19: 'Incorrect answer.',
		20: 'Do not timely filed (Incorrect UserID).',
		21: 'Link not allowed.',
		22: 'Prohibited submit.',
		23: 'Entering prohibited.',
		24: 'Too little credit.',
		25: 'No entry found.',
		26: 'No Conditions accepted.',
		27: 'No coupon code found in the database.',
		28: 'Already unused voucher code.',
		29: 'maxTimeout under 60 seconds.',
		30: 'User not found.'
	}

class py9kw:
	def __init__(self,apikey,env_proxy=False,verbose=False):
		"""Initialize py9kw with a APIKEY and Optional verbose mode.
		Verbose mode will print each step to stdout."""
		self.verbose	=	verbose
		self.apikey	=	apikey
		self.captchaid	=	''
		self.rslt	=	(False,False)
		if env_proxy == True:
			self.proxy		=	getenv('http_proxy')
			if self.proxy == None:
				self.proxyhdl	=	urllib.request.ProxyHandler({})
				if self.verbose:
					print("[py9kw] Warning: You have set env_proxy=True, but http_proxy is not set!")
					print("[py9kw] I will countine without a Proxy.")
			else:
				self.proxyhdl	=	urllib.request.ProxyHandler({'http',self.proxy})
				if self.verbose:
					print("[py9kw] Loaded http_proxy => {}".format(self.proxy))
		else:
			self.proxyhdl		=	urllib.request.ProxyHandler({})
		self.opener	=	urllib.request.build_opener(self.proxyhdl)
		self.opener.add_headers	=	[('User-Agent' , 'Python-urllib/3.x (py9kw-api)')]
		urllib.request.install_opener(self.opener)
	
	def uploadcaptcha(self,imagedata,maxtimeout=60,prio=5):
		"""Upload the Captcha to 9kw.eu (gif/jpg/png)."""
		self.maxtimeout	=	maxtimeout
		self.prio	=	prio
		if self.verbose:
			print("[py9kw] Uploading captcha...")
			print('[py9kw] Check if the imagedata is already base64 encoded...',end='')
		try:
			if b64encode(b64decode(imagedata)) == imagedata:
				if self.verbose:
					print('...[YES, already encoded]')
				self.imagedata	=	imagedata
			else:
				if self.verbose:
					print('...[NO, encode it now]')
				self.imagedata	=	b64encode(imagedata)
		except binascii.Error as e:
			self.imagedata	=	b64encode(imagedata)
		self.data	=	{
			'action' : 'usercaptchaupload',
			'apikey' : self.apikey,
			'file-upload-01' : self.imagedata,
			'prio'   : str(self.prio),
			'base64' : '1',
			'maxtimeout' : str(self.maxtimeout),
			'source' : 'py9kw-api',
#			'selfsolve' : '1',	# For debugging, it's faster.
#			'nomd5' : '1'		# always send a new imageid
		}
		
		if self.verbose:
			print('[py9kw] Priority: %d of 10, Maxtimeout: %d of 3999s (MAXIMUM)' % (self.prio,self.maxtimeout))
			print('[py9kw] Upload %d bytes to 9kw.eu...' % len(self.imagedata),end='')
		
		self.captchaid	=	(urllib.request.urlopen(webservice_url,data=urlencode(self.data).encode('utf-8','ignore')).read()).decode('utf-8','ignore')
		
		if self.verbose:
			print('...[DONE]')
		
		for i in range(10,30):
			if '00%d' % i in self.captchaid:
				if self.verbose:
					print('[py9kw] Error %d: %s' % (i,error_codes[i]))
				return error_codes[i],False
		for i in range(0,9):
			if '000%d' % i in self.captchaid:
				if self.verbose:
					print('[py9kw] Error: %d: %s' % (i,error_codes[i]))
				return error_codes[i],False
		
		if self.verbose:
			print('[py9kw] Uploaded => Captcha-id:',self.captchaid)
	
	def sleep(self,time=0):
		"""Wait until the Captcha is solved."""
		if self.verbose:
			print('[py9kw] Waiting until the Captcha is solved or maxtimeout has expired.')
		self.counter	=	self.maxtimeout
		if time == 0:
			for i in range(1,9):
				self.getresult()
				if self.rslt[1]:
					break
				else:
					if self.verbose:
						print('...[%s]' % self.rslt[0])
				self.counter	=	self.counter - (self.maxtimeout / 10)
				if self.verbose:
					print('[py9kw] Sleep..Zzzzz... %ds' % self.counter)
				sleep(self.maxtimeout / 10)
		else:
			for i in range(1,9):
				self.getresult()
				if self.rslt[1]:
					break
				self.counter	=	self.counter - (time / 10)
				if self.verbose:
					print('[py9kw] Sleep..Zzzzz... %ds' % (time / 10))
				sleep(time / 10)
		if self.verbose and not self.rslt[1]:
			print('[py9kw] !Enough sleeped!')
	
	def getresult(self):
		"""Get result from 9kw.eu."""
		self.data	=	{
			'action'	: 'usercaptchacorrectdata',
			'id'		: self.captchaid,
			'apikey'	: self.apikey,
			'info'		: '1',
			'source'	: 'py9kw-api'
		}
		if self.verbose:
			print('[py9kw] Try to fetch the solved result from 9kw.eu...',end='')
		self.string	=	(urllib.request.urlopen('%s?%s' % (webservice_url,urlencode(self.data))).read()).decode('utf-8','ignore')
		if self.string == 'NO DATA':
			self.rslt = ('No Data received!',False)
			return
		elif self.string == 'ERROR NO USER':
			self.rslt = ('Not enough users Online who solve the Captchas!',False)
			return
		for i in range(10,30):
			if '00%d' % i in self.string:
				if self.verbose:
					print('[py9kw] Error %d:' % i ,error_codes[i])
				self.rslt = (error_codes[i],False)
				return
		for i in range(0,9):
			if '000%d' % i in self.string:
				if self.verbose:
					print('[py9kw] Error: %d' % i,error_codes[i])
				self.rslt = (error_codes[i],False)
				return
		if self.verbose:
			print('...[SUCCESS]')
			print('[py9kw] Captcha solved! String: \'%s\'' % self.string)
		self.rslt = (self.string,True)
		return
	
	def captcha_correct(self,iscorrect):
		"""Send feedback, is the Captcha wrong?"""
		if iscorrect:
			if self.verbose:
				print('[py9kw] Sending feedback that the \'solved\' captcha was right...',end='')
			self.correct	=	'1'
		else:
			if self.verbose:
				print('[py9kw] Sending feedback that the \'solved\' captcha was wrong...',end='')
			self.correct	=	'2'
		self.data	=	{
			'action'  : 'usercaptchacorrectback',
			'correct' : self.correct,
			'id'      : self.captchaid,
			'apikey'  : self.apikey,
			'source'  : 'py9kw-api'
		}
		urllib.request.urlopen('%s?%s' % (webservice_url,urlencode(self.data))).read()
		if self.verbose:
			print('...[OK]')
	
	def getcredits(self):
		"""Get aviable Credits..."""
		if self.verbose:
			print('[py9kw] Get aviable Credits...',end='')
		self.data	=	{
			'action' : 'usercaptchaguthaben',
			'apikey' : self.apikey
		}
		self.rslt	=	int((urllib.request.urlopen('%s?%s' % (webservice_url,urlencode(self.data))).read()).decode('utf-8','ignore'))
		if self.verbose:
			print('...[{}]'.format(self.rslt))
		return self.rslt
		
if __name__ == '__main__':
	from sys import argv
	if len(argv) != 3:
		print('Usage:',argv[0],'<APIKEY> <TIME TO SOLVE>')
		exit(0)
	
	# Get a Sample-Captcha
	try:
		print('[py9kw-test] Get a samplecaptcha from: \'confluence.atlassian.com\'...',end='')
		image_data	=	urllib.request.urlopen('https://confluence.atlassian.com/download/attachments/216957808/captcha.png?version=1&modificationDate=1272411042125&api=v2').read()
		print('...[OK]')
	except IOError as e:
		print('...[FAIL]')
		print('[py9kw-test] Error while getting a SampleCaptcha from a Website!')
		if hasattr(e,'args'):
			print('[py9kw-test]',e.args[0])
		else:
			print('[py9kw-test]',e.filename,':',e.strerror,'.')
		exit(1)
	
	n = py9kw(argv[1],True,True)
	
	credits = n.getcredits()
	if credits < 10:
		print('[py9kw-test] Not enough Credits! < 10')
		exit(0)
	print('[py9kw-test] Credits: {}'.format(credits))
	
	#Upload it
	try:
		n.uploadcaptcha(image_data,int(argv[2]),10)
	except IOError as e:
		print('[py9kw-test] Error while uploading the Captcha!')
		if hasattr(e,'args'):
			print('[py9kw-test]',e.args[0])
		else:
			print('[py9kw-test]',e.filename,':',e.strerror,'.')
		exit(1)
	#Sleep
	n.sleep()
	
	#Get Result
	try:
		if not n.rslt[1]:
			n.getresult()
	except IOError as e:
		print('[py9kw-test] Error while getting the Result!')
		if hasattr(e,'args'):
			print('[py9kw-test]',e.args[0])
		else:
			print('[py9kw-test]',e.filename,':',e.strerror,'.')
		exit(1)
	if n.rslt[1]:
		print('[py9kw-test] String returned!')
		print('[py9kw-test] Checking if the received string is "viearer"...',end='')
		if n.rslt[0].lower() == "viearer":
			print('...[PASS]')
			try:
				n.captcha_correct(True)
				print('[py9kw-test] [!DONE!]')
			except IOError:
				pass
		else:
			print('...[FAIL]')
			print('[py9kw-test] Returned String:',n.rslt[0])
			try:
				n.captcha_correct(False)
				print('[py9kw-test] [!DONE!]')
			except IOError:
				pass
	else:
		print('[py9kw-test] Error: %s' % n.rslt[0])
		exit(1)

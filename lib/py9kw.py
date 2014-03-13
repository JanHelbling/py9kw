#!/usr/bin/python3
#
#    py9kw.py - A API for the Captcha-resolvingservice 9kw.eu
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

import urllib.request
from urllib.parse import urlencode

from base64 import b64encode
from time import sleep

webservice_url	=	'https://www.9kw.eu/index.cgi'

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


class py9kw:
	def __init__(self,apikey,verbose=False):
		"""Initialize py9kw with a APIKEY."""
		self.verbose	=	verbose
		self.apikey	=	apikey
		self.captchaid	=	""
		self.rslt	=	(False,False)
		self.opener	=	urllib.request.build_opener()
		self.opener.add_headers	=	[('User-Agent' , 'Python-urllib/3.x (py9kw-api)')]
		urllib.request.install_opener(self.opener)
	
	def uploadcaptcha(self,imagedata,maxtimeout=60,prio=5):
		"""Upload the Captcha base64 encoded to 9kw.eu (gif/jpg/png)."""
		self.maxtimeout	=	maxtimeout
		self.prio	=	prio
		self.imagedata	=	b64encode(imagedata)
		self.data	=	{
			'action' : 'usercaptchaupload',
			'apikey' : self.apikey,
			'file-upload-01' : self.imagedata,
			'prio'   : str(self.prio),
			'base64' : '1',
			'maxtimeout' : str(self.maxtimeout),
			'source' : 'py9kw-api'
		}
		
		if self.verbose:
			print("[py9kw] Upload %d bytes to 9kw.eu..." % len(self.imagedata))
		
		self.captchaid	=	(urllib.request.urlopen(webservice_url,data=urlencode(self.data).encode('utf-8')).read()).decode('utf-8')
		for i in range(10,30):
			if '00%d' % i in self.captchaid:
				if self.verbose:
					print("Error %d:" % i ,error_codes[i])
					exit(1)
				return error_codes[i],False
		for i in range(0,9):
			if '000%d' % i in self.captchaid:
				if self.verbose:
					print("Error: %d" % i,error_codes[i])
					exit(1)
				return error_codes[i],False
		
		if self.verbose:
			print("[py9kw] Uploaded. Captcha-id:",self.captchaid)
	
	def sleep(self,time=0):
		"""Wait until the Captcha is resolved."""
		self.counter	=	self.maxtimeout
		if time == 0:
			for i in range(1,9):
				self.getresult()
				if self.rslt[1]:
					break
				else:
					print("...%s" % self.rslt[0])
				self.counter	=	self.counter - (self.maxtimeout / 10)
				if self.verbose:
					print("[py9kw] Sleep..Zzzzz... %ds" % self.counter)
				sleep(self.maxtimeout / 10)
		else:
			for i in range(1,9):
				self.getresult()
				if self.rslt[1]:
					break
				self.counter	=	self.counter - (time / 10)
				if self.verbose:
					print("[py9kw] Sleep..Zzzzz... %ds" % (time / 10))
				sleep(time / 10)
		if self.verbose:
			print("[py9kw] !Enough sleeped!")
	
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
			print("[py9kw] Try to get the result from 9kw.eu...",end="")
		self.string	=	(urllib.request.urlopen('%s?%s' % (webservice_url,urlencode(self.data))).read()).decode('utf-8')
		if self.string == 'NO DATA':
			self.rslt = ('No Data!',False)
			return
		elif self.string == 'ERROR NO USER':
			self.rslt = ('Not enough users!',False)
			return
		for i in range(10,30):
			if '00%d' % i in self.string:
				if self.verbose:
					print("Error %d:" % i ,error_codes[i])
				self.rslt = (error_codes[i],False)
				return
		for i in range(0,9):
			if '000%d' % i in self.string:
				if self.verbose:
					print("Error: %d" % i,error_codes[i])
				self.rslt = (error_codes[i],False)
				return
		if self.verbose:
			print("[py9kw] Captcha resolved! String: '%s'" % self.string)
		self.rslt = (self.string,True)
		return
	
	def captcha_correct(self,iscorrect):
		"""Send feedback, is the Captcha wrong?"""
		if iscorrect:
			self.correct	=	"1"
		else:
			self.correct	=	"2"
		self.data	=	{
			'action'  : 'usercaptchacorrectback',
			'correct' : self.correct,
			'id'      : self.captchaid,
			'apikey'  : self.apikey,
			'source'  : 'py9kw-api'
		}
		if self.verbose:
			print('[py9kw] Sending correct=%s (1=Ok,2=Fail)' % self.correct)
		urllib.request.urlopen('%s?%s' % (webservice_url,urlencode(self.data))).read()

if __name__ == '__main__':
	from sys import argv
	if len(argv) != 3:
		print('Usage:',argv[0],'<APIKEY> <TIME TO RESOLVE>')
		exit(0)
	
	# Get a Sample-Captcha
	try:
		print("Get a Samplecaptcha from: 'http://jan-helbling.no-ip.biz/images/captcha.png'.")
		image_data = urllib.request.urlopen('http://jan-helbling.no-ip.biz/images/captcha.png').read()
	except IOError as e:
		print('Error while get a SampleCaptcha from a website!')
		if hasattr(e,'args'):
			print(e.args[0])
		else:
			print(e.filename,':',e.strerror,'.')
		exit(1)
	
	n = py9kw(argv[1],True)
	
	#Upload it
	try:
		n.uploadcaptcha(image_data,int(argv[2]),10)
	except IOError as e:
		print('Error while uploading the Captcha!')
		if hasattr(e,'args'):
			print(e.args[0])
		else:
			print(e.filename,':',e.strerror,'.')
		exit(1)
	#Sleep
	n.sleep()
	
	#Get Result
	try:
		if not n.rslt[1]:
			n.getresult()
	except IOError as e:
		print('Error while getting the Result!')
		if hasattr(e,'args'):
			print(e.args[0])
		else:
			print(e.filename,':',e.strerror,'.')
		exit(1)
	if n.rslt[1]:
		print("String returned!")
		print("Checking if string is CUOBX...")
		if n.rslt[0].lower() == 'cuobx':
			print('String is CUOBX!!!')
			try:
				print('Sending positive correct-feedback!')
				n.captcha_correct(True)
				print('[!DONE!]')
			except IOError:
				pass
		else:
			print('String is not CUOBX!!!')
			print('Returned String:',n.rslt[0])
			try:
				print('Sending negative correct-feedback!')
				n.captcha_correct(False)
				print('[!DONE!]')
			except IOError:
				pass
	else:
		print("Error:",n.rslt[0])
		exit(1)

#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    py9kw.py - A API for the Captcha-solvingservice 9kw.eu
#
#    Copyright (C) 2014 by Jan Helbling <jan.helbling@mailbox.org>
#    Updted 2020-01-25 by over_nine_thousand
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

import binascii
import json
import re
import time
import urllib.request
from base64 import b64encode, b64decode
from os import getenv
from urllib.parse import urlencode


def printInfo(msg):
    print('[py9kw] %s' % msg)


# See API docs: https://www.9kw.eu/api.html
API_BASE = 'https://www.9kw.eu/index.cgi'
# Parameter used as 'source' in all API requests
API_SOURCE = 'py9kw-api'
# Values according to website 2020-01-25
PARAM_MIN_PRIO = 1
PARAM_MAX_PRIO = 10
PARAM_MIN_MAXTIMEOUT = 60
PARAM_MAX_MAXTIMEOUT = 3999
PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA = 10


class Py9kw:

    def __init__(self, apikey, env_proxy=False, verbose=False):
        """Initialize py9kw with a APIKEY and Optional verbose mode.
        Verbose mode will print each step to stdout."""
        self.verbose = verbose
        self.prio = PARAM_MIN_PRIO
        self.maxtimeout = PARAM_MIN_MAXTIMEOUT
        self.apikey = apikey
        self.captchaid = ''
        self.credits = -1
        # Custom errors: 600"ERROR NO USER", 666"Error while parsing error number and message"
        self.errorint = -1
        self.errormsg = None
        if env_proxy:
            self.proxy = getenv('http_proxy')
            if self.proxy is None:
                self.proxyhdl = urllib.request.ProxyHandler({})
                if self.verbose:
                    printInfo("Warning: You have set env_proxy=True, but http_proxy is not set!")
                    printInfo("I will countine without a Proxy.")
            else:
                self.proxyhdl = urllib.request.ProxyHandler({'http', self.proxy})
                if self.verbose:
                    printInfo("Loaded http_proxy => {}".format(self.proxy))
        else:
            self.proxyhdl = urllib.request.ProxyHandler({})
        self.opener = urllib.request.build_opener(self.proxyhdl)
        self.opener.add_headers = [('User-Agent', 'Python-urllib/3.x (py9kw-api)')]
        urllib.request.install_opener(self.opener)

    # Checks for errors in json response and returns error_code(int) and error_message(String) separated as API returns them both in one String.
    def checkError(self, response, showStatus):
        error_plain = response.get('error', None)
        if error_plain is not None:
            # Error found
            if self.verbose or showStatus:
                printInfo('[checkError] Found error: Plain error: %s' % error_plain)
            try:
                error_MatchObject = re.compile(r'^(\d{4}) (.+)').search(error_plain)
                self.errorint = int(error_MatchObject.group(1))
                self.errormsg = error_MatchObject.group(2)
                if self.verbose or showStatus:
                    printInfo('[checkError] Found error: Number: %d | Message: %s' % (self.errorint, self.errormsg))
            except:
                # This should never happen
                self.errormsg = 'Error while parsing error number and message'
                self.errorint = 666
                printInfo(self.errormsg)
        else:
            # No error found
            if self.verbose or showStatus:
                printInfo('[checkError] OK - NO ERROR')
            # Reset error state
            self.errorint = -1
            self.errormsg = None
        return self.errorint, self.errormsg

    def setPriority(self, prio):
        if prio < PARAM_MIN_PRIO:
            printInfo(
                'Wished \'prio\' value %d is lower than lowest possible value %d --> Using lowest value %d instead' % (
                    prio, PARAM_MIN_PRIO, PARAM_MIN_PRIO))
            prio = PARAM_MIN_PRIO
        elif prio > PARAM_MAX_PRIO:
            printInfo(
                'Wished \'prio\' value %d is higher than highest possible value %d --> Using highest value %d instead' % (
                    prio, PARAM_MAX_PRIO, PARAM_MAX_PRIO))
            prio = PARAM_MAX_PRIO
        self.prio = prio

    def setTimeout(self, maxtimeout):
        if maxtimeout < PARAM_MIN_MAXTIMEOUT:
            printInfo(
                'Wished \'maxtimeout\' value %d is lower than lowest possible value %d --> Using lowest value %d instead' % (
                    maxtimeout, PARAM_MIN_MAXTIMEOUT, PARAM_MIN_MAXTIMEOUT))
            maxtimeout = PARAM_MIN_MAXTIMEOUT
        elif maxtimeout > PARAM_MAX_MAXTIMEOUT:
            printInfo(
                'Wished \'maxtimeout\' value %d is higher than highest possible value %d --> Using highest value %d instead' % (
                    maxtimeout, PARAM_MAX_MAXTIMEOUT, PARAM_MAX_MAXTIMEOUT))
            maxtimeout = PARAM_MAX_MAXTIMEOUT
        self.maxtimeout = maxtimeout

    def uploadcaptcha(self, imagedata, maxtimeout=None, prio=None):
        """Upload the Captcha to 9kw.eu (gif/jpg/png)."""
        # TODO: Add ability to define custom fields for getdata because even though this class is only designed to handle normal picture captchas, it is possible to specify more details of the captcha we're sending.
        if maxtimeout is not None:
            self.setTimeout(maxtimeout)
        if prio is not None:
            self.setPriority(prio)
        if self.verbose:
            printInfo("Uploading captcha...")
        if self.credits > -1 and self.credits < PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA:
            printInfo('Not enough credits to solve a captcha')
            return None
        try:
            printInfo('Check if the imagedata is already base64 encoded...')
            if b64encode(b64decode(imagedata)) == imagedata:
                if self.verbose:
                    printInfo('...[YES, already encoded]')
                imagedata = imagedata
            else:
                if self.verbose:
                    printInfo('...[NO, encode it now]')
                imagedata = b64encode(imagedata)
        except binascii.Error as e:
            imagedata = b64encode(imagedata)
        getdata = {
            'action': 'usercaptchaupload',
            'apikey': self.apikey,
            'file-upload-01': imagedata,
            'prio': str(self.prio),
            'base64': '1',
            'maxtimeout': str(self.maxtimeout),
            'source': API_SOURCE,
            'json': '1'
            #			'selfsolve' : '1',	# For debugging, it's faster.
            #			'nomd5' : '1'		# always send a new imageid
        }

        if self.verbose:
            printInfo('Priority: %d of 10, Maxtimeout: %d of 3999s' % (self.prio, self.maxtimeout))
            printInfo('Upload %d bytes to 9kw.eu...' % len(imagedata))
        json_plain = urllib.request.urlopen('%s?%s' % (API_BASE, urlencode(getdata))).read().decode('utf-8', 'ignore')
        print('json debug: ' + json_plain)
        response = json.loads(json_plain)
        self.checkError(response, True)
        self.captchaid = int(response.get('captchaid', -1))
        if self.errorint > -1 or self.captchaid == -1:
            printInfo('Error ...')
            return None
        if self.verbose:
            printInfo('...[DONE]')
        if self.verbose:
            printInfo('Uploaded => Captcha-id: %d' % self.captchaid)
        return self.captchaid

    def sleepAndGetResult(self, custom_timeout=None):
        """Wait until the Captcha is solved and return result."""
        total_timeout = None
        if custom_timeout is not None and custom_timeout >= PARAM_MIN_MAXTIMEOUT:
            total_timeout = custom_timeout
        else:
            total_timeout = self.maxtimeout
        if self.verbose:
            printInfo('Waiting until the Captcha is solved or maxtimeout %d has expired ...' % total_timeout)
        total_time_waited = 0
        wait_seconds_inbetween = 10
        maxloops = int(total_timeout / 10)
        printInfo('Waiting for captcha result')
        printInfo('Max. waittime: %s | Number of loops: %d' % (total_timeout, maxloops))
        for i in range(maxloops):
            printInfo('Wait-Loop %d of %d' % (i + 1, maxloops))
            result = self.getresult()
            if result is not None:
                # We've reached our goal :)
                print('Total time waited for result: %d' % total_time_waited)
                return result
            # This is the only case where we should retry: {"answer":"NO DATA","message":"OK","nodata":1,"status":{"success":true,"https":1},"info":1}
            if self.errorint > -1:
                # The only error for which we don't have to 'give up': "0012 Bereits erledigt. / Already done." --> Will be ignored anyways as a result will be available!
                print('Error happened --> Giving up')
                break
            if self.verbose:
                printInfo('Waiting %d seconds' % wait_seconds_inbetween)
            time.sleep(wait_seconds_inbetween)
            total_time_waited += wait_seconds_inbetween

        printInfo('Time expired! Failed to find result!')
        return None

    def getresult(self) -> str:  # https://stackoverflow.com/questions/42127461/pycharm-function-doesnt-return-anything
        """Get result from 9kw.eu. Use sleepAndGetResult for auto-wait handling! """
        answer = None
        getdata = {
            'action': 'usercaptchacorrectdata',
            'id': self.captchaid,
            'apikey': self.apikey,
            'info': '1',
            'source': API_SOURCE,
            'json': '1'
        }
        if self.verbose:
            printInfo('Try to fetch the solved result from 9kw.eu...')
        plain_json = urllib.request.urlopen('%s?%s' % (API_BASE, urlencode(getdata))).read().decode('utf-8', 'ignore')
        if self.verbose:
            printInfo(plain_json)
        response = json.loads(plain_json)
        self.checkError(response, True)
        # TODO: Add errorhandling
        answer = response.get('answer', None)
        nodata = response.get('nodata', -1)
        if nodata == 1:
            printInfo('No answer yet')
            return None
        elif answer is not None and answer == 'ERROR NO USER':
            # Special: We need to set an error to make sure that our sleep handling would stop!
            self.errorint = 600
            self.errormsg = 'ERROR NO USER'
            printInfo('No users there to solve at this moment --> Or maybe your timeout is too small')
            return None
        elif self.errorint > -1:
            printInfo('Error %d: %s' % (self.errorint, self.errormsg))
            return None
        if answer is None:
            # This should never happen
            if self.verbose:
                printInfo('[FAILURE] --> Unknown failure')
        else:
            if self.verbose:
                printInfo('[SUCCESS]')
                printInfo('Captcha solved! String: \'%s\'' % answer)
        return answer

    def captcha_correct(self, iscorrect):
        """Send feedback, is the Captcha result correct?"""
        if iscorrect:
            if self.verbose:
                printInfo('Sending feedback that the \'solved\' captcha was right...')
            correct = '1'
        else:
            if self.verbose:
                printInfo('Sending feedback that the \'solved\' captcha was wrong...')
            correct = '2'
        getdata = {
            'action': 'usercaptchacorrectback',
            'correct': correct,
            'id': self.captchaid,
            'apikey': self.apikey,
            'source': API_SOURCE,
            'json': '1'
        }
        try:
            response = json.loads(
                urllib.request.urlopen('%s?%s' % (API_BASE, urlencode(getdata))).read().decode('utf-8', 'ignore'))
            # Check for errors but do not handle them. If something does wrong here it is not so important!
            self.checkError(response, True)
        except:
            printInfo('Error in captcha_correct')
        return

    def getcredits(self):
        """Get aviable Credits..."""
        if self.verbose:
            printInfo('Get available Credits...')
        getdata = {
            'action': 'usercaptchaguthaben',
            'apikey': self.apikey,
            'source': API_SOURCE,
            'json': '1'
        }

        response = json.loads(
            urllib.request.urlopen('%s?%s' % (API_BASE, urlencode(getdata))).read().decode('utf-8', 'ignore'))
        self.checkError(response, False)
        if self.errorint > -1:
            printInfo('Error: %s' % self.errormsg)
            return None
        usercredits = response.get('credits', -1)
        if self.verbose:
            printInfo('%d credits available --> Enough to solve approximately %d captchas' % (
                usercredits, (usercredits / PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA)))
        self.credits = usercredits
        return self.credits


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        print('Usage:', argv[0], '<APIKEY> <TIME TO SOLVE>')
        exit(0)

    # Get a Sample-Captcha
    image_data = None
    try:
        print('[py9kw-test] Get a samplecaptcha from: \'confluence.atlassian.com\'...')
        image_data = urllib.request.urlopen(
            'https://confluence.atlassian.com/download/attachments/216957808/captcha.png?version=1&modificationDate=1272411042125&api=v2').read()
        print('...[OK]')
    except IOError as e:
        print('...[FAIL]')
        print('[py9kw-test] Error while getting a SampleCaptcha from a Website!')
        if hasattr(e, 'args'):
            print('[py9kw-test]', e.args[0])
        else:
            print('[py9kw-test]', e.filename, ':', e.strerror, '.')
        exit(1)

    n = Py9kw(argv[1], True, True)

    testcredits = n.getcredits()
    if testcredits < PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA:
        print('[py9kw-test] Not enough Credits! < %d' % PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA)
        exit(0)
    print('[py9kw-test] Credits: {}'.format(testcredits))

    # Upload it
    try:
        n.uploadcaptcha(image_data, int(argv[2]), 10)
    except IOError as e:
        print('[py9kw-test] Error while uploading the Captcha!')
        if hasattr(e, 'args'):
            print('[py9kw-test]', e.args[0])
        else:
            print('[py9kw-test]', e.filename, ':', e.strerror, '.')
        exit(1)
    # Sleep and get result
    result = n.sleepAndGetResult()
    # Evaluate Result
    if result is None:
        printInfo('[py9kw-test] Error while getting the Result!')
        exit(1)
    printInfo('[py9kw-test] String returned!')
    printInfo('[py9kw-test] Checking if the received string is "viearer"...')
    if result.lower() == "viearer":
        printInfo('[py9kw-test] Test passed --> executing captcha_correct')
        n.captcha_correct(True)
        printInfo('[py9kw-test] [!DONE!]')
    else:
        printInfo('[py9kw-test] Test FAILED --> executing captcha_correct')
        printInfo('[py9kw-test] Returned String: %s' % result)
        n.captcha_correct(False)
    printInfo('[py9kw-test] [!DONE!]')
    exit(0)

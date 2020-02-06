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
import validators
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
PARAM_MAX_PRIO = 20
# -1 or 0 = do not send 'prio' parameter at all.
PARAM_DEFAULT_PRIO = -1
PARAM_MIN_MAXTIMEOUT = 60
PARAM_MAX_MAXTIMEOUT = 3999
PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA = 10


class Py9kw:

    def __init__(self, apikey, env_proxy=False, verbose=False):
        """Initialize py9kw with a APIKEY and Optional verbose mode.
        Verbose mode will print each step to stdout."""
        logger_prefix = '[init] '
        self.verbose = verbose
        self.prio = PARAM_DEFAULT_PRIO
        self.maxtimeout = PARAM_MIN_MAXTIMEOUT
        self.apikey = apikey
        self.captchaid = -1
        self.credits = -1
        self.extrauploaddata = None
        # Custom errors also possible besides known API errorcodes e.g. 600 --> "ERROR_NO_USER" --> See README.md
        self.errorint = -1
        self.errormsg = None
        if env_proxy:
            self.proxy = getenv('http_proxy')
            if self.proxy is None:
                self.proxyhdl = urllib.request.ProxyHandler({})
                if self.verbose:
                    printInfo(logger_prefix + "Warning: You have set env_proxy=True, but http_proxy is not set!")
                    printInfo(logger_prefix + "I will countine without a Proxy.")
            else:
                self.proxyhdl = urllib.request.ProxyHandler({'http', self.proxy})
                if self.verbose:
                    printInfo(logger_prefix + "Loaded http_proxy => {}".format(self.proxy))
        else:
            self.proxyhdl = urllib.request.ProxyHandler({})
        self.opener = urllib.request.build_opener(self.proxyhdl)
        self.opener.add_headers = [('User-Agent', 'Python-urllib/3.x (py9kw-api)')]
        urllib.request.install_opener(self.opener)
        if self.verbose:
            printInfo(logger_prefix + 'Current cost for one captcha: %d' % self.getCaptchaCost())

    def resetSolver(self):
        """ Call this to reset all runtime values if you e.g. want to re-use a previously created solver instance while keeping your settings (prio, maxtimeout and so on).  """
        self.captchaid = -1
        return

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

    def getCaptchaCost(self):
        """Returns how much credits it would cost to solve one captcha with the current settings."""
        captcha_cost = PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA
        if self.prio > 0:
            captcha_cost += self.prio
        return captcha_cost

    def setPriority(self, prio):
        if prio > PARAM_MAX_PRIO:
            printInfo(
                'Wished \'prio\' value %d is higher than highest possible value %d --> Using highest value %d instead' % (
                    prio, PARAM_MAX_PRIO, PARAM_MAX_PRIO))
            self.prio = PARAM_MAX_PRIO
        else:
            # Either user defined prio value or default
            self.prio = prio
        return

    def setAdditionalCaptchaUploadParams(self, uploaddata):
        """ Use this to add extra captcha upload parameters such as: 'case-sensitive':'1'. Be sure to always use Strings! """
        if uploaddata is not None:
            self.extrauploaddata = uploaddata
        return

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
        return

    def getCaptchaImageFromWebsite(self, image_url, image_path=None):
        """ Returns (captcha) image file obtained from website. And optionally saves it to <image_path>. """
        imagefile = None
        try:
            imagefile = urllib.request.urlopen(image_url).read()
            # Save file only if path is given
            if image_path is not None:
                with open(image_path, 'wb') as file:
                    file.write(imagefile)
                file.close()

            if self.verbose:
                printInfo('[getCaptchaImageFromWebsite] [OK]')
        except IOError as e:
            printInfo('[getCaptchaImageFromWebsite] [FAIL]')
            self.errorint = 603
            self.errormsg = 'CAPTCHA_DOWNLOAD_FAILURE'
        return imagefile, self.errorint, self.errormsg

    def uploadcaptcha(self, imagedata, store_image_path=None, maxtimeout=None, prio=None):
        """Upload the Captcha to 9kw.eu (gif/jpg/png)."""
        logger_prefix = '[uploadcaptcha] '
        # Step 1: Set optional parameters and check if user has enough credits
        if self.verbose:
            printInfo(logger_prefix + 'Attempting to upload captcha...')
        if maxtimeout is not None:
            self.setTimeout(maxtimeout)
        if prio is not None:
            self.setPriority(prio)
        if self.credits > -1 and self.credits < PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA:
            printInfo(logger_prefix + 'Not enough credits to solve a captcha')
            return None
        # Step 2: Prepare image data we want to upload
        # First check if we have an URL --> Download image first
        if isinstance(imagedata, str) and validators.url(imagedata):
            if self.verbose:
                printInfo(logger_prefix + 'Provided source is an URL: %s' % imagedata)
            imagedata, erri, errm = self.getCaptchaImageFromWebsite(imagedata, store_image_path)
            if self.errorint > -1:
                # Error during picture download
                return self.captchaid, self.errorint, self.errormsg
        try:
            if self.verbose:
                printInfo(logger_prefix + 'Check if the imagedata is already base64 encoded...')
            if b64encode(b64decode(imagedata)) == imagedata:
                if self.verbose:
                    printInfo(logger_prefix + 'YES, already encoded')
                imagedata = imagedata
            else:
                if self.verbose:
                    printInfo(logger_prefix + 'NO, encoding it now')
                imagedata = b64encode(imagedata)
        except binascii.Error as e:
            imagedata = b64encode(imagedata)
        # Step 3: Prepare all other parameters we want to send
        getdata = {
            'action': 'usercaptchaupload',
            'apikey': self.apikey,
            'file-upload-01': imagedata,
            'base64': '1',
            'maxtimeout': str(self.maxtimeout),
            'source': API_SOURCE,
            'json': '1'
            #			'selfsolve' : '1',	# For debugging, it's faster.
            #			'nomd5' : '1'		# always send a new imageid
        }
        if self.prio > 0:
            prio_str = str(self.prio)
            getdata['prio'] = prio
            if self.verbose:
                printInfo(logger_prefix + 'Uploading captcha with prio %d' % self.prio)
        else:
            prio_str = 'None'
            if self.verbose:
                printInfo(logger_prefix + 'Uploading captcha without prio')
        if self.extrauploaddata is not None:
            if self.verbose:
                getdata.update(self.extrauploaddata)

        # Step 4: Send data and return captchaid
        if self.verbose:
            printInfo(logger_prefix + 'Priority: %s of 10, Maxtimeout: %d of 3999s' % (prio_str, self.maxtimeout))
            printInfo(logger_prefix + 'Upload %d bytes to 9kw.eu...' % len(imagedata))
        json_plain = urllib.request.urlopen('%s?%s' % (API_BASE, urlencode(getdata))).read().decode('utf-8', 'ignore')
        if self.verbose:
            printInfo(logger_prefix + 'json debug: ' + json_plain)
        response = json.loads(json_plain)
        self.checkError(response, True)
        self.captchaid = int(response.get('captchaid', -1))
        if self.errorint > -1 or self.captchaid == -1:
            printInfo(logger_prefix + 'Error ...')
            return None
        if self.verbose:
            printInfo(logger_prefix + '[DONE]')
        if self.verbose:
            printInfo(logger_prefix + 'Uploaded => Captcha-id: %d' % self.captchaid)
        return self.captchaid, self.errorint, self.errormsg

    def sleepAndGetResult(self, custom_timeout=None):
        """Wait until the Captcha is solved and return result."""
        logger_prefix = '[sleepAndGetResult] '
        wait_seconds_inbetween = 10
        total_timeout = None
        if custom_timeout is not None and custom_timeout >= PARAM_MIN_MAXTIMEOUT:
            total_timeout = custom_timeout
        else:
            total_timeout = self.maxtimeout
        total_timeout += wait_seconds_inbetween
        if self.verbose:
            printInfo(logger_prefix + 'Waiting until the Captcha is solved or maxtimeout %d (includes %d extra seconds) has expired ...' % (total_timeout, wait_seconds_inbetween))
        total_time_waited = 0
        maxloops = int(total_timeout / 10)
        printInfo(logger_prefix + 'Waiting for captcha result')
        printInfo(logger_prefix + 'Max. waittime: %s | Number of loops: %d' % (total_timeout, maxloops))
        for i in range(maxloops):
            printInfo(logger_prefix + 'Wait-Loop %d / %d' % (i + 1, maxloops))
            result, response, erri, errm = self.getresult()
            server_says_try_again = response.get('try_again', False)
            if result is not None:
                # We've reached our goal :)
                printInfo(logger_prefix + 'Total seconds waited for result: %d' % total_time_waited)
                return result, self.errorint, self.errormsg
            if self.errorint > -1 and self.errorint != 602:
                # Retry only on 602 NO_ANSWER_YET - step out of loop if any other error happens
                printInfo(logger_prefix + 'Error happened --> Giving up')
                break
            elif server_says_try_again == 0:
                printInfo(logger_prefix + 'Server does not want us to try again --> Stopping')
                break
            if self.verbose:
                printInfo(logger_prefix + 'Waiting %d seconds' % wait_seconds_inbetween)
            time.sleep(wait_seconds_inbetween)
            total_time_waited += wait_seconds_inbetween
        printInfo(logger_prefix + 'Time expired! Failed to find result!')
        self.errorint = 601
        self.errormsg = 'ERROR_INTERNAL_TIMEOUT'
        return None, self.errorint, self.errormsg

    def getresult(self) -> str:  # https://stackoverflow.com/questions/42127461/pycharm-function-doesnt-return-anything
        """Get result from 9kw.eu. Use sleepAndGetResult for auto-wait handling! """
        logger_prefix = '[getresult] '
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
            printInfo(logger_prefix + 'Try to fetch the solved result from 9kw.eu...')
        plain_json = urllib.request.urlopen('%s?%s' % (API_BASE, urlencode(getdata))).read().decode('utf-8', 'ignore')
        if self.verbose:
            printInfo(plain_json)
        response = json.loads(plain_json)
        self.checkError(response, True)
        answer = response.get('answer', None)
        nodata = response.get('nodata', -1)
        thiscredits = response.get('credits', -1)
        if thiscredits != -1:
            # 2020-02-06: API might sometimes return this as a String although it is supposed to be a number
            if isinstance(thiscredits, str):
                thiscredits = int(thiscredits)
            if self.verbose:
                print(logger_prefix + 'Updated credits: %d' % thiscredits)
            self.credits = thiscredits
        if nodata == 1:
            printInfo(logger_prefix + 'No answer yet')
            self.errorint = 602
            self.errormsg = 'NO_ANSWER_YET'
            return None, response, self.errorint, self.errormsg
        elif answer is not None and answer == 'ERROR NO USER':
            # Special: We need to set an error to make sure that our sleep handling would stop!
            self.errorint = 600
            self.errormsg = 'ERROR_NO_USER'
            printInfo(logger_prefix + 'No users there to solve at this moment --> Or your timeout is too small OR you\'ve aborted this captcha before')
            return None, response, self.errorint, self.errormsg
        elif self.errorint > -1:
            printInfo(logger_prefix + 'Error %d: %s' % (self.errorint, self.errormsg))
            return None, response, self.errorint, self.errormsg
        elif answer is None:
            # Answer is not given but also we did not get any errormessage
            if self.verbose:
                printInfo(logger_prefix + '[FAILURE] --> Failed to find answer --> Unknown failure')
        else:
            # Answer is given
            if self.verbose:
                printInfo(logger_prefix + '[SUCCESS]')
                printInfo(logger_prefix + 'Captcha solved! String: \'%s\'' % answer)
        return answer, response, self.errorint, self.errormsg

    def captcha_correct(self, iscorrect):
        """Send feedback, is the Captcha result correct or not?"""
        logger_prefix = '[captcha_correct] '
        if iscorrect:
            if self.verbose:
                printInfo(logger_prefix + 'Sending POSITIVE captcha solved feedback ...')
            feedback = 1
        else:
            if self.verbose:
                printInfo(logger_prefix + 'Sending NEGATIVE captcha solved feedback ...')
            feedback = 2
        return self.sendCaptchaFeedback(feedback)

    def captcha_correct_abort(self):
        """Send feedback, aborts the already sent captcha. If no answer is available yet, no credits will be used in this case!"""
        return self.sendCaptchaFeedback(3)

    def sendCaptchaFeedback(self, feedback_status):
        """Send feedback, is the Captcha result correct(=1) or not(=2) or does the user want to abort(=3)?"""
        logger_prefix = '[sendCaptchaFeedback] '
        if self.verbose:
            printInfo(logger_prefix + 'Sending captcha feedback : %d' % feedback_status)
        if self.captchaid is None or self.captchaid == -1:
            # This should only happen on wrong usage
            printInfo(logger_prefix + 'Cannot send captcha feedback because captchaid is not given')
            return self.errorint, self.errormsg
        getdata = {
            'action': 'usercaptchacorrectback',
            'correct': feedback_status,
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
            printInfo(logger_prefix + 'Error in captcha_correct')
        return self.errorint, self.errormsg

    def getcredits(self):
        """Get aviable Credits..."""
        logger_info = '[getcredits] '
        if self.verbose:
            printInfo(logger_info + 'Get available Credits...')
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
            printInfo(logger_info + 'Error: %s' % self.errormsg)
            return None
        usercredits = response.get('credits', -1)
        if self.verbose:
            cost_per_captcha = self.getCaptchaCost()
            printInfo(logger_info + '%d credits available | Cost per captcha (with current prio %d): %d | Enough to solve approximately %d captchas' % (
                usercredits, self.prio, cost_per_captcha, (usercredits / cost_per_captcha)))
        self.credits = usercredits
        return self.credits, self.errorint, self.errormsg


if __name__ == '__main__':
    from sys import argv

    if len(argv) != 3:
        printInfo('Usage:', argv[0], '<APIKEY> <TIME TO SOLVE>')
        exit(0)

    captchaSolver = Py9kw(argv[1], True, True)
    # Get a Sample-Captcha    image_data =
    sample_captcha_url = 'https://confluence.atlassian.com/download/attachments/216957808/captcha.png?version=1&modificationDate=1272411042125&api=v2'
    test_image_data, erri, errm = captchaSolver.getCaptchaImageFromWebsite(sample_captcha_url)
    if erri > -1:
        print('[py9kw-test] Captcha download failure')
        exit(1)

    testcredits, erri, errm = captchaSolver.getcredits()
    if testcredits < PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA:
        print('[py9kw-test] Not enough Credits! < %d' % PARAM_MIN_CREDITS_TO_SOLVE_ONE_CAPTCHA)
        exit(0)
    print('[py9kw-test] Credits: {}'.format(testcredits))

    # Upload it
    try:
        test_captchaid, erri, errm = captchaSolver.uploadcaptcha(test_image_data, True, int(argv[2]),
                                                                                   10)
    except IOError as e:
        print('[py9kw-test] Error while uploading the Captcha!')
        if hasattr(e, 'args'):
            print('[py9kw-test]', e.args[0])
        else:
            print('[py9kw-test]', e.filename, ':', e.strerror, '.')
        exit(1)
    # Sleep and get result
    result, erri, errm = captchaSolver.sleepAndGetResult()
    # Evaluate Result
    if result is None:
        printInfo('[py9kw-test] Error while getting the Result!')
        exit(1)
    printInfo('[py9kw-test] String returned!')
    printInfo('[py9kw-test] Checking if the received string is "viearer"...')
    if result.lower() == "viearer":
        printInfo('[py9kw-test] Test passed --> executing captcha_correct')
        captchaSolver.captcha_correct(True)
        printInfo('[py9kw-test] [!DONE!]')
    else:
        printInfo('[py9kw-test] Test FAILED --> executing captcha_correct')
        printInfo('[py9kw-test] Returned String: %s' % result)
        captchaSolver.captcha_correct(False)
    printInfo('[py9kw-test] [!DONE!]')
    exit(0)

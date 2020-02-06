## py9kw - a library for captcha solving service 9kw.eu

### Sample code
```python
import sys
import urllib

from py9kw import Py9kw

captchaSolver = Py9kw('<APIKEY>', False, True)
captchaSolver.setTimeout(62)
# Define exactly what we expect as a result according to: https://www.9kw.eu/api.html#apisubmit-tab
captchaSolver.setAdditionalCaptchaUploadParams({'numeric': '1', 'min_len': '7', 'max_len': '7'})

creds, errorint, errormsg = captchaSolver.getcredits()
print('Credits left: %d' % creds)

test_url = 'https://confluence.atlassian.com/download/attachments/216957808/captcha.png?version=1&modificationDate=1272411042125&api=v2'
captcha_path = 'captcha.png'
captcha_expected_result = 'viearer'
captchaSolver.uploadcaptcha(test_url, captcha_path)

# Use this switch to test captcha abort --> Should not waste any credits
abortCaptcha = False
if abortCaptcha:
    print('Trying to abort already uploaded captcha --> No credits should be used')
    erri, errm = captchaSolver.captcha_correct_abort()
    if erri == -1:
        print('Successfully aborted captcha')
    else:
        # This should never happen
        print('Failed to abort captcha')
    captchaSolver.getresult()
    sys.exit(0)

print('Getting result ...')
result, erri, errm = captchaSolver.sleepAndGetResult()
result_is_correct = False
if result is not None:
    print('Result = \'%s\' | Expected result = %s' % (result, captcha_expected_result))
    if result == captcha_expected_result:
        result_is_correct = True
        print('Result is correct :)')
        captchaSolver.captcha_correct(True)
    else:
        print('Result is wrong :(')
        captchaSolver.captcha_correct(False)
else:
    print('No result :(')

creds_after, erri, errm = captchaSolver.getcredits()
creds_used = creds - creds_after
print('Credits used for this test: %d' % creds_used)
if creds_used > 0 and result is not None and not result_is_correct:
    print('Your %d used credits should soon get refunded as the obtained result was wrong' % creds_used)
elif creds_used > 0 and result is None:
    print('Your %d user credits should soon get refunded as you did not get any result' % creds_used)
elif creds_used > 0:
    print('Your %d used credits will never come back :(' % creds_used)
print('Credits left: %d' % creds_after)
print('END')
sys.exit(0)

```
### Possible errorcodes
Most of all possible errorcodes with their corresponding errormessages are listed in the [9kw API docs](https://www.9kw.eu/api.html).  
**For this reason only the errorcodes which are only returned by this lib will be listed here (with one exception).**

Errorcode | Explanation
--- | ---
600 | ERROR_NO_USER This happens when there were no users available to solve the uploaded captcha within the given maxtimeout. Example API json: {"status":{"https":1,"success":true},"message":"OK","answer":"ERROR NO USER"}
601 | ERROR_INTERNAL_TIMEOUT Basically the same as 600 but in this case, the internal timout happened before the serverside timeout happened. This may also happen in case the server responds with 'try_again' without returning an error.
602 | NO_ANSWER_YET No captcha result available yet. This is the only case in which sleepAndGetResult is allowed to retry. Example API json: {"answer":"NO DATA","message":"OK","nodata":1,"status":{"success":true,"https":1},"info":1}
603 | CAPTCHA_DOWNLOAD_FAILURE This may happen before a captcha gets sent to 9kw if the provided URL is e.g. offline or returns an http error status.
666 | Error while parsing error number and message --> This should never happen
0012 | **Special case returned by API: 0012 Bereits erledigt.** This will return an errorcode along with a (correct)captcha result!


#### FAQ

**Which captchas can this library handle?**  
All text based captchas. The 9kw service can handle many more captcha types but support for them has not been implemented in this library (yet) see [9kw API docs](https://www.9kw.eu/api.html#apisubmit-tab).  

### TODOs (not sorted)
* Nicer loggers/output
* Support for other captcha types
* Make start params nicer
* Add start params for 'Playground.py' test class --> Important because if I don't, I will forget my apikey in there at some point :D
* Update 'Playground.py' to never waste any credits

Original version's usage instructions:
```
class py9kw(builtins.object)
     |  Methods defined here:
     |  
step1|  __init__(self, apikey, verbose=False)
     |      Initialize py9kw with a APIKEY.
     |  
step4|  captcha_correct(self, iscorrect)
     |      Send feedback, is the Captcha answer wrong?
     |  
step3|  sleepAndGetResult(self)
     |      Wait until the Captcha is solved and get the result
     |  
step2|  uploadcaptcha(self, imagedata, maxtimeout=60)
     |      Upload the Captcha base64 encoded to 9kw.eu. (gif/jpg/png)
```


Original version's copyright information:
```

    py9kw.py - A API for the Captcha-solvingservice 9kw.eu

    Copyright (C) 2014 by Jan Helbling <jan.helbling@mailbox.org>
    Updted 2020-01-25 by over_nine_thousand
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

```
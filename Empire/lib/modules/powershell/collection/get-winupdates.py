from lib.common import helpers

class Module:

    def __init__(self, mainMenu, params=[]):

        # metadata info about the module, not modified during runtime
        self.info = {
            # name for the module that will appear in module menus
            'Name': 'Get Microsoft Updates',

            # list of one or more authors for the module
            'Author': ['Maarten Hartsuijker','@classityinfosec'],

            # more verbose multi-line description of the module
            'Description': ('This module will list the Microsoft update history, including pending updates, of the machine'),

            # True if the module needs to run in the background
            'Background' : True,

            # True if we're saving the output as a file
            'SaveOutput' : False,

            'OutputExtension' : None,

            # True if the module needs admin rights to run
            'NeedsAdmin' : True,

            # True if the method doesn't touch disk/is reasonably opsec safe
            'OpsecSafe' : True,

            'Language' : 'powershell',

            'MinLanguageVersion' : '2',

            # list of any references/other comments
            'Comments': [
                'Have fun'
            ]
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                # The 'Agent' option is the only one that MUST be in a module
                'Description'   :   'Agent to run the module on.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'ComputerName' : {
                # The 'ComputerName' option defaults to localhost but is adjustable
                'Description'   :   'The ComputerName this agents user has admin access to that must be queried for updates',
                'Required'      :   True,
                'Value'         :   'localhost'
            },
            'OutFile' : {
                'Description'   :   'Path to Output File',
                'Required'      :   False,
                'Value'         :   ''
            }
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu


        if params:
            for param in params:
                # parameter format is [Name, Value]
                option, value = param
                if option in self.options:
                    self.options[option]['Value'] = value


    def generate(self, obfuscate=False, obfuscationCommand=""):


        computername = self.options['ComputerName']['Value']
        print helpers.color("[+] Querying: " + str(computername))


        # if you're reading in a large, external script that might be updates,
        #   use the pattern below
        # read in the common module source code
        moduleSource = self.mainMenu.installPath + "/data/module_source/collection/Get-WinUpdates.ps1"
        if obfuscate:
            helpers.obfuscate_module(moduleSource=moduleSource, obfuscationCommand=obfuscationCommand)
            moduleSource = moduleSource.replace("module_source", "obfuscated_module_source")
        try:
            f = open(moduleSource, 'r')
        except:
            print helpers.color("[!] Could not read module source path at: " + str(moduleSource))
            return ""

        moduleCode = f.read()
        f.close()

        script = moduleCode

        scriptEnd = " Get-WinUpdates"
        scriptEnd += " -ComputerName "+computername

        if obfuscate:
            scriptEnd = helpers.obfuscate(self.mainMenu.installPath, psScript=scriptEnd, obfuscationCommand=obfuscationCommand)
        script += scriptEnd
        return script

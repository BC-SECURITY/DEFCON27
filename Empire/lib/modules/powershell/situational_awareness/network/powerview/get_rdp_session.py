from lib.common import helpers

class Module:

    def __init__(self, mainMenu, params=[]):

        self.info = {
            'Name': 'Get-NetRDPSession',

            'Author': ['@harmj0y'],

            'Description': ("Query a given RDP remote service for active sessions and originating IPs (replacement for qwinsta). "
                            "Note: needs admin rights on the remote server you're querying"),

            'Background' : True,

            'OutputExtension' : None,
            
            'NeedsAdmin' : False,

            'OpsecSafe' : True,
            
            'Language' : 'powershell',

            'MinLanguageVersion' : '2',
            
            'Comments': [
                'https://github.com/PowerShellMafia/PowerSploit/blob/dev/Recon/'
            ]
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                'Description'   :   'Agent to run module on.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'ComputerName' : {
                'Description'   :   'The hostname to query for active RDP sessions.',
                'Required'      :   True,
                'Value'         :   'localhost'
            }
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        for param in params:
            # parameter format is [Name, Value]
            option, value = param
            if option in self.options:
                self.options[option]['Value'] = value


    def generate(self, obfuscate=False, obfuscationCommand=""):
        
        moduleName = self.info["Name"]
        
        # read in the common powerview.ps1 module source code
        moduleSource = self.mainMenu.installPath + "/data/module_source/situational_awareness/network/powerview.ps1"

        try:
            f = open(moduleSource, 'r')
        except:
            print helpers.color("[!] Could not read module source path at: " + str(moduleSource))
            return ""

        moduleCode = f.read()
        f.close()

        # get just the code needed for the specified function
        script = helpers.strip_powershell_comments(moduleCode)

        script += "\n" + moduleName + " "

        for option,values in self.options.iteritems():
            if option.lower() != "agent":
                if values['Value'] and values['Value'] != '':
                    if values['Value'].lower() == "true":
                        # if we're just adding a switch
                        script += " -" + str(option)
                    else:
                        script += " -" + str(option) + " " + str(values['Value']) 

        script += ' | Out-String | %{$_ + \"`n\"};"`n'+str(moduleName)+' completed!"'
        if obfuscate:
            script = helpers.obfuscate(self.mainMenu.installPath, psScript=script, obfuscationCommand=obfuscationCommand)
        return script

from lib.common import helpers

class Module:

    def __init__(self, mainMenu, params=[]):

        self.info = {
            'Name': 'Get-DomainComputer',

            'Author': ['@harmj0y'],

            'Description': ('Queries the domain for current computer objects. Part of PowerView.'),

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
            'Identity' : {
                'Description'   :   'A SamAccountName, DistinguishedName, SID, GUID, or a dns host name, wildcards accepted.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Unconstrained' : {
                'Description'   :   'Switch. Return computer objects that have unconstrained delegation.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'TrustedToAuth' : {
                'Description'   :   'Switch. Return computer objects that are trusted to authenticate for other principals.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Printers' : {
                'Description'   :   'Switch. Return only printers.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'SPN' : {
                'Description'   :   'Return computers with a specific service principal name, wildcards accepted.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'OperatingSystem' : {
                'Description'   :   'Return computers with a specific operating system, wildcards accepted.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'ServicePack' : {
                'Description'   :   'Return computers with the specified service pack, wildcards accepted.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'SiteName' : {
                'Description'   :   'Return computers in the specific AD Site name, wildcards accepted.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Ping' : {
                'Description'   :   "Switch. Ping each host to ensure it's up before enumerating.",
                'Required'      :   False,
                'Value'         :   ''
            },
            'Domain' : {
                'Description'   :   'The domain to use for the query, defaults to the current domain.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'LDAPFilter' : {
                'Description'   :   'Specifies an LDAP query string that is used to filter Active Directory objects.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Properties' : {
                'Description'   :   'Specifies the properties of the output object to retrieve from the server.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'SearchBase' : {
                'Description'   :   'The LDAP source to search through, e.g. "LDAP://OU=secret,DC=testlab,DC=local" Useful for OU queries.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Server' : {
                'Description'   :   'Specifies an active directory server (domain controller) to bind to',
                'Required'      :   False,
                'Value'         :   ''
            },
            'SearchScope' : {
                'Description'   :   'Specifies the scope to search under, Base/OneLevel/Subtree (default of Subtree)',
                'Required'      :   False,
                'Value'         :   ''
            },
            'ResultPageSize' : {
                'Description'   :   'Specifies the PageSize to set for the LDAP searcher object.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'ServerTimeLimit' : {
                'Description'   :   'Specifies the maximum amount of time the server spends searching. Default of 120 seconds.',
                'Required'      :   False,
                'Value'         :   ''
            },
            'Tombstone' : {
                'Description'   :   'Switch. Specifies that the search should also return deleted/tombstoned objects.',
                'Required'      :   False,
                'Value'         :   ''
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

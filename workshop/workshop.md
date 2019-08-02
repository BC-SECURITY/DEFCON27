# Introduction to Sandbox Evasion and AMSI Bypasses

Here you will find all of the resources and setup. Please have these things ready at the start of the workshop.

## Kali VM Setup
1. Download **Kali VM** from [offensive-security.com](https://www.offensive-security.com/kali-linux-vm-vmware-virtualbox-image-download/)

2. Download **Empire** from the dev branch of [BC-Security's fork](https://github.com/BC-SECURITY/Empire). We've [made modifications](https://github.com/BC-SECURITY/Empire/pull/1/files) required for the course.
```sh
git clone https://github.com/BC-SECURITY/Empire.git
cd Empire
git checkout dev
sudo ./setup/install.sh
sudo ./setup/reset.sh

```
## Windows 10 VM Setup
1. Download **Windows 10 VM** from [microsoft.com](https://developer.microsoft.com/en-us/windows/downloads/virtual-machines)

2. Download our sample scripts from the [samples directory](./samples). These will be used throughout the workshop. Don't extract until after creating an exclusion in the next step.

3. Create a "defcon" directory on your desktop, then add an exclusion to Windows Defender to the directory. [Steps on microsoft.com](https://support.microsoft.com/en-us/help/4028485/windows-10-add-an-exclusion-to-windows-security)

4. Extract the samples zip to the excluded directory. The .zip is password protected to bypass Windows Defender. The password is `defcon`.

5. We included a copy of [Invoke-Obfuscation](https://github.com/danielbohannon/Invoke-Obfuscation) in the samples.zip.

In PowerShell as an admin:
```ps
cd ~/Desktop/defcon/Samples/Samples/Invoke-Obfuscation-master
./start-up.ps1
Import-Module ./Invoke-Obfuscation.psd1
Invoke-Obfuscation

```

6. Install office 365 from [office.com](https://www.office.com)

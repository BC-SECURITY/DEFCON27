# Introduction to Sandbox Evasion and AMSI Bypasses

Here you will find all of the resources and setup. Please have these things ready at the start of the workshop.

## Kali VM Setup
1. Download **Kali VM** from [offensive-security.com](https://www.offensive-security.com/kali-linux-vm-vmware-virtualbox-image-download/)

2. Download **Empire** from the dev branch of [BC-Security's fork](https://github.com/BC-SECURITY/Empire)
```sh
git clone https://github.com/BC-SECURITY/Empire.git
cd Empire
git checkout dev
sudo ./setup/install.sh
sudo ./setup/reset.sh

```
## Windows 10 VM Setup
1. Download **Windows 10 VM** from [microsoft.com](https://developer.microsoft.com/en-us/windows/downloads/virtual-machines)

2. Download our sample scripts from the [scripts directory](./scripts). These will be used throughout the workshop. Don't extract until after creating an exclusion in the next step.

3. Add an exclusion to Windows Defender to the samples directory. TODO: link to some instructions.

4. Extract the samples zip to the 
Note: The .zip is password protected to bypass Windows Defender. The password is: `defcon`

5. Install office 365. TODO link.

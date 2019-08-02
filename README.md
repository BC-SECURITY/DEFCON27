[1.1]: http://i.imgur.com/tXSoThF.png (twitter icon with padding)
[2.1]: http://i.imgur.com/P3YfQoD.png (facebook icon with padding)
[3.1]: http://i.imgur.com/yCsTjba.png (google plus icon with padding)
[4.1]: http://i.imgur.com/YckIOms.png (tumblr icon with padding)
[5.1]: http://i.imgur.com/1AGmwO3.png (dribbble icon with padding)
[6.1]: http://i.imgur.com/0o48UoR.png (github icon with padding)

[1]: https://twitter.com/bcsecurity1
[2]: http://www.facebook.com/XXXXXXX
[3]: https://plus.google.com/XXXXXXX
[4]: http://XXXXXXX.tumblr.com
[5]: http://dribbble.com/XXXXXXX
[6]: http://www.github.com/BC-SECURITY
[7]: https://www.bc-security.org/blog

 # DEFCON27
[![alt text][1.1]][1]
[![alt text][6.1]][6]

Keep up-to-date on our blog at [https://www.bc-security.org/blog][7]

## Hack to Basics – Adapting Exploit Frameworks to Evade Microsoft ATP
When: 1000-1050
Where: Recon Village

Many pentesters are avoiding existing frameworks due to security improvements from Microsoft and smarter practices by network Admins. Red teams don’t have to throw away existing tools because their attacks are being thwarted and contrary to belief, Powershell is not dead. We updated existing tools and demonstrated that they can still be used to launch successful attacks. We would want to get back to the basics and demonstrate that successful attacks are still possible by modifying tools like Empire.

Our pentest used open-source intelligence (OSINT) to learn a ridiculous amount about our targets to launch spearphishing attacks. We used a targeted macro enabled doc to launch our Powershell code, which we developed from a complex academic process (failures, more obfuscation, more failures, success, ????, and Profit). 

We will go over the methods employed by Microsoft Advanced Threat Protections (ATP) in both their antivirus and their sandbox environment, how we enumerated, and characterized their system to avoid detection. In addition, we avoided detection from Darktrace on a commercial network by masking our JA3 signature and weaponized Microsoft Azure for our covert C2 channel. In the end, we were able to launch a successful attack again a large company using Empire and our wits.

## Introduction to Sandbox Evasion and AMSI Bypasses
When: 1430-1830 
Where: Flamingo, Red Rock IV

Microsoft is constantly adapting their security to counter new threats. Specifically, the introduction of the Microsoft Antimalware Scan Interface (AMSI) and its integration with Windows Defender has significantly raised the bar. In this hands-on class, we will learn the methodology behind obfuscating malware and avoiding detection. Students will explore the inner workings of Windows Defender and learn to employ AMSI bypass techniques and obfuscate malware using Visual Basic (VB) and Powershell. Then identify and evade sandbox environments to ensure the payloads are masked when arriving at the intended target. The final capstone will be tying all the concepts together.

In this workshop we will:
1. Introduce AMSI and explain its importance
2. Learn to analyze malware scripts before and after execution
3. Understand how obfuscate code to avoid AMSI and Windows Defender
4. Detect and avoid sandbox environments

### Workshop Resources
[Workshop Resources](./workshop/workshop.md)
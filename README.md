# Automatically Detecting Cryptographic Algorithms in Firmware Binaries

This repository contains the software developed to help in the writing of this final year project. It contains two parts: the data collection script and the analysing script.  

## 1. Data Collection Script

### Description

As the name suggests, this ```Python 3.6``` script has been developed to help in the data gathering part. It was built using a simple design. It has
a core element which is the entry point of the software. This handles the menu and the threads holding the actual scrappers. 

The second element of the script are the scrappers. A scrapper must inherit the ```ModuleAbstractClass``` and can be added or removed from the core script. 

### Usage and Dependencies

For usage and dependencies, please check [the collection script information](COLLECTIONSCRIPT.md)

## 2. Analysing Script

### Description

This ```PowerShell 5``` script has been developed to ease the analysis of the big amount of data gathered with the collection script. It combines simple functions such as 
extracting archives, producing reports of the binaries using third party software and analysing the reports using regex. 

### Usage and Dependencies

For usage and dependencies, plese check [the analysing script information](ANALYSINGSCRIPT.md)
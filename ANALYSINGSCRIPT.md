# Data Analysing Script

This file contains technical information about the data analysing script

## Dependencies

This ```PowerShell 5.0``` script has been developed to ease the analysis of the big amount of data gathered with the collection script. It combines simple functions such as 
extracting archives, producing reports of the binaries using third party software and analysing the reports using regex. 

Being a ```PowerShell 5.0``` script, you need to have a Windows machine. The script can be replicated on a Unix based machine.

### Third Party Dependencies

In order for the script to work, you need the following third party softwares

[WinRar](https://www.rarlab.com/download.htm) which extracts all the ```*.bin``` files from any archives in the downloaded data. Other archive managers work, but be sure to modify the changes in the script.

[signsrch](http://aluigi.altervista.org/mytoolz.htm) used for searching signatures in binary files. It checks the binaries for over 3000 binaries.

[strings](https://docs.microsoft.com/en-us/sysinternals/downloads/strings) which is a useful tool that looks for strings in binary files.

### Usage

Clone the repository and enjoy.

The script also takes parameters

```$winrar``` specifies the path to WinRar archive manager. Change it in the code if you want to use something else. If this path is not specified a default path will be considered.

```$signsrch``` holds the path to signsrch. This parameter is optional and if it is not specified, the script will look for res\signsrch.exe

```$strings``` stores the path to strings executable. This parameter is optional and if it is not specified, the script will look for res\strings64.exe

```$sourcepath``` is compulsory and refers to the path of the data to be analysed.

There is no destination path. The signsrch reports, extracted binaries and final report are stored in the same folder as the script so make sure you run the script in a folder with read and write access.

You can check the signsrch reports and the final report for my data [here](results)
# Data Collection Script

This file contains technical information about the data collection script

## Dependencies

The data collection script has been developed using ```Python 3.6.4``` and ```Anaconda``` for virtual environment and package management. It has not been tested with any other Python version.

### Python Dependencies

```Anaconda``` is completely optional, although it makes life on Windows much easier. Besides the ```Python``` interpreter, you will need the following packages:

The [selenium module](https://www.seleniumhq.org/) which offers browser automation capabilities and therefore the scrapping possibility 

>$ pip install -U selenium (or the conda equivalent)

The [stem module](https://stem.torproject.org/) which provides control for Tor
    
>$ pip install stem (package is not available in conda, so use pip)

The [requests module](http://docs.python-requests.org/en/master/) used to increase the downloading time and avoid problems with downloading through selenium.

>$ pip install requests (or the conda equivalent)

The [pdfkit module](https://pypi.python.org/pypi/pdfkit) helps rendering html pages to pdf (useful whenever you want to check information about the data you've downloaded)

>$ pip install pdfkit (if you are a Windows user, I highly recommend installing it using pip in anaconda)

The [BeautifulSoup module](https://www.crummy.com/software/BeautifulSoup/) extends the capabilities of selenium, helping with finding the download links using regex

>$ pip install beautifulsoup4 (or the conda equivalent)

### Third Party Dependencies

In order for the script to work, you need some third party applications.

[Chromedriver](https://sites.google.com/a/chromium.org/chromedriver/) is the web driver for Chrome. Selenium needs it to interact with Google Chrome. Make sure the script always has the latest chromedriver version. Otherwise unexpected exceptions might appear.

[wkhtmltopdf](https://wkhtmltopdf.org/) is the actual tool that renders html pages to pdf, pdfkit being the bridge between python and this application.

[Tor](https://www.torproject.org/) is used to provide anonimity and security, with stem being the controller. Note that you should download and install the Tor bundle, not the Tor browser.

[Google Chrome](https://www.google.com/chrome/) which selenium controls via chromedriver.

All the third party applications are also available for Linux and Mac making the script portable.

### Setup Dependencies Using Anaconda

If you choose to use Anaconda, it will make your life easier. Anaconda provides an option to install packages defined in a file. Some packages cannot be installed from conda repository such as stem.

Step by step guide:

1. Download and Anaconda from [here](https://www.anaconda.com/download/) and install it.
2. To create a new virtual environment with the necessary dependencies installed start Anaconda Prompt and run:
<br \>```conda env create -f```[data-collection-env.yml](data-collection-env\data-collection-env.yml)
3. Run the command
<br \>```activate data-collection-env```
4. To test that everything has been installed correctly check the dependencies by running
<br \>```conda list```

### Usage

No setup is available. Simply clone the repository and enjoy.

Commands

```
-help                                                       Print the help panel.
-start                                                      Start the script
-add -scrapper [MODULE_NAME] [CLASS_NAME]                   Add a scrapper to the script with the given scrapper name and class name.
-add -search_term [SEARCH_TERM]                             Add a search term to the script.
-delete -scrapper [MODULE_NAME]                             Delete a scrapper that is not currently running from the scrappers list.
-delete -search_term [SEARCH_TERM]                          Delete a search term from the script.
-set -threads [POSITIVE INTEGER]                            Set the max threads that can be run at once to another positive integer.
-set -chrome_path [CHROME PATH]                             Set the path to the chromedriver binary.
-set -wkhtmltopdf_path [WKHTMLTOPDF PATH]                   Set the path to the wkhtmltopdf binary.
-set -headless [BOOLEAN]                                    Set whether to run chromedriver headless or not.
-set -tor [BOOLEAN]                                         Set whether to use tor or not.
-set -tor_path [TOR PATH]                                   Set the path to Tor bundle binary.
-set -socks_p [POSITIVE INTEGER]                            Set the socks port for Tor. Note it must be a valid port.
-set -control_p [POSITIVE INTEGER]                          Set the control port for Tor. Note it must be a valid port.
-export                                                     Export the current configuration into the default file 'config.ini' so it can later be loaded.
-load                                                       Load the 'config.ini' if it exists.
```

Note that the script will download data. Make sure to run it in a directory where you have read and write access.
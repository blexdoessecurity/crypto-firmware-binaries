"""
Module responsible with scrapper related general classes.
A module represents a scrapper for a website.
"""
from selenium import webdriver
from abc import ABC, abstractmethod
from enum import Enum

import threading
import requests
import os
import datetime
import re
import pdfkit


class ModuleAbstractClass(ABC, threading.Thread):
    """
    Class that a module scrapper must inherit in order to be incorporated in the script.
    """

    def __init__(self, script_config, scrapper_name, lock):

        super(ModuleAbstractClass, self).__init__()

        self._lock = lock
        self._stop_event = threading.Event()

        self.search_terms = script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value]
        self.scrapper_name = scrapper_name
        self.wkhtmltopdf_path = script_config[ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value]
        self.chromedriver_path = script_config[ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value]
        self.use_tor = script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value]
        run_headless = script_config[ConfigsEnum.RUN_HEADLESS_CONFIG.value]

        if self.use_tor:
            self.proxy = "127.0.0.1:%s" \
                         % str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.SOCKS_PORT_CONFIG.value])

        try:
            self._log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

            os.makedirs(self._log_path, exist_ok=True)

            self._log_path = os.path.join(self._log_path, "log_%s.txt" % scrapper_name)
        except OSError as e:
            print("%s: An OS error occurred.")
            print(e)
            exit(1)

        print("%s: Writing the log file to %s." % (self.scrapper_name, self._log_path))

        try:
            self._download_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads"),
                                               self.scrapper_name)

            os.makedirs(self._download_path, exist_ok=True)
        except OSError as e:
            print("%s: An OS error occurred.")
            print(e)
            exit(1)

        print("%s: Downloading to %s." % (self.scrapper_name, self._download_path))

        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.set_headless(run_headless)

            if self.use_tor:
                chrome_options.add_argument("--proxy-server=socks5://%s" % self.proxy)

            self.browser = webdriver.Chrome(executable_path=self.chromedriver_path, chrome_options=chrome_options)
        except Exception as e:
            print("%s: An exception occurred while trying to open Chrome Driver. Check the exception and try to fix it."
                  % self.scrapper_name)
            print("%s: %s" % (self.scrapper_name, e))
            exit(1)

        self.browser_agent = self.browser.execute_script("return navigator.userAgent")

    @abstractmethod
    def run(self):
        """
        Method that overrides the thread run and must be implemented by the module scrapper.
        """
        pass

    def stop(self):
        """
        Method that sets the stop event to true in order to stop the thread.
        """
        self._stop_event.set()

    def is_stopped(self):
        """
        Method that checks if the module should stop or not
        """
        return self._stop_event.is_set()

    def get_scrapper_name(self):
        """
        Method that returns the scrapper name as a string
        :return: String representing the scrapper's name
        """
        return self.scrapper_name

    def download(self, download_link, dir_name, file_name, cookies):
        """
        Download file in the download link to the file path with the optional cookie.
        :param download_link: Download link.
        :param dir_name: Name of the directory that contains the file.
        :param file_name: File name to save the downloaded file
        :param cookies: The cookies
        """
        print("%s: Downloading file %s..." % (self.scrapper_name, file_name))
        self.write_log("Downloading file %s..." % file_name)
        try:
            pattern = re.compile("[\W_]+", re.UNICODE)
            sanitised_dir_name = pattern.sub("", dir_name)
            dir_path = os.path.join(self._download_path, sanitised_dir_name)

            os.makedirs(dir_path, exist_ok=True)
            if file_name[0] == " ":
                file_path = os.path.join(dir_path, file_name[1:])
            else:
                file_path = os.path.join(dir_path, file_name[1:])
            if os.path.isfile(file_path):
                print("%s: File %s already exists" % (self.scrapper_name, file_name))
                self.write_log("File %s already exists" % file_name)
                return

            headers = {"User-Agent": self.browser_agent}
            if self.use_tor:
                proxies = {
                    "http": "socks5h://%s" % self.proxy,
                    "https": "socks5h://%s" % self.proxy,
                    "ftp": "socks5h://%s" % self.proxy
                }
                r = requests.get(download_link, cookies=cookies, headers=headers, proxies=proxies)
            else:
                r = requests.get(download_link, cookies=cookies, headers=headers)

            with open(file_path, "wb") as f:
                f.write(r.content)

            print("%s: File %s has finished downloading" % (self.scrapper_name, file_name))
            self.write_log("File %s has finished downloading" % file_name)
        except IOError as e:
            print("%s: An I/O error occurred while trying to download the file. Check log file." % self.scrapper_name)
            self.write_log("An I/O error occurred while trying to download the file. ")
            self.write_log(e)
        except OSError as e:
            print("%s: An OS error occurred while trying to download the file. Check log file." % self.scrapper_name)
            self.write_log("An OS error occurred while trying to download the file. ")
            self.write_log(e)
        except Exception as e:
            print("%s: An error occurred while trying to download the file. Check log file." % self.scrapper_name)
            self.write_log("An error occurred while trying to download the file.")
            self.write_log(e)

    def write_log(self, message):
        """
        Write log file to a basic log.
        :param message: The message to be logged.
        """
        try:
            current_datetime = datetime.datetime.now()
            with open(self._log_path, "a") as log:
                log.write("[%s] %s %s\n" % (current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                            self.scrapper_name, message))
        except IOError as e:
            print("%s: An I/O error occurred when logging message." % self.scrapper_name)
            print("%s: %s" % (self.scrapper_name, e))
        except Exception as e:
            print("%s: An error occurred." % self.scrapper_name)
            print("%s: %s" % (self.scrapper_name, e))

    def take_screenshot(self, url, dir_name, cookies, page_number=None):
        """
        Take a screen shot of the webdriver's screen at the moment and save it in the given directory name
        :param url: The url of the site to be saved in pdf
        :param dir_name: The directory name and the screen shot name
        :param cookies: Cookies for accessing the site
        :param page_number: Optional. Pass the page number of the pdf from topic
        """
        print("%s: Taking a screen shot pdf..." % self.scrapper_name)
        self.write_log("Taking a screen shot pdf...")
        try:
            # Sanitise the name
            pattern = re.compile("[\W_]+", re.UNICODE)
            sanitised_dir_name = pattern.sub("", dir_name)
            # Create the dir path
            dir_path = os.path.join(self._download_path, sanitised_dir_name)
            # Create the dirs if they do not exist
            os.makedirs(dir_path, exist_ok=True)
            # Create the pdf path
            if page_number:
                pdf_path = os.path.join(dir_path, "%s_%s.pdf" % (sanitised_dir_name, page_number))
            else:
                pdf_path = os.path.join(dir_path, "%s.pdf" % sanitised_dir_name)

            if os.path.isfile(pdf_path):
                print("%s: Screen shot already exists" % self.scrapper_name)
                self.write_log("Screen shot already exists")
                return

            # Create options for the pdfkit
            if self.use_tor:
                options = {
                    "cookie": cookies.items(),
                    "javascript-delay": 1000,
                    "custom-header": [
                        ("User-Agent", self.browser_agent)
                    ],
                    "proxy": "socks5://%s" % self.proxy
                }
            else:
                options = {
                    "cookie": cookies.items(),
                    "javascript-delay": 1000,
                    "custom-header": [
                        ("User-Agent", self.browser_agent)
                    ]
                }
            # Show the path to wkhtmltopdf
            config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
            # Save pdf url
            pdfkit.from_url(url, pdf_path, configuration=config, options=options)

            print("%s: Screen shot success." % self.scrapper_name)
            self.write_log("Screen shot success.")
        except IOError as e:
            print("%s: An I/O error occurred while trying to take a screen shot. Check log file." % self.scrapper_name)
            self.write_log("An I/O error occurred while trying to take a screen shot.")
            self.write_log(e)
        except Exception as e:
            print("%s: A general error occurred. Check log file." % self.scrapper_name)
            self.write_log("A general error occurred.")
            self.write_log(e)

    def write_topic_url(self, url, dir_name):
        try:
            # Sanitise the name
            pattern = re.compile("[\W_]+", re.UNICODE)
            sanitised_dir_name = pattern.sub("", dir_name)
            # Create the dir path
            dir_path = os.path.join(self._download_path, sanitised_dir_name)
            # Create the dirs if they do not exist
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, "%s.txt" % sanitised_dir_name)
            if not os.path.isfile(file_path):
                with open(file_path, "a") as write_topic_url:
                    write_topic_url.write(url)
        except IOError as e:
            print("%s: An I/O error occurred while trying to take a screen shot. Check log file." % self.scrapper_name)
            self.write_log("An I/O error occurred while trying to take a screen shot.")
            self.write_log(e)
        except Exception as e:
            print("%s: A general error occurred. Check log file." % self.scrapper_name)
            self.write_log("A general error occurred.")
            self.write_log(e)


class ScrapperQueue:
    """
    Class that represents a queue specially designed to be thread-safe and keep modules.
    """
    # Empty modules list initially
    def __init__(self):
        self.modules_list = []
        self.modules_lock = threading.Lock()

    # Return the lock
    def get_lock(self):
        """
        Method that returns the lock so it can be used in other packages.
        :return: The lock used.
        """
        return self.modules_lock

    # Return the modules list
    def get_modules(self):
        """
        Method that returns the list holding the modules.
        :return: List holding the moduels.
        """
        return self.modules_list

    # Add a module at the end of the list to simulate queue
    def put(self, module_name, class_name):
        """
        Method that adds at the end of the queue the module scrapper only if it is not already in the list.
        :param module_name: The module_name part of the module scrapper
        :param class_name: The class_name part of the module scrapper
        """
        if not self.contains(module_name):
            self.modules_lock.acquire()
            self.modules_list.append((module_name, class_name))
            self.modules_lock.release()

    # Get the first module and remove it from the list if list is not empty to simulate a queue
    # Return None if list is empty
    def get(self):
        """
        Method that returns the first item in the queue and remove it from the list.
        :return: The first item if it exists. None otherwise.
        """
        self.modules_lock.acquire()

        if (len(self.modules_list)) == 0:
            self.modules_lock.release()
            return None

        element = self.modules_list.pop(0)
        self.modules_lock.release()
        return element

    # Delete a module from a list
    def delete(self, module_name):
        """
        Method that deletes a module from the list, if it exists.
        :param module_name: The module_name part of the module scrapper.
        """
        self.modules_lock.acquire()

        for aux_module in self.modules_list:
            if str(aux_module[0]).lower() == module_name:
                try:
                    self.modules_list.remove(aux_module)
                except ValueError as e:
                    print(e)

        self.modules_lock.release()

    # Return size of the list
    def size(self):
        """
        Method that returns the size of the queue.
        :return: The size of the queue.
        """
        self.modules_lock.acquire()
        size = len(self.modules_list)
        self.modules_lock.release()
        return size

    def show_modules(self):
        """
        Method that returns all the modules stored in the queue as a string.
        :return: The string representing the modules stored in the queue.
        """
        self.modules_lock.acquire()
        str_modules = ""
        for aux_module in self.modules_list:
            str_modules = str_modules + str(aux_module[0]) + " "
        self.modules_lock.release()
        return str_modules.rstrip()

    def contains(self, module_name):
        """
        Method that returns true if the module scrapper represented by the module_name is in the lists
        and false otherwise.
        :param module_name: The module_name that represents the module_scrapper
        :return: True if it is in the list and false otherwise.
        """
        self.modules_lock.acquire()

        for aux_module in self.modules_list:
            if str(aux_module[0]).lower() == module_name:
                self.modules_lock.release()
                return True

        self.modules_lock.release()
        return False

    def is_empty(self):
        """
        Method that returns true if the queue is empty and false otherwise.
        :return: True if queue is empty, false otherwise
        """
        return self.size() == 0


class CommandsEnum(Enum):
    # Commands constants
    HELP_COMMAND = "-help"
    ADD_COMMAND = "-add"
    START_COMMAND = "-start"
    DELETE_COMMAND = "-delete"
    CONFIG_COMMAND = "-config"
    SET_COMMAND = "-set"
    EXPORT_COMMAND = "-export"
    LOAD_COMMAND = "-load"


class OptionsEnum(Enum):
    # Options
    SCRAPPER_OPTION = "-scrapper"
    SEARCH_TERM_OPTION = "-search_term"
    MAX_THREADS_OPTION = "-threads"
    CONTROL_PORT_OPTION = "-control_p"
    SOCKS_PORT_OPTION = "-socks_p"
    USE_TOR_OPTION = "-tor"
    CHROMEDRIVER_PATH_OPTION = "-chrome_path"
    WKHTMLTOPDF_PATH_OPTION = "-wkhtmltopdf_path"
    RUN_HEADLESS_OPTION = "-headless"
    TOR_PATH_OPTION = "-tor_path"


class ConfigsEnum(Enum):
    # CONFIG constants
    SCRAPPERS_CONFIG = "scrappers"
    MAX_THREADS_CONFIG = "max_threads"
    SEARCH_TERMS_CONFIG = "search_terms"
    CONTROL_PORT_CONFIG = "control_port"
    SOCKS_PORT_CONFIG = "socks_port"
    USE_TOR_CONFIG = "use_tor"
    RUN_HEADLESS_CONFIG = "run_headless"
    TOR_CONFIG = "tor_config"

    # WKHTMLTOPDF PATH
    WKTHTMLTOPDF_PATH_CONFIG = "wkhtmltopdf_path"

    # Tor PATH
    TOR_PATH_CONFIG = "tor_path"

    # Chrome driver PATH
    CHROMEDRIVER_PATH_CONFIG = "chromedriver_path"


class SectionsEnum(Enum):
    # Section Constants
    SCRAPPERS_SECTION = "Scrappers"
    GENERAL_SECTION = "General Configuration"
    TOR_SECTION = "Tor Configuration"

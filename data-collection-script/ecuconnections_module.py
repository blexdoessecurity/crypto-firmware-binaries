import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

import random
import getpass
import time
import re
import requests
import os

from bs4 import BeautifulSoup

from scrapper import ModuleAbstractClass


class CustomModule(ModuleAbstractClass):

    def __init__(self, script_config, scrapper_name, lock):
        # Set the url and open it
        self.url = "http://ecuconnections.com/forum/"
        self.browser_session = requests.Session()
        super(CustomModule, self).__init__(script_config=script_config, scrapper_name=scrapper_name, lock=lock)

    def run(self):

        try:
            # Check point for stop
            if super(CustomModule, self).is_stopped():
                self.browser.quit()
                return

            self.browser.get(self.url)

            try:
                WebDriverWait(self.browser, 120).until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                                                   "#page-body > form > "
                                                                                   "fieldset > input.button2")))
            except TimeoutException:
                print("%s: Could not load %s. Timeout error occurred." % (self.scrapper_name, self.url))
                super(CustomModule, self).write_log("Could not load %s. Timeout error occurred." % self.url)
                self.browser.quit()
                return
            except Exception as e:
                print("%s: Could not load %s. A more general exception occurred." % (self.scrapper_name, self.url))
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not load %s. "
                                                    "A more general exception occurred. "
                                                    "Check the error and try to solve it." % self.url)
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return

            print("%s: Page loaded successfully." % self.scrapper_name)
            super(CustomModule, self).write_log("Page loaded successfully.")

            # Call the function that handles login
            if self.login() == -1:
                return

            # Go through the search terms
            if self.search(self.search_terms) == -1:
                return

            self.browser.quit()
            return
        except Exception:
            if self._lock and self._lock.locked():
                self._lock.release()
            self.browser.quit()
            return

    def login(self):
        logged_in = False

        # Loop for log in to check for wrong username and password
        while not logged_in and not super(CustomModule, self).is_stopped():

            # Take username to login
            self._lock.acquire()
            username = input("%s: Username: " % self.scrapper_name)
            print("%s: Username is %s." % (self.scrapper_name, username))
            super(CustomModule, self).write_log("Username is %s." % username)
            self._lock.release()

            # Take the password
            self._lock.acquire()
            pwd = getpass.getpass("%s: Password: " % self.scrapper_name)
            self._lock.release()

            # Login part

            # Take the username input field
            try:
                navbar_username = self.browser.find_element_by_css_selector("#username")
            except NoSuchElementException:
                print("%s: Could not find the username input field. "
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the username input field. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if username input field changed and modify the module.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the username input field. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not handle the username input field. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Clear whatever is inside it, just to be sure
            navbar_username.clear()
            # Send the username
            navbar_username.send_keys(username)

            # Sleep between 2 and 4 seconds
            time.sleep(2 + random.random() * 2)

            # Take the password input field
            try:
                navbar_password_hint = self.browser.find_element_by_css_selector("#password")
            except NoSuchElementException:
                print("%s: Could not find the password input field. "
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the password input field. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if password input field changed and modify the module.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the password input field. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not handle the username input field. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Clear whatever is inside it, just to be sure
            navbar_password_hint.clear()
            # Send the password
            navbar_password_hint.send_keys(pwd)

            # Sleep between 2 and 4 seconds
            time.sleep(2 + random.random() * 2)

            # Try and click the login button
            try:
                self.browser.find_element_by_css_selector("#page-body > form > fieldset > input.button2").click()
            except NoSuchElementException:
                print("%s: Could not find the login button."
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the login button. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if the login button still exists or if it changed.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the login button."
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not handle the session length forever option. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Wait for the page to load after login
            try:
                # Successfully logged in if the Welcom posts appears
                WebDriverWait(self.browser, 120).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#page-body > div:nth-child(4) > div > ul:nth-child(2) > li > dl > dt > a")))
                logged_in = True
            except TimeoutException:
                # If we could not find the element in the DOM, try to check if invalid username / password appeared
                try:
                    WebDriverWait(self.browser, 60).until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#login > div:nth-child(1) > div > div > fieldset > div")))

                    invalid_login_credential = self.browser.find_element_by_css_selector(
                        "##login > div:nth-child(1) > div > div > fieldset > div").text
                    print("%s: %s" % (self.scrapper_name, invalid_login_credential))
                    super(CustomModule, self).write_log(invalid_login_credential)
                except TimeoutException:
                    # If it is not invalid username / password, something else went wrong
                    print("%s: Could not load login. "
                          "Timeout error occurred. "
                          "Check log for more details." % self.scrapper_name)
                    super(CustomModule, self).write_log("Could not login. "
                                                        "Timeout error occurred."
                                                        "Check internet connection "
                                                        "or check that the wrong username / password "
                                                        "verification is still valid.")
                    self.browser.quit()
                    return -1
                except Exception as e:
                    # If other exception apart from timeout exception appeared, something else went wrong
                    print("%s: Could not handle login. "
                          "A general exception occurred." % self.scrapper_name)
                    print("%s: %s" % (self.scrapper_name, e))
                    super(CustomModule, self).write_log("Could not login. "
                                                        "A general exception occurred. "
                                                        "Check the error and try to solve it.")
                    super(CustomModule, self).write_log(e)
                    self.browser.quit()
                    return -1
            except Exception as e:
                # If other exception other than timeout exception appeared, something else went wrong
                print("%s: Could not handle login. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not login. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Check if stopped was called
        if super(CustomModule, self).is_stopped():
            self.browser.quit()
            return -1

        print("%s: Logged in." % self.scrapper_name)
        super(CustomModule, self).write_log("Logged in.")

        # So to make everything faster, we store the cookie session
        for cookie in self.browser.get_cookies():
            if cookie["value"]:
                self.browser_session.cookies.set(cookie["name"], cookie["value"])

        return 0

    def search(self, search_terms):

        for search_term in search_terms:
            # Check if stopped was called
            if super(CustomModule, self).is_stopped():
                self.browser.quit()
                return -1

            time.sleep(1 + random.random() * 3)

            # Try to press advanced search
            try:
                self.browser.find_element_by_css_selector("#search > fieldset > a").click()
            except NoSuchElementException:
                print("%s: Could not find the advanced search button. "
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the advanced search button. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if the advanced search button. still exists "
                                                    "or if it changed.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the advanced search button. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not handle the advanced search button. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Wait until the search_bar appears
            try:
                WebDriverWait(self.browser, 120).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#keywords")))
            except TimeoutException:
                print("%s: Could not load advanced search page. Timeout error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not load advanced search page. Timeout error occurred.")
                self.browser.quit()
                return
            except Exception as e:
                print(
                    "%s: Could not load advanced search page. A more general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not load advanced search page. "
                                                    "A more general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return

            # Try to focus the search bar
            try:
                search_bar = self.browser.find_element_by_css_selector("#keywords")
            except NoSuchElementException:
                print("%s: Could not find the search input field. "
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the search input field. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if the search field still exists or if it changed.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the search input. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not click the login button. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Clear the search bar in any case
            search_bar.clear()
            # Write search parameter in the search field
            search_bar.send_keys(search_term)

            # Wait between 1 and 3 seconds
            time.sleep(1 + random.random() * 3)

            # Try and click Topics at Display Results part
            try:
                self.browser.find_element_by_css_selector(
                    "#page-body > form > div.panel.bg2 > div > "
                    "fieldset > dl:nth-child(5) > dd > label:nth-child(2)").click()
            except NoSuchElementException:
                print("%s: Could not find the topics radio button. "
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the topics radio button. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if the topics button still exists or if it changed.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the topics radio button. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not handle the topics radio button. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Try and click the search button
            try:
                self.browser.find_element_by_css_selector(
                    "#page-body > form > div.panel.bg3 > div > fieldset > input.button1").click()
            except NoSuchElementException:
                print("%s: Could not find the search button. "
                      "NoSuchElementException error occurred." % self.scrapper_name)
                super(CustomModule, self).write_log("Could not find the search button. "
                                                    "NoSuchElementException error occurred. "
                                                    "Check if the search button still exists or if it changed.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not handle the search button. "
                      "A general exception occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not handle the search button. "
                                                    "A general exception occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Wait for the results to appear
            try:
                WebDriverWait(self.browser, 120).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, "#page-body > p:nth-child(2) > a")))
            except TimeoutException:
                print("%s: Could not load results page. "
                      "Timeout error occurred" % self.scrapper_name)
                super(CustomModule, self).write_log("Could not load results page. "
                                                    "Timeout error occurred.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: Could not load results page. "
                      "A general error occurred." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("Could not load results page. "
                                                    "A general error occurred. "
                                                    "Check the error and try to solve it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # First page is the results page
            search_page_links = [self.browser.current_url]
            if self.handle_search_pages(search_page_links) == -1:
                return -1

        return 0

    def handle_search_pages(self, search_page_links):

        for search_page_link in search_page_links:
            # Go to the specified link if we are not already there
            if self.browser.current_url != search_page_link:
                self.browser.get(search_page_link)

            try:
                WebDriverWait(self.browser, 120).until(EC.visibility_of_all_elements_located((
                    By.CSS_SELECTOR, "#page-body > form > div > div.rightside.pagination")))
                aux_search_pages = self.browser.find_elements_by_css_selector("#page-body > form > div > "
                                                                              "div.rightside.pagination > span > a")
            except NoSuchElementException:
                print("%s: NoSuchElementException occurred when trying to find the pages of the search results. "
                      "Maybe check CSS Path and fix it." % self.scrapper_name)
                super(CustomModule, self).write_log("NoSuchElementException occurred when "
                                                    "trying to find the pages of the search results.  "
                                                    "Maybe check CSS Path and fix it.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: A general exception occurred when trying to find the pages of the search results. "
                      "Check exception and try to fix it." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("A general exception occurred when "
                                                    "trying to find the pages of the search results. "
                                                    "Check exception and try to fix it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            # Add all of them to the links page
            for aux_search_page in aux_search_pages:
                if aux_search_page.get_attribute("href") not in search_page_links:
                    search_page_links.append(aux_search_page.get_attribute("href"))

            try:
                aux_topics_list = self.browser.find_elements_by_css_selector(
                    "#page-body > div > div > ul.topiclist.topics "
                    "> li > dl > dt > a.topictitle")
            except Exception as e:
                print("%s: A general exception occurred when trying to get the topics list. "
                      "Check the exception and try to fix it." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("A general exception occurred when trying to get the topics list. "
                                                    "Check exception and try to fix it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            topics_links = []
            counter = 0
            for topic in aux_topics_list:
                counter = counter + 1
                try:
                    self.browser.find_element_by_css_selector("#page-body > div > div > ul.topiclist.topics > "
                                                               "li:nth-child(%s) > dl > dt > img" % counter)
                    topics_links.append(topic)
                # If it does not have attachments, no need to look at it
                except NoSuchElementException:
                    pass
                except Exception as e:
                    print("%s: A general exception occurred when trying to get the topics list with attachments. "
                          "Check the exception and try to fix it." % self.scrapper_name)
                    print("%s: %s" % (self.scrapper_name, e))
                    super(CustomModule, self).write_log("A general exception occurred when trying to "
                                                        "get the topics list with attachments. "
                                                        "Check the exception and try to fix it.")
                    super(CustomModule, self).write_log(e)
                    self.browser.quit()
                    return -1

            # Check if stopped was called
            if super(CustomModule, self).is_stopped():
                self.browser.quit()
                return -1

            # Go through each link and click it
            for topic in topics_links:

                if super(CustomModule, self).is_stopped():
                    self.browser.quit()
                    return -1

                topic_title = topic.text
                # Try and switch between the windows
                window_before = self.browser.current_window_handle
                actions = ActionChains(self.browser)
                actions.key_down(Keys.CONTROL).click(topic).key_up(Keys.CONTROL).perform()
                window_after = self.browser.window_handles[1]
                self.browser.switch_to.window(window_after)

                # First element is the current page in a tuple with the page url and the page number
                page_links = [(self.browser.current_url, "1")]

                if self.handle_page_links(page_links, topic_title) == -1:
                    return -1

                self.browser.close()
                self.browser.switch_to.window(window_before)
                time.sleep(2 + random.random() * 3)

            # Check if stopped was called
            if super(CustomModule, self).is_stopped():
                self.browser.quit()
                return -1

        # Check if stopped was called
        if super(CustomModule, self).is_stopped():
            self.browser.quit()
            return -1

        return 0

    def handle_page_links(self, page_links, topic_title):
        for page_link in page_links:

            self.browser.get(page_link[0])

            try:
                WebDriverWait(self.browser, 120).until(EC.visibility_of_all_elements_located((
                    By.CSS_SELECTOR, "#page-body > div > div.pagination")))
                # Find all the pages of this topic
                page_link_elements = self.browser.find_elements_by_css_selector(
                    "#page-body > div:nth-child(3) > div.pagination > span > a")
            except NoSuchElementException:
                print("%s: NoSuchElementException occurred when trying to find the pages of the topic. "
                      "Maybe check CSS Path and fix it." % self.scrapper_name)
                super(CustomModule, self).write_log("NoSuchElementException occurred when "
                                                    "trying to find the pages of the topic.  "
                                                    "Maybe check CSS Path and fix it.")
                self.browser.quit()
                return -1
            except Exception as e:
                print("%s: A general exception occurred when trying to find the pages of the topic. "
                      "Check exception and try to fix it." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("A general exception occurred when "
                                                    "trying to find the pages of the topic. "
                                                    "Check exception and try to fix it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            try:
                for page_link_element in page_link_elements:
                    href = page_link_element.get_attribute("href")
                    page_no = page_link_element.text
                    if (href, page_no) not in page_links:
                        page_links.append((page_link_element.get_attribute("href"), page_link_element.text))
            except StaleElementReferenceException:
                # Retry this page link
                page_links.append(page_link)

            self.handle_download_links(topic_title, page_link[1])

            time.sleep(2 + random.random() * 3)

        return 0

    def handle_download_links(self, topic_title, page_number):
        soup = BeautifulSoup(self.browser.page_source, "html.parser")

        # Get all the download links from the page
        # Match all the links that contain dlattach and do not end with image
        download_links = soup.findAll("a", href=re.compile(r"download"))

        # If download link is not empty, print screen to pdf
        if download_links:
            super(CustomModule, self).take_screenshot(self.browser.current_url,
                                                      topic_title,
                                                      self.browser_session.cookies,
                                                      page_number=page_number)
            super(CustomModule, self).write_topic_url(self.browser.current_url, topic_title)

        # For each link in download links list, try and download the file
        for link in download_links:
            super(CustomModule, self).download("%s%s" % (self.url, link.get("href")[2:]), topic_title,
                                               link.get_text(), self.browser_session.cookies)
            print("%s: Link - %s%s" % (self.scrapper_name, self.url, link.get("href")[2:]))
            super(CustomModule, self).write_log("Link - %s%s" % (self.url, link.get("href")[2:]))
            # Sleep random between 1 and 3
            time.sleep(1 + random.random() * 2)

        return 0

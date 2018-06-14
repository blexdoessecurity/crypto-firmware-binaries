import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        self.url = "http://digital-kaos.co.uk/forums/"
        self.browser_session = requests.Session()
        super(CustomModule, self).__init__(script_config=script_config, scrapper_name=scrapper_name, lock=lock)

    def run(self):

        # Big try / except to protect from unknown / unwanted exceptions
        try:
            # Check point for stop
            if super(CustomModule, self).is_stopped():
                self.browser.quit()
                return

            self.browser.get(self.url)

            try:
                WebDriverWait(self.browser, 120).until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                                                  "#navbar_loginform > ul > li.submitButton"
                                                                                   " > input[type=\"image\"]")))
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

            if self.search(self.search_terms) == -1:
                return

            self.browser.quit()
            return
        except Exception:
            if self._lock and self._lock.locked():
                self._lock.release()
            self.browser.quit()
            return

    # Handle the login part
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
                navbar_username = self.browser.find_element_by_css_selector("#navbar_username")
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
                navbar_password_hint = self.browser.find_element_by_css_selector("#navbar_password_hint")
                navbar_password = self.browser.find_element_by_css_selector("#navbar_password")
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

            navbar_password_hint.clear()
            # Send the password
            navbar_password.send_keys(pwd)

            # Sleep between 2 and 4 seconds
            time.sleep(2 + random.random() * 2)

            # Try and click the login button
            try:
                self.browser.find_element_by_css_selector("#navbar_loginform > ul > li.submitButton "
                                                          "> input[type=\"image\"]").click()
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
                # Successfully logged in if the logout button appears
                WebDriverWait(self.browser, 120).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#toplinks > ul > li:nth-child(1) > a")))
                logged_in = True
            except TimeoutException:
                # If we could not find the element in the DOM, try to check if invalid username / password appeared
                try:
                    WebDriverWait(self.browser, 60).until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#contentMain > div > div > div > div > div > div > div "
                                          "> div > div.body_wrapper > div.standard_error > form "
                                          "> div.blockbody.formcontrols > div.blockrow.restore")))

                    invalid_login_credential = self.browser.find_element_by_css_selector(
                        "#contentMain > div > div > div > div > div > div > div "
                        "> div > div.body_wrapper > div.standard_error > form "
                        "> div.blockbody.formcontrols > div.blockrow.restore").text

                    if "You have entered an invalid username or password." in invalid_login_credential:
                        print("%s: %s" % (self.scrapper_name, "You have entered an invalid username or password."))
                        super(CustomModule, self).write_log("You have entered an invalid username or password.")
                    else:
                        print("%s: %s" % (self.scrapper_name, "Could not log in. Unknown reason."))
                        super(CustomModule, self).write_log("Could not log in. Unknown reason.")
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
                self.browser_session.cookies.set(cookie["name"], cookie["value"])

        return 0

    # Handle the search part
    def search(self, search_terms):

        for search_term in search_terms:

            # Check if stopped was called
            if super(CustomModule, self).is_stopped():
                self.browser.quit()
                return -1

            # Try to focus the search bar
            try:
                search_bar = self.browser.find_element_by_css_selector(
                    "#header > div.searchBox > form > ul:nth-child(3) > li:nth-child(1) > div > input")
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

            # Try and click the search button
            try:
                self.browser.find_element_by_css_selector(
                    "#header > div.searchBox > form > ul:nth-child(3) > li:nth-child(2) > input[type=\"image\"]")\
                    .click()
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
                    By.CSS_SELECTOR, "#breadcrumb > div > div > div > ul > li.navbit.lastnavbit > span")))
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
            elif self.handle_search_pages(search_page_links) == 1:
                search_terms.append(search_term)

        return 0

    def handle_search_pages(self, search_page_links):

        for search_page_link in search_page_links:
            # Go to the specified link if we are not already there
            if self.browser.current_url != search_page_link:
                self.browser.get(search_page_link)

            try:
                # Take the next page from the next button.
                next_search_page = self.browser.find_element_by_css_selector("#yui-gen4 > span.prev_next "
                                                                             "> a[rel=\"next\"]")
                search_page_links.append(next_search_page.get_attribute("href"))
            except NoSuchElementException:
                # Try and check if "Sorry error page appeared"
                try:
                    sorry_error_page = self.browser.find_element_by_css_selector("#contentMain > div > div > div > "
                                                                                 "div > div > div > div > div > "
                                                                                 "div.body_wrapper > div.standard_error"
                                                                                 " > div > div")
                    return 1
                except NoSuchElementException:
                    # If this happened, we are done with this term
                    pass
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

            try:
                topics_link = self.browser.find_elements_by_css_selector("div > div.threadinfo.thread > "
                                                                         "div > h3 > a.title")
            except Exception as e:
                print("%s: A general exception occurred when trying to find attachments pages. "
                      "Check the exception and try to fix it." % self.scrapper_name)
                print("%s: %s" % (self.scrapper_name, e))
                super(CustomModule, self).write_log("A general exception occurred when "
                                                    "trying to find attachments pages. "
                                                    "Check exception and try to fix it.")
                super(CustomModule, self).write_log(e)
                self.browser.quit()
                return -1

            for topic_link in topics_link:
                thread_id = str(topic_link.get_attribute("id")).replace("_title", "")
                topic_name = topic_link.text
                try:
                    attachment_link = self.browser.find_element_by_css_selector("#%s > div > div.threadinfo.thread "
                                                                                "> div > div > div > div > div > a"
                                                                                % thread_id)
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print("%s: A general exception occurred when "
                          "trying to find attachment link. "
                          "Check exception and try to fix it." % self.scrapper_name)
                    print("%s: %s" % (self.scrapper_name, e))
                    super(CustomModule, self).write_log("A general exception occurred when "
                                                        "trying to find attachment link. "
                                                        "Check exception and try to fix it.")
                    super(CustomModule, self).write_log(e)
                    self.browser.quit()
                    return -1

                # Try and switch between the windows
                window_before = self.browser.current_window_handle
                actions = ActionChains(self.browser)
                actions.key_down(Keys.CONTROL).click(attachment_link).key_up(Keys.CONTROL).perform()
                window_after = self.browser.window_handles[1]
                self.browser.switch_to.window(window_after)

                if self.handle_download_links(topic_name) == -1:
                    return -1

                self.browser.close()
                self.browser.switch_to.window(window_before)
                time.sleep(2 + random.random() * 3)

        return 0

    def handle_download_links(self, topic_name):
        soup = BeautifulSoup(self.browser.page_source, "html.parser")

        # Get all the download links from the page
        # Match all the links that contain dlattach and do not end with image
        download_links = soup.findAll("a", href=re.compile(r"attachment.php\?attachmentid"))

        # If download link is not empty, print screen to pdf
        if download_links:
            super(CustomModule, self).take_screenshot(self.browser.current_url,
                                                      topic_name,
                                                      self.browser_session.cookies)
            super(CustomModule, self).write_topic_url(self.browser.current_url, topic_name)

        # For each link in download links list, try and download the file
        for link in download_links:
            super(CustomModule, self).download("%s%s" % (self.url, link.get("href")), topic_name,
                                               link.get_text(), self.browser_session.cookies)
            print("%s: Link - %s%s" % (self.scrapper_name, self.url, link.get("href")))
            super(CustomModule, self).write_log("Link - %s" % link.get("href"))
            # Sleep random between 1 and 3
            time.sleep(1 + random.random() * 2)

        return 0

"""
Main module responsible with running the actual script.
"""

import importlib
import signal
import sys
import os
import configparser
import stem.process
import threading

from scrapper import ScrapperQueue, CommandsEnum, OptionsEnum, ConfigsEnum, SectionsEnum


if __name__ == "__main__":

    # Handle SIGTERM and SIGINT to kill script correctly
    def _signal_handler(signum, frame):
        """
        Methods to handle SIGTERM and SIGINT signals.
        """
        try:
            global tor_subprocess
            for worker_thread in worker_threads:
                worker_thread.stop()

            if tor_subprocess and not tor_subprocess.poll():
                tor_subprocess.kill
                tor_subprocess = None

            if modules_lock and modules_lock.locked():
                modules_lock.release()
        except Exception:
            pass
        finally:
            sys.exit(0)

    # Use this function to print the help page for the script
    def _print_help():
        """This function will print the help panel"""
        first = [CommandsEnum.HELP_COMMAND.value,
                 CommandsEnum.START_COMMAND.value,
                 "%s %s [MODULE_NAME] [CLASS_NAME]" % (CommandsEnum.ADD_COMMAND.value,
                                                       OptionsEnum.SCRAPPER_OPTION.value),
                 "%s %s [SEARCH_TERM]" % (CommandsEnum.ADD_COMMAND.value,
                                          OptionsEnum.SEARCH_TERM_OPTION.value),
                 "%s %s [MODULE_NAME]" % (CommandsEnum.DELETE_COMMAND.value,
                                          OptionsEnum.SCRAPPER_OPTION.value),
                 "%s %s [SEARCH_TERM]" % (CommandsEnum.DELETE_COMMAND.value,
                                          OptionsEnum.SEARCH_TERM_OPTION.value),
                 "%s %s [POSITIVE INTEGER]" % (CommandsEnum.SET_COMMAND.value,
                                               OptionsEnum.MAX_THREADS_OPTION.value),
                 "%s %s [CHROME PATH]" % (CommandsEnum.SET_COMMAND.value,
                                          OptionsEnum.CHROMEDRIVER_PATH_OPTION.value),
                 "%s %s [WKHTMLTOPDF PATH]" % (CommandsEnum.SET_COMMAND.value,
                                               OptionsEnum.WKHTMLTOPDF_PATH_OPTION.value),
                 "%s %s [BOOLEAN]" % (CommandsEnum.SET_COMMAND.value,
                                      OptionsEnum.RUN_HEADLESS_OPTION.value),
                 "%s %s [BOOLEAN]" % (CommandsEnum.SET_COMMAND.value,
                                      OptionsEnum.USE_TOR_OPTION.value),
                 "%s %s [TOR PATH]" % (CommandsEnum.SET_COMMAND.value,
                                       OptionsEnum.TOR_PATH_OPTION.value),
                 "%s %s [POSITIVE INTEGER]" % (CommandsEnum.SET_COMMAND.value,
                                               OptionsEnum.SOCKS_PORT_OPTION.value),
                 "%s %s [POSITIVE INTEGER]" % (CommandsEnum.SET_COMMAND.value,
                                               OptionsEnum.CONTROL_PORT_OPTION.value),
                 "%s" % CommandsEnum.EXPORT_COMMAND.value,
                 "%s" % CommandsEnum.LOAD_COMMAND.value]

        second = ["Print the help panel.",
                  "Start the script. Make sure it has at least one module added.",
                  "Add a scrapper to the script with the given scrapper name and class name.",
                  "Add a search term to the script.",
                  "Delete a scrapper that is not currently running from the scrappers list.",
                  "Delete a search term from the script.",
                  "Set the max threads that can be run at once to another positive integer.",
                  "Set the path to the chromedriver binary.",
                  "Set the path to the wkhtmltopdf binary.",
                  "Set whether to run chromedriver headless or not.",
                  "Set whether to use tor or not.",
                  "Set the path to Tor bundle binary.",
                  "Set the socks port for Tor. Note it must be a valid port.",
                  "Set the control port for Tor. Note it must be a valid port.",
                  "Export the current configuration into the default file 'config.ini' so it can later be loaded.",
                  "Load the 'config.ini' if it exists."]

        print("Here is a list of commands that can be used:")

        maxlen = len(max(first, key=len))
        for i, j in zip(first, second):
            print("%s\t%s" % (i.ljust(maxlen, " "), j))

    # Start the modules part
    def _start_scrappers():
        """This function will start the running of the scrappers."""
        global tor_subprocess
        print("Trying to start modules.")
        # If modules list is empty, we cannot start anything
        if script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].is_empty():
            print("No more items where added to the module list.")
            print("Add a new module or stop the script.")
            return

        if script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value] \
                and (not tor_subprocess or tor_subprocess.poll()):
            try:
                tor_subprocess = stem.process.launch_tor_with_config(
                    tor_cmd=script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.TOR_PATH_CONFIG.value],
                    config={
                        "ControlPort": str(
                            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.CONTROL_PORT_CONFIG.value]
                        ),
                        "SocksPort": str(
                            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.SOCKS_PORT_CONFIG.value]
                        )
                    },
                    init_msg_handler=_print_bootstrap_lines
                )
            except OSError as e:
                print("An OSError occurred while trying to start Tor. "
                      "Check error and try to fix it or start script without Tor by setting use_tor to false.")
                print(e)
                return
            except Exception as e:
                print("An error occurred while trying to start Tor. "
                      "Check error and try to fix it. or start script without Tor by setting use_tor to false.")
                print(e)
                return

        # Initially no thread is started
        while (script_config[ConfigsEnum.MAX_THREADS_CONFIG.value] == 0
               or len(worker_threads) < script_config[ConfigsEnum.MAX_THREADS_CONFIG.value]) \
                and not script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].is_empty():
            try:
                current_module = script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].get()
                mod = importlib.import_module(current_module[0])
                to_be_executed_class = getattr(mod, current_module[1])
                print("Current module is %s." % current_module[0])
                worker_thread = to_be_executed_class(script_config, "%s" % current_module[0], modules_lock)
                worker_threads.append(worker_thread)
            except ModuleNotFoundError as e:
                print(e)
                print("Check module name and path.")
            except AttributeError as e:
                print(e)
                print("Check that the imported module respects the 'ModuleAbstractClass' from 'scrapper.py'.")
            except Exception as e:
                print(e)

        for worker_thread in worker_threads:
            worker_thread.start()

        for worker_thread in worker_threads:
            worker_thread.join()

        worker_threads.clear()

    # Delete module from the list of modules
    def _delete_scrapper(scrapper_name):
        """This function will delete the scrapper with the given scrapper from the list of scrappers if it exists."""
        script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].delete(scrapper_name)

    # Add a module to the modules queue
    def _add_scrapper(scrapper_name, class_name):
        """
        This function adds the created tuple with the given scrapper_name and class_name thar represents a scrapper
        and adds it to the scrappers list if it does not exist already.
        """
        script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].put(scrapper_name, class_name)

    # Delete the given search term if it exists
    def _delete_searchterm(search_term):
        """This function will delete the search term from the search terms list"""
        script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value].remove(search_term.lower())

    # Add the given search term to the list
    def _add_searchterm(search_term):
        """This function will add the search term to the search terms list"""
        if search_term not in script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value]:
            script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value].append(search_term.lower())

    # Print invalid command notice
    def _invalid_command():
        """This function will print an invalid command notice"""
        print("Command not found. Type -help for a list of commands.")

    # Set the max_threads to the new_value if it is valid i.e. a positive number
    def _set_max_threads(new_value):
        """This function will set the maximum number of threads that can be run at once to the given value"""
        try:
            if int(new_value) >= 0:
                script_config[ConfigsEnum.MAX_THREADS_CONFIG.value] = int(new_value)
        except ValueError as e:
            print(e)

    # Set chrome driver path
    def _set_chromedriver_path(new_path):
        """This function will set the chromedriver path to the new given path"""
        script_config[ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value] = new_path

    # Set wkhtmltopdf path
    def _set_wkhtmltopdf_path(new_path):
        """This function will set the wkhtmltopdf path to the new given path"""
        script_config[ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value] = new_path

    # Set run headless option to True / False
    def _set_run_headless(new_value):
        """This function will set the run headless variable to True if the given value is true or 1
        and false otherwise"""
        if new_value.lower() == "true" or new_value.lower() == "1":
            script_config[ConfigsEnum.RUN_HEADLESS_CONFIG.value] = True
        else:
            script_config[ConfigsEnum.RUN_HEADLESS_CONFIG.value] = False

    # Set use tor option to True / False
    def _set_use_tor(new_value):
        """This function will set the use tor variable to True if the  given value is true or 1 and false otherwise"""
        global tor_subprocess
        if tor_subprocess and not tor_subprocess.poll():
            tor_subprocess.kill
            tor_subprocess = None

        if new_value.lower() == "true" or new_value.lower() == "1":
            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value] = True
        else:
            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value] = False

    # Set tor path to a new given path
    def _set_tor_path(new_path):
        """This function will set the path to the tor executable to a new path"""
        global tor_subprocess
        if tor_subprocess and not tor_subprocess.poll():
            tor_subprocess.kill
            tor_subprocess = None

        script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.TOR_PATH_CONFIG.value] = new_path

    # Set the socks port of tor to a new value
    def _set_socks_port(new_port):
        """This function will set the socks port of tor to a new socks port. The port must be a positive integer."""
        global tor_subprocess
        try:
            if int(new_port) >= 0:
                if tor_subprocess and not tor_subprocess.poll():
                    tor_subprocess.kill
                    tor_subprocess = None
                script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.SOCKS_PORT_CONFIG.value] = int(new_port)
        except ValueError as e:
            print(e)

    # Set the control port of tor to a new value
    def _set_control_port(new_port):
        """This function will set the control port of tor to a new control port. The port must be a positive integer."""
        global tor_subprocess
        try:
            if int(new_port) >= 0:
                if tor_subprocess and not tor_subprocess.poll():
                    tor_subprocess.kill
                    tor_subprocess = None
                script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.CONTROL_PORT_CONFIG.value] = int(new_port)
        except ValueError as e:
            print(e)

    # Helper function to return a list of elements as a string with elements separated by whitespaces
    def _to_pretty_string(some_list):
        """This function takes the parsed list and prints its elements separated by whitespaces"""
        some_list_string = ""

        if not isinstance(some_list, list):
            return some_list_string

        for item in some_list:
            some_list_string = some_list_string + "%s," % str(item)
        return some_list_string.rstrip(",")

    # Helper function to take a string of simple elements delimited by a space and split them to create a list
    def _read_pretty_string(string_input):
        """
        This function takes a simple string input that represents a list of items delimited by whitespaces
        and returns a list
        :return: Returns the list of elements
        """
        if not isinstance(string_input, str):
            return []

        input_list = string_input.split(",")
        return input_list

    # Function that exports the config file
    def _export_config():
        """
        This function exports the configuration of the script when called
        """
        # Take the path to the file
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        # Create the config parser
        config = configparser.ConfigParser()

        # In the general values section add the chromedriver path, the wkhtmltopdf path, the run_headless option
        # max_threads and search_terms
        config[SectionsEnum.GENERAL_SECTION.value] = {}

        config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value] = \
            script_config[ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value]

        config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value] = \
            script_config[ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value]

        config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.RUN_HEADLESS_CONFIG.value] = \
            str(script_config[ConfigsEnum.RUN_HEADLESS_CONFIG.value])

        config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.MAX_THREADS_CONFIG.value] = \
            str(script_config[ConfigsEnum.MAX_THREADS_CONFIG.value])

        # We cannot save a list in the list format so we need to create a string with the elements and delimit them
        # with a whitespace
        config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.SEARCH_TERMS_CONFIG.value] = \
            _to_pretty_string(script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value])

        # Now we change our attention to Tor Config where we export use_tor, tor_path, socks_port and control_port
        config[SectionsEnum.TOR_SECTION.value] = {}

        config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.USE_TOR_CONFIG.value] = \
            str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value])

        config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.TOR_PATH_CONFIG.value] = \
            str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.TOR_PATH_CONFIG.value])

        config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.SOCKS_PORT_CONFIG.value] = \
            str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.SOCKS_PORT_CONFIG.value])

        config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.CONTROL_PORT_CONFIG.value] = \
            str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.CONTROL_PORT_CONFIG.value])

        # Because the scrapper is represented by a tuple of scrapper name and class name
        # we store the scrapper settings in a section
        config[SectionsEnum.SCRAPPERS_SECTION.value] = {}
        aux_scrapper_list = script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].get_modules()
        for scrapper in aux_scrapper_list:
            config[SectionsEnum.SCRAPPERS_SECTION.value][scrapper[0]] = scrapper[1]

        try:
            if not os.path.isfile(config_path):
                with open(config_path, 'w+') as configfile:
                    config.write(configfile)
            else:
                with open(config_path, 'w') as configfile:
                    config.write(configfile)
        except IOError as e:
            print("Could not export configuration.")
            print(e)
        except Exception as e:
            print("Could not export configuration.")
            print(e)

    # Function that loads a configuration file if it exists
    def _load_config():
        # Take the path to the file
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

        # If the file does not exist, print and return
        if not os.path.isfile(config_path):
            print("Config file does not exist.")
            return

        global tor_subprocess
        if tor_subprocess and not tor_subprocess.poll():
            tor_subprocess.kill
            tor_subprocess = None

        config = configparser.ConfigParser()
        try:
            # Read the file
            config.read(config_path)
            # Take the scrappers configuration section
            aux_scrappers_list = config[SectionsEnum.SCRAPPERS_SECTION.value]

            # Reinitialise the scrapper queue and put elements from the list
            script_config[ConfigsEnum.SCRAPPERS_CONFIG.value] = ScrapperQueue()
            for item in aux_scrappers_list:
                script_config[ConfigsEnum.SCRAPPERS_CONFIG.value]\
                    .put(item, config[SectionsEnum.SCRAPPERS_SECTION.value][item])

            # Take from general section the chromedriver_path, wkhmtltopdf path, run_headless variable, max_threads
            # and search_terms

            script_config[ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value] = \
                config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value]

            script_config[ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value] = \
                config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value]

            script_config[ConfigsEnum.RUN_HEADLESS_CONFIG.value] = \
                config[SectionsEnum.GENERAL_SECTION.value].getboolean(ConfigsEnum.RUN_HEADLESS_CONFIG.value)

            # Read the maximum number of threads and try to convert it into int
            script_config[ConfigsEnum.MAX_THREADS_CONFIG.value] = \
                int(config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.MAX_THREADS_CONFIG.value])

            # Take the search terms string and split it using the whitespace delimiter
            script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value] = \
                _read_pretty_string(config[SectionsEnum.GENERAL_SECTION.value][ConfigsEnum.SEARCH_TERMS_CONFIG.value])

            # Now take the tor config that contains use_tor, tor_path, socks_port and control_port
            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value] = \
                config[SectionsEnum.TOR_SECTION.value].getboolean(ConfigsEnum.USE_TOR_CONFIG.value)

            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.TOR_PATH_CONFIG.value] = \
                config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.TOR_PATH_CONFIG.value]

            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.SOCKS_PORT_CONFIG.value] = \
                int(config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.SOCKS_PORT_CONFIG.value])

            script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.CONTROL_PORT_CONFIG.value] = \
                int(config[SectionsEnum.TOR_SECTION.value][ConfigsEnum.CONTROL_PORT_CONFIG.value])

        except IOError as e:
            print("Could not load configuration.")
            print(e)
        except KeyError as e:
            print("Could not load configuration.")
            print(e)
        except ValueError as e:
            print("Could not load configuration.")
            print(e)
        except Exception as e:
            print("Could not load configuration.")
            print(e)

    # Print and handle configuration
    def _check_config():
        """This function will print the actual configuration and will let handle changing config"""
        print("Current configuration is:")
        print(SectionsEnum.GENERAL_SECTION.value)
        print("%s = %s" % (ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value,
                           script_config[ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value]))
        print("%s = %s" % (ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value,
                           script_config[ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value]))
        print("%s = %s" % (ConfigsEnum.RUN_HEADLESS_CONFIG.value,
                           str(script_config[ConfigsEnum.RUN_HEADLESS_CONFIG.value])))
        print("%s = %s" % (ConfigsEnum.MAX_THREADS_CONFIG.value,
                           str(script_config[ConfigsEnum.MAX_THREADS_CONFIG.value])))
        print("%s = %s" % (ConfigsEnum.SEARCH_TERMS_CONFIG.value,
                           _to_pretty_string(script_config[ConfigsEnum.SEARCH_TERMS_CONFIG.value])))

        print(SectionsEnum.TOR_SECTION.value)
        print("%s = %s" % (ConfigsEnum.USE_TOR_CONFIG.value,
                           str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.USE_TOR_CONFIG.value])))
        print("%s = %s" % (ConfigsEnum.TOR_PATH_CONFIG.value,
                           script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.TOR_PATH_CONFIG.value]))
        print("%s = %s" % (ConfigsEnum.SOCKS_PORT_CONFIG.value,
                           str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.SOCKS_PORT_CONFIG.value])))
        print("%s = %s" % (ConfigsEnum.CONTROL_PORT_CONFIG.value,
                           str(script_config[ConfigsEnum.TOR_CONFIG.value][ConfigsEnum.CONTROL_PORT_CONFIG.value])))

        print(SectionsEnum.SCRAPPERS_SECTION.value)
        print("%s = %s" % (ConfigsEnum.SCRAPPERS_CONFIG.value,
                           script_config[ConfigsEnum.SCRAPPERS_CONFIG.value].show_modules()))

    # Parse the received command and handle it
    def _handle_command(last_command):
        """This function will parse the received command and handle it"""
        command_pieces = last_command.split(" ")
        if len(command_pieces) == 1:
            if command_pieces[0].lower() == CommandsEnum.HELP_COMMAND.value:
                _print_help()
            elif command_pieces[0].lower() == CommandsEnum.START_COMMAND.value:
                _start_scrappers()
            elif command_pieces[0].lower() == CommandsEnum.CONFIG_COMMAND.value:
                _check_config()
            elif command_pieces[0].lower() == CommandsEnum.EXPORT_COMMAND.value:
                _export_config()
            elif command_pieces[0].lower() == CommandsEnum.LOAD_COMMAND.value:
                _load_config()
            else:
                _invalid_command()
        elif len(command_pieces) == 3:
            if command_pieces[0].lower() == CommandsEnum.ADD_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.SEARCH_TERM_OPTION.value:
                _add_searchterm(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.DELETE_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.SCRAPPER_OPTION.value:
                _delete_scrapper(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.DELETE_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.SEARCH_TERM_OPTION.value:
                _delete_searchterm(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.MAX_THREADS_OPTION.value:
                _set_max_threads(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.CHROMEDRIVER_PATH_OPTION.value:
                _set_chromedriver_path(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.WKHTMLTOPDF_PATH_OPTION.value:
                _set_wkhtmltopdf_path(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.RUN_HEADLESS_OPTION.value:
                _set_run_headless(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.USE_TOR_OPTION.value:
                _set_use_tor(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.TOR_PATH_OPTION.value:
                _set_tor_path(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.SOCKS_PORT_OPTION.value:
                _set_socks_port(command_pieces[2])
            elif command_pieces[0].lower() == CommandsEnum.SET_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.CONTROL_PORT_OPTION.value:
                _set_control_port(command_pieces[2])
            else:
                _invalid_command()
        elif len(command_pieces) == 4:
            if command_pieces[0].lower() == CommandsEnum.ADD_COMMAND.value \
                    and command_pieces[1].lower() == OptionsEnum.SCRAPPER_OPTION.value:
                _add_scrapper(command_pieces[2], command_pieces[3])
            else:
                _invalid_command()
        else:
            _invalid_command()

    # Print all the lines that have "Bootstrapped" in them from tor
    def _print_bootstrap_lines(line):
        if "Bootstrapped " in line:
            print(line)

    def _initialise_script():
        global worker_threads, script_config, tor_subprocess, modules_lock
        # Initialise modules to be consumed variable with empty list
        # This is a blocking queue which will store all the modules to be run later one by one
        scrappers_to_be_consumed = ScrapperQueue()

        # This variable will hold the worker thread
        worker_threads = []

        # Max number of threads - 0 means unlimited
        max_threads = 1

        # This variable will hold the search terms
        search_terms = ["firmware", "dump", "flash"]

        # Control Port = 9051 default
        control_port = 9051

        # Socks port = 9050 default
        socks_port = 9050

        # Use tor default True
        use_tor = True

        # Tor path default
        tor_path = "res/tor/Tor/tor.exe"

        # Chrome driver default path
        chromedriver_path = "res/chromedriver.exe"

        # Run headless
        run_headless = False

        # WKHTMLTOPDF default path
        wkhtmltopdf_path = "res/wkhtmltopdf/bin/wkhtmltopdf.exe"

        tor_config = {
            ConfigsEnum.USE_TOR_CONFIG.value: use_tor,
            ConfigsEnum.TOR_PATH_CONFIG.value: tor_path,
            ConfigsEnum.CONTROL_PORT_CONFIG.value: control_port,
            ConfigsEnum.SOCKS_PORT_CONFIG.value: socks_port
        }

        script_config = {
            ConfigsEnum.SCRAPPERS_CONFIG.value: scrappers_to_be_consumed,
            ConfigsEnum.MAX_THREADS_CONFIG.value: max_threads,
            ConfigsEnum.SEARCH_TERMS_CONFIG.value: search_terms,
            ConfigsEnum.CHROMEDRIVER_PATH_CONFIG.value: chromedriver_path,
            ConfigsEnum.RUN_HEADLESS_CONFIG.value: run_headless,
            ConfigsEnum.WKTHTMLTOPDF_PATH_CONFIG.value: wkhtmltopdf_path,
            ConfigsEnum.TOR_CONFIG.value: tor_config
        }

        tor_subprocess = None

        modules_lock = threading.Lock()

    # ------------------------ SCRIPT RUNNING -------------------------------------

    # Set handlers for signals
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    _initialise_script()

    # If config.ini does not exist, let the user know the defaults will be used
    expected_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    if not os.path.isfile(expected_config_path):
        print("Could not find %s." % expected_config_path)
        print("Default configuration is in place. Type %s to check configuration." % CommandsEnum.CONFIG_COMMAND.value)
    else:
        print("Configuration was found. Trying to load config.")
        _load_config()

    print("Type %s to see a list of available commands." % CommandsEnum.HELP_COMMAND.value)
    while 1:
        _handle_command(input("Please input a command:\n"))

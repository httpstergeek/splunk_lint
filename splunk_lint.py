__author__ = 'x243'

# Currently require a splunk_cycle.cfg file to run
#
#


import logging
import logging.handlers
import subprocess
from ConfigParser import ConfigParser

import os


def setup_logger(level):
    """
        @param level: Logging level
        @type level: logger object
        @rtype: logger object
    """
    logger = logging.getLogger('splunk_lint')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)
    file_handler = logging.handlers.RotatingFileHandler(os.path.join('splunk_lint.log'), maxBytes=5000000,backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    logger.addHandler(consolehandler)
    return logger

logger = setup_logger(logging.INFO)


def process(command):
    """
    @param command: list of commands to run
    @type command: list
    """
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout, stderr

def getconfig(objfile, stanza):
    """
        Gets custom config file
        @param objfile: absolute path of config file
        @type objfile: str
        @param stanza: config option
        @type str: str
    """
    executepath = os.path.dirname(__file__)
    filepath = os.path.join(executepath, objfile)
    config = ConfigParser()
    settings = dict()
    try:
        config.read(filepath)
        options = config.options(stanza)
        for option in options:
            settings[option] = config.get(stanza, option)
    except Exception, e:
        return dict(message=e)
    return settings

if __name__ == '__main__':
    # Attempts to load config file
    try:
        command = []
        configfile = os.path.basename(__file__).replace('.py', '.cfg')
        print configfile
        splunkconfig = getconfig(configfile, 'splunk')
        command.append(splunkconfig['splunk_path'])
    except Exception as e:
        logger.info(e)
        exit(1)
    command.append('restart')
    stdout, stderr = process(command)
    print stdout

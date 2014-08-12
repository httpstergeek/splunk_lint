__author__ = 'x243'

#!/usr/bin/env python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
# written by: Bernardo Macias ( httpstergeek@httpstergeek.com )

# Currently require a splunk_lint.cfg file to run
#
#


import logging
import logging.handlers
import subprocess
import argparse
from shutil import rmtree, copytree, ignore_patterns
from ConfigParser import ConfigParser
import re
from time import sleep
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
    # retrieve command line args
    parser = argparse.ArgumentParser(description='Copies Repo to Splunk App directory.  Use splunk_lint.cfg configure splunk and repo locations')
    parser.add_argument('--repo', help='name of repo', required=True)
    args = parser.parse_args()

    # get pid
    pid = str(os.getpid())
    execute_path = os.path.dirname(os.path.realpath(__file__))
    pidfile = os.path.join(execute_path, 'pid')
    logger.info('verify_status=%s build_name=%s' % ('start', args.repo))
    # Attempts to load config file and generate pid file
    try:
        cnt = 0
        while 5 >= cnt :
            file_exists = os.path.isfile(pidfile)
            if file_exists:
                logger.info('verify_status=%s build_name=%s' % ('wait', args.repo))
                cnt += 1
                sleep(60)
            elif file_exists and 5 >= cnt:
                logger.info('verify_status=%s build_status=%s build_name=%s' % ('end','fail', args.repo))
                exit(2)
            else:
                logger.info('write_pid=%s' % pidfile)
                file(pidfile, 'w').write(pid)
                break

        command = []
        config_file = os.path.basename(__file__).replace('.py', '.cfg')
        splunk_config = getconfig(config_file, 'splunk')
        splunk_path = splunk_config['splunk_path']
        repo_path = os.path.join(splunk_config['repo_path'], args.repo)
        pattern = splunk_config['pattern']
        command.append(os.path.join(splunk_path, 'bin', 'splunk'))
    except Exception as e:
        logger.info(e)
        os.unlink(pidfile)
        exit(1)

    # validate repo exists and copies to Splunk App Dir
    if os.path.isdir(repo_path):
        splunk_apps = os.path.join(splunk_path, 'etc', 'apps')
        copy_location = os.path.join(splunk_apps, args.repo)
        msg = 'copying src=%s dest=%s' % (repo_path, copy_location)
        logger.info(msg)
        if os.path.isdir(copy_location):
            logger.info('cleaning previous build=%s' % args.repo)
            rmtree(copy_location)
        else:
            copytree(repo_path, copy_location, symlinks=True, ignore=ignore_patterns('.git', '.gitignore'))
    else:
        msg = '%s not found' % repo_path
        logger.info('')
        os.unlink(pidfile)
        exit(1)

    # restarting splunk
    command.append('restart')
    command.append('--no-prompt')
    logger.info('verify_status=%s build_name=%s' % ('running', args.repo))
    stdout, stderr = process(command)
    errormatch = re.compile(pattern)
    output = stdout.splitlines()

    # Validating configurations
    err_flag = False
    logger.info('verify_status=%s build_name=%s' % ('validating', args.repo))
    if stderr:
        stderr = stderr.rstrip(' \t\n\r').replace('\n', ' ')
        logger.info(re.sub(r'\'(/[^/]+){4}/', ' ', stderr))
    for line in output:
        if errormatch.search(line):
            logger.info(re.sub(r'\s(/[^/]+){4}/', ' ', line.strip(' \t\n\r')))
            err_flag = True
    if stderr or err_flag:
        msg = 'verify_status=%s build_status=%s build_name=%s' % ('completed', 'fail', args.repo)
        exit_code = 2
    else:
        exit_code = 0
        msg = 'verify_status=%s build_status=%s build_name=%s' % ('completed', 'success', args.repo)
    logger.info(msg)

    msg = 'removing build_name=%s dest=%s' % (args.repo, copy_location)
    logger.info(msg)
    rmtree(copy_location)
    logger.info('remove_pid=%s' % pidfile)
    os.unlink(pidfile)
    exit(exit_code)



#!/usr/bin/python
#commons.py

import json
import os
import re
import subprocess
import sys
from enum import Enum

from pydispatch import dispatcher

from flow.logger import Logger


class Commons:
    quiet = False

content_json = 'application/json'
build_config_file = 'buildConfig.json'
forward_slash = '/'
content_oct_stream = 'application/octet-stream'
clazz = 'commons'


def flush_out(string):
    method = 'flush_out'
    print_msg(clazz, method, string)
    sys.stdout.flush()


def byteify(input_str):
    if isinstance(input_str, dict):
        return {byteify(key): byteify(value)
                for key, value in input_str.items()}
    elif isinstance(input_str, list):
        return [byteify(element) for element in input_str]
    elif isinstance(input_str, str):
        return input_str.encode('utf-8')
    else:
        return input_str


# TODO this could probably be moved to the abc for code repo
def extract_story_id_from_commit_messages(commit_messages):
    method = 'extract_story_id_from_commit_messages'
    story_list = []

    for commit_string in commit_messages:
        # Do we need this anymore?
        #try:
        #    commit_string = commit_string.decode('utf8')
        #except:
        #    print_msg(clazz, method, 'commit message is already string')
        
        # check if there is a starting bracket and if there are balanced brackets
        if commit_string.count('[') > 0 and commit_string.count('[') == commit_string.count(']'):
            # for each starting bracket
            for m in re.finditer('\[', commit_string):
                # find the next subsequent ending bracket
                ending_bracket = commit_string.find(']', m.start())
                # find the contents between the brackets
                stories = commit_string[m.start()+1:ending_bracket]

                # verify there isn't a embedded bracket, if so just skip this one and keep marching.
                if stories.find('[') == -1:  # there is a nested starting bracket
                    # now dig out the number in single number format or multiple separated by commas.
                    r = re.compile('[0-9,]+(,[0-8]+)*,?')
                    stories = ''.join(filter(r.match, stories))

                    for story in [_f for _f in stories.split(',') if _f]:
                        # split out by comma.
                        if story not in story_list:
                            story_list.append(story)

    print_msg(clazz, method, "Story list: {}".format(story_list))
    return story_list


def print_msg(class_name, method, message, level='DEBUG'):
    if level.lower() != 'error' and Commons.quiet:
        return

    log_level = '[' + level + ']'
    log_message = '{:7s} {:11s}  {:35s} {!s:s}'.format(log_level, class_name, method, message)
    try:
        print(log_message)
        Logger(log_message)
    except:
        print(log_message.encode('utf-8'))

    if level == 'ERROR':
        SIGNAL = 'publish-error-signal'
        sender = {}
        new_message = ''.join(str(v) for v in message)
        dispatcher.send(signal=SIGNAL, sender=sender, message=new_message, class_name=class_name, method_name=method)


def write_to_file(path, text, open_func=open, mode="a"):
    with open_func(path, mode) as f:
        f.write(text)


def get_files_of_type_from_directory(file_type, directory):
    out = os.listdir(directory)
    out = [os.path.join(directory, element) for element in out]
    out = [file for file in filter(os.path.isfile, out) if file.lower().endswith(file_type)]

    out = [os.path.basename(file) for file in filter(os.path.isfile, out)]
    return out


# TODO convert all popens that need decoding to call this
def execute_command(cmd):
    process = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # output from subprocess is always a unicode bytearray and not ascii
    # need to read it and go ahead and convert it to a string
    output = process.stdout.read().decode("UTF8")
    return output


def verify_version(config):
    method = 'verify_version'

    if config.version_number is None:
        print_msg(clazz, method, 'Version not defined.  Is your repo tagged with a version number?', 'ERROR')
        exit(1)


class DeploymentState(Enum):
    failure = 'fail'
    success = 'success'


class Object:
    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)



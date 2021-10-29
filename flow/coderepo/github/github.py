#!/usr/bin/python
# github.py

import json
import os
import re
import shutil
import subprocess
import tarfile
import time
import datetime

import requests
from flow.buildconfig import BuildConfig
from flow.coderepo.code_repo_abc import Code_Repo

import flow.utils.commons as cicommons
import flow.utils.commons as commons
from flow.utils.commons import Object


class GitHub(Code_Repo):
    clazz = 'GitHub'
    url = None
    org = None
    repo = None
    token = None
    config = BuildConfig
    http_timeout = 10

    all_tags_and_shas = []
    all_commits = []
    found_all_commits = False

    def __init__(self, config_override=None, verify_repo=True):
        method = '__init__'
        commons.print_msg(GitHub.clazz, method, 'begin')

        # check if we provided an override
        if config_override is not None:
            self.config = config_override

        if verify_repo is True:
            self._load_github_token()

            #self._refresh_tags()

            self._verify_required_attributes()

            self._verify_repo_existence(GitHub.url, GitHub.org, GitHub.repo)

        commons.print_msg(GitHub.clazz, method, 'end')

    def _load_github_token(self):
        method = '_load_github_token'
        commons.print_msg(GitHub.clazz, method, 'begin')

        GitHub.token = os.getenv('GITHUB_TOKEN')

        if not GitHub.token:
            commons.print_msg(GitHub.clazz, method, "No github token found.  If your repo doesn't allow anonymous "
                                                    "access, some operations may fail. To define a token, please set "
                                                    "environment variable 'GITHUB_TOKEN'", 'WARN')

        commons.print_msg(GitHub.clazz, method, 'end')

    def _refresh_tags(self):
        method = '_refresh_tags'
        commons.print_msg(GitHub.clazz, method, 'getting latest tags')

        pull_tags_cmd = "git pull --tags"
        pull_tags = subprocess.Popen(pull_tags_cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        pull_tags_outputs, pull_tags_errs = pull_tags.communicate(timeout=300)

        for tag_line in pull_tags_outputs.splitlines():
            commons.print_msg(GitHub.clazz, method, tag_line.decode("utf-8"))

    def _verify_required_attributes(self):
        method = '_verify_required_attributes'

        try:
            # noinspection PyStatementEffect
            self.config.json_config['github']
            GitHub.url = self.config.json_config['github']['URL']
            GitHub.org = self.config.json_config['github']['org']
            GitHub.repo = self.config.json_config['github']['repo']
        except KeyError as e:
            commons.print_msg(GitHub.clazz, method, "The build config associated with github is missing, {}."
                              .format(e), 'ERROR')
            exit(1)

    def _verify_repo_existence(self, url, org, repo, token=None):
        method = '_verify_repo_existence'
        commons.print_msg(GitHub.clazz, method, 'begin')

        repo_url = url + '/' + org + '/' + repo

        if token is None:
            token = GitHub.token

        if token is not None:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json,
                       'Authorization': ('token ' + token)}
        else:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json}

        commons.print_msg(GitHub.clazz, method, repo_url)

        retries = 0
        finished = False
        while not finished:
            try:
                resp = requests.get(repo_url, headers=headers, timeout=self.http_timeout)
                finished = True
            except requests.ConnectionError:
                commons.print_msg(GitHub.clazz, method, "Request to GitHub timed out, retrying...")
                if retries < 2:
                    time.sleep(retries * 5)
                    retries += 1
                    continue
                commons.print_msg(GitHub.clazz, method, "Request to GitHub timed out.", "ERROR")
                exit(1)
            except Exception as e:
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {}, retrying".format(e))
                if retries < 2:
                    time.sleep(retries * 5)
                    retries += 1
                    continue
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {}".format(e), "ERROR")
                exit(1)

        # noinspection PyUnboundLocalVariable
        commons.print_msg(GitHub.clazz, method, resp)

        if resp.status_code != 200:
            commons.print_msg(GitHub.clazz, method, "Failed to access github location {url}\r\n Response: {rsp}"
                              .format(url=repo_url,
                                     rsp=resp.text),
                             "ERROR")
            exit(1)

        commons.print_msg(GitHub.clazz, method, 'end')

    def add_tag_and_release_notes_to_github(self, new_version_tag_array, release_notes=None):
        # TODO this needs to be split out and better unit testing added.
        # testing is hard because json attributes are not ordered.

        method = 'add_tag_and_release_notes_to_github'
        commons.print_msg(GitHub.clazz, method, 'begin')

        me = Object()
        me.tag_name = self.convert_semver_tag_array_to_semver_string(new_version_tag_array)
        me.target_commitish = self.config.build_env_info['associatedBranchName']
        me.name = self.convert_semver_tag_array_to_semver_string(new_version_tag_array)

        if release_notes is not None and len(release_notes) > 0:
            me.body = release_notes
        else:
            me.body = 'No Release Notes'

        me.draft = False
        me.prerelease = True

        # release builds will have a build index of 0.
        if self._is_semver_tag_array_release_or_snapshot(new_version_tag_array) == 'release':
            me.prerelease = False

        tag_and_release_note_payload = me.to_JSON()

        url_params = {'org': self.org, 'repo': self.repo}
        commons.print_msg(GitHub.clazz, method, self.url)
        commons.print_msg(GitHub.clazz, method, self.org)
        commons.print_msg(GitHub.clazz, method, self.repo)

        release_url = self.url + '/' + self.org + '/' + self.repo + '/releases'

        commons.print_msg(GitHub.clazz, method, release_url)
        commons.print_msg(GitHub.clazz, method, tag_and_release_note_payload)
        commons.print_msg(GitHub.clazz, method, ("?", url_params))

        if self.token is not None:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json, 'Authorization': ('token ' + self.token)}
        else:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json}

        try:
            resp = requests.post(release_url, tag_and_release_note_payload, headers=headers, params=url_params, timeout=self.http_timeout)
        except requests.ConnectionError:
            commons.print_msg(GitHub.clazz, method, 'Request to GitHub timed out.', 'ERROR')
            exit(1)
        except:
            commons.print_msg(GitHub.clazz, method, "The github add release notes call failed to {} has failed".format(
                release_url), 'ERROR')
            exit(1)

        # noinspection PyUnboundLocalVariable
        if resp.status_code != 200 and resp.status_code != 201:
            commons.print_msg(GitHub.clazz, method, "The github add release notes call failed to {url}\r\n Response: {rsp}"
                              .format(url=release_url,
                                     rsp=resp.text),
                             'ERROR')
            exit(1)
        else:
            commons.print_msg(GitHub.clazz, method, resp.text)

        commons.print_msg(GitHub.clazz, method, 'end')

    def format_github_specific_release_notes_from_project_tracker_story_details(self, story_details):

        formatted_release_notes = None

        if story_details is not None and isinstance(story_details, list) and len(story_details) > 0:

            for i, release_note in enumerate(story_details):
                if release_note.get('story_type') == "release":
                    story_emoji = ":checkered_flag:"
                elif release_note.get('story_type') == "bug":
                    story_emoji = ":beetle:"
                elif release_note.get('story_type') == "chore":
                    story_emoji = ":wrench:"
                else:
                    story_emoji = ":star:"

                if formatted_release_notes is None:
                    formatted_release_notes = ""

                formatted_release_notes = formatted_release_notes + story_emoji + '<a href="' + release_note.get('url') + '">' + release_note.get('story_type') + ' **' + str(release_note.get('id')) + '**</a>' + ' ' + '\r\n ' + \
                               '&nbsp;&nbsp;&nbsp;&nbsp; **' + release_note.get('name') + '** \r\n ' + \
                               '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + (release_note.get('description').replace('\n', '\r\n &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;') + '\r\n' if release_note.get('description') is not None else '') + '\r\n\r\n'

        if formatted_release_notes is None:
            formatted_release_notes = 'No Release Notes'

        return formatted_release_notes

    def append_release_notes(self, release_name, text_to_append):

        method='append_release_notes'
        commons.print_msg(GitHub.clazz, method, 'begin')

        release_url_api = self.url + '/' + self.org + '/' + self.repo + '/releases/tags/' + release_name
        if self.token is None:
            commons.print_msg(GitHub.clazz, method, 'GITHUB_TOKEN is required to use this method.', 'ERROR')
            exit(1)
        headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json, 'Authorization': ('token ' + self.token)}

        try:
            resp = requests.get(release_url_api, headers=headers, timeout=self.http_timeout)
        except requests.ConnectionError:
            commons.print_msg(GitHub.clazz, method, 'Request to GitHub timed out.', 'ERROR')
            exit(1)
        except:
            commons.print_msg(GitHub.clazz, method, 'The github add release notes call failed to {} has failed'.format(
                release_url_api), 'ERROR')
            exit(1)

        # noinspection PyUnboundLocalVariable
        resp_json = resp.json()
        git_release_body = resp_json['body']
        git_release_id = resp_json['id']
        git_release_body += '\r\n\r\n%s' % text_to_append

        jsonMessage = {
            'body' : git_release_body
        }
        release_url_api = self.url + '/' + self.org + '/' + self.repo + '/releases/' + str(git_release_id)
        try:
            requests.patch(release_url_api, json=jsonMessage, headers=headers, timeout=self.http_timeout)
        except requests.ConnectionError:
            commons.print_msg(GitHub.clazz, method, 'Request to GitHub timed out.', 'ERROR')
            exit(1)
        except:
            commons.print_msg(GitHub.clazz, method, 'The github add release notes call failed to {} has failed'.format(
                release_url_api), 'ERROR')
            exit(1)

        commons.print_msg(GitHub.clazz, method, 'end')


    def calculate_next_semver(self, tag_type, bump_type, highest_version_array):
        method = 'calculate_next_semver'
        commons.print_msg(GitHub.clazz, method, 'begin')

        if highest_version_array is not None:
            commons.print_msg(GitHub.clazz, method, "Hightest Git tag: {}".format(
                             self.convert_semver_tag_array_to_semver_string(highest_version_array)))
        else:
            commons.print_msg(GitHub.clazz, method, "Hightest Git tag: {}".format(str(highest_version_array)))

        commons.print_msg(GitHub.clazz, method, "Bump Type: {}".format(str(bump_type)))
        commons.print_msg(GitHub.clazz, method, "Tag Type: {}".format(str(tag_type)))

        new_version_array = None

        if tag_type != "release" and tag_type != "snapshot":
            commons.print_msg(GitHub.clazz, method, "Tag types can only be 'release' or 'snapshot', instead {} was "
                                                   "provided.".format(str(tag_type)))
            exit(1)

        if tag_type == "release" and bump_type != "major" and bump_type != "minor" and bump_type != "bug":
            commons.print_msg(GitHub.clazz, method, "Bump types can only be 'major', 'minor' or 'bug', instead {} was "
                                                   "provided.".format(str(bump_type)))
            exit(1)

        if tag_type == 'snapshot':
            if highest_version_array is None:  # no previous snapshot
                new_version_array = [0, 0, 0, 1]
            else:
                commons.print_msg(GitHub.clazz, method, "Incrementing +buildnumber based on last tag, since it's a "
                                                       "snapshot build.")
                new_version_array = highest_version_array[:]
                # the build index is the 4th item (3rd position)
                new_version_array[3] = new_version_array[3]+1

        elif tag_type == 'release':
            commons.print_msg(GitHub.clazz, method, 'New Release semver')

            if highest_version_array is None:
                new_version_array = [0, 0, 0, 0]
            else:
                new_version_array = highest_version_array[:]
                # release builds don't have build numbers, so always set to zero
                new_version_array[3] = 0

            if bump_type == 'major':
                # if major rolls then set minor and bug to zero.
                new_version_array[0] = new_version_array[0]+1
                new_version_array[1] = 0
                new_version_array[2] = 0
            elif bump_type == 'minor':
                # if minor rolls then set bug to zero.
                new_version_array[1] = new_version_array[1]+1
                new_version_array[2] = 0
            elif bump_type == 'bug':
                new_version_array[2] = new_version_array[2]+1

        commons.print_msg(GitHub.clazz, method, "New Git tag {}".format(self.convert_semver_tag_array_to_semver_string(
            new_version_array)))
        commons.print_msg(GitHub.clazz, method, 'end')
        return new_version_array

    def calculate_next_calver(self, tag_type, bump_type, highest_version_array, year_format):
        #This version strategy is using a calver variant that looks like: year.major.patch+snapshot
        method = 'calculate_next_calver'
        commons.print_msg(GitHub.clazz, method, 'begin')

        if highest_version_array is not None:
            commons.print_msg(GitHub.clazz, method, "Hightest Git tag: {}".format(
                             self.convert_semver_tag_array_to_semver_string(highest_version_array)))
        else:
            commons.print_msg(GitHub.clazz, method, "Hightest Git tag: {}".format(str(highest_version_array)))

        if os.getenv('CALVER_BUMP_TYPE'):
            bump_type = os.getenv('CALVER_BUMP_TYPE')

        commons.print_msg(GitHub.clazz, method, "Bump Type: {}".format(str(bump_type)))
        commons.print_msg(GitHub.clazz, method, "Tag Type: {}".format(str(tag_type)))

        new_version_array = None

        if tag_type != "release" and tag_type != "snapshot":
            commons.print_msg(GitHub.clazz, method, "Tag types can only be 'release' or 'snapshot', instead {} was "
                                                   "provided.".format(str(tag_type)))
            exit(1)

        if tag_type == "release" and bump_type != "major" and bump_type != "patch":
            commons.print_msg(GitHub.clazz, method, "Bump types can only be 'major' or 'patch', instead {} was "
                                                   "provided.".format(str(bump_type)))
            exit(1)

        if tag_type == 'snapshot':
            if highest_version_array is None:  # no previous snapshot
                new_version_array = [0, 0, 0, 1]
            else:
                commons.print_msg(GitHub.clazz, method, "Incrementing +buildnumber based on last tag, since it's a "
                                                       "snapshot build.")
                new_version_array = highest_version_array[:]
                # the build index is the 4th item (3rd position)
                new_version_array[3] = new_version_array[3]+1

        elif tag_type == 'release':
            commons.print_msg(GitHub.clazz, method, 'New Release semver')

            if highest_version_array is None:
                new_version_array = [0, 0, 0, 0]
            else:
                new_version_array = highest_version_array[:]
                # release builds don't have build numbers, so always set to zero
                new_version_array[3] = 0

            if bump_type == 'major':
                # if major rolls then set minor and bug to zero.
                new_version_array[1] = new_version_array[1]+1
                new_version_array[2] = 0
            elif bump_type == 'patch':
                # if minor rolls then set bug to zero.
                new_version_array[2] = new_version_array[2]+1

        if year_format == 'short':
            #set year in version to be current 2 digit year
            new_version_array[0] = int(datetime.date.today().strftime("%y"))
        else:
            #set 4 digit year in version
            new_version_array[0] = datetime.date.today().year

        #Rollover to a new year resets the major, patch and snapshot values to 0 if a previous version existed.
        if highest_version_array is not None and new_version_array[0] > highest_version_array[0]:
            new_version_array[1] = 0
            new_version_array[2] = 0
            new_version_array[3] = 0

        commons.print_msg(GitHub.clazz, method, "New Git tag {}".format(self.convert_semver_tag_array_to_semver_string(
            new_version_array)))
        commons.print_msg(GitHub.clazz, method, 'end')
        return new_version_array

    def get_git_last_tag(self, start_from_version=None):
        method = "get_git_last_tag"
        commons.print_msg(GitHub.clazz, method, 'begin')

        if start_from_version is not None:
            return start_from_version

        last_tag = None
        if self.config.artifact_category.lower() == 'release':
            tags = self.get_all_tags_and_shas_from_github(need_release=1)
            for name, _ in tags:
                if '+' not in name:
                    last_tag = name
                    break
        else:
            tags = self.get_all_tags_and_shas_from_github(need_snapshot=1)
            for name, _ in tags:
                if '+' in name:
                    last_tag = name
                    break

        commons.print_msg(GitHub.clazz, method, "last_tag is: {}".format(last_tag))
        return last_tag

    def get_git_previous_tag(self, start_from_version=None):
        method = "get_git_previous_tag"
        commons.print_msg(GitHub.clazz, method, 'begin')

        beginning_tag = None

        
        if self.config.artifact_category.lower() == 'release':
            tags = self.get_all_tags_and_shas_from_github(need_release=2)
        else:
            tags = self.get_all_tags_and_shas_from_github(need_snapshot=2)
        if start_from_version is None:
            for name, _ in tags:
                if self.config.artifact_category.lower() == 'release' and '+' not in name:
                    beginning_tag = name
                    break
                elif self.config.artifact_category.lower() != 'release' and '+' in name:
                    beginning_tag = name
                    break
        else:
            beginning_tag = start_from_version
        
        commons.print_msg(GitHub.clazz, method, "starting with {}".format(beginning_tag))
        commons.print_msg(GitHub.clazz, method, "Category: " + self.config.artifact_category.lower())  
        found_tag = False
        for name, _ in tags:
            if found_tag:
                out_name = None
                if self.config.artifact_category.lower() == 'release' and '+' not in name:
                    out_name = name
                elif self.config.artifact_category.lower() != 'release' and '+' in name:
                    out_name = name
                if out_name is not None:
                    commons.print_msg(GitHub.clazz, method, name)
                    commons.print_msg(GitHub.clazz, method, 'end')
                    return out_name
            if name == beginning_tag:
                found_tag = True
        commons.print_msg(GitHub.clazz, method, 'tag not found, or was the first tag')
        return None

    def get_all_commits_from_github(self, start_from_sha=None):
        method = "get_all_commits_from_github"
        commons.print_msg(GitHub.clazz, method, 'begin')

        if len(GitHub.all_commits) > 0:
            if GitHub.found_all_commits:
                commons.print_msg(GitHub.clazz, method, 'All commits pulled, returning cached results')
                return GitHub.all_commits

            foundSha = False
            for commit in GitHub.all_commits:
                if commit['sha'] == start_from_sha:
                    foundSha = True
                    commons.print_msg(GitHub.clazz, method, 'The beginning sha is in our cached list')
            if foundSha:
                commons.print_msg(GitHub.clazz, method, 'Returning cached results')
                return GitHub.all_commits
            commons.print_msg(GitHub.clazz, method, 'Beginning sha is not in our cached list, pulling more commits')

        per_page = 100
        start_page = (len(GitHub.all_commits)//per_page)+1
        finished = False
        output = GitHub.all_commits
        branch = self.config.build_env_info['associatedBranchName']
            
        repo_url = GitHub.url + '/' + GitHub.org + '/' + GitHub.repo + '/commits?per_page=' + str(per_page) + '&page=' + str(start_page) + '&sha=' + str(branch)
        token = GitHub.token
        if token is not None:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json,
                        'Authorization': ('token ' + token)}
        else:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json}
        
        retries = 0

        while not finished:

            commons.print_msg(GitHub.clazz, method, repo_url)

            try:
                resp = requests.get(repo_url, headers=headers, timeout=self.http_timeout)
            except Exception as e:
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {}".format(e))
                if retries < 2:
                    time.sleep(retries * 5)
                    retries += 1
                    continue
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {}".format(e), "ERROR")
                exit(1)

            retries = 0

            if 'next' in resp.links:
                repo_url = resp.links['next']['url']
            else:
                GitHub.found_all_commits = True
                finished = True

            if resp.status_code != 200:
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {url}\r\n Response: {rsp}"
                                  .format(url=repo_url,
                                         rsp=resp.text),
                                 "ERROR")
                exit(1)
            else:
                #commons.print_msg(GitHub.clazz, method, resp.text)
                #commons.print_msg(GitHub.clazz, method, resp.json())
                simplified = []
                for commit in resp.json():
                    simplified.append({'sha': commit['sha'], 'commit': { 'message': commit['commit']['message'] } })
                    if commit['sha'] == start_from_sha:
                        commons.print_msg(GitHub.clazz, method, 'Found the beginning sha, stopping lookup')
                        finished = True
                output.extend(simplified)

        commons.print_msg(GitHub.clazz, method, '{} total commits'.format(len(output)))
        commons.print_msg(GitHub.clazz, method, 'end')

        GitHub.all_commits = output

        

        return output

    def _verify_tags_found(self, tag_list, need_snapshot, need_release, need_tag, need_base):
        found_snapshot = 0
        found_release = 0
        found_tag = need_tag is None
        
        for name, _ in tag_list:
            if need_snapshot > found_snapshot:
                if '+' in name:
                    found_snapshot += 1
            if need_release > found_release:
                if '+' not in name:
                    found_release += 1
            if not found_tag:
                if need_base:
                    if name.split("+")[0] == need_tag:
                        found_tag = True
                elif name == need_tag:
                    found_tag = True
            if found_snapshot >= need_snapshot and found_release >= need_release and found_tag:
                return True
        return False
    
    # if need_snapshot, need_release, and need_tag are all left as defaults,
    # this method will only pull one page of results.
    def get_all_tags_and_shas_from_github(self, need_snapshot=0, need_release=0, need_tag=None, need_base=False):
        method = "get_all_tags_and_shas_from_github"

        if len(GitHub.all_tags_and_shas) > 0:
            if self._verify_tags_found(GitHub.all_tags_and_shas, need_snapshot, need_release, need_tag, need_base):
                commons.print_msg(GitHub.clazz, method, 'Already pulled necessary tags, returning cached results')
                return GitHub.all_tags_and_shas
            commons.print_msg(GitHub.clazz, method, 'Necessary tags are not in our cached list, pulling more tags')
       
        per_page = 100
        start_page = (len(GitHub.all_tags_and_shas)//per_page)+1
        finished = False
        output = GitHub.all_tags_and_shas
        repo_url = GitHub.url + '/' + GitHub.org + '/' + GitHub.repo + '/tags?per_page=' + str(per_page) + '&page=' + str(start_page)
        token = GitHub.token

        if token is not None:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json,
                       'Authorization': ('token ' + token)}
        else:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json}

        retries = 0

        while not finished:
            commons.print_msg(GitHub.clazz, method, repo_url)

            try:
                resp = requests.get(repo_url, headers=headers, timeout=self.http_timeout)
            except Exception as e:
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {}".format(e))
                if retries < 2:
                    time.sleep(retries * 5)
                    retries += 1
                    continue
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {}".format(e), "ERROR")
                exit(1)

            retries = 0

            if 'next' in resp.links:
                repo_url = resp.links['next']['url']
            else:
                finished = True

            if resp.status_code != 200:
                commons.print_msg(GitHub.clazz, method, "Failed to access github location {url}\r\n Response: {rsp}"
                                  .format(url=repo_url,
                                         rsp=resp.text),
                                 "ERROR")
                exit(1)
            else:
                #commons.print_msg(GitHub.clazz, method, resp.text)
                #commons.print_msg(GitHub.clazz, method, resp.json())
                simplified = list(map(lambda obj: (obj['name'], obj['commit']['sha']), resp.json()))
                output.extend(simplified)
                if self._verify_tags_found(output, need_snapshot, need_release, need_tag, need_base):
                    commons.print_msg(GitHub.clazz, method, 'Found necessary tags, stopping lookup')
                    finished = True

        #commons.print_msg(GitHub.clazz, method, output)

        commons.print_msg(GitHub.clazz, method, '{} total tags'.format(len(output)))
        commons.print_msg(GitHub.clazz, method, 'end')
        GitHub.all_tags_and_shas = output

        return output

    def get_all_semver_tags(self, need_snapshot=0, need_release=0, need_tag=None, need_base=False):
        method = "get_all_semver_tags"
        all_tags_output = self.get_all_tags_and_shas_from_github(need_snapshot=need_snapshot, need_release=need_release, need_tag=need_tag, need_base=need_base)

        all_tags = all_tags_output#.splitlines()
        tag_data = []

        for tag, _ in all_tags:
            try:
                if BuildConfig.version_strategy == 'calver_year' and BuildConfig.calver_year_format == 'short':
                    tag_array = self.convert_semver_string_to_semver_tag_array(tag)
                    if len(tag_array[0]) <= 2:
                        tag_data.append(tag_array)
                else:
                    tag_data.append(self.convert_semver_string_to_semver_tag_array(tag))
            except Exception:
                commons.print_msg(GitHub.clazz, method, "This tag didn't parse right skipping: {} ".format(tag))

        tag_data.sort(reverse=True)
        GitHub.all_tags_sorted = tag_data
        return tag_data

    def get_highest_semver_tag(self):
        all_semver_tags = self.get_all_semver_tags()
        # index 0 is the highest order number
        if len(all_semver_tags) > 0:
            return all_semver_tags[0]
        else:
            return None

    def get_highest_semver_release_tag(self):
        all_semver_tags = self.get_all_semver_tags(need_release=1)
        # index 0 is the highest order semver number
        # since array is in order from highest version
        # to lowest version, then start at 0
        # and find the last release build
        for tag in all_semver_tags:
            if self._is_semver_tag_array_release_or_snapshot(tag) == 'release':
                return tag

        return None

    def get_highest_semver_snapshot_tag(self):
        all_semver_tags = self.get_all_semver_tags(need_snapshot=1)
        # index 0 is the highest order semver number
        # since array is in order from highest version
        # to lowest version, then start at 0
        # and find the last snapshot build
        for tag in all_semver_tags:
            if self._is_semver_tag_array_release_or_snapshot(tag) == 'snapshot':
                return tag

        return None

    def get_highest_semver_array_snapshot_tag_from_base(self, base_release_version):
        all_semver_tags = self.get_all_semver_tags(need_tag=self.convert_semver_tag_array_to_semver_string(base_release_version), need_base=True)
        # index 0 is the highest order semver number
        # since array is in order from highest version
        # to lowest version, then start at 0

        # There are three options to this effort:
        # Found a snapshot that matches the base, then return the highest
        # Found only a release that matches the base, no snapshots, return release
        # no base found, return base.

        found_tag = None
        for tag in all_semver_tags:
            if tag[0] == base_release_version[0] and tag[1] == base_release_version[1] and tag[2] == base_release_version[2]:
                # this could be a snapshot, or release, really don't care.
                # both are fine.
                found_tag = tag
                break

        return found_tag

    def _does_semver_tag_exist(self, tag_array):
        all_semver_tags = self.get_all_semver_tags(need_tag=self.convert_semver_tag_array_to_semver_string(tag_array))
        # index 0 is the highest order number
        if tag_array in all_semver_tags:
            return True
        else:
            return False

    def convert_semver_tag_array_to_semver_string(self, tag_array):
        if tag_array is None:
            return None

        tag_string = "v"
        tag_string += str(tag_array[0])  # major
        tag_string += "." + str(tag_array[1])  # minor
        tag_string += "." + str(tag_array[2])  # bug
        if len(tag_array) == 4 and tag_array[3] != 0:
            tag_string += "+" + str(tag_array[3])  # build
        return tag_string

    def convert_semver_string_to_semver_tag_array(self, tag_string):
        if tag_string is None:
            return None

        tag_array = []
        regex = "^v(\d+)\.(\d+).(\d+)(\+(\d+))?$"
        match = re.fullmatch(regex, tag_string.strip())
        if match:
            # major
            tag_array.append(int(match.group(1)))
            # minor
            tag_array.append(int(match.group(2)))
            # bug
            tag_array.append(int(match.group(3)))
            # build
            # group 3 is the "+digit" match
            # group 4 is the digit match sub group
            # so skip 3
            if match.group(5) is not None:
                tag_array.append(int(match.group(5)))
            else:
                tag_array.append(0)
        else:
            raise Exception("Tag format invalid v0.0.0[+0] instead it was: " + tag_string)

        return tag_array

    def verify_sem_ver_tag(self, tag):

        # None tags are valid (no tags for the repo)
        if tag is None:
            return True

        tag_string = self.convert_semver_tag_array_to_semver_string(tag)

        regex = "^v(\d+)\.(\d+).(\d+)(\+(\d+))?$"
        match = re.fullmatch(regex, tag_string.strip())
        if match:
            return True
        else:
            return False

    def get_all_git_commit_history_between_provided_tags(self, semver_array_beginning_version,
                                                         semver_array_ending_version=None):
        # if you set the semver_array_beginning_version to None, it will pull *ALL* history **be gentle**

        method = 'get_all_git_commit_history_between_provided_tags'
        commons.print_msg(GitHub.clazz, method, method)

        if self.verify_sem_ver_tag(semver_array_beginning_version) is False:
            commons.print_msg(GitHub.clazz, method, "Invalid beginning version defined {}".format(
                semver_array_beginning_version), 'ERROR')
            exit(1)

        if semver_array_ending_version is not None and self.verify_sem_ver_tag(semver_array_ending_version) is False:
            commons.print_msg(GitHub.clazz, method, "Invalid ending version defined {}".format(
                semver_array_ending_version), 'ERROR')
            exit(1)

        semver_array_beginning_version = self.convert_semver_tag_array_to_semver_string(semver_array_beginning_version)
        # noinspection PyTypeChecker
        semver_array_ending_version = self.convert_semver_tag_array_to_semver_string(semver_array_ending_version)

        # get all tags to get shas
        tags = self.get_all_tags_and_shas_from_github(need_tag=semver_array_beginning_version)
        ending_sha = ''
        beginning_sha = ''

        if semver_array_ending_version is not None:
            commons.print_msg(GitHub.clazz, method, semver_array_ending_version)
            filtered_tags = list(filter(lambda tag: tag[0] == semver_array_ending_version, tags))
            if len(filtered_tags) == 0:
                print("Version tag not found {}".format(semver_array_ending_version))
                commons.print_msg(GitHub.clazz, method, "Version tag not found {}".format(semver_array_ending_version),
                                 'ERROR')
                exit(1)
            else:
                beginning_sha = filtered_tags[0][1]
            ending_sha = filtered_tags[0][1]
        if semver_array_beginning_version is not None:
            commons.print_msg(GitHub.clazz, method, semver_array_beginning_version)
            filtered_tags = list(filter(lambda tag: tag[0] == semver_array_beginning_version, tags))
            if len(filtered_tags) == 0:
                print("Version tag not found {}".format(semver_array_beginning_version))
                commons.print_msg(GitHub.clazz, method, "Version tag not found {}".format(semver_array_beginning_version),
                                 'ERROR')
                exit(1)
            else:
                beginning_sha = filtered_tags[0][1]

        commons.print_msg(GitHub.clazz, method, ending_sha + ' , ' + beginning_sha)

        # get all commits here
        commits = self.get_all_commits_from_github(beginning_sha)
        trimmed_commits = []
        found_beginning = False

        if semver_array_beginning_version is None and semver_array_ending_version is None:  # Everything!
            commons.print_msg(GitHub.clazz, method, "No tag present. Pulling all git commit statements instead.")
            trimmed_commits = commits[:]
            found_beginning = True
        elif semver_array_ending_version is None:  # Everything since tag
            commons.print_msg(GitHub.clazz, method, "The first tag: {}".format(semver_array_beginning_version))
            for commit in commits:
                if commit['sha'] == beginning_sha:
                    found_beginning = True
                    break
                trimmed_commits.append(commit)
        else:  # Between two tags.  Mostly used when re-deploying old versions to send release notes
            commons.print_msg(GitHub.clazz, method, "The first tag: ".format(semver_array_beginning_version))
            commons.print_msg(GitHub.clazz, method, "The last tag: ".format(semver_array_ending_version))
            found_end = False
            for commit in commits:
                if commit['sha'] == ending_sha:
                    found_end = True
                if commit['sha'] == beginning_sha:
                    found_beginning = True
                    break
                if found_end:
                    trimmed_commits.append(commit)

        trimmed_commits = list(map(lambda current_sommit: "{} {}".format(current_sommit['sha'][0:7], current_sommit['commit']['message']), trimmed_commits))

        commons.print_msg(GitHub.clazz, method, "Number of commits found: {}".format(len(trimmed_commits)))
        if not found_beginning:
            branch = self.config.build_env_info['associatedBranchName']
            commons.print_msg(GitHub.clazz, method, "The commit sha {} could not be found in the commit history of branch '{}', so no tracker stories will be pulled.".format(beginning_sha, branch), 'WARN')
            commons.print_msg(GitHub.clazz, method, "This likely means tag {} was created on a branch other than {}.".format(semver_array_beginning_version, branch))
            trimmed_commits = []
        commons.print_msg(GitHub.clazz, method, 'end')
        return trimmed_commits

    def _is_semver_tag_array_release_or_snapshot(self, semver_array):
        # check the 0.0.0.x position.
        # if x == 0 then it is release
        # if x > 0 then it is snapshot.

        if semver_array[3] == 0:
            return 'release'
        elif semver_array[3] > 0:
            return 'snapshot'
        else:
            return None

    def download_code_at_version(self):
        method = "download_code_at_version"
        commons.print_msg(GitHub.clazz, method, "begin")

        artifact_to_download = self._get_artifact_url()

        artifact = self.config.version_number + '.tar.gz'

        commons.print_msg(GitHub.clazz, method, ("Attempting to download from github: {}".format(artifact_to_download)))

        if not os.path.exists(os.path.join(self.config.push_location, 'unzipped')):
            os.makedirs(os.path.join(self.config.push_location, 'unzipped'))

        download_path = self.config.push_location + "/" + artifact

        if GitHub.token is not None:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json, 'Authorization': ('token ' + GitHub.token)}
        else:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json}

        try:
            download_resp = requests.get(artifact_to_download, headers=headers)

            with open(download_path, 'wb') as f:
                for chunk in download_resp.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)

            tar = tarfile.open(self.config.push_location + '/' + artifact)
            tar.extractall(os.path.join(self.config.push_location, 'unzipped'))
            tar.close()

            self._copy_unzipped_file_to_deployment_directory()

        except Exception as ex:
            commons.print_msg(GitHub.clazz, method, "Failed to download {art}.  Error: {e}".format(art=artifact, e=ex),
                             'ERROR')
            exit(1)

        commons.print_msg(GitHub.clazz, method, "end")

    def _get_artifact_url(self):
        method = "_get_artifact_url"

        commons.print_msg(GitHub.clazz, method, "begin")

        if GitHub.token is not None:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json, 'Authorization': ('token ' + GitHub.token)}
        else:
            headers = {'Content-type': cicommons.content_json, 'Accept': cicommons.content_json}

        tag_information_url = GitHub.url.replace('\\', '/').rstrip('/') + '/' + self.org + '/' + self.repo + \
                              '/releases/tags/' + self.config.version_number

        commons.print_msg(GitHub.clazz, method, ("Retrieving Github information from " + tag_information_url))

        resp = requests.get(tag_information_url, headers=headers)

        if resp.status_code != 200:
            commons.print_msg(GitHub.clazz, method, ("Failed to access github tag information at " + tag_information_url + "\r\n Response: " + resp.text), "ERROR")
            exit(1)
        else:
            commons.print_msg(GitHub.clazz, method, resp.text)

        json_data = json.loads(resp.text)

        artifact_to_download = json_data['tarball_url']

        return artifact_to_download

        # return self.domainURL.replace('\\','/').rstrip('/') + '/' +  \
        #     self.org + '/' + \
        #     self.repo + '/archive/' + \
        #     self.config.version_number + \
        #     'tar.gz'

    def _copy_unzipped_file_to_deployment_directory(self):
        method = "_copy_unzipped_file_to_deployment_directory"
        commons.print_msg(GitHub.clazz, method, "begin")

        try:
            # github tar puts it in a parent directory.  Pull everything out of the parent directory
            if len([name for name in os.listdir(os.path.join(self.config.push_location, 'unzipped')) if os.path.isdir(os.path.join(self.config.push_location, 'unzipped', name))]) == 1:
                commons.print_msg(GitHub.clazz, method, "Github contents unzipped.  Copying out of parent directory. ")
                for current_dir in os.listdir(os.path.join(self.config.push_location, 'unzipped')):
                    if os.path.isdir(os.path.join(self.config.push_location, 'unzipped', current_dir)):
                        self._copy_tree(os.path.join(self.config.push_location, 'unzipped', current_dir),
                                        self.config.push_location+'/',
                                        False, None)

        except Exception as ex:
            print(ex)
            commons.print_msg(GitHub.clazz, method,
                              ("failed to move files from", os.path.join(self.config.push_location, 'unzipped'), "to", self.config.push_location), "ERROR")
            exit(1)

        commons.print_msg(GitHub.clazz, method, "end")

    def _copy_tree(self, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

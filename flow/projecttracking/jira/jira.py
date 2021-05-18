import base64
import json
import os
import re

import requests
from flow.buildconfig import BuildConfig
from flow.projecttracking.project_tracking_abc import Project_Tracking

import flow.utils.commons as commons
from flow.utils.commons import Object

#https://<site-url>/rest/api/3/<resource-name>
class Jira(Project_Tracking):
    clazz = 'Jira'
    token = None
    user = None
    project_keys = None
    jira_url = None
    jira_basic_auth = None
    config = BuildConfig
    http_timeout = 30

    def __init__(self, config_override=None):
        method = '__init__'
        commons.print_msg(Jira.clazz, method, 'begin')

        if config_override is not None:
            self.config = config_override

        Jira.token = os.getenv('JIRA_TOKEN')
        Jira.user = os.getenv('JIRA_USER')

        if not Jira.token:
            if not Jira.user:
                commons.print_msg(Jira.clazz, method, 'No jira user, jira token found in environment.  Did you define '
                                                     'environment variables \'JIRA_USER\' and \'JIRA_TOKEN\'?', 'ERROR') 
            else:
                commons.print_msg(Jira.clazz, method, 'No jira token found in environment.  Did you define '
                                                     'environment variable \'JIRA_TOKEN\'?', 'ERROR')
            exit(1)
        elif not Jira.user:
            commons.print_msg(Jira.clazz, method, 'No jira user found in environment.  Did you define '
                                                     'environment variable \'JIRA_USER\'?', 'ERROR')
            exit(1)

        # Check for jira url first in buildConfig, second try settings.ini

        try:
            jira_json_config = self.config.json_config['projectTracking']['jira']
            commons.print_msg(Jira.clazz, method, jira_json_config)
            # noinspection PyUnboundLocalVariable
            Jira.jira_url = jira_json_config['url']
        except KeyError as e:
            if e.args[0] == 'url':
                if self.config.settings.has_section('jira') and self.config.settings.has_option('jira', 'url'):
                    Jira.jira_url = self.config.settings.get('jira', 'url')
                else:
                    commons.print_msg(Jira.clazz, method, 'No jira url found in buildConfig or settings.ini.',
                                  'ERROR')
                    exit(1)
            else:
                commons.print_msg(Jira.clazz,
                                  method,
                                  "The build config associated with projectTracking is missing key {}".format(str(e)),
                                  'ERROR')
                exit(1)

        Jira.jira_basic_auth = base64.b64encode("{0}:{1}".format(Jira.user, Jira.token).encode('ascii')).decode('ascii')

        try:
            # since api call to get project data uses key or id just always call to fetch id.
            if jira_json_config.get('projectKey') is not None and jira_json_config.get('projectKeys') is not None:
                raise KeyError('projectKeys')
            elif jira_json_config.get('projectKey') is not None:
                project_data = self._retrieve_project_info(str(jira_json_config['projectKey']))
                Jira.project_keys = [(project_data['id'], project_data['key'])]
            elif jira_json_config.get('projectKeys') is not None:
                Jira.project_keys = []
                for project_key in jira_json_config.get('projectKeys'):
                    project_data = self._retrieve_project_info(str(project_key))
                    Jira.project_keys.append((project_data['id'], project_data['key']))
            else:
                raise KeyError('projectKey')
            
            commons.print_msg(Jira.clazz, method, Jira.project_keys)
        except KeyError as e:
            if e.args[0] == 'projectKeys':
                commons.print_msg(Jira.clazz,
                                  method,
                                  "The build config may only contain 'projectKey' for single project key"
                                  " or 'projectKeys' containing an array of project keys",
                                  'ERROR')
            else:
                commons.print_msg(Jira.clazz,
                                  method,
                                  "The build config associated with projectTracking is missing key {}".format(str(e)),
                                  'ERROR')
            exit(1)

        commons.print_msg(Jira.clazz, method, 'end')

    def get_details_for_all_stories(self, story_list):
        method = 'get_details_for_all_stories'
        commons.print_msg(Jira.clazz, method, 'begin')

        story_details = []
        commons.print_msg(Jira.clazz, method, story_list)

        for i, story_id in enumerate(story_list):
            story_detail = self._retrieve_story_detail(story_id)

            if story_detail is not None:
                story_details.append(story_detail)

        commons.print_msg(Jira.clazz, method, story_details)
        commons.print_msg(Jira.clazz, method, 'end')
        return story_details

    def _retrieve_project_info(self, project_id):
        method = '_retrieve_project_info'
        commons.print_msg(Jira.clazz, method, 'begin')

        json_data = None
        resp = None

        project_detail = {'url': '{0}/rest/api/3/project/{1}'.format(Jira.jira_url, project_id)}
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

        try:
            commons.print_msg(Jira.clazz, method, project_detail['url'])
            resp = requests.get(project_detail['url'], headers=headers, timeout=self.http_timeout)
        except requests.ConnectionError as e:
            commons.print_msg(Jira.clazz, method, "Failed retrieving project detail from call to {}".format(
                project_detail.get('url', '')), 'ERROR')
            commons.print_msg(Jira.clazz, method, e, 'ERROR')
            exit(1)

        if resp.status_code == 200:
            json_data = json.loads(resp.text)
            commons.print_msg(Jira.clazz, method, "Project Key: {key}, Project Id: {id}".format(key=json_data['key'], 
                                                                                                id=json_data['id']))
        else:
            commons.print_msg(Jira.clazz, method, "Failed retrieving project detail from call to {url}. \r\n "
                                                "Response: {response}".format(url=project_detail.get('url', ''),
                                                                            response=resp.text), 'WARN')

        commons.print_msg(Jira.clazz, method, 'end')
        return json_data


    def _retrieve_story_detail(self, story_id):
        method = '_retrieve_story_detail'
        commons.print_msg(Jira.clazz, method, 'begin')

        json_data = None
        resp = None

        story_detail = {'url': '{0}/rest/api/3/issue/{1}'.format(Jira.jira_url, story_id)}
        
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

        try:
            commons.print_msg(Jira.clazz, method, story_detail['url'])
            resp = requests.get(story_detail['url'], headers=headers, timeout=self.http_timeout)
        except requests.ConnectionError as e:
            commons.print_msg(Jira.clazz, method, "Failed retrieving story detail from call to {}".format(
                story_detail.get('url', '')), 'ERROR')
            commons.print_msg(Jira.clazz, method, e, 'ERROR')
            exit(1)
        
        if resp.status_code == 200:
            json_data = json.loads(resp.text)
            commons.print_msg(Jira.clazz, method, json_data)
        else:
            commons.print_msg(Jira.clazz, method, "Failed retrieving story detail from call to {url}. \r\n "
                                                         "Response: {response}".format(url=story_detail.get('url', ''),
                                                                                       response=resp.text), 'WARN')

        commons.print_msg(Jira.clazz, method, 'end')
        return json_data

    def tag_stories_in_commit(self, story_list):
        method = 'tag_stories_in_commit'
        commons.print_msg(Jira.clazz, method, 'begin')

        version = '{0}-{1}'.format(self.config.project_name, self.config.version_number)
        self._add_version_to_project(version)

        for story in story_list:
            self._add_version_to_story(story, version)

        commons.print_msg(Jira.clazz, method, 'end')

    def _add_version_to_project(self, version):
        method = '_add_version_to_project'
        commons.print_msg(Jira.clazz, method, 'begin')

        for idx, project_id in enumerate(self.project_keys):
            does_version_exist = self._determine_if_project_version_exists(project_id[0], version.lower())
            if does_version_exist:
                commons.print_msg(Jira.clazz, method, 'Version {version} already exists for project {project}, skipping.'.format(version=version.lower(), project=project_id[1]))
            else:
                version_to_post = Object()
                version_to_post.projectId = project_id[0]
                version_to_post.name = version.lower()
                
                jira_url = "{url}/rest/api/3/version".format(url=Jira.jira_url)

                headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                        'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

                commons.print_msg(Jira.clazz, method, 'Post body for create project version:\n{}'.format(version_to_post.to_JSON()))

                try:
                    resp = requests.post(jira_url, version_to_post.to_JSON(), headers=headers, timeout=self.http_timeout)

                    if resp.status_code != 201:
                        commons.print_msg(Jira.clazz, method, "Unable to create version {version} for project {project} \r\n "
                                                            "Response: {response}".format(version=version, project=project_id[1], response=resp.text), 'WARN')
                    else: 
                        commons.print_msg(Jira.clazz, method, resp.text)
                except requests.ConnectionError as e:
                    commons.print_msg(Jira.clazz, method, 'Connection error. ' + str(e), 'WARN')
                except Exception as e:
                    commons.print_msg(Jira.clazz, method, "Unable to create version {version} for project {project}".format(
                        version=version, project=project_id[1]), 'WARN')
                    commons.print_msg(Jira.clazz, method, e, 'WARN')

        commons.print_msg(Jira.clazz, method, 'end')

    def _determine_if_project_version_exists(self, project_id, version):
        method = '_determine_if_project_version_exists'
        commons.print_msg(Jira.clazz, method, 'begin')

        jira_url = "{url}/rest/api/3/project/{project}/versions".format(url=Jira.jira_url, project=project_id)

        headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                    'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

        version_exists = False

        try:
            resp = requests.get(jira_url, headers=headers, timeout=self.http_timeout)
            if resp.status_code != 200:
                    commons.print_msg(Jira.clazz, method, "Unable to fetch versions for project {project} \r\n "
                                                          "Response: {response}".format(project=project_id, response=resp.text), 'WARN')
                    return False
            else:
                project_versions = json.loads(resp.text)
                version_exists = any(v['name'] == version for v in project_versions)
        except requests.ConnectionError as e:
                commons.print_msg(Jira.clazz, method, 'Connection error. ' + str(e), 'WARN')
        except Exception as e:
            commons.print_msg(Jira.clazz, method, "Unable to fetch versions for project {project} \r\n "
                                                          "Response: {response}".format(project=project_id, response=resp.text), 'WARN')
            commons.print_msg(Jira.clazz, method, e, 'WARN')

        commons.print_msg(Jira.clazz, method, 'end')
        return version_exists

    def _add_version_to_story(self, story_id, version):
        method = '_add_version_to_story'
        commons.print_msg(Jira.clazz, method, 'begin')

        jira_url = "{url}/rest/api/3/issue/{id}".format(url = Jira.jira_url, id = story_id)

        headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

        data = {
            "update": {
                "fixVersions": [
                    {
                        "add": {
                            "name": version.lower()
                        }
                    }
                ]
            }
        }

        put_data = json.dumps(data, default=lambda o: o.__dict__, sort_keys=False, indent=4)

        commons.print_msg(Jira.clazz, method, jira_url)

        try:
            resp = requests.put(jira_url, put_data, headers=headers, timeout=self.http_timeout)

            if resp.status_code != 204:
                commons.print_msg(Jira.clazz, method, "Unable to add version {version} to issue {story} \r\n "
                                                          "Response: {response}".format(version=version, story=story_id, response=resp.text), 'WARN')
            else:
                commons.print_msg(Jira.clazz, method, resp.text)
        except requests.ConnectionError as e:
                commons.print_msg(Jira.clazz, method, 'Connection error. ' + str(e), 'WARN')
        except Exception as e:
            commons.print_msg(Jira.clazz, method, "Unable to add version {version} for story {story}".format(
                version=version, story=story_id), 'WARN')
            commons.print_msg(Jira.clazz, method, e, 'WARN')

        commons.print_msg(Jira.clazz, method, 'end')

    def determine_semantic_version_bump(self, story_details):
        method = 'determine_semantic_version_bump'
        commons.print_msg(Jira.clazz, method, 'begin')

        bump_type = None

        for i, story in enumerate(story_details):
            #jira labels are global across all projects but could still be used
            for j, label in enumerate(story.get('fields').get('labels')):
                if label.lower() == 'major':
                    return 'major'

            #jira components behave closest to tracker labels, are per project
            for k, component in enumerate(story.get('fields').get('components')):
                if component.get('name') == 'major':
                    return 'major'

            story_type = story.get('fields').get('issuetype').get('name').lower()

            if story_type == 'story' or story_type == 'chore' or story_type == 'release':
                bump_type = 'minor'
            elif story_type == 'bug' and bump_type is None:
                bump_type = 'bug'

        # This fall-through rule is needed because if there are no tracker
        # stories present in the commits, we need to default to something,
        # else calculate_next_semver will throw an error about getting 'None'
        if bump_type is None:
            bump_type = 'minor'

        commons.print_msg(Jira.clazz, method, "bump type: {}".format(bump_type))

        commons.print_msg(Jira.clazz, method, 'end')

        return bump_type

    def extract_story_id_from_commit_messages(self, commit_messages):
        method = 'extract_story_id_from_commit_messages'
        commons.print_msg(Jira.clazz, method, 'begin')

        story_list = []

        for commit_string in commit_messages:
            
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
                        # now dig out the tracker number or jira key in single number format or multiple separated by commas.
                        r = re.compile('(?:[a-zA-Z]+\-[0-9]+,?)+(,([a-zA-Z]+\-[0-9]+,?))*,?')
                        stories_array = stories.split(',')
                        stories = list(filter(r.match, stories_array))
                        for story in stories:
                            # split out by comma.
                            if story not in story_list:
                                story_list.append(story)

        commons.print_msg(Jira.clazz, method, "Story list: {}".format(story_list))
        commons.print_msg(Jira.clazz, method, 'end')
        return story_list

    """
        This methods needs to return an array of stories with 4 specific fields for each story:
            story_type
            id
            name
            description
            url
            current_state
    """
    def flatten_story_details(self, story_details):
        method = 'flatten_story_details'
        commons.print_msg(Jira.clazz, method, 'begin')

        if story_details is None:
            return None
        story_release_notes = []
        for story in story_details:
            story_release_note_summary = {}
            story_release_note_summary['story_type'] = story.get('fields').get('issuetype').get('name').lower()
            story_release_note_summary['id'] = story.get('key').upper()
            story_release_note_summary['name'] = story.get('fields').get('summary')
            story_release_note_summary['url'] = '{0}/browse/{1}'.format(Jira.jira_url, story.get('key').upper())
            story_release_note_summary['current_state'] = story.get('fields').get('status').get('name')
            description_text = []
            if story.get('fields').get('description') is not None:
                for i, description_content in enumerate(story.get('fields').get('description').get('content')):
                    if description_content.get('type') == 'paragraph':
                        for j, paragraph_content in enumerate(description_content.get('content')):
                            if paragraph_content.get('type') == 'text':
                                description_text.append(paragraph_content.get('text'))
            if len(description_text) > 0:
                description_text = ' '.join(description_text)
            else:
                description_text = None
            story_release_note_summary['description'] = description_text
            story_release_notes.append(story_release_note_summary)

        commons.print_msg(Jira.clazz, method, story_release_notes)
        commons.print_msg(Jira.clazz, method, 'end')
        return story_release_notes

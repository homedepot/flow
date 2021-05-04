import base64
import json
import os

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
    project_ids = None
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

        Jira.jira_basic_auth = base64.b64encode("{0}:{1}".format(Jira.user, Jira.token).encode('ascii')).decode('ascii')

        try:
            jira_json_config = self.config.json_config['projectTracking']['jira']

            # if projectId is actually project key and not id then need to fetch id.
            # since api call to get project data uses key or id just always call to fetch id.
            if jira_json_config.get('projectId') is not None and jira_json_config.get('projectIds') is not None:
                    raise KeyError('projectIds')
            elif jira_json_config.get('projectId') is not None:
                project_data = self._retrieve_project_info(str(jira_json_config['projectId']))
                Jira.project_ids = [(project_data['id'], project_data['key'])]
            elif jira_json_config.get('projectIds') is not None:
                Jira.project_ids = []
                for project_id in jira_json_config.get('projectIds'):
                    project_data = self._retrieve_project_info(str(jira_json_config['projectId']))
                    Jira.project_ids.append((project_data['id'], project_data['key']))
            else:
                raise KeyError('projectId')
            
            commons.print_msg(Jira.clazz, method, Jira.project_ids)
        except KeyError as e:
            if e.args[0] == 'projectIds':
                commons.print_msg(Jira.clazz,
                                  method,
                                  "The build config may only contain 'projectId' for single project id"
                                  "or 'projectIds' containing an array of project ids",
                                  'ERROR')
            else:
                commons.print_msg(Jira.clazz,
                                  method,
                                  "The build config associated with projectTracking is missing key {}".format(str(e)),
                                  'ERROR')
            exit(1)

        # Check for jira url first in buildConfig, second try settings.ini

        try:
            # noinspection PyUnboundLocalVariable
            Jira.jira_url = jira_json_config['url']
        except KeyError:
            if self.config.settings.has_section('jira') and self.config.settings.has_option('jira', 'url'):
                Jira.jira_url = self.config.settings.get('jira', 'url')
            else:
                commons.print_msg(Jira.clazz, method, 'No jira url found in buildConfig or settings.ini.',
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
        method = '_retrieve_project_id'
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
                                                "Response: {response}".format(url=story_detail.get('url', ''),
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

        for story in story_list:
            version = '{0}-{1}'.format(self.config.project_name, self.config.version_number)
            self._add_version_to_project(version)
            self._add_version_to_story(story, version)

        commons.print_msg(Jira.clazz, method, 'end')

    def _add_version_to_project(self, version):
        method = '_add_version_to_project'
        commons.print_msg(Jira.clazz, method, 'begin')

        for idx, project_id in enumerate(self.project_ids):
            version_to_post = Object()
            version_to_post.projectId = project_id[0]
            version_to_post.name = version.lower()

            jira_url = "{url}/rest/api/3/version".format(url=Jira.jira_url)

            headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

            commons.print_msg(Jira.clazz, method, version_to_post.to_JSON())

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

    def _add_version_to_story(self, story_id, version):
        method = '_add_version_to_story'
        commons.print_msg(Jira.clazz, method, 'begin')

        jira_url = "{url}/rest/api/3/issue/{id}".format(url = Jira.jira_url, id = story_id)

        headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'Authorization': 'Basic {0}'.format(Jira.jira_basic_auth)}

        version_to_put = Object()
        version_to_put.name = version.lower()
        update_method = Object()
        update_method.set = [version_to_put, ]
        update = Object()
        update.fixVersions = [update_method, ]
        version_to_put = Object()
        version_to_put.update = update

        commons.print_msg(Jira.clazz, method, jira_url)
        commons.print_msg(Jira.clazz, method, version_to_put)

        try:
            resp = requests.put(jira_url, version_to_put, headers=headers, timeout=self.http_timeout)
        
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

            if story_type == 'feature' or story_type == 'chore' or story_type == 'release':
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
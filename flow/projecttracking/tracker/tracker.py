import json
import os
import re

import requests
from flow.buildconfig import BuildConfig
from flow.projecttracking.project_tracking_abc import Project_Tracking

import flow.utils.commons as commons
from flow.utils.commons import Object


class Tracker(Project_Tracking):
    clazz = 'Tracker'
    token = None
    project_ids = None
    tracker_url = None
    config = BuildConfig
    http_timeout = 30

    def __init__(self, config_override=None):
        method = '__init__'
        commons.print_msg(Tracker.clazz, method, 'begin')

        if config_override is not None:
            self.config = config_override

        Tracker.token = os.getenv('TRACKER_TOKEN')

        if not Tracker.token:
            commons.print_msg(Tracker.clazz, method, 'No tracker token found in environment.  Did you define '
                                                     'environment variable \'TRACKER_TOKEN\'?', 'ERROR')
            exit(1)

        try:
            # below line is to maintain backwards compatibility since stanza was renamed
            tracker_json_config = self.config.json_config['tracker'] if 'tracker' in self.config.json_config else \
                self.config.json_config['projectTracking']["tracker"]

            if tracker_json_config.get('projectId') is not None and tracker_json_config.get('projectIds') is not None:
                raise KeyError('projectIds')
            elif tracker_json_config.get('projectId') is not None:
                Tracker.project_ids = [str(tracker_json_config['projectId'])]
            elif tracker_json_config.get('projectIds') is not None:
                Tracker.project_ids = []
                for project_id in tracker_json_config.get('projectIds'):
                    Tracker.project_ids.append(str(project_id))
            else:
                raise KeyError('projectId')

            commons.print_msg(Tracker.clazz, method, Tracker.project_ids)
        except KeyError as e:
            if e.args[0] == 'projectIds':
                commons.print_msg(Tracker.clazz,
                                  method,
                                  "The build config may only contain 'projectId' for single project id"
                                  "or 'projectIds' containing an array of project ids",
                                  'ERROR')
            else:
                commons.print_msg(Tracker.clazz,
                                  method,
                                  "The build config associated with projectTracking is missing key {}".format(str(e)),
                                  'ERROR')
            exit(1)

        # Check for tracker url first in buildConfig, second try settings.ini

        try:
            # noinspection PyUnboundLocalVariable
            Tracker.tracker_url = tracker_json_config['url']
        except KeyError:
            if self.config.settings.has_section('tracker') and self.config.settings.has_option('tracker', 'url'):
                Tracker.tracker_url = self.config.settings.get('tracker', 'url')
            else:
                commons.print_msg(Tracker.clazz, method, 'No tracker url found in buildConfig or settings.ini.',
                                  'ERROR')
                exit(1)

    def get_details_for_all_stories(self, story_list):
        method = 'get_details_for_all_stories'
        commons.print_msg(Tracker.clazz, method, 'begin')

        story_details = []
        commons.print_msg(Tracker.clazz, method, story_list)

        for i, story_id in enumerate(story_list):
            story_detail = self._retrieve_story_detail(story_id)

            if story_detail is not None:
                story_details.append(story_detail)

        commons.print_msg(Tracker.clazz, method, story_details)
        commons.print_msg(Tracker.clazz, method, 'end')
        return story_details

    def _retrieve_story_detail(self, story_id):
        method = '_retrieve_story_detail'
        commons.print_msg(Tracker.clazz, method, 'begin')

        tracker_story_details = []
        json_data = None
        resp = None

        if Tracker.project_ids is not None:
            for project_id in Tracker.project_ids:
                tracker_story_details.append(
                    {'url': Tracker.tracker_url + '/services/v5/projects/' + project_id + '/stories/' + story_id})

        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': Tracker.token}

        for story_detail in tracker_story_details:
            try:
                commons.print_msg(Tracker.clazz, method, story_detail['url'])
                resp = requests.get(story_detail['url'], headers=headers, timeout=self.http_timeout)
            except requests.ConnectionError as e:
                commons.print_msg(Tracker.clazz, method, 'Connection error. ' + str(e), 'ERROR')
                exit(1)
            except Exception as e:
                commons.print_msg(Tracker.clazz, method, "Failed retrieving story detail from call to {} ".format(
                    story_detail.get('url', '')), 'ERROR')
                commons.print_msg(Tracker.clazz, method, e, 'ERROR')
                exit(1)

            if resp.status_code == 200:
                json_data = json.loads(resp.text)
                commons.print_msg(Tracker.clazz, method, json_data)
                break
            else:
                commons.print_msg(Tracker.clazz, method, "Failed retrieving story detail from call to {url}. \r\n "
                                                         "Response: {response}".format(url=story_detail.get('url', ''),
                                                                                       response=resp.text), 'WARN')

        commons.print_msg(Tracker.clazz, method, 'end')
        return json_data

    def tag_stories_in_commit(self, story_list):
        method = 'tag_stories_in_commit'
        commons.print_msg(Tracker.clazz, method, 'begin')

        for story in story_list:
            label = self.config.project_name + '-' + self.config.version_number

            self._add_label_to_tracker(story, label)

        commons.print_msg(Tracker.clazz, method, 'end')

    def _add_label_to_tracker(self, story_id, label):
        method = '_add_label_to_tracker'
        commons.print_msg(Tracker.clazz, method, 'begin')

        label_to_post = Object()
        label_to_post.name = label.lower()

        for project_id in Tracker.project_ids:
            tracker_url = "{url}/services/v5/projects/{projid}/stories/{storyid}/labels".format(url=Tracker.tracker_url,
                                                                                                projid=project_id,
                                                                                                storyid=story_id)

            headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'X-TrackerToken': Tracker.token}

            commons.print_msg(Tracker.clazz, method, tracker_url)
            commons.print_msg(Tracker.clazz, method, label_to_post.to_JSON())

            try:
                resp = requests.post(tracker_url, label_to_post.to_JSON(), headers=headers, timeout=self.http_timeout)

                if resp.status_code != 200:
                    commons.print_msg(Tracker.clazz, method, "Unable to tag story {story} with label {lbl} \r\n "
                                                             "Response: {response}".format(story=story_id, lbl=label,
                                                                                           response=resp.text), 'WARN')
                else:
                    commons.print_msg(Tracker.clazz, method, resp.text)
            except requests.ConnectionError as e:
                commons.print_msg(Tracker.clazz, method, 'Connection error. ' + str(e), 'WARN')
            except Exception as e:
                commons.print_msg(Tracker.clazz, method, "Unable to tag story {story} with label {lbl}".format(
                    story=story_id, lbl=label), 'WARN')
                commons.print_msg(Tracker.clazz, method, e, 'WARN')

        commons.print_msg(Tracker.clazz, method, 'end')

    def determine_semantic_version_bump(self, story_details):
        method = 'determine_semantic_version_bump'
        commons.print_msg(Tracker.clazz, method, 'begin')

        bump_type = None

        for i, story in enumerate(story_details):
            for j, label in enumerate(story.get('labels')):
                if label.get('name') == 'major':
                    return 'major'

            if story.get('story_type') == 'feature' or story.get('story_type') == 'chore' or story.get(
                    'story_type') == 'release':
                bump_type = 'minor'
            elif story.get('story_type') == 'bug' and bump_type is None:
                bump_type = 'bug'

        # This fall-through rule is needed because if there are no tracker
        # stories present in the commits, we need to default to something,
        # else calculate_next_semver will throw an error about getting 'None'
        if bump_type is None:
            bump_type = 'minor'

        commons.print_msg(Tracker.clazz, method, "bump type: {}".format(bump_type))

        commons.print_msg(Tracker.clazz, method, 'end')

        return bump_type

    def extract_story_id_from_commit_messages(self, commit_messages):
        method = 'extract_story_id_from_commit_messages'
        commons.print_msg(Tracker.clazz, method, 'begin')

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
                        r = re.compile('[0-9,]+(,[0-9]+)*,?')
                        stories = ''.join(filter(r.match, stories))

                        for story in [_f for _f in stories.split(',') if _f]:
                            # split out by comma.
                            if story not in story_list:
                                story_list.append(story)

        commons.print_msg(Tracker.clazz, method, "Story list: {}".format(story_list))
        commons.print_msg(Tracker.clazz, method, 'end')
        return story_list

    """
        This methods needs to flatten an array of stories to ensure 6 specific
        fields exist at the top level of the dictionary for each story:
            story_type
            id
            name
            description
            url
            current_state
    """
    def flatten_story_details(self, story_details):
        method = 'flatten_story_details'
        commons.print_msg(Tracker.clazz, method, 'begin')

        if story_details is None:
            return None

        story_release_notes = []
        for story in story_details:
            story_release_note_summary = {}
            story_release_note_summary['story_type'] = story.get('story_type')
            story_release_note_summary['id'] = story.get('id')
            story_release_note_summary['name'] = story.get('name')
            story_release_note_summary['description'] = story.get('description')
            story_release_note_summary['url'] = story.get('url')
            story_release_note_summary['current_state'] = story.get('current_state')
            story_release_notes.append(story_release_note_summary)

        commons.print_msg(Tracker.clazz, method, story_release_notes)
        commons.print_msg(Tracker.clazz, method, 'end')
        return story_release_notes
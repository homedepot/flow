import json
import os

import requests
from flow.buildconfig import BuildConfig
from flow.projecttracking.project_tracking_abc import Project_Tracking

import flow.utils.commons as commons
from flow.utils.commons import Object


class Tracker(Project_Tracking):

    clazz = 'Tracker'
    token = None
    project_id = None
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

            Tracker.project_id = str(tracker_json_config['projectId'])
        except KeyError as e:
            commons.print_msg(Tracker.clazz,
                              method,
                             "The build config associated with projectTracking is missing key {}".format(str(e)), 'ERROR')
            exit(1)

        # Check for tracker url first in buildConfig, second try settings.ini

        try:
            # noinspection PyUnboundLocalVariable
            Tracker.tracker_url = tracker_json_config['url']
        except:
            if self.config.settings.has_section('tracker') and self.config.settings.has_option('tracker', 'url'):
                Tracker.tracker_url = self.config.settings.get('tracker', 'url')
            else:
                commons.print_msg(Tracker.clazz, method, 'No tracker url found in buildConfig or settings.ini.', 'ERROR')
                exit(1)

    def get_details_for_all_stories(self, story_list):
        method = 'get_details_for_all_stories'
        commons.print_msg(Tracker.clazz, method, 'begin')

        story_details = []

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

        tracker_story_details_url = Tracker.tracker_url + '/services/v5/projects/' + Tracker.project_id + '/stories/' + story_id

        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': Tracker.token}

        commons.print_msg(Tracker.clazz, method, tracker_story_details_url)

        try:
            resp = requests.get(tracker_story_details_url, headers=headers, timeout=self.http_timeout)
        except requests.ConnectionError:
            commons.print_msg(Tracker.clazz, method, 'Request to Tracker timed out.', 'ERROR')
            exit(1)
        except Exception as e:
            commons.print_msg(Tracker.clazz, method, "Failed retrieving story detail from call to {} ".format(
                tracker_story_details_url), 'ERROR')
            commons.print_msg(Tracker.clazz, method, e, 'ERROR')
            exit(1)

        json_data = None

        # noinspection PyUnboundLocalVariable
        if resp.status_code == 200:
            json_data = json.loads(resp.text)
            commons.print_msg(Tracker.clazz, method, json_data)
            commons.print_msg(Tracker.clazz, method, resp.text)
        else:
            commons.print_msg(Tracker.clazz, method, "Failed retrieving story detail from call to {url}. \r\n "
                                                    "Response: {response}".format(url=tracker_story_details_url,
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

        tracker_url = "{url}/services/v5/projects/{projid}/stories/{storyid}/labels".format(url=Tracker.tracker_url,
                                                                                            projid=Tracker.project_id,
                                                                                            storyid=story_id)

        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': Tracker.token}

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
        except requests.ConnectionError:
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

            if story.get('story_type') == 'feature' or story.get('story_type') == 'chore' or story.get('story_type') == 'release':
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

import configparser
import json
import os
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
import pytest

from flow.projecttracking.tracker.tracker import Tracker

from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "projectTracking": {
        "tracker": {
            "projectId": 123456
        }
    },
    "environments": {
        "unittest": {
            "artifactCategory": "release"
        }
    },
    "slack": {
        "botName": "Flow",
        "emoji": ":robot_face:",
        "channel": "#spigot-ci"
    }
}

mock_build_config_dict_multi_projects = {
    "projectInfo": {
        "name": "testproject"
    },
    "projectTracking": {
        "tracker": {
            "projectIds": [123456, 423476]
        }
    },
    "environments": {
        "unittest": {
            "artifactCategory": "release"
        }
    },
    "slack": {
        "botName": "Flow",
        "emoji": ":robot_face:",
        "channel": "#spigot-ci"
    }
}

mock_build_config_missing_tracker_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "environments": {
        "unittest": {
            "artifactCategory": "release"
        }
    },
    "slack": {
        "botName": "Flow",
        "emoji": ":robot_face:",
        "channel": "#spigot-ci"
    }
}

mock_build_config_missing_project_id_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "projectTracking": {
        "tracker": {
        }
    },
    "environments": {
        "unittest": {
            "artifactCategory": "release"
        }
    },
    "slack": {
        "botName": "Flow",
        "emoji": ":robot_face:",
        "channel": "#spigot-ci"
    }
}

mock_build_config_dict_both_project_ids = {
    "projectInfo": {
        "name": "testproject"
    },
    "projectTracking": {
        "tracker": {
            "projectId": 123456,
            "projectIds": [654321, 999999]
        }
    },
    "environments": {
        "unittest": {
            "artifactCategory": "release"
        }
    },
    "slack": {
        "botName": "Flow",
        "emoji": ":robot_face:",
        "channel": "#spigot-ci"
    }
}

mock_setting_ini = """
[tracker]
url = https://www.pivotaltracker.com
"""


def mock_get_multiple_project_story_details_response(*args, **kwargs):
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories_bug.json", 'r') as myfile:
        tracker_data = myfile.read()

    _response_mock = Mock()
    _response_mock.text = tracker_data
    if args[0] == 'http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082057':
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082058':
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/services/v5/projects/123456/stories/264082058':
        _response_mock.text = ''
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/services/v5/projects/423476/stories/264082058':
        _response_mock.status_code = 200
    else:
        _response_mock.text = []
        _response_mock.status_code = 500

    return _response_mock


def mock_get_multiple_project_labels_response(*args, **kwargs):
    _response_mock = Mock()
    _response_mock.text = ''
    if args[0] == 'http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082057':
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/services/v5/projects/423476/stories/134082057':
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/services/v5/projects/123456/stories/222082037':
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/services/v5/projects/423476/stories/222082037':
        _response_mock.status_code = 200
    else:
        _response_mock.status_code = 500

    return _response_mock


def test_no_initialize_object(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    _tracker = Tracker(config_override=_b)
    assert _tracker is not None


def test_get_details_for_all_stories(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    parser = configparser.ConfigParser()
    parser.add_section('tracker')
    parser.set('tracker', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': 'fake_token'}
        timeout = 30
        current_test_directory = os.path.dirname(os.path.realpath(__file__))
        with open(current_test_directory + "/tracker_stories_bug.json", 'r') as myfile:
            tracker_data = myfile.read()
        mock_request.return_value.text = tracker_data
        mock_request.return_value.status_code = 200
        _tracker = Tracker(config_override=_b)
        story_details = _tracker.get_details_for_all_stories(story_list=["134082057", "134082058"])
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082057',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082058',
                                     headers=headers, timeout=timeout)
        assert story_details[0] == json.loads(tracker_data)


def test_get_details_for_all_stories_for_multiple_projects(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_multi_projects['environments']['unittest']
    _b.json_config = mock_build_config_dict_multi_projects

    parser = configparser.ConfigParser()
    parser.add_section('tracker')
    parser.set('tracker', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': 'fake_token'}
        timeout = 30
        current_test_directory = os.path.dirname(os.path.realpath(__file__))
        with open(current_test_directory + "/tracker_stories_bug.json", 'r') as myfile:
            tracker_data = myfile.read()
        _tracker = Tracker(config_override=_b)
        mock_request.side_effect = mock_get_multiple_project_story_details_response

        story_details = _tracker.get_details_for_all_stories(story_list=["134082057", "134082058", "264082058"])
        # assert mock_request.call_counts == 4
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082057',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082058',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/264082058',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/423476/stories/264082058',
                                     headers=headers, timeout=timeout)
        assert story_details[0] == json.loads(tracker_data)


def test_tag_stories_in_commit(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0'
    _b.json_config = mock_build_config_dict

    parser = configparser.ConfigParser()
    parser.add_section('tracker')
    parser.set('tracker', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.post') as mock_request:
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': 'fake_token'}
        timeout = 30
        label = {
                    "name": "testproject-v1.0"
                }
        json_label = json.dumps(label, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.return_value.text = ''
        mock_request.return_value.status_code = 200

        _tracker = Tracker(config_override=_b)
        _tracker.tag_stories_in_commit(story_list=['134082057', '134082058'])
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082057/labels',
                                     json_label, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082058/labels',
                                     json_label, headers=headers, timeout=timeout)


def test_tag_stories_in_commit_for_multiple_projects(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_multi_projects['environments']['unittest']
    _b.project_name = mock_build_config_dict_multi_projects['projectInfo']['name']
    _b.version_number = 'v1.0'
    _b.json_config = mock_build_config_dict_multi_projects

    parser = configparser.ConfigParser()
    parser.add_section('tracker')
    parser.set('tracker', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.post') as mock_request:
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-TrackerToken': 'fake_token'}
        timeout = 30
        label = {
                    "name": "testproject-v1.0"
                }
        json_label = json.dumps(label, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.return_value.text = ''
        mock_request.return_value.status_code = 200
        mock_request.side_effect = mock_get_multiple_project_labels_response

        _tracker = Tracker(config_override=_b)
        _tracker.tag_stories_in_commit(story_list=['134082057', '222082037'])
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/123456/stories/134082057/labels',
                                     json_label, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/services/v5/projects/423476/stories/222082037/labels',
                                     json_label, headers=headers, timeout=timeout)


def test_story_bump_bug(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories_bug.json", 'r') as myfile:
        tracker_json_data = json.loads(myfile.read())

    bump_type = _tracker.determine_semantic_version_bump(story_details=tracker_json_data["stories"])

    assert bump_type == "bug"


def test_story_bump_minor(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories_minor.json", 'r') as myfile:
        tracker_json_data = json.loads(myfile.read())

    bump_type = _tracker.determine_semantic_version_bump(story_details=tracker_json_data["stories"])

    assert bump_type == "minor"


def test_story_bump_major(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories_major.json", 'r') as myfile:
        tracker_json_data = json.loads(myfile.read())

    bump_type = _tracker.determine_semantic_version_bump(story_details=tracker_json_data["stories"])

    assert bump_type == "major"


def test_init_for_multiple_projects_too_many_project_id_keys(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_both_project_ids['environments']['unittest']
    _b.json_config = mock_build_config_dict_both_project_ids

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__',
                                            "The build config may only contain 'projectId' for single project id"
                                            "or 'projectIds' containing an array of project ids", 'ERROR')


def test_init_missing_tracker(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_tracker_dict

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__',
                                            "The build config associated with projectTracking is "
                                            "missing key 'projectTracking'", 'ERROR')


def test_init_missing_tracker_project_id(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_project_id_dict

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__',
                                            "The build config associated with projectTracking is missing key "
                                            "'projectId'",
                                            'ERROR')


def test_init_missing_tracker_url(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    _b.settings = parser

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__',
                                            'No tracker url found in buildConfig or settings.ini.', 'ERROR')


def test_init_missing_tracker_url_but_contains_tracker_in_config_parser(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    parser.add_section('tracker')
    _b.settings = parser

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__',
                                            'No tracker url found in buildConfig or settings.ini.', 'ERROR')


def test_init_missing_env_variable(monkeypatch):
    if os.getenv('TRACKER_TOKEN'):
        monkeypatch.delenv('TRACKER_TOKEN')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Tracker()

        mock_printmsg_fn.assert_called_with('Tracker', '__init__',
                                            "No tracker token found in environment.  Did you define environment variable 'TRACKER_TOKEN'?",
                                            'ERROR')

def test_extract_story_id_with_empty_list(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    story_list = _tracker.extract_story_id_from_commit_messages([])
    assert len(story_list) == 0

commit_example = [
"223342f Adding ability to specify artifactory user [#134082057]",
"4326d00 Adding slack channel option for errors [#130798449]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_two_stories(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    story_list = _tracker.extract_story_id_from_commit_messages(commit_example)
    assert len(story_list) == 2

commit_example_nested_brackets = [
"223342f Adding ability to specify artifactory user [#134082057, [bubba]]",
"4326d00 Adding slack channel option for errors [#130798449]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_nested_brackets(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    story_list = _tracker.extract_story_id_from_commit_messages(commit_example_nested_brackets)
    print(str(story_list))
    assert len(story_list) == 1


commit_example_multiple_per_brackets = [
"223342f Adding ability to specify artifactory user [#134082057,#134082058]",
"4326d00 Adding slack channel option for errors [#130798449,123456]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_multiple_per_brackets(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    story_list = _tracker.extract_story_id_from_commit_messages(commit_example_multiple_per_brackets)
    print(str(story_list))
    assert len(story_list) == 4



commit_example_dedup = [
"223342f Adding ability to specify artifactory user [#134082057,#134082057]",
"4326d00 Adding slack channel option for errors [#134082057,134082057]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_dedup(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    story_list = _tracker.extract_story_id_from_commit_messages(commit_example_dedup)
    print(str(story_list))
    assert len(story_list) == 1

def test_flatten_story_details_with_None_story_details(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)

    flat_story_details = _tracker.flatten_story_details(None)
    assert flat_story_details is None

def test_flatten_story_details_with_empty_story_details(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)

    flat_story_details = _tracker.flatten_story_details([])
    assert len(flat_story_details) == 0

def test_flatten_story_details_with_story_details(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    flat_story_expected = [
        {
            "story_type" : "bug",
            "id" : 123456,
            "name" : "Test Bug",
            "url" : "https://www.pivotaltracker.com/story/show/fake",
            "current_state" : "started",
            "description" : "This is a test bug description"
        },
        {
            "story_type" : "bug",
            "id" : 12345678,
            "name" : "Another test bug",
            "url" : "https://www.pivotaltracker.com/story/show/fake",
            "current_state" : "started",
            "description" : "Another test bug"
        }
    ]

    _tracker = Tracker(config_override=_b)

    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories_bug.json", 'r') as myfile:
        tracker_data = myfile.read()
    story_details = json.loads(tracker_data).get('stories')

    flat_story_details = _tracker.flatten_story_details(story_details)
    assert flat_story_expected == flat_story_details
    for story in flat_story_details:
        assert 'story_type' in story
        assert 'id' in story
        assert 'name' in story
        assert 'description' in story
        assert 'url' in story
        assert 'current_state' in story
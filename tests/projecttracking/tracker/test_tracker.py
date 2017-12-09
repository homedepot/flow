import configparser
import json
import os
from unittest.mock import MagicMock
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

mock_build_config_missing_projectid_dict = {
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

mock_setting_ini = """
[tracker]
url = https://www.pivotaltracker.com
"""


def test_no_initialize_object(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _tracker = Tracker(config_override=_b)
    assert _tracker is not None


# def test_get_story_details_from_commits():
#     _tracker = Tracker()
#     story_details = _tracker.get_story_details_from_commits(commit_history=["134082057", "134082058"])
#     assert len(story_details) == 2


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


def test_init_missing_tracker(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_tracker_dict

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:

            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__', "The build config associated with projectTracking is "
                                                                   "missing key 'projectTracking'", 'ERROR')


def test_init_missing_tracker_project_id(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_projectid_dict

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:

            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__', "The build config associated with projectTracking is missing key 'projectId'", 'ERROR')


def test_init_missing_tracker_url(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    _b.settings = parser

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:

            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__', 'No tracker url found in buildConfig or settings.ini.', 'ERROR')


def test_init_missing_tracker_url_but_contains_tracker_in_config_parser(monkeypatch):
    monkeypatch.setenv('TRACKER_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    parser.add_section('tracker')
    _b.settings = parser

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:

            Tracker(config_override=_b)

        mock_printmsg_fn.assert_called_with('Tracker', '__init__', 'No tracker url found in buildConfig or settings.ini.', 'ERROR')


def test_init_missing_env_variable(monkeypatch):
    if os.getenv('TRACKER_TOKEN'):
        monkeypatch.delenv('TRACKER_TOKEN')

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:

            Tracker()

        mock_printmsg_fn.assert_called_with('Tracker', '__init__', "No tracker token found in environment.  Did you define environment variable 'TRACKER_TOKEN'?", 'ERROR')

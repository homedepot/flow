import base64
import configparser
import json
import os
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
import pytest

from flow.projecttracking.jira.jira import Jira

from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "projectTracking": {
        "jira": {
            "projectId": "TEST"
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
        "jira": {
            "projectIds": ["TEST", "TEST2"]
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

mock_build_config_missing_jira_dict = {
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
        "jira": {
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
        "jira": {
            "projectId": "TEST",
            "projectIds": ["TEST", "TEST2"]
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
[jira]
url = https://thd.atlassian.net
"""


def mock_get_multiple_project_story_details_response(*args, **kwargs):
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/jira_stories_bug.json", 'r') as myfile:
        jira_data = myfile.read()

    _response_mock = Mock()
    _response_mock.text = jira_data
    if args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST-123':
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST-456':
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST-468':
        _response_mock.text = ''
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST2-123':
        _response_mock.status_code = 200
    else:
        _response_mock.text = []
        _response_mock.status_code = 500

    return _response_mock


def mock_get_multiple_project_labels_response(*args, **kwargs):
    _response_mock = Mock()
    _response_mock.text = ''
    if args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST-123':
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST2-123':
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST-456':
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST2-456':
        _response_mock.status_code = 200
    else:
        _response_mock.status_code = 500

    return _response_mock


def test_no_initialize_object(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    
    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        current_test_directory = os.path.dirname(os.path.realpath(__file__))
        with open(current_test_directory + "/jira_projects.json", 'r') as myfile:
            jira_project_data = json.loads(myfile.read())

        jira_project = json.dumps(jira_project_data["projects"][0], default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.return_value.text = jira_project
        mock_request.return_value.status_code = 200

        _jira = Jira(config_override=_b)
        assert _jira is not None


def test_get_details_for_all_stories(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        current_test_directory = os.path.dirname(os.path.realpath(__file__))
        with open(current_test_directory + "/jira_stories_bug.json", 'r') as myfile:
            jira_project_data = myfile.read()
        mock_request.return_value.text = jira_data
        mock_request.return_value.status_code = 200
        _jira = Jira(config_override=_b)
        story_details = _jira.get_details_for_all_stories(story_list=["TEST-123", "TEST-456"])
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-456',
                                     headers=headers, timeout=timeout)
        assert story_details[0] == json.loads(jira_data)


def test_get_details_for_all_stories_for_multiple_projects(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_multi_projects['environments']['unittest']
    _b.json_config = mock_build_config_dict_multi_projects

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        current_test_directory = os.path.dirname(os.path.realpath(__file__))
        with open(current_test_directory + "/jira_stories_bug.json", 'r') as myfile:
            jira_data = myfile.read()
        _jira = Jira(config_override=_b)
        mock_request.side_effect = mock_get_multiple_project_story_details_response

        story_details = _jira.get_details_for_all_stories(story_list=["TEST-123", "TEST-456", "TEST-468", "TEST2-123"])
        # assert mock_request.call_counts == 4
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-456',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-468',
                                     headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST2-123',
                                     headers=headers, timeout=timeout)
        assert story_details[0] == json.loads(jira_data)


def test_tag_stories_in_commit(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0'
    _b.json_config = mock_build_config_dict

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.post') as mock_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        project = {
                    "projectId" : "TEST",
                    "name": "testproject-v1.0"
                }
        json_project = json.dumps(project, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        version = {
            "update": {
                "fixVersions": [
                    {
                        "set": [
                            {
                                "name": "testproject-v1.0"
                            }
                        ]
                    }
                ]
            }
        }
        json_version = json.dumps(version, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.return_value.text = ''
        mock_request.return_value.status_code = 200

        _jira = Jira(config_override=_b)
        _jira.tag_stories_in_commit(story_list=['TEST-123', 'TEST-456'])
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/version',
                                     json_project, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     json_version, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/version',
                                     json_project, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-456',
                                     json_version, headers=headers, timeout=timeout)


def test_tag_stories_in_commit_for_multiple_projects(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_multi_projects['environments']['unittest']
    _b.project_name = mock_build_config_dict_multi_projects['projectInfo']['name']
    _b.version_number = 'v1.0'
    _b.json_config = mock_build_config_dict_multi_projects

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.post') as mock_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        project = {
                    "projectId" : "TEST",
                    "name": "testproject-v1.0"
                }
        json_project = json.dumps(project, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        project2 = {
                    "projectId" : "TEST",
                    "name": "testproject-v1.0"
                }
        json_project2 = json.dumps(project2, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        version = {
            "update": {
                "fixVersions": [
                    {
                        "set": [
                            {
                                "name": "testproject-v1.0"
                            }
                        ]
                    }
                ]
            }
        }
        json_version = json.dumps(version, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.return_value.text = ''
        mock_request.return_value.status_code = 200
        mock_request.side_effect = mock_get_multiple_project_labels_response

        _jira = Jira(config_override=_b)
        _jira.tag_stories_in_commit(story_list=['TEST-123', 'TEST2-456'])
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/version',
                                     json_project, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     json_version, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/version',
                                     json_project2, headers=headers, timeout=timeout)
        mock_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST2-456',
                                     json_version, headers=headers, timeout=timeout)


def test_story_bump_bug(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _jira = Jira(config_override=_b)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/jira_stories_bug.json", 'r') as myfile:
        jira_json_data = json.loads(myfile.read())

    bump_type = _jira.determine_semantic_version_bump(story_details=jira_json_data["stories"])

    assert bump_type == "bug"


def test_story_bump_minor(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _jira = Jira(config_override=_b)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/jira_stories_minor.json", 'r') as myfile:
        jira_json_data = json.loads(myfile.read())

    bump_type = _jira.determine_semantic_version_bump(story_details=jira_json_data["stories"])

    assert bump_type == "minor"


def test_story_bump_major(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict

    _jira = Jira(config_override=_b)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/jira_stories_major.json", 'r') as myfile:
        jira_json_data = json.loads(myfile.read())

    bump_type = _jira.determine_semantic_version_bump(story_details=jira_json_data["stories"])

    assert bump_type == "major"


def test_init_for_multiple_projects_too_many_project_id_keys(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_both_project_ids['environments']['unittest']
    _b.json_config = mock_build_config_dict_both_project_ids

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira(config_override=_b)

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "The build config may only contain 'projectId' for single project id"
                                            "or 'projectIds' containing an array of project ids", 'ERROR')


def test_init_missing_jira(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_jira_dict

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira(config_override=_b)

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "The build config associated with projectTracking is "
                                            "missing key 'projectTracking'", 'ERROR')


def test_init_missing_jira_project_id(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_project_id_dict

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira(config_override=_b)

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "The build config associated with projectTracking is missing key "
                                            "'projectId'",
                                            'ERROR')


def test_init_missing_jira_url(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    _b.settings = parser

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira(config_override=_b)

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            'No jira url found in buildConfig or settings.ini.', 'ERROR')


def test_init_missing_jira_url_but_contains_jira_in_config_parser(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    parser.add_section('jira')
    _b.settings = parser

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira(config_override=_b)

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            'No jira url found in buildConfig or settings.ini.', 'ERROR')


def test_init_missing_all_env_variable(monkeypatch):
    if os.getenv('JIRA_USER'):
        monkeypatch.delenv('JIRA_USER')
    if os.getenv('JIRA_TOKEN'):
        monkeypatch.delenv('JIRA_TOKEN')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira()

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "No jira user, jira token found in environment.  Did you define environment variables 'JIRA_USER' and 'JIRA_TOKEN'?",
                                            'ERROR')

def test_init_missing_user_env_variable(monkeypatch):
    if os.getenv('JIRA_USER'):
        monkeypatch.delenv('JIRA_USER')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira()

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "No jira user found in environment.  Did you define environment variables 'JIRA_USER'?",
                                            'ERROR')

def test_init_missing_token_env_variable(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    if os.getenv('JIRA_TOKEN'):
        monkeypatch.delenv('JIRA_TOKEN')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira()

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "No jira token found in environment.  Did you define environment variable 'JIRA_TOKEN'?",
                                            'ERROR')
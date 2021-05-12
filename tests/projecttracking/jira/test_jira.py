import base64
import configparser
import json
import os
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import ANY
import pytest

from flow.projecttracking.jira.jira import Jira

from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "projectTracking": {
        "jira": {
            "projectKey": "TEST"
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
            "projectKeys": ["TEST", "TEST2"]
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
            "projectKey": "TEST",
            "projectKeys": ["TEST", "TEST2"]
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
        _response_mock.status_code = 204
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST2-123':
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST-456':
        _response_mock.status_code = 404
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/issue/TEST2-456':
        _response_mock.status_code = 204
    else:
        _response_mock.status_code = 500

    return _response_mock

def mock_get_multiple_project_ids_response(*args, **kwargs):
    _response_mock = Mock()
    _response_mock.text = ''
    if args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/TEST':
        project_data = {
            "id": "123456",
            "self": "http://happy.happy.joy.joy/rest/api/3/project/fake",
            "key": "TEST"
        }
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/123456':
        project_data = {
            "id": "123456",
            "self": "http://happy.happy.joy.joy/rest/api/3/project/fake",
            "key": "TEST"
        }
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/TEST2':
        project_data = {
            "id": "1234567",
            "self": "http://happy.happy.joy.joy/rest/api/3/project/fake",
            "key": "TEST2"
        }
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/1234567':
        project_data = {
            "id": "1234567",
            "self": "http://happy.happy.joy.joy/rest/api/3/project/fake",
            "key": "TEST2"
        }
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    else:
        project_data = {
            "errorMessage": [
                "No project could be found with key/id"
            ],
            "errors": {}
        }
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 404
    print(_response_mock)
    return _response_mock

def mock_get_project_versions(*args, **kwargs):
    _response_mock = Mock()
    _response_mock.text = ''
    if args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/TEST/versions':
        project_data = [
            {
                "id": "11123",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11123",
                "name": "testproject-v0.1"
            },
            {
                "id": "11124",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11124",
                "name": "testproject-v0.2"
            }
        ]
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/123456/versions':
        project_data = [
            {
                "id": "11123",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11123",
                "name": "testproject-v0.1"
            },
            {
                "id": "11124",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11124",
                "name": "testproject-v0.2"
            }
        ]
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/TEST2/versions':
        project_data = [
            {
                "id": "11223",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11223",
                "name": "testproject-v0.9"
            },
            {
                "id": "11224",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11224",
                "name": "testproject-v1.0"
            }
        ]
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    elif args[0] == 'http://happy.happy.joy.joy/rest/api/3/project/1234567/versions':
        project_data = [
            {
                "id": "11223",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11223",
                "name": "testproject-v0.9"
            },
            {
                "id": "11224",
                "self": "http://happy.happy.joy.joy/rest/api/3/version/11224",
                "name": "testproject-v1.0"
            }
        ]
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 200
    else:
        project_data = {
            "errorMessage": [
                "No project could be found with key/id"
            ],
            "errors": {}
        }
        _response_mock.text = json.dumps(project_data, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        _response_mock.status_code = 404
    print(_response_mock)
    return _response_mock

def test_no_initialize_object(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    _b.settings
    
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
            jira_data = myfile.read()
        with open(current_test_directory + "/jira_projects.json", 'r') as myfile:
            jira_project_data = json.loads(myfile.read())

        jira_project = json.dumps(jira_project_data["projects"][0], default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.return_value.text = jira_project
        mock_request.return_value.status_code = 200
        _jira = Jira(config_override=_b)
        mock_request.return_value.text = jira_data
        mock_request.return_value.status_code = 200
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
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
    with patch('requests.get') as mock_get_request, patch('requests.post') as mock_post_request, patch('requests.put') as mock_put_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        project = {
            "projectId" : "123456",
            "name": "testproject-v1.0"
        }
        version = {
            "update": {
                "fixVersions": [
                    {
                        "add": {
                            "name": "testproject-v1.0"
                        }
                    }
                ]
            }
        }
        mock_get_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        mock_get_request.side_effect = mock_get_project_versions
        mock_post_request.return_value.text = ''
        mock_post_request.return_value.status_code = 201
        mock_put_request.return_value.text = ''
        mock_put_request.return_value.status_code = 204

        mock_get_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/project/TEST',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/123456/versions',
                                     headers=headers, timeout=timeout)
        ]

        _jira.tag_stories_in_commit(story_list=['TEST-123', 'TEST-456'])
        mock_get_request.assert_has_calls(mock_get_calls)
        mock_post_request.assert_called_once_with('http://happy.happy.joy.joy/rest/api/3/version',
                                     ANY, headers=headers, timeout=timeout)
        mock_post_request_calls = mock_post_request.call_args_list
        call_args, call_kwargs = mock_post_request_calls[0]
        post_data_arg = call_args[1]
        assert project == json.loads(post_data_arg)
        mock_put_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     ANY, headers=headers, timeout=timeout)
        mock_put_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-456',
                                     ANY, headers=headers, timeout=timeout)
        mock_put_request_calls = mock_put_request.call_args_list
        for i, put_call in enumerate(mock_put_request_calls):
            call_args, call_kwargs = put_call
            put_data_arg = call_args[1]
            assert version == json.loads(put_data_arg)

def test_tag_stories_in_commit_with_existing_version(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v0.1'
    _b.json_config = mock_build_config_dict

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_get_request, patch('requests.post') as mock_post_request, patch('requests.put') as mock_put_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        project = {
            "projectId" : "123456",
            "name": "testproject-v0.1"
        }
        version = {
            "update": {
                "fixVersions": [
                    {
                        "add": {
                            "name": "testproject-v0.1"
                        }
                    }
                ]
            }
        }
        mock_get_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        mock_get_request.side_effect = mock_get_project_versions
        mock_post_request.return_value.text = ''
        mock_post_request.return_value.status_code = 201
        mock_put_request.return_value.text = ''
        mock_put_request.return_value.status_code = 204

        mock_get_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/project/TEST',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/123456/versions',
                                     headers=headers, timeout=timeout)
        ]

        _jira.tag_stories_in_commit(story_list=['TEST-123', 'TEST-456'])
        mock_get_request.assert_has_calls(mock_get_calls)
        mock_post_request.assert_not_called()
        mock_put_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     ANY, headers=headers, timeout=timeout)
        mock_put_request.assert_any_call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-456',
                                     ANY, headers=headers, timeout=timeout)
        mock_put_request_calls = mock_put_request.call_args_list
        for i, put_call in enumerate(mock_put_request_calls):
            call_args, call_kwargs = put_call
            put_data_arg = call_args[1]
            assert version == json.loads(put_data_arg)


def test_tag_stories_in_commit_for_multiple_projects(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict_multi_projects['environments']['unittest']
    _b.project_name = mock_build_config_dict_multi_projects['projectInfo']['name']
    _b.version_number = 'v1.1'
    _b.json_config = mock_build_config_dict_multi_projects

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_get_request, patch('requests.post') as mock_post_request, patch('requests.put') as mock_put_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        project = {
                    "projectId" : "123456",
                    "name": "testproject-v1.1"
                }
        project2 = {
                    "projectId" : "1234567",
                    "name": "testproject-v1.1"
                }
        version = {
            "update": {
                "fixVersions": [
                    {
                        "add": {
                            "name": "testproject-v1.1"
                        }
                    }
                ]
            }
        }
        mock_get_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        mock_get_request.side_effect = mock_get_project_versions
        mock_post_request.return_value.text = ''
        mock_post_request.return_value.status_code = 201
        mock_put_request.return_value.text = ''
        mock_put_request.return_value.status_code = 204
        mock_put_request.side_effect = mock_get_multiple_project_labels_response

        mock_get_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/project/TEST',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/TEST2',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/123456/versions',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/1234567/versions',
                                     headers=headers, timeout=timeout)
        ]

        mock_post_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/version',
                                     ANY, headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/version',
                                     ANY, headers=headers, timeout=timeout)
        ]
        
        mock_put_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     ANY, headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/issue/TEST2-456',
                                     ANY, headers=headers, timeout=timeout)
        ]

        _jira.tag_stories_in_commit(story_list=['TEST-123', 'TEST2-456'])
        mock_get_request.assert_has_calls(mock_get_calls, any_order=True)
        mock_post_request.assert_has_calls(mock_post_calls)
        mock_post_request_calls = mock_post_request.call_args_list
        call_args, call_kwargs = mock_post_request_calls[0]
        post_data_arg = call_args[1]
        assert project == json.loads(post_data_arg)
        call_args2, call_kwargs2 = mock_post_request_calls[1]
        post_data_arg2 = call_args2[1]
        assert project2 == json.loads(post_data_arg2)
        mock_put_request.assert_has_calls(mock_put_calls)
        mock_put_request_calls = mock_put_request.call_args_list
        for i, put_call in enumerate(mock_put_request_calls):
            call_args, call_kwargs = put_call
            put_data_arg = call_args[1]
            assert version == json.loads(put_data_arg)

def test_tag_stories_in_commit_for_multiple_projects_when_version_exists_on_one_project(monkeypatch):
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
    with patch('requests.get') as mock_get_request, patch('requests.post') as mock_post_request, patch('requests.put') as mock_put_request:
        basic_auth = base64.b64encode("{0}:{1}".format('flow_tester@homedepot.com', 'fake_token').encode('ascii')).decode('ascii')
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'Authorization': 'Basic {0}'.format(basic_auth)}
        timeout = 30
        project = {
                    "projectId" : "123456",
                    "name": "testproject-v1.0"
                }
        project2 = {
                    "projectId" : "1234567",
                    "name": "testproject-v1.0"
                }
        version = {
            "update": {
                "fixVersions": [
                    {
                        "add": {
                            "name": "testproject-v1.0"
                        }
                    }
                ]
            }
        }
        mock_get_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        mock_get_request.side_effect = mock_get_project_versions
        mock_post_request.return_value.text = ''
        mock_post_request.return_value.status_code = 201
        mock_put_request.return_value.text = ''
        mock_put_request.return_value.status_code = 204
        mock_put_request.side_effect = mock_get_multiple_project_labels_response

        mock_get_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/project/TEST',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/TEST2',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/123456/versions',
                                     headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/project/1234567/versions',
                                     headers=headers, timeout=timeout)
        ]

        mock_post_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/version',
                                     ANY, headers=headers, timeout=timeout)
        ]

        mock_put_calls = [
            call('http://happy.happy.joy.joy/rest/api/3/issue/TEST-123',
                                     ANY, headers=headers, timeout=timeout),
            call('http://happy.happy.joy.joy/rest/api/3/issue/TEST2-456',
                                     ANY, headers=headers, timeout=timeout)
        ]

        _jira.tag_stories_in_commit(story_list=['TEST-123', 'TEST2-456'])
        mock_get_request.assert_has_calls(mock_get_calls, any_order=True)
        mock_post_request.assert_has_calls(mock_post_calls)
        assert mock_post_request.call_count == 1
        mock_post_request_calls = mock_post_request.call_args_list
        call_args, call_kwargs = mock_post_request_calls[0]
        post_data_arg = call_args[1]
        assert project == json.loads(post_data_arg)
        mock_put_request.assert_has_calls(mock_put_calls)
        mock_put_request_calls = mock_put_request.call_args_list
        for i, put_call in enumerate(mock_put_request_calls):
            call_args, call_kwargs = put_call
            put_data_arg = call_args[1]
            assert version == json.loads(put_data_arg)

def test_story_bump_bug(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
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

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mock_get_multiple_project_ids_response
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

    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser
    with patch('requests.get') as mock_request:
        mock_request.side_effect = mock_get_multiple_project_ids_response
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
                                            "The build config may only contain 'projectKey' for single project key"
                                            " or 'projectKeys' containing an array of project keys", 'ERROR')


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


def test_init_missing_jira_project_key(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_project_id_dict

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            Jira(config_override=_b)

        mock_printmsg_fn.assert_called_with('Jira', '__init__',
                                            "The build config associated with projectTracking is missing key "
                                            "'projectKey'",
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
                                            "No jira user found in environment.  Did you define environment variable 'JIRA_USER'?",
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

def test_extract_story_id_with_empty_list(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        story_list = _jira.extract_story_id_from_commit_messages([])
        assert len(story_list) == 0

commit_example = [
"223342f Adding ability to specify artifactory user [TEST-100]",
"4326d00 Adding slack channel option for errors [TEST-102]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_two_stories(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        story_list = _jira.extract_story_id_from_commit_messages(commit_example)
        assert len(story_list) == 2

commit_example_nested_brackets = [
"223342f Adding ability to specify artifactory user [TEST-101, [bubba]]",
"4326d00 Adding slack channel option for errors [TEST-201]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_nested_brackets(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        story_list = _jira.extract_story_id_from_commit_messages(commit_example_nested_brackets)
        print(str(story_list))
        assert len(story_list) == 1


commit_example_multiple_per_brackets = [
"223342f Adding ability to specify artifactory user [TEST-100,TEST-101]",
"4326d00 Adding slack channel option for errors [TEST-98,TEST-99]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_multiple_per_brackets(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        story_list = _jira.extract_story_id_from_commit_messages(commit_example_multiple_per_brackets)
        print(str(story_list))
        assert len(story_list) == 4



commit_example_dedup = [
"223342f Adding ability to specify artifactory user [TEST-100,TEST-100]",
"4326d00 Adding slack channel option for errors [TEST-100,TEST-100]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_dedup(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)
        story_list = _jira.extract_story_id_from_commit_messages(commit_example_dedup)
        print(str(story_list))
        assert len(story_list) == 1

def test_flatten_story_details_with_None_story_details(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)

        flat_story_details = _jira.flatten_story_details(None)
        assert flat_story_details is None

def test_flatten_story_details_with_empty_story_details(monkeypatch):
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
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)

        flat_story_details = _jira.flatten_story_details([])
        assert len(flat_story_details) == 0

def test_flatten_story_details_with_story_details(monkeypatch):
    monkeypatch.setenv('JIRA_USER', 'flow_tester@homedepot.com')
    monkeypatch.setenv('JIRA_TOKEN', 'fake_token')

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    parser.add_section('jira')
    parser.set('jira', 'url', 'http://happy.happy.joy.joy')
    _b.settings = parser

    flat_story_expected = [
        {
            "story_type" : "bug",
            "id" : "TEST-123",
            "name" : "Test Bug",
            "url" : "http://happy.happy.joy.joy/browse/TEST-123",
            "current_state" : "In Progress",
            "description" : "This is a test bug description"
        },
        {
            "story_type" : "bug",
            "id" : "TEST-456",
            "name" : "Another test Bug",
            "url" : "http://happy.happy.joy.joy/browse/TEST-456",
            "current_state" : "Code Review",
            "description" : "Another test bug"
        }
    ]

    with patch('requests.get') as mock_request:
        mock_request.side_effect = mock_get_multiple_project_ids_response
        _jira = Jira(config_override=_b)

        current_test_directory = os.path.dirname(os.path.realpath(__file__))
        with open(current_test_directory + "/jira_stories_bug.json", 'r') as myfile:
            jira_data = myfile.read()
        story_details = json.loads(jira_data).get('stories')

        flat_story_details = _jira.flatten_story_details(story_details)
        assert flat_story_expected == flat_story_details
        for story in flat_story_details:
            assert 'story_type' in story
            assert 'id' in story
            assert 'name' in story
            assert 'description' in story
            assert 'url' in story
            assert 'current_state' in story

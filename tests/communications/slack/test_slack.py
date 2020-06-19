import configparser
import json
import os
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import ANY

import pytest
from flow.communications.slack.slack import Slack
from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "artifact": {
        "artifactoryDomain": "https://testdomain/artifactory",
        "artifactoryRepoKey": "release-repo",
        "artifactoryRepoKeySnapshot": "snapshot-repo",
        "artifactoryGroup": "group",
        "artifactType": "type",
        "artifactDirectory": "directory"
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

slack_webhook_url = 'https://hooks.slack.com/services/T03PB1F2E/B22KH4LAG/NOTAVLIDHOOK'

slack_request_for_custom_message = {
    "icon_emoji": ":robot_face:",
    "channel": "#spigot-ci",
    "username": "Flow",
    "attachments": [
        {
            "pretext": "Message \twith new line\r\n Testing",
            "fallback": "Message \twith new line\r\n Testing",
            "color": "#0000ff",
            "author_name": "testproject unittest rockyroad",
            "title_link": "",
            "footer": "Flow"
        }
    ]
}


def test_publish_deployment_missing_version(monkeypatch):
    monkeypatch.setenv('SLACK_WEBHOOK_URL', slack_webhook_url)

    current_test_directory = os.path.dirname(os.path.realpath(__file__))

    with open(current_test_directory + "/tracker_stories.json", 'r') as myfile:
        tracker_json_data = json.loads(myfile.read())
        with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
            with pytest.raises(SystemExit):
                _b = MagicMock(BuildConfig)
                _b.build_env_info = mock_build_config_dict['environments']['unittest']
                _b.json_config = mock_build_config_dict
                _b.project_name = mock_build_config_dict['projectInfo']['name']
                _b.version_number = None

                slack = Slack(config_override=_b)

                slack.publish_deployment(tracker_json_data)
                print(str(mock_printmsg_fn.mock_calls))

            mock_printmsg_fn.assert_called_with('commons', 'verify_version', 'Version not defined.  Is your repo tagged '
                                                                             'with a version number?', 'ERROR')


def test_publish_deployment_missing_webhook(monkeypatch):
    if os.getenv('SLACK_WEBHOOK_URL'):
        monkeypatch.delenv('SLACK_WEBHOOK_URL')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_dict['environments']['unittest']
            _b.json_config = mock_build_config_dict
            _b.project_name = mock_build_config_dict['projectInfo']['name']
            _b.version_number = 'v0.0.1'

            slack = Slack(config_override=_b)

            slack.publish_deployment('blah')
            print(str(mock_printmsg_fn.mock_calls))

        mock_printmsg_fn.assert_called_with('Slack', 'publish_deployment', 'No Slack URL was found in the environment.  Did you set  SLACK_WEBHOOK_URL in your pipeline?', 'ERROR')


def test_publish_deployment_no_valid_webhook(monkeypatch):
    _fake_slack_url = 'http://fake_url'
    monkeypatch.setenv('SLACK_WEBHOOK_URL', _fake_slack_url)

    with patch('requests.post') as mock_request:
        mock_request.return_value.text = {}
        mock_request.return_value.status_code = 404
        with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
            with pytest.raises(SystemExit):
                _b = MagicMock(BuildConfig)
                _b.build_env_info = mock_build_config_dict['environments']['unittest']
                _b.json_config = mock_build_config_dict
                _b.project_name = mock_build_config_dict['projectInfo']['name']
                parser = configparser.ConfigParser()
                parser.add_section('slack')
                _b.settings = parser
                _b.build_env = 'unittest'
                _b.version_number = 'v0.0.1'

                slk = Slack(config_override=_b)

                slk.publish_deployment(story_details={})

        mock_printmsg_fn.assert_called_with('Slack', 'publish_deployment', 'Failed sending slack message to '
                                            +_fake_slack_url+ '.  \r\n Response: {}')


def test_publish_custom_message(monkeypatch):
    monkeypatch.setenv('SLACK_WEBHOOK_URL', slack_webhook_url)

    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    parser = configparser.ConfigParser()
    parser.add_section('slack')
    _b.settings = parser
    _b.build_env = 'unittest'
    _b.version_number = 'rockyroad'
    with patch('requests.post') as mock_request:
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        timeout = 30
        _slack = Slack(config_override=_b)
        mock_request.return_value.text = {}
        mock_request.return_value.status_code = 200

        _slack.publish_custom_message("Message \twith new line\r\n Testing")

        assert mock_request.call_args[0][1] == json.dumps(slack_request_for_custom_message, default=lambda o: o.__dict__, sort_keys=False, indent=4)
        mock_request.assert_called_once_with(slack_webhook_url, ANY, headers=headers, timeout=timeout)


def test_publish_error_to_slack_missing_webhook(monkeypatch):
    monkeypatch.delenv('SLACK_WEBHOOK_URL', raising=False)

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        slack = Slack()
        slack.publish_error('test', 'test', 'test')

    mock_printmsg_fn.assert_any_call('Slack', 'publish_error', 'No Slack URL was found in the environment.  Did you set SLACK_WEBHOOK_URL in your pipeline?', 'WARN')








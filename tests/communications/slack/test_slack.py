import json
import os
from unittest.mock import MagicMock
from unittest.mock import patch

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


def test_publish_deployment_missing_version(monkeypatch):
    monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/NOTAREALWEBHOOK')

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

#TODO find out why this is failing with a circular reference
# def test_publish_deployment_no_valid_webhook(monkeypatch):
#     monkeypatch.setenv('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/T03PB1F2E/B22KH4LAG/NOTAVLIDHOOK')
#
#     with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
#         with pytest.raises(SystemExit) as cm:
#             _b = MagicMock(BuildConfig)
#             _b.build_env_info = mock_build_config_dict['environments']['unittest']
#             _b.json_config = mock_build_config_dict
#             _b.project_name = mock_build_config_dict['projectInfo']['name']
#             _b.version_number = 'v0.0.1'
#
#             slk = Slack(config_override=_b)
#
#             slk.publish_deployment()
#             print(str(mock_printmsg_fn.mock_calls))
#
#         mock_printmsg_fn.assert_called_with('Slack', 'publish_deployment', 'Failed sending slack message to https://hooks.slack.com/services/NOTAREALWEBHOOK')


def test_publish_error_to_slack_missing_webhook(monkeypatch):
    if os.getenv('SLACK_WEBHOOK_URL'):
        monkeypatch.delenv('SLACK_WEBHOOK_URL')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        Slack.publish_error('test', 'test', 'test', 'test', )
        print(str(mock_printmsg_fn.mock_calls))

    mock_printmsg_fn.assert_any_call('Slack', 'publish_error', 'No Slack URL was found in the environment.  Did you set SLACK_WEBHOOK_URL in your pipeline?', 'WARN')
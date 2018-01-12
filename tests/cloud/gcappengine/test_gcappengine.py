import os
from unittest.mock import patch
import pytest
import subprocess
from flow.cloud.gcappengine.gcappengine import GCAppEngine
from unittest.mock import MagicMock
from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "MyProjectName",
        "language": "java",
        "versionStrategy": "tracker"
    },
    "artifact": {
        "artifactoryDomain": "https://maven.artifactory.fake.com/artifactory",
        "artifactoryRepoKey": "libs-release-local",
        "artifactoryRepoKeySnapshot": "libs-snapshot-local",
        "artifactoryGroup": "com/fake/team",
        "artifactType": "tar.gz"
    },
    "github": {
        "org": "Org-GitHub",
        "repo": "Repo-GitHub",
        "URL": "https://github.fake.com/api/v3/repos"
    },
    "tracker": {
        "projectId": 2222222,
        "url": "https://www.pivotaltracker.com"
    },
    "slack": {
        "channel": "fake-deployments",
        "botName": "DeployBot",
        "emoji": ":package:"
    },
    "environments": {
        "develop": {
            "cf": {
                "apiEndpoint": "api.run-np.fake.com",
                "domain": "apps-np.fake.com",
                "space": "develop",
                "org": "org-awesome"
            },
            "artifactCategory": "snapshot",
            "associatedBranchName": "develop"
        }
    }
}

def test_init_missing_json_login(monkeypatch):
    if os.getenv('GCAPPENGINE_USER_JSON'):
        monkeypatch.delenv('GCAPPENGINE_USER_JSON')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _gcAppEngine = GCAppEngine()
            _gcAppEngine.deploy()

        mock_printmsg_fn.assert_called_with('GCAppEngine', '_verfify_required_attributes', 'Credentials not loaded.  Please define '
                                                                       'environment variable '
                                                                       '\'GCAPPENGINE_USER_JSON\'', 'ERROR')

def test_no_promote(monkeypatch):
    monkeypatch.setenv("PROMOTE", "false")

    _b = MagicMock(BuildConfig)
    _b.push_location = 'fordeployment'
    _b.build_env_info = mock_build_config_dict['environments']['develop']
    _b.json_config = mock_build_config_dict
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0.0'

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = ("EVERYTHING IS AWESOME", 'FAKE_RETURN')
            _gcAppEngine = GCAppEngine(config_override=_b)
            _gcAppEngine._gcloud_deploy('dummy.yml', promote=False)

        mock_printmsg_fn.assert_any_call('GCAppEngine', '_gcloud_deploy', 'gcloud app deploy fordeployment/dummy.yml '
                                                        '--quiet --version v1-0-0 --no-promote')


def test_promote(monkeypatch):
    monkeypatch.setenv("PROMOTE", "false")

    _b = MagicMock(BuildConfig)
    _b.push_location = 'fordeployment'
    _b.build_env_info = mock_build_config_dict['environments']['develop']
    _b.json_config = mock_build_config_dict
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0.0'

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = ("EVERYTHING IS AWESOME", 'FAKE_RETURN')
            _gcAppEngine = GCAppEngine(config_override=_b)
            _gcAppEngine._gcloud_deploy('dummy.yml', promote=True)

        mock_printmsg_fn.assert_any_call('GCAppEngine', '_gcloud_deploy', 'gcloud app deploy fordeployment/dummy.yml --quiet --version v1-0-0 ')
import os
import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from flow.cloud.cloudfoundry.cloudfoundry import CloudFoundry

from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "environments": {
        "unittest": {
            "cf": {
                "apiEndpoint": "api.run-np.fake.com",
                "domain": "apps-np.fake.com",
                "space": "development",
                "org": "ci"
            },
            "artifactCategory": "snapshot",
            "associatedBranchName": "develop"
        }
    }
}

mock_build_config_dict_missing_project_name = {
    "projectInfo": {
    },
    "environments": {
        "unittest": {
            "cf": {
                "apiEndpoint": "api.run-np.fake.com",
                "domain": "apps-np.fake.com",
                "space": "development",
                "org": "ci"
            },
            "artifactCategory": "snapshot",
            "associatedBranchName": "develop"
        }
    }
}

mock_build_config_missing_space_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "environments": {
        "unittest": {
            "cf": {
                "apiEndpoint": "api.run-np.fake.com",
                "domain": "apps-np.fake.com",
                "org": "ci"
            },
            "artifactCategory": "snapshot",
            "associatedBranchName": "develop"
        }
    }
}


mock_build_config_missing_apiEndpoint_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "environments": {
        "unittest": {
            "cf": {
                "domain": "apps-np.fake.com",
                "space": "development",
                "org": "ci"
            },
            "artifactCategory": "snapshot",
            "associatedBranchName": "develop"
        }
    }
}


mock_build_config_missing_org_dict = {
    "projectInfo": {
        "name": "testproject"
    },
    "environments": {
        "unittest": {
            "cf": {
                "apiEndpoint": "api.run-np.fake.com",
                "domain": "apps-np.fake.com",
                "space": "development"
            },
            "artifactCategory": "snapshot",
            "associatedBranchName": "develop"
        }
    }
}

mock_started_apps_already_started = 'CI-HelloWorld-v2.9.0+1'

def test_verify_required_attributes_missing_user(monkeypatch):
    if os.getenv('DEPLOYMENT_USER'):
        monkeypatch.delenv('DEPLOYMENT_USER')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _cf = CloudFoundry()
            _cf._verify_required_attributes()

    mock_printmsg_fn.assert_called_with('CloudFoundry', '_verify_required_attributes', "No User Id. Did you forget to define environment variable 'DEPLOYMENT_USER?", 'ERROR')


def test_verify_required_attributes_missing_pwd(monkeypatch):
    monkeypatch.setenv('DEPLOYMENT_USER', 'DUMMY')

    if os.getenv('DEPLOYMENT_PWD'):
        monkeypatch.delenv('DEPLOYMENT_PWD')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _cf = CloudFoundry()
            _cf._verify_required_attributes()

    mock_printmsg_fn.assert_called_with('CloudFoundry', '_verify_required_attributes', "No User Password. Did you forget to define environment variable 'DEPLOYMENT_PWD'?", 'ERROR')


def test_verify_required_attributes_missing_project_name(monkeypatch):
    monkeypatch.setenv('DEPLOYMENT_USER', 'DUMMY')
    monkeypatch.setenv('DEPLOYMENT_PWD', 'DUMMY')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_dict_missing_project_name['environments']['unittest']
            _b.json_config = mock_build_config_dict_missing_project_name
            _b.version_number = None
            _b.project_name = None

            _cf = CloudFoundry(_b)
            _cf._verify_required_attributes()

    mock_printmsg_fn.assert_called_with('CloudFoundry', '_verify_required_attributes', "The build config associated with cloudfoundry is missing key 'name'", 'ERROR')


def test_verify_required_attributes_missing_endpoint(monkeypatch):
    monkeypatch.setenv('DEPLOYMENT_USER', 'DUMMY')
    monkeypatch.setenv('DEPLOYMENT_PWD', 'DUMMY')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_missing_apiEndpoint_dict['environments']['unittest']
            _b.json_config = mock_build_config_missing_apiEndpoint_dict
            _b.version_number = None

            _cf = CloudFoundry(_b)
            _cf._verify_required_attributes()

    mock_printmsg_fn.assert_called_with('CloudFoundry', '_verify_required_attributes', "The build config associated with cloudfoundry is missing key 'apiEndpoint'", 'ERROR')


def test_verify_required_attributes_missing_space(monkeypatch):
    monkeypatch.setenv('DEPLOYMENT_USER', 'DUMMY')
    monkeypatch.setenv('DEPLOYMENT_PWD', 'DUMMY')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_missing_space_dict['environments']['unittest']
            _b.json_config = mock_build_config_missing_space_dict
            _b.version_number = None

            _cf = CloudFoundry(_b)
            _cf._verify_required_attributes()

    mock_printmsg_fn.assert_called_with('CloudFoundry', '_verify_required_attributes', "The build config associated with cloudfoundry is missing key 'space'", 'ERROR')


def test_verify_required_attributes_missing_org(monkeypatch):
    monkeypatch.setenv('DEPLOYMENT_USER', 'DUMMY')
    monkeypatch.setenv('DEPLOYMENT_PWD', 'DUMMY')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_missing_org_dict['environments']['unittest']
            _b.json_config = mock_build_config_missing_org_dict
            _b.version_number = None

            _cf = CloudFoundry(_b)
            _cf._verify_required_attributes()

    mock_printmsg_fn.assert_called_with('CloudFoundry', '_verify_required_attributes', "The build config associated with cloudfoundry is missing key 'org'", 'ERROR')


def test_get_started_apps_already_started():

        with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:

            with patch.object(subprocess, 'Popen') as mocked_popen:
                with pytest.raises(SystemExit):
                    mocked_popen.return_value.returncode = 0
                    mocked_popen.return_value.communicate.return_value = (mock_started_apps_already_started.encode(),
                                                                          'FAKE_ERR_OUTPUT')
                    _b = MagicMock(BuildConfig)
                    _b.project_name = 'CI-HelloWorld'
                    _b.version_number = 'v2.9.0+1'
                    _cf = CloudFoundry(_b)

                    with patch.object(_cf, '_cf_logout'):
                        _cf._get_started_apps()

        mock_printmsg_fn.assert_any_call('CloudFoundry', '_get_started_apps', "App version CI-HelloWorld-v2.9.0+1 "
                                                                              "already exists and is running. Cannot "
                                                                              "perform zero-downtime deployment.  To "
                                                                              "override, set force flag = 'true'",
                                         'ERROR')


def test_get_started_apps_already_started_force_deploy():

        with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
            with patch.object(subprocess, 'Popen') as mocked_popen:
                mocked_popen.return_value.returncode = 0
                mocked_popen.return_value.communicate.return_value = (mock_started_apps_already_started.encode(), 'FAKE_ERR_OUTPUT')
                _b = MagicMock(BuildConfig)
                _b.project_name = 'CI-HelloWorld'
                _b.version_number = 'v2.9.0+1'
                _cf = CloudFoundry(_b)

                with patch.object(_cf, '_cf_logout'):
                    _cf._get_started_apps(True)
        mock_printmsg_fn.assert_any_call('CloudFoundry', '_get_started_apps', "Already found CI-HelloWorld-v2.9.0+1 but force_deploy turned on. Continuing with deployment.  Downtime will occur during deployment.")


def test_get_started_apps_already_started_failed_cmd():

        with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
            with pytest.raises(SystemExit):
                with patch.object(subprocess, 'Popen') as mocked_popen:
                    mocked_popen.return_value.returncode = 1
                    mocked_popen.return_value.communicate.return_value = (mock_started_apps_already_started.encode(), 'FAKE_ERR_OUTPUT')
                    _b = MagicMock(BuildConfig)
                    _b.project_name = 'CI-HelloWorld'
                    _b.version_number = 'v2.9.0+1'
                    _cf = CloudFoundry(_b)

                    with patch.object(_cf, '_cf_logout'):
                        _cf._get_started_apps('true')
        mock_printmsg_fn.assert_any_call('CloudFoundry', '_get_started_apps', "Failed calling cf apps | grep CI-HelloWorld*-v\\d*\\.\\d*\\.\\d* | grep started | awk '{print $1}'. Return code of 1", 'ERROR')




def test_find_deployable_multiple_files():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            with patch('os.listdir', return_value=['file1.txt', 'file2.txt', 'file3.txt']):
                with patch('os.path.isfile', return_value=True):
                    _b = MagicMock(BuildConfig)
                    _b.project_name = 'CI-HelloWorld'
                    _b.version_number = 'v2.9.0+1'
                    _b.push_location = 'fordeployment'
                    _cf = CloudFoundry(_b)

                    _cf.find_deployable('txt', 'fake_push_dir')

    mock_printmsg_fn.assert_called_with('Cloud', 'find_deployable', 'Found more than 1 artifact in fake_push_dir',
                                        'ERROR')

# def test_find_deployable_no_files_only_directories():
#     with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
#         with pytest.raises(SystemExit):
#             with patch('os.listdir', return_value=['file1.txt', 'file2.txt', 'file3.txt']):
#                 with patch('os.path.isfile', return_value=False):
#                     _b = MagicMock(BuildConfig)
#                     _b.project_name = 'CI-HelloWorld'
#                     _b.version_number = 'v2.9.0+1'
#                     _b.push_location = 'fordeployment'
#                     _cf = CloudFoundry(_b)
#                     _cf.find_deployable('txt', 'fake_push_dir')
#
#     mock_printmsg_fn.assert_called_with('Cloud', 'find_deployable', 'Could not find file of type txt in fake_push_dir',
#                                         'ERROR')


def test_find_deployable_no_files_only_directories():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            with patch('os.listdir', return_value=['file1.txt', 'file2.txt', 'file3.txt']):
                with patch('os.path.isfile', return_value=False):
                    _b = MagicMock(BuildConfig)
                    _b.project_name = 'CI-HelloWorld'
                    _b.version_number = 'v2.9.0+1'
                    _b.push_location = 'fordeployment'
                    _cf = CloudFoundry(_b)
                    _cf.find_deployable('txt', 'fake_push_dir')

    mock_printmsg_fn.assert_called_with('Cloud', 'find_deployable', 'Could not find file of type txt in fake_push_dir',
                                        'ERROR')

def test_find_deployable_one_file():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('zipfile.ZipFile') as mocked_ZipFile:
            mocked_ZipFile.return_value.returncode = 0
            with patch('os.listdir', return_value=['file1.jar', 'file2.abc', 'file3.abc']):
                with patch('os.path.isfile', return_value=True):
                    _b = MagicMock(BuildConfig)
                    _b.project_name = 'CI-HelloWorld'
                    _b.version_number = 'v2.9.0+1'
                    _b.push_location = 'fordeployment'
                    _cf = CloudFoundry(_b)

                    _cf.find_deployable('jar', 'fake_push_dir')

    mock_printmsg_fn.assert_any_call('Cloud', 'find_deployable', 'Looking for a jar in fake_push_dir')


def test_push_location_returns_empty_for_docker_artifact_type():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.artifact_extension = 'docker'
        _cf = CloudFoundry(_b)

        result = _cf._determine_push_location()

    assert result == ""


def test_push_location_for_zip_artifact_type():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.artifact_extension = 'zip'
        _b.push_location = 'fordeployment'
        _cf = CloudFoundry(_b)

        result = _cf._determine_push_location()

    assert result == "-p fordeployment"


def test_push_location_for_tar_artifact_type():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.artifact_extension = 'tar'
        _b.push_location = 'fordeployment'
        _cf = CloudFoundry(_b)

        result = _cf._determine_push_location()

    assert result == "-p fordeployment"


def test_push_location_for_tar_gz_artifact_type():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.artifact_extension = 'tar.gz'
        _b.push_location = 'fordeployment'
        _cf = CloudFoundry(_b)

        result = _cf._determine_push_location()

    assert result == "-p fordeployment"


def test_push_location_for_jar_artifact_type():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('os.listdir', return_value=['file1.jar', 'file2.war', 'file3.abc']):
            with patch('os.path.isfile', return_value=True):
                _b = MagicMock(BuildConfig)
                _b.artifact_extension = 'jar'
                _b.push_location = 'fake_push_dir'
                _cf = CloudFoundry(_b)
                result = _cf._determine_push_location()


    mock_printmsg_fn.assert_any_call('Cloud', 'find_deployable', 'Looking for a jar in fake_push_dir')

    assert result == "-p fake_push_dir/file1.jar"


def test_push_location_for_war_artifact_type():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('os.listdir', return_value=['file1.jar', 'file2.war', 'file3.abc']):
            with patch('os.path.isfile', return_value=True):
                _b = MagicMock(BuildConfig)
                _b.artifact_extension = 'war'
                _b.push_location = 'fake_push_dir'
                _cf = CloudFoundry(_b)
                result = _cf._determine_push_location()


    mock_printmsg_fn.assert_any_call('Cloud', 'find_deployable', 'Looking for a war in fake_push_dir')

    assert result == "-p fake_push_dir/file2.war"


def test_determine_push_location_called_by_cf_push():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('os.listdir', return_value=['file1.jar', 'file2.war', 'file3.abc']):
            with patch('os.path.isfile', return_value=True):
                with patch.object(subprocess, 'Popen') as mocked_popen:
                    mocked_popen.return_value.returncode = 0
                    _b = MagicMock(BuildConfig)
                    _b.artifact_extension = 'war'
                    _b.push_location = 'fake_push_dir'
                    _cf = CloudFoundry(_b)
                
                    _cf._cf_push('fake_manifest.yml')

    mock_printmsg_fn.assert_any_call('Cloud', 'find_deployable', 'Looking for a war in fake_push_dir')
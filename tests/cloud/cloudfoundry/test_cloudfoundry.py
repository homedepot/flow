import os
import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch
from subprocess import TimeoutExpired

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
mock_list_of_existing_apps = [ 'CI-HelloWorld-v2.9.0+1'.encode(), 'CI-HelloWorld-v2.7.0'.encode(), 'CI-HelloWorld-v2.8.0+12'.encode(), 'CI-HelloWorld-v1.15.2'.encode()]
mock_routes_domains_output = 'CI-HelloWorld apps-np.fake.com'

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

def test_fetch_app_routes():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (mock_routes_domains_output.encode(),
                                                                          'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)

            result = _cf._fetch_app_routes('CI-HelloWorld-v2.9.0+1'.encode())
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_fetch_app_routes', 'cf routes grep CI-HelloWorld-v2.9.0+1 [\'awk\', \'{{print $2,$3}}\']')
    assert result is not None
    assert result.decode("utf-8") == mock_routes_domains_output

def test_fetch_app_routes_with_no_routes_returned():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (''.encode(),
                                                                        'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)

            result = _cf._fetch_app_routes('CI-HelloWorld-v2.9.0+1'.encode())
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_fetch_app_routes', 'cf routes grep CI-HelloWorld-v2.9.0+1 [\'awk\', \'{{print $2,$3}}\']')
    assert result.decode("utf-8") == ''

def test_fetch_app_routes_with_error():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.returncode = 1
            mocked_popen.return_value.communicate.return_value = (''.encode(),
                                                                        'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)

            result = _cf._fetch_app_routes('CI-HelloWorld-v2.9.0+1'.encode())
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_fetch_app_routes', 'cf routes grep CI-HelloWorld-v2.9.0+1 [\'awk\', \'{{print $2,$3}}\']')
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_fetch_app_routes', 'Failed calling cf routes grep CI-HelloWorld-v2.9.0+1 [\'awk\', \'{{print $2,$3}}\']. Return code of 1', 'ERROR')
    assert result is None

def test_fetch_app_routes_with_timeout():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            mocked_popen.return_value.returncode = 1
            mocked_popen.return_value.communicate.side_effect = TimeoutExpired("get_routes", 1)
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)

            result = _cf._fetch_app_routes('CI-HelloWorld-v2.9.0+1'.encode())
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_fetch_app_routes', 'cf routes grep CI-HelloWorld-v2.9.0+1 [\'awk\', \'{{print $2,$3}}\']')
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_fetch_app_routes', 'Timed out calling cf routes grep CI-HelloWorld-v2.9.0+1 [\'awk\', \'{{print $2,$3}}\']', 'ERROR')
    assert result is None

def test_split_app_routes_to_list():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _cf = CloudFoundry(_b)

        result_routes, result_domains = _cf._split_app_routes_to_list(mock_routes_domains_output.encode())
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_split_app_routes_to_list', 'Found route CI-HelloWorld')
    assert len(result_routes) == 1
    assert result_routes[0] == 'CI-HelloWorld'
    assert len(result_domains) == 1
    assert result_domains[0] == 'apps-np.fake.com'

def test_split_app_routes_to_list_when_input_is_empty():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _cf = CloudFoundry(_b)

        result_routes, result_domains = _cf._split_app_routes_to_list(''.encode())
    assert mock_printmsg_fn.call_count == 4 #begin/end for both init and function
    assert len(result_routes) == 0
    assert len(result_domains) == 0

def test_split_app_routes_to_list_when_input_is_None():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _cf = CloudFoundry(_b)

        result_routes, result_domains = _cf._split_app_routes_to_list(None)
    assert mock_printmsg_fn.call_count == 4 #begin/end for both init and function
    assert len(result_routes) == 0
    assert len(result_domains) == 0

def test_get_routes_domains_for_latest_in_app_list():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _cf = CloudFoundry(_b)
        with patch.object(_cf, '_fetch_app_routes') as mock_fetch_app_routes_fn:
            mock_fetch_app_routes_fn.return_value = mock_routes_domains_output.encode()
            result_version, result_routes, result_domains = _cf._get_routes_domains_for_latest_in_app_list(mock_list_of_existing_apps)
    assert result_version.decode("utf-8") == 'CI-HelloWorld-v2.9.0+1'
    assert len(result_routes) == 1
    assert result_routes[0] == 'CI-HelloWorld'
    assert len(result_domains) == 1
    assert result_domains[0] == 'apps-np.fake.com'

def test_get_routes_domains_for_latest_in_app_list_with_no_routes():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _cf = CloudFoundry(_b)
        with patch.object(_cf, '_fetch_app_routes') as mock_fetch_app_routes_fn:
            mock_fetch_app_routes_fn.return_value = ''.encode()
            result_version, result_routes, result_domains = _cf._get_routes_domains_for_latest_in_app_list(mock_list_of_existing_apps)
    assert result_version.decode("utf-8") == 'CI-HelloWorld-v2.9.0+1'
    assert len(result_routes) == 0
    assert len(result_domains) == 0

def test_get_routes_domains_for_empty_app_list():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result_version, result_routes, result_domains = _cf._get_routes_domains_for_latest_in_app_list([])
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_get_routes_domains_for_latest_in_app_list', 'App list is empty, cannot retrieve routes without at least one app', 'ERROR')

def test_modify_route_for_app_map_route():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_route = 'CI-HelloWorld'
            input_domain = 'apps-np.fake.com'
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_route_action = 'map'
            return_string="Adding route {route}.{domain} from app {app} in org test / space test as TEST_USER...".format(
                route = input_route,
                domain = input_domain,
                app = input_app
            )
            command_string = 'cf {action}-route {app} {domain} -n {route}'.format(
                action = input_route_action,
                app = input_app,
                domain = input_domain,
                route = input_route
            )
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (return_string.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._modify_route_for_app(input_route, input_app, input_domain, input_route_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', return_string)
    assert result == False

def test_modify_route_for_app_unmap_route():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_route = 'CI-HelloWorld'
            input_domain = 'apps-np.fake.com'
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_route_action = 'unmap'
            return_string="Removing route {route}.{domain} from app {app} in org test / space test as TEST_USER...".format(
                route = input_route,
                domain = input_domain,
                app = input_app
            )
            command_string = 'cf {action}-route {app} {domain} -n {route}'.format(
                action = input_route_action,
                app = input_app,
                domain = input_domain,
                route = input_route
            )
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (return_string.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._modify_route_for_app(input_route, input_app, input_domain, input_route_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', return_string)
    assert result == False

def test_modify_route_for_app_bad_action():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            input_route = 'CI-HelloWorld'
            input_domain = 'apps-np.fake.com'
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_route_action = 'badmap'
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._modify_route_for_app(input_route, input_app, input_domain, input_route_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', "Modify route action was {action} it must be either "
                                                          "\"map\" or \"unmap\"".format(
                                                          action=input_route_action),
                                                          'ERROR')

def test_modify_route_for_app_map_route_non_zero_return():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_route = 'CI-HelloWorld'
            input_domain = 'apps-np.fake.com'
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_route_action = 'map'
            return_string="Adding route {route}.{domain} from app {app} in org test / space test as TEST_USER...".format(
                route = input_route,
                domain = input_domain,
                app = input_app
            )
            command_string = 'cf {action}-route {app} {domain} -n {route}'.format(
                action = input_route_action,
                app = input_app,
                domain = input_domain,
                route = input_route
            )
            mocked_popen.return_value.returncode = 1
            mocked_popen.return_value.communicate.return_value = (return_string.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._modify_route_for_app(input_route, input_app, input_domain, input_route_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', return_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', 'Failed calling {command}. Return code of {rtn}'.format(
                                        command = command_string,
                                        rtn = 1
                                        ), 'ERROR')
    assert result == True

def test_modify_route_for_app_with_timeout():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_route = 'CI-HelloWorld'
            input_domain = 'apps-np.fake.com'
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_route_action = 'map'
            return_string="Adding route {route}.{domain} from app {app} in org test / space test as TEST_USER...".format(
                route = input_route,
                domain = input_domain,
                app = input_app
            )
            command_string = 'cf {action}-route {app} {domain} -n {route}'.format(
                action = input_route_action,
                app = input_app,
                domain = input_domain,
                route = input_route
            )
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.side_effect = TimeoutExpired("modify_route", 1)
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._modify_route_for_app(input_route, input_app, input_domain, input_route_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_modify_route_for_app', 'Timed out calling {cmd}'.format(
                                        cmd = command_string
                                        ), 'ERROR')
    assert result == True

def test_start_stop_delete_app_with_start_action():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_app_action = 'start'
            return_string='Starting app {app} in org test / space test as TEST_USER'.format(
                app=input_app
            )
            command_string = 'cf {action} {app} -f'.format(
                action = input_app_action,
                app = input_app
            )
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (return_string.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._start_stop_delete_app(input_app, input_app_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', return_string)
    assert result == False

def test_start_stop_delete_app_with_stop_action():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_app_action = 'stop'
            return_string='Stopping app {app} in org test / space test as TEST_USER'.format(
                app=input_app
            )
            command_string = 'cf {action} {app} -f'.format(
                action = input_app_action,
                app = input_app
            )
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (return_string.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._start_stop_delete_app(input_app, input_app_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', return_string)
    assert result == False

def test_start_stop_delete_app_with_delete_action():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_app_action = 'delete'
            return_string='Deleting app {app} in org test / space test as TEST_USER'.format(
                app=input_app
            )
            command_string = 'cf {action} {app} -f'.format(
                action = input_app_action,
                app = input_app
            )
            mocked_popen.return_value.returncode = 0
            mocked_popen.return_value.communicate.return_value = (return_string.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._start_stop_delete_app(input_app, input_app_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', return_string)
    assert result == False

def test_start_stop_delete_app_with_unexpected_action():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_app_action = 'unexpected'
            error_string = 'App action was {action}: it must be either "start", "stop" or "delete"'.format(action=input_app_action)
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._start_stop_delete_app(input_app, input_app_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', error_string, 'ERROR')

def test_start_stop_delete_app_with_non_zero_return_code():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch.object(subprocess, 'Popen') as mocked_popen:
            input_app = 'CI-HelloWorld-v2.9.0+1'
            input_app_action = 'delete'
            command_string = 'cf {action} {app} -f'.format(
                action = input_app_action,
                app = input_app
            )
            error_string = 'Failed calling {command}. Return code of {rtn}'.format(
                command=command_string,
                rtn=1
            )
            mocked_popen.return_value.returncode = 1
            mocked_popen.return_value.communicate.return_value = (''.encode(),
                                                                  'FAKE_ERR_OUTPUT')
            _b = MagicMock(BuildConfig)
            _cf = CloudFoundry(_b)
            result = _cf._start_stop_delete_app(input_app, input_app_action)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', error_string, 'ERROR')
    assert result == True

def test_start_stop_delete_app_with_timeout():
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(TimeoutExpired):
            with patch.object(subprocess, 'Popen') as mocked_popen:
                input_app = 'CI-HelloWorld-v2.9.0+1'
                input_app_action = 'delete'
                command_string = 'cf {action} {app} -f'.format(
                    action = input_app_action,
                    app = input_app
                )
                error_string = 'Timed out calling {command}'.format(command=command_string)
                mocked_popen.return_value.returncode = 0
                mocked_popen.return_value.communicate.side_effect = TimeoutExpired("modify_app_state", 1)
                _b = MagicMock(BuildConfig)
                _cf = CloudFoundry(_b)
                result = _cf._start_stop_delete_app(input_app, input_app_action)
                assert result == False # this is here because result wasn't defined at top level
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', command_string)
    mock_printmsg_fn.assert_any_call('CloudFoundry', '_start_stop_delete_app', error_string, 'ERROR')
    assert mocked_popen.return_value.communicate.call_count == 2
    
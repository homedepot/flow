import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import responses
from flow.buildconfig import BuildConfig
from requests.exceptions import HTTPError

from flow.artifactstorage.artifactory.artifactory import ArtiFactory, ArtifactException

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

mock_build_config_artifactoryConfig_include_POM = {
    "projectInfo": {
        "name": "testproject"
    },
    "artifactoryConfig": {
        "artifactoryDomain": "https://testdomain/artifactory",
        "artifactoryRepoKey": "release-repo",
        "artifactoryRepoKeySnapshot": "snapshot-repo",
        "artifactoryGroup": "group",
        "artifactType": "type",
        "artifactDirectory": "directory",
        "includePom": "true"
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



mock_build_config_missing_artifact_dict = {
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
response_body_artifactory = """
{
  "repo" : "release-repo",
  "path" : "/group/testproject/v1.0.0",
  "created" : "2016-09-09T13:02:49.851-04:00",
  "createdBy" : "svc_cicd",
  "lastModified" : "2016-09-09T13:02:49.851-04:00",
  "modifiedBy" : "svc_cicd",
  "lastUpdated" : "2016-09-09T13:02:49.851-04:00",
  "children" : [ {
    "uri" : "/unittest",
    "folder" : true
  }, {
    "uri" : "/testproject.bob",
    "folder" : false
  },
   {
    "uri" : "/testproject.vcl",
    "folder" : false
  }
  ],
  "uri" : "https://maven.artifactory.fake.com/artifactory/api/storage/libs-release-local/com/fake/thd-store-info-service/v1.2.0"
}
"""

response_body_artifactory_no_matching_children = """
{
  "repo" : "release-repo",
  "path" : "/group/testproject/v1.0.0",
  "created" : "2016-09-09T13:02:49.851-04:00",
  "createdBy" : "svc_cicd",
  "lastModified" : "2016-09-09T13:02:49.851-04:00",
  "modifiedBy" : "svc_cicd",
  "lastUpdated" : "2016-09-09T13:02:49.851-04:00",
  "children" : [ {
    "uri" : "/unittest",
    "folder" : true
  }, {
    "uri" : "/testproject.nonexistenttype",
    "folder" : false
  } ],
  "uri" : "https://maven.artifactory.fake.com/artifactory/api/storage/libs-release-local/com/fake/thd-store-info-service/v1.2.0"
}
"""

response_body_artifactory_no_children = """
{
  "repo" : "release-repo",
  "path" : "/group/testproject/v1.0.0",
  "created" : "2016-09-09T13:02:49.851-04:00",
  "createdBy" : "svc_cicd",
  "lastModified" : "2016-09-09T13:02:49.851-04:00",
  "modifiedBy" : "svc_cicd",
  "lastUpdated" : "2016-09-09T13:02:49.851-04:00",
  "children" : [ ],
  "uri" : "https://maven.artifactory.fake.com/artifactory/api/storage/libs-release-local/com/fake/thd-store-info-service/v1.2.0"
}
"""

response_body_artifactory_not_found = """
{
  "errors" : [ {
    "status" : 404,
    "message" : "Unable to find item"
  } ]
}
"""

@responses.activate
def test_get_urls_of_artifacts():
    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0.0'
    _b.artifact_extension = None
    _b.artifact_extensions = ["bob", "vcl"]
    art = ArtiFactory(config_override=_b)

    test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

    responses.add(responses.GET,
                  test_url,
                  body=response_body_artifactory,
                  status=200,
                  content_type="application/json")

    urls = art.get_urls_of_artifacts()

    assert urls == ["https://testdomain/artifactory/release-repo/group/testproject/v1.0.0/testproject.bob", "https://testdomain/artifactory/release-repo/group/testproject/v1.0.0/testproject.vcl"]

@responses.activate
def test_get_artifact_url():
    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0.0'
    _b.artifact_extension = 'bob'
    _b.artifact_extensions = None
    art = ArtiFactory(config_override=_b)

    test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

    responses.add(responses.GET,
                  test_url,
                  body=response_body_artifactory,
                  status=200,
                  content_type="application/json")

    url = art.get_artifact_url()

    assert url == "https://testdomain/artifactory/release-repo/group/testproject/v1.0.0/testproject.bob"

@responses.activate
def test_get_artifact_with_includePom():
    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_artifactoryConfig_include_POM['environments']['unittest']
    _b.json_config = mock_build_config_artifactoryConfig_include_POM
    _b.project_name = mock_build_config_artifactoryConfig_include_POM['projectInfo']['name']
    _b.include_pom = mock_build_config_artifactoryConfig_include_POM['artifactoryConfig']['includePom']
    _b.version_number = 'v1.0.0'
    _b.artifact_extension = 'bob'
    _b.artifact_extensions = None
    art = ArtiFactory(config_override=_b)

    test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

    responses.add(responses.GET,
                  test_url,
                  body=response_body_artifactory,
                  status=200,
                  content_type="application/json")

    url = art.get_artifact_url()

    assert url == "https://testdomain/artifactory/release-repo/group/testproject/v1.0.0/testproject.bob"


@responses.activate
def test_get_artifact_url_failure():

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.build_env_info = mock_build_config_dict['environments']['unittest']
        _b.json_config = mock_build_config_dict
        _b.project_name = mock_build_config_dict['projectInfo']['name']
        _b.version_number = 'v1.0.0'

        art = ArtiFactory(config_override=_b)

        test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

        exception = HTTPError('Something went wrong')
        responses.add(responses.GET,
                      test_url,
                      body=exception)

        with pytest.raises(ArtifactException) as cm:
            art.get_artifact_url()

        print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with('ArtiFactory', 'get_artifact_url', 'Unable to locate artifactory path https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0', 'ERROR')


@responses.activate
def test_get_artifact_url_not_found():

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.build_env_info = mock_build_config_dict['environments']['unittest']
        _b.json_config = mock_build_config_dict
        _b.project_name = mock_build_config_dict['projectInfo']['name']
        _b.version_number = 'v1.0.0'

        art = ArtiFactory(config_override=_b)

        test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

        responses.add(responses.GET,
                      test_url,
                      body=response_body_artifactory_not_found,
                      status=404,
                      content_type="application/json")

        with pytest.raises(ArtifactException) as cm:
            art.get_artifact_url()

        print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with('ArtiFactory', 'get_artifact_url', 'Unable to locate artifactory path https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0\r\n Response: \n{\n  "errors" : [ {\n    "status" : 404,\n    "message" : "Unable to find item"\n  } ]\n}\n', 'ERROR')


@responses.activate
def test_get_artifact_url_specified_type_does_not_exist():

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.build_env_info = mock_build_config_dict['environments']['unittest']
        _b.json_config = mock_build_config_dict
        _b.project_name = mock_build_config_dict['projectInfo']['name']
        _b.version_number = 'v1.0.0'
        _b.artifact_extension = 'bob'

        art = ArtiFactory(config_override=_b)

        test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

        responses.add(responses.GET,
                      test_url,
                      body=response_body_artifactory_no_matching_children,
                      status=200,
                      content_type="application/json")

        with pytest.raises(ArtifactException) as cm:
            art.get_artifact_url()

        print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with('ArtiFactory', 'get_artifact_url', 'Could not locate artifact bob',
                                            'ERROR')


@responses.activate
def test_get_artifact_url_specified_path_has_no_children():

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        _b = MagicMock(BuildConfig)
        _b.build_env_info = mock_build_config_dict['environments']['unittest']
        _b.json_config = mock_build_config_dict
        _b.project_name = mock_build_config_dict['projectInfo']['name']
        _b.version_number = 'v1.0.0'
        _b.artifact_extension = 'bob'
        _b.artifact_extensions = None

        art = ArtiFactory(config_override=_b)

        test_url = "https://testdomain/artifactory/api/storage/release-repo/group/testproject/v1.0.0"

        responses.add(responses.GET,
                      test_url,
                      body=response_body_artifactory_no_children,
                      status=200,
                      content_type="application/json")

        with pytest.raises(ArtifactException) as cm:
            art.get_artifact_url()

        print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with('ArtiFactory', 'get_artifact_url', 'Could not locate artifact bob',
                                            'ERROR')


def test__get_artifactory_file_name_directory_not_defined(monkeypatch):
    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0.0'

    art = ArtiFactory(config_override=_b)

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        if os.getenv('ARTIFACT_BUILD_DIRECTORY'):
            monkeypatch.delenv('ARTIFACT_BUILD_DIRECTORY')

        with pytest.raises(SystemExit) as cm:
            art._get_artifactory_files_name_from_build_dir()

        print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with('ArtiFactory', '_get_artifactory_files_name_from_build_dir', ('Missing artifact build path. Did you forget to define the environment variable \'ARTIFACT_BUILD_DIRECTORY\'? '), 'ERROR')


# def foo(self, test1, test2):
#     print(test1)
#     print(test2)
#     pass

# @patch('utils.commons.CommonUtils.get_files_of_type_from_directory', new=foo)
def test__get_artifactory_files_name_no_artifact_found(monkeypatch):
    _b = MagicMock(BuildConfig)
    _b.build_env_info = mock_build_config_dict['environments']['unittest']
    _b.json_config = mock_build_config_dict
    _b.project_name = mock_build_config_dict['projectInfo']['name']
    _b.version_number = 'v1.0.0'
    _b.artifact_extension = 'bob'
    _b.artifact_extensions = None

    art = ArtiFactory(config_override=_b)

    def _get_files_of_type_from_directory(type, directory):
        print(type)
        print(directory)

    with patch('flow.utils.commons.get_files_of_type_from_directory', new=_get_files_of_type_from_directory):
        with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
            monkeypatch.setenv('ARTIFACT_BUILD_DIRECTORY', 'mydir')

            with pytest.raises(SystemExit) as cm:
                art._get_artifactory_files_name_from_build_dir()

            print(str(mock_printmsg_fn.mock_calls))
            mock_printmsg_fn.assert_called_with('ArtiFactory', '_get_artifactory_files_name_from_build_dir',
                                                'Failed to find artifact of type bob in mydir', 'ERROR')

def test_get_artifact_home_url_no_defined_version():
    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_dict['environments']['unittest']
            _b.json_config = mock_build_config_dict
            _b.project_name = mock_build_config_dict['projectInfo']['name']
            _b.version_number = None

            art = ArtiFactory(config_override=_b)

            art.get_artifact_home_url()
            print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with('commons', 'verify_version', 'Version not defined.  Is your '
                                                                                     'repo tagged with a version '
                                                                                     'number?', 'ERROR')

def test_download_and_extract_artifacts_locally_no_defined_version():
    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit) as cm:
            _b = MagicMock(BuildConfig)
            _b.build_env_info = mock_build_config_dict['environments']['unittest']
            _b.json_config = mock_build_config_dict
            _b.project_name = mock_build_config_dict['projectInfo']['name']
            _b.version_number = None

            art = ArtiFactory(config_override=_b)

            art.download_and_extract_artifacts_locally('download_dir')
            print(str(mock_printmsg_fn.mock_calls))

        mock_printmsg_fn.assert_called_with('commons', 'verify_version', 'Version not defined.  Is your '
                                                                                     'repo tagged with a version '
                                                                                     'number?', 'ERROR')

def test_init_missing_artifactory(monkeypatch):
    _b = MagicMock(BuildConfig)
    _b.json_config = mock_build_config_missing_artifact_dict

    with patch('flow.utils.commons.printMSG') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            ArtiFactory(config_override=_b)

        mock_printmsg_fn.assert_called_with('ArtiFactory', '__init__', "The build config associated with artifactory is missing key 'artifact'", 'ERROR')



import datetime
import json
import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import responses
from flow.coderepo.github.github import GitHub

from flow.buildconfig import BuildConfig

mock_build_config_dict = {
    "projectInfo": {
        "name": "MyProjectName",
        "language": "java",
        "versionStrategy": "tracker"
    },
    "artifact": {
        "artifactoryDomain": "https://fakeartifactory.com/artifactory",
        "artifactoryRepoKey": "libs-release-local",
        "artifactoryRepoKeySnapshot": "libs-snapshot-local",
        "artifactoryGroup": "com/fake/teamname",
        "artifactType": "tar.gz"
    },
    "github": {
        "org": "Org-GitHub",
        "repo": "Repo-GitHub",
        "URL": "https://fakegithub.com/api/v3/repos"
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

mock_build_config_missing_github_dict = {
    "projectInfo": {
        "name": "MyProjectName",
        "language": "java",
        "versionStrategy": "tracker"
    }
}

mock_build_config_missing_org_dict = {
    "projectInfo": {
        "name": "MyProjectName",
        "language": "java",
        "versionStrategy": "tracker"
    },
    "github": {
        "repo": "Repo-GitHub",
        "URL": "https://github.fake.com/api/v3/repos"
    }
}


def test_no_initialize_object():
    _github = GitHub(verify_repo=False)
    assert _github is not None


def test_initialize_object_with_mock():
    _github = MagicMock(GitHub)
    assert _github is not None


def test_convert_semver_string_to_semver_tag_array_snapshot():
    _github = GitHub(verify_repo=False)
    tag_array = _github.convert_semver_string_to_semver_tag_array("v1.2.3+4")
    assert tag_array == [1, 2, 3, 4]


def test_convert_semver_string_to_semver_tag_array_release():
    _github = GitHub(verify_repo=False)

    tag_array = _github.convert_semver_string_to_semver_tag_array("v1.2.3")
    assert tag_array == [1, 2, 3, 0]


def test_convert_semver_string_to_semver_tag_array_bad_format():
    _github = GitHub(verify_repo=False)
    with pytest.raises(Exception):
        _github.convert_semver_string_to_semver_tag_array("homer_was_here")
        assert True


def test_convert_semver_string_to_semver_tag_array_bad_format_missing_v():
    _github = GitHub(verify_repo=False)
    with pytest.raises(Exception):
        _github.convert_semver_string_to_semver_tag_array("1.0.0")
        assert True


def test_convert_semver_string_to_semver_tag_array_bad_format_missing_build_number():
    _github = GitHub(verify_repo=False)
    with pytest.raises(Exception):
        _github.convert_semver_string_to_semver_tag_array("v1.0.0+")
        assert True


def test_convert_semver_tag_array_to_semver_string_snapshot():
    _github = GitHub(verify_repo=False)
    tag_string = _github.convert_semver_tag_array_to_semver_string([1,2,3,4])
    assert tag_string == "v1.2.3+4"


def test_convert_semver_tag_array_to_semver_string_release():
    _github = GitHub(verify_repo=False)
    tag_string = _github.convert_semver_tag_array_to_semver_string([1,2,3,0])
    assert tag_string == "v1.2.3"


def test_convert_semver_tag_array_to_semver_string_tag_is_none():
    _github = GitHub(verify_repo=False)
    tag_string = _github.convert_semver_tag_array_to_semver_string(None)
    assert tag_string is None


# this point is under discussion about if these are legitimate.
# at this point if these are enabled then the regex needs to be more lenient
# and then what about the output of tag, should it be a flag that lets you set
# the v or not?  Something in buildconfig.json?

# def test_convert_semver_tag_array_to_semver_string_snapshot_no_v():
#     _github = GitHub(verify_repo=False)
#     tag_string = _github.convert_semver_tag_array_to_semver_string([1,2,3,4])
#     assert tag_string == "1.2.3+4"
#
# def test_convert_semver_tag_array_to_semver_string_release_no_v():
#     _github = GitHub(verify_repo=False)
#     tag_string = _github.convert_semver_tag_array_to_semver_string([1,2,3,0])
#     assert tag_string == "1.2.3"

def test_call_verify_tags_found_both():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_three_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().strip().split('\n')))
    assert _github._verify_tags_found(captured_tag_data, 0, 0, None, False) == True
    assert _github._verify_tags_found(captured_tag_data, 5, 1, None, False) == True
    assert _github._verify_tags_found(captured_tag_data, 12, 1, None, False) == False
    assert _github._verify_tags_found(captured_tag_data, 5, 12, None, False) == False
    assert _github._verify_tags_found(captured_tag_data, 10, 3, None, False) == True

def test_call_verify_tags_found_multiple_snapshot_multiple_found():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_three_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().strip().split('\n')))
    assert _github._verify_tags_found(captured_tag_data, 10, 0, None, False) == True
    assert _github._verify_tags_found(captured_tag_data, 5, 0, None, False) == True
    assert _github._verify_tags_found(captured_tag_data, 12, 0, None, False) == False

def test_call_verify_tags_found_multiple_release_multiple_found():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_three_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().strip().split('\n')))
    assert _github._verify_tags_found(captured_tag_data, 0, 2, None, False) == True
    assert _github._verify_tags_found(captured_tag_data, 0, 3, None, False) == True
    assert _github._verify_tags_found(captured_tag_data, 0, 4, None, False) == False

def test_call_verify_tags_found_multiple_release_one_found():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_one_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().strip().split('\n')))
    assert _github._verify_tags_found(captured_tag_data, 0, 2, None, False) == False
    assert _github._verify_tags_found(captured_tag_data, 0, 1, None, False) == True


def test_call_verify_tags_found_particular_release():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_one_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().strip().split('\n')))
    assert _github._verify_tags_found(captured_tag_data, 2, 0, 'v1.2.3+5', False) == True
    assert _github._verify_tags_found(captured_tag_data, 2, 0, 'v1.2.3+9', False) == False

def test_call_verify_tags_found_base_version():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_one_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().strip().split('\n')))
    assert _github._verify_tags_found(captured_tag_data, 0, 0, 'v1.2.3', True) == True
    assert _github._verify_tags_found(captured_tag_data, 0, 0, 'v1.2.4', True) == False

def test_call_get_all_tags_sorted():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_mock_output.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    all_tags = _github.get_all_semver_tags()
    # there are 176 tags in the file
    # but after tag format validation there are 131
    assert len(all_tags) == 131


def test_call_get_all_semver_tags_sorted_from_random():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_mock_output_random.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    all_tags = GitHub.get_all_semver_tags(_github)
    # assert the length, first and last
    assert len(all_tags) == 131
    assert all_tags[0] == [1, 67, 0, 0]
    assert all_tags[-1] == [0, 0, 0, 56]


def test_get_highest_semver_tag():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_last_was_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    highest_tag = _github.get_highest_semver_tag()
    assert highest_tag == [0, 2, 0, 0]


def test_get_highest_semver_release_tag():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_last_was_snapshot.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    highest_tag = _github.get_highest_semver_release_tag()
    assert highest_tag == [0, 2, 0, 0]


def test_get_highest_semver_snapshot_tag():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_last_was_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    highest_tag = _github.get_highest_semver_snapshot_tag()
    assert highest_tag == [0, 1, 0, 2]


def test_get_highest_semver_tag_when_no_tags():
    _github = GitHub(verify_repo=False)
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=[])
    highest_tag = _github.get_highest_semver_tag()
    assert highest_tag is None


def test_get_highest_semver_snapshot_tag_when_no_tags():
    _github = GitHub(verify_repo=False)
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=[])
    highest_tag = _github.get_highest_semver_snapshot_tag()
    assert highest_tag is None


def test_does_semver_tag_exist():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_last_was_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    existing_tag = [0, 2, 0, 0]
    exists = _github._does_semver_tag_exist(existing_tag)
    assert exists == True


def test_does_semver_tag_not_exist():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_last_was_release.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    existing_tag = [0, 3, 0, 0]
    exists = _github._does_semver_tag_exist(existing_tag)
    assert exists == False

def test_get_git_last_tag():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_mock_output_small.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)

    old_artifact_category = _github.config.artifact_category

    _github.config.artifact_category = 'snapshot' 
    last_tag = _github.get_git_last_tag()
    assert last_tag == '1.68.0+1'

    _github.config.artifact_category = 'release' 
    last_tag = _github.get_git_last_tag()
    assert last_tag == '1.68.0'

    _github.config.artifact_category = old_artifact_category

def test_get_git_previous_tag_snapshot():
    _github = GitHub(verify_repo=False)
    old_artifact_category = _github.config.artifact_category
    
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/git_tag_mock_output_small.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)


    _github.config.artifact_category = 'snapshot' 
    existing_tag = '1.67.0+10'
    previous_tag = _github.get_git_previous_tag(existing_tag)
    assert previous_tag == '1.67.0+9'

    existing_tag = '1.67.0+1'
    previous_tag = _github.get_git_previous_tag(existing_tag)
    assert previous_tag == '1.66.0+2'

    _github.config.artifact_category = 'release' 
    existing_tag = '1.68.0'
    previous_tag = _github.get_git_previous_tag(existing_tag)
    assert previous_tag == '1.67.0'

    _github.config.artifact_category = old_artifact_category

def test_fetch_commit_history():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    import json
    with open(current_test_directory + "/github_commit_history_output.txt", 'r') as myfile:
        captured_commit_history_data=json.loads(myfile.read())
    _github.get_all_commits_from_github = MagicMock(return_value=captured_commit_history_data)
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=[("v1.0.0", "c968da6")])
    commits_array = _github.get_all_git_commit_history_between_provided_tags([1, 0, 0, 0])
    print(str(commits_array))
    assert len(commits_array) == 59


def test_fetch_commit_history_multiline():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/github_commit_history_output_multiline.txt", 'r') as myfile:
        captured_commit_history_data=json.loads(myfile.read())
    _github.get_all_commits_from_github = MagicMock(return_value=captured_commit_history_data)
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=[("v1.0.0", "4a3ddfb")])
    commits_array = _github.get_all_git_commit_history_between_provided_tags([1, 0, 0, 0])
    print(str(commits_array))
    assert len(commits_array) == 59


def test_fetch_commit_history_for_repo_with_no_tags():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/github_commit_history_output.txt", 'r') as myfile:
        captured_commit_history_data=json.loads(myfile.read())
    _github.get_all_commits_from_github = MagicMock(return_value=captured_commit_history_data)
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=[("v1.0.0", "c968da6")])
    commits_array = _github.get_all_git_commit_history_between_provided_tags(None)
    print(str(commits_array))
    assert len(commits_array) == 60


# noinspection PyUnresolvedReferences
@responses.activate
def test_verify_repo_existence():

    _github = GitHub(verify_repo=False)

    responses.add(responses.GET,
                  "http://mygithub/my_org/my_repo",
                  status=200)
    _github._verify_repo_existence("http://mygithub", "my_org", "my_repo", "my_token")

    assert len(responses.calls) == 1


# noinspection PyUnresolvedReferences
@responses.activate
def test_verify_repo_does_not_existence():

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:

        _github = GitHub(verify_repo=False)

        responses.add(responses.GET,
                      "http://mygithub/my_org/my_repo",
                      status=201)
        with pytest.raises(SystemExit):
            _github._verify_repo_existence("http://mygithub", "my_org", "my_repo", "my_token")

        print(str(mock_printmsg_fn.mock_calls))
        mock_printmsg_fn.assert_called_with("GitHub", "_verify_repo_existence", "Failed to access github location "
                                                                                "http://mygithub/my_org/my_repo\r\n Response: ", "ERROR")
        assert len(responses.calls) == 1


def test_calculate_next_semver_no_tag_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = None
            bump_type = None
            highest_version_array = None
            _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_semver', "Tag types can only be 'release' or "
                                                                           "'snapshot', instead None was provided.")


def test_calculate_next_semver_bad_tag_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = "bubba"
            bump_type = None
            highest_version_array = None
            _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_semver', "Tag types can only be 'release' or 'snapshot', instead bubba was provided.")


def test_calculate_next_semver_tag_type_release_but_no_bump_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = "release"
            bump_type = None
            highest_version_array = None
            _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_semver', "Bump types can only be 'major', 'minor' or 'bug', instead None was provided.")


def test_calculate_next_semver_tag_type_release_but_bad_bump_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = "release"
            bump_type = "bubba"
            highest_version_array = None
            _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_semver', "Bump types can only be 'major', "
                                                                           "'minor' or 'bug', instead bubba was "
                                                                           "provided.")


def test_calculate_next_semver_first_snapshot():
    _github = GitHub(verify_repo=False)
    tag_type = "snapshot"
    bump_type = None
    highest_version_array = None
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 0, 0, 1]


def test_calculate_next_semver_first_release_bug():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "bug"
    highest_version_array = None
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 0, 1, 0]


def test_calculate_next_semver_first_release_minor():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "minor"
    highest_version_array = None
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 1, 0, 0]


def test_calculate_next_semver_first_release_major():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "major"
    highest_version_array = None
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [1, 0, 0, 0]


def test_calculate_next_semver_next_release_bug():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "bug"
    highest_version_array = [0, 0, 1, 0]
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 0, 2, 0]


def test_calculate_next_semver_next_release_bug_with_minor():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="bug"
    highest_version_array=[0, 1, 1, 1]
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 1, 2, 0]


def test_calculate_next_semver_next_release_minor_with_minor():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="minor"
    highest_version_array=[0, 1, 1, 1]
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 2, 0, 0]


def test_calculate_next_semver_next_snapshot_after_release():
    _github = GitHub(verify_repo=False)
    tag_type="snapshot"
    bump_type="minor"
    highest_version_array=[0, 1, 0, 0]
    new_tag_array = _github.calculate_next_semver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array)
    assert new_tag_array == [0, 1, 0, 1]


def test_calculate_next_calver_no_tag_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = None
            bump_type = None
            highest_version_array = None
            short_year = False
            _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_calver', "Tag types can only be 'release' or "
                                                                           "'snapshot', instead None was provided.")


def test_calculate_next_calver_bad_tag_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = "bubba"
            bump_type = None
            highest_version_array = None
            short_year = False
            _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_calver', "Tag types can only be 'release' or 'snapshot', instead bubba was provided.")


def test_calculate_next_calver_tag_type_release_but_no_bump_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = "release"
            bump_type = None
            highest_version_array = None
            short_year = False
            _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_calver', "Bump types can only be 'major' or 'patch', instead None was provided.")


def test_calculate_next_calver_tag_type_release_but_bad_bump_type():
    _github = GitHub(verify_repo=False)
    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            # tag type must be either "release" or "snapshot"
            tag_type = "release"
            bump_type = "bubba"
            highest_version_array = None
            short_year = False
            _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    mock_printmsg_fn.assert_called_with('GitHub', 'calculate_next_calver', "Bump types can only be 'major' or 'patch', instead bubba was provided.")


def test_calculate_next_calver_first_snapshot():
    _github = GitHub(verify_repo=False)
    tag_type = "snapshot"
    bump_type = None
    highest_version_array = None
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2021, 1, 1)
        _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2021, 0, 0, 1]


def test_calculate_next_calver_next_snapshot():
    _github = GitHub(verify_repo=False)
    tag_type = "snapshot"
    bump_type = None
    highest_version_array = [21, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2021, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2021, 1, 1, 2]


def test_calculate_next_calver_first_release_patch():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "patch"
    highest_version_array = None
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2021, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2021, 0, 1, 0]


def test_calculate_next_calver_first_release_major():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "major"
    highest_version_array = None
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2021, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2021, 1, 0, 0]


def test_calculate_next_calver_next_release_patch():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="patch"
    highest_version_array=[0, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2021, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2021, 1, 2, 0]


def test_calculate_next_calver_next_release_major():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="major"
    highest_version_array=[0, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2021, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2021, 2, 0, 0]


def test_calculate_next_calver_new_year():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="patch"
    highest_version_array=[2021, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2022, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2022, 1, 2, 0]


def test_calculate_next_calver_major_bump_type_env_var_when_bump_type_is_none(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'major')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type=None
    highest_version_array=[2021, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2022, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2022, 2, 0, 0]


def test_calculate_next_calver_major_bump_type_env_var_when_bump_type_is_patch(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'major')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="patch"
    highest_version_array=[2021, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2022, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2022, 2, 0, 0]


def test_calculate_next_calver_patch_bump_type_env_var_when_bump_type_is_none(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'patch')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type=None
    highest_version_array=[2021, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2022, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2022, 1, 2, 0]


def test_calculate_next_calver_patch_bump_type_env_var_when_bump_type_is_major(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'patch')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="major"
    highest_version_array=[2021, 1, 1, 1]
    short_year = False
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2022, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [2022, 1, 2, 0]

# =================================================================
def test_calculate_next_calver_first_snapshot():
    _github = GitHub(verify_repo=False)
    tag_type = "snapshot"
    bump_type = None
    highest_version_array = None
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(21, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [21, 0, 0, 1]


def test_calculate_next_calver_next_snapshot():
    _github = GitHub(verify_repo=False)
    tag_type = "snapshot"
    bump_type = None
    highest_version_array = [21, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(21, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [21, 1, 1, 2]


def test_calculate_next_calver_first_release_patch():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "patch"
    highest_version_array = None
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(21, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [21, 0, 1, 0]


def test_calculate_next_calver_first_release_major():
    _github = GitHub(verify_repo=False)
    tag_type = "release"
    bump_type = "major"
    highest_version_array = None
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(21, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [21, 1, 0, 0]


def test_calculate_next_calver_next_release_patch():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="patch"
    highest_version_array=[0, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(21, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [21, 1, 2, 0]


def test_calculate_next_calver_next_release_major():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="major"
    highest_version_array=[0, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(21, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [21, 2, 0, 0]


def test_calculate_next_calver_new_year():
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="patch"
    highest_version_array=[21, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(22, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [22, 1, 2, 0]


def test_calculate_next_calver_major_bump_type_env_var_when_bump_type_is_none(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'major')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type=None
    highest_version_array=[21, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(22, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [22, 2, 0, 0]


def test_calculate_next_calver_major_bump_type_env_var_when_bump_type_is_patch(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'major')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="patch"
    highest_version_array=[21, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(22, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [22, 2, 0, 0]


def test_calculate_next_calver_patch_bump_type_env_var_when_bump_type_is_none(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'patch')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type=None
    highest_version_array=[21, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(22, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [22, 1, 2, 0]


def test_calculate_next_calver_patch_bump_type_env_var_when_bump_type_is_major(monkeypatch):
    monkeypatch.setenv('CALVER_BUMP_TYPE', 'patch')
    _github = GitHub(verify_repo=False)
    tag_type="release"
    bump_type="major"
    highest_version_array=[21, 1, 1, 1]
    short_year = True
    with patch('flow.coderepo.github.github.datetime') as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(22, 1, 1)
        new_tag_array = _github.calculate_next_calver(tag_type=tag_type, bump_type=bump_type, highest_version_array=highest_version_array, short_year=short_year)
    assert new_tag_array == [22, 1, 2, 0]

# noinspection PyUnresolvedReferences
@responses.activate
def test_add_tag_and_release_notes_to_github():

    # this is pretty weak but also an indication that the
    # target method of testing is *too* big. Need to split out
    # add_tag_and_release_notes_to_github

    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories.json", 'r') as myfile:
        tracker_json_data = json.loads(myfile.read())

    with patch('flow.utils.commons.execute_command', return_value="master\n"):
        _b = MagicMock(BuildConfig)
        _b.build_env_info = mock_build_config_dict['environments']['develop']
        _b.json_config = mock_build_config_dict
        _b.project_name = mock_build_config_dict['projectInfo']['name']
        _github = GitHub(config_override=_b, verify_repo=False)
        _github._verify_required_attributes()

        responses.add(responses.POST,
                      "https://fakegithub.com/api/v3/repos/Org-GitHub/Repo-GitHub/releases",
                      status=200)

        _github.add_tag_and_release_notes_to_github([0, 0, 0, 1], tracker_json_data["stories"])

    assert len(responses.calls) == 1


def test_get_highest_semver_snapshot_tag_from_base():
    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    #with open(current_test_directory + "/git_tag_mock_output.txt", 'r') as myfile:
    with open(current_test_directory + "/git_tag_unordered_manual_versions.txt", 'r') as myfile:
        #captured_tag_data=myfile.read()
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))
    _github.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)
    base_release_version = [0, 1, 0, 0]
    highest_tag = _github.get_highest_semver_array_snapshot_tag_from_base(base_release_version)
    assert highest_tag == [0, 1, 0, 2]


def test_format_github_specific_release_notes_from_project_tracker_story_details():

    _github = GitHub(verify_repo=False)
    current_test_directory = os.path.dirname(os.path.realpath(__file__))
    with open(current_test_directory + "/tracker_stories.json", 'r') as myfile:
        tracker_json_data = json.loads(myfile.read())

    release_notes = _github.format_github_specific_release_notes_from_project_tracker_story_details(story_details=tracker_json_data["stories"])

    assert len(release_notes) == 696


def test_format_github_specific_release_notes_from_project_tracker_story_details_empty_array():

    _github = GitHub(verify_repo=False)

    release_notes = _github.format_github_specific_release_notes_from_project_tracker_story_details(story_details=[])

    assert release_notes == 'No Release Notes'


def test_format_github_specific_release_notes_from_project_tracker_story_details_pass_one():

    _github = GitHub(verify_repo=False)

    release_notes = _github.format_github_specific_release_notes_from_project_tracker_story_details(story_details=None)

    assert release_notes == 'No Release Notes'


def test_init_without_github_token(monkeypatch):
    if os.getenv('GITHUB_TOKEN'):
        monkeypatch.delenv('GITHUB_TOKEN')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        _github = GitHub(verify_repo=False)
        _github._load_github_token()
    mock_printmsg_fn.assert_any_call('GitHub', '_load_github_token', "No github token found.  If your repo doesn't allow anonymous "
                                                    "access, some operations may fail. To define a token, please set "
                                                    "environment variable 'GITHUB_TOKEN'", 'WARN')

def test_verify_required_attributes_missing(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fake_token')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.json_config = mock_build_config_missing_github_dict

            GitHub(config_override=_b)

    mock_printmsg_fn.assert_called_with('GitHub', '_verify_required_attributes', "The build config associated with "
                                                                                 "github is missing, 'github'.", 'ERROR')


def test_verify_required_attributes_missing_org(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fake_token')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.json_config = mock_build_config_missing_org_dict

            GitHub(config_override=_b)

    mock_printmsg_fn.assert_called_with('GitHub', '_verify_required_attributes', "The build config associated with "
                                                                                 "github is missing, 'org'."
                                                                                 , 'ERROR')

def test_get_all_git_commit_history_between_provided_tags_invalid_beginning_tag(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fake_token')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.json_config = mock_build_config_dict

            _gh = GitHub(config_override=_b,verify_repo=False)
            good_tag = ['v', 1, 0, 0]
            bad_tag = [1, 0, 0]
            _gh.get_all_git_commit_history_between_provided_tags(good_tag, bad_tag)

    mock_printmsg_fn.assert_called_with('GitHub', 'get_all_git_commit_history_between_provided_tags',
                                        "Invalid beginning version defined ['v', 1, 0, 0]", 'ERROR')


def test_get_all_git_commit_history_between_provided_tags_invalid_ending_tag(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fake_token')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.json_config = mock_build_config_dict

            _gh = GitHub(config_override=_b,verify_repo=False)
            good_tag = [1, 0, 0]
            bad_tag = ['v', 1, 0, 0]
            _gh.get_all_git_commit_history_between_provided_tags(good_tag, bad_tag)

    mock_printmsg_fn.assert_called_with('GitHub', 'get_all_git_commit_history_between_provided_tags',
                                        "Invalid ending version defined ['v', 1, 0, 0]", 'ERROR')


def test_get_all_git_commit_history_between_provided_tags_beginning_tag_not_found(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'fake_token')
    current_test_directory = os.path.dirname(os.path.realpath(__file__))

    with open(current_test_directory + "/git_tag_mock_output_random.txt", 'r') as myfile:
        captured_tag_data=list(map(lambda tag: (tag, 'sha'), myfile.read().split('\n')))

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            _b.json_config = mock_build_config_dict

            _gh = GitHub(config_override=_b,verify_repo=False)
            _gh.get_all_tags_and_shas_from_github = MagicMock(return_value=captured_tag_data)

            good_tag = [1, 99, 98]
            _gh.get_all_git_commit_history_between_provided_tags(good_tag)

    mock_printmsg_fn.assert_any_call('GitHub', 'get_all_git_commit_history_between_provided_tags', "Version tag not "
                                                                                                   "found v1.99.98",
                                     'ERROR')

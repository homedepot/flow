from io import StringIO, TextIOWrapper
from unittest.mock import MagicMock
from unittest.mock import PropertyMock
from unittest.mock import mock_open
from unittest.mock import patch

import flow.aggregator
import pytest
from argparse import ArgumentParser
from argparse import Namespace
from flow.coderepo.github.github import GitHub
from flow.projecttracking.tracker.tracker import Tracker
from flow.staticqualityanalysis.sonar.sonarmodule import SonarQube
from flow.artifactstorage.artifactory.artifactory import ArtiFactory


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
        "artifactoryGroup": "com/fake/teamname",
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

mock_build_config_minimal = {
    "projectInfo": {
        "name": "MyProjectName",
        "language": "java",
        "versionStrategy": "manual"
    },
    "github": {
        "org": "Org-GitHub",
        "repo": "Repo-GitHub",
        "URL": "https://github.fake.com/api/v3/repos"
    }
}

# def test_aggregator_github_version():
#
#     _a = MagicMock(aggregator)
#
#     assert(_a is not None)
#
#     _b = MagicMock(BuildConfig)
#     _b.build_env_info = mock_build_config_dict['environments']['develop']
#     _b.json_config = mock_build_config_dict
#     _b.project_name = mock_build_config_dict['projectInfo']['name']
#     _b.version_strategy = mock_build_config_dict['environments']['develop']['artifactCategory']
#
#
#     _github = MagicMock(GitHub)
#
#     _github.config = _b
#     _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
#
#     #_github = GitHub(config_override=_b, initialize=False)
#
#
#     assert(_github is not None)
#
#     _a.call_github_version(_github, _b)
#
#     assert _a.call_github_version.called
#     assert _github.get_highest_semver_tag.called
#     #assert _github.get_highest_semver_tag.called
#     #assert _github.add_tag_and_release_notes_to_github.called

def test_aggregator_github_version_tracker_snapshot():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[0, 2, 0, 0])
    _github.get_highest_semver_snapshot_tag = MagicMock(return_value=[0, 1, 4, 8])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[0, 2, 0, 1])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'snapshot'

    flow.aggregator.call_github_version(_github, _tracker, _config)

    _github.get_all_git_commit_history_between_provided_tags.assert_called_with([0, 1, 4, 8])
    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_called_with([0, 2, 0, 1], 'No Release Notes')


def test_aggregator_github_version_tracker_release():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'release'

    flow.aggregator.call_github_version(_github, _tracker, _config)

    print(str(_github.method_calls))

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 0], 'No Release Notes')

def test_aggregator_github_version_manual_release():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'release'

    _parser = ArgumentParser()
    _parser.add_argument('--version')
    _parser.add_argument('--no-publish', action='store_true')
    _parser.add_argument('--release-notes-output-path', type=open)
    _args = _parser.parse_args(['--version', 'v1.1.0.0'])

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 0], 'No Release Notes')

def test_aggregator_github_version_manual_snapshot():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')
    _github.calculate_next_semver = MagicMock(return_value=[1,1,0,1])

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'snapshot'

    _parser = ArgumentParser()
    _parser.add_argument('--version')
    _parser.add_argument('--no-publish', action='store_true')
    _parser.add_argument('--release-notes-output-path', type=open)
    _args = _parser.parse_args(['--version', 'v1.1.0.0'])

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 1], 'No Release Notes')

def test_aggregator_github_version_tracker_snapshot_no_publish():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 0, 0, 1])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'snapshot'

    _parser = ArgumentParser()
    _parser.add_argument('--no-publish', action='store_true')
    _parser.add_argument('--release-notes-output-path', type=open)
    _args = _parser.parse_args(['--no-publish'])

    flow.aggregator.call_github_version(_github, _tracker, _config, args=_args)

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_not_called()


def test_aggregator_github_version_tracker_release_no_publish():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'release'

    _parser = ArgumentParser()
    _parser.add_argument('--no-publish', action='store_true')
    _parser.add_argument('--release-notes-output-path', type=open)
    _args = _parser.parse_args(['--no-publish'])

    flow.aggregator.call_github_version(_github, _tracker, _config, args=_args)

    print(str(_github.method_calls))

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_not_called()

def test_aggregator_github_version_manual_release_no_publish():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'release'

    _parser = ArgumentParser()
    _parser.add_argument('--version')
    _parser.add_argument('--no-publish', action='store_true')
    _parser.add_argument('--release-notes-output-path', type=open)
    _args = _parser.parse_args(['--version', 'v1.1.0.0', '--no-publish'])

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_not_called()

def test_aggregator_github_version_manual_snapshot_no_publish():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')
    _github.calculate_next_semver = MagicMock(return_value=[1,1,0,1])

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'snapshot'

    _parser = ArgumentParser()
    _parser.add_argument('--version')
    _parser.add_argument('--no-publish', action='store_true')
    _parser.add_argument('--release-notes-output-path', type=open)
    _args = _parser.parse_args(['--version', 'v1.1.0.0', '--no-publish'])

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_not_called()

def test_aggregator_github_version_tracker_snapshot_release_notes_output():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 0, 0, 1])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'snapshot'

    _args = MagicMock(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=False
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, _tracker, _config, args=_args)

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 0, 0, 1], 'No Release Notes')
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_tracker_release_release_notes_output():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'release'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=False
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, _tracker, _config, args=_args)

    print(str(_github.method_calls))

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 0], 'No Release Notes')
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_manual_release_release_notes_output():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'release'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=False,
        version='v1.1.0.0'
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 0], 'No Release Notes')
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_manual_snapshot_release_notes_output():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')
    _github.calculate_next_semver = MagicMock(return_value=[1,1,0,1])

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'snapshot'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=False,
        version='v1.1.0.0'
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 1], 'No Release Notes')
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_tracker_snapshot_no_publish_release_notes_output():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 0, 0, 1])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'snapshot'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=True
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, _tracker, _config, args=_args)

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_not_called()
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_tracker_release_no_publish_release_notes_output():

    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)
    # _b.build_env_info = mock_build_config_dict['environments']['develop']
    _config.json_config = mock_build_config_dict
    # _b.project_name = mock_build_config_dict['projectInfo']['name']
    _config.version_strategy = 'tracker'
    _config.artifact_category = 'release'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=True
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, _tracker, _config, args=_args)

    print(str(_github.method_calls))

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_not_called()
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_manual_release_no_publish_release_notes_output():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'release'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=True,
        version='v1.1.0.0'
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_not_called()
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_github_version_manual_snapshot_no_publish_release_notes_output():

    _github = MagicMock(GitHub)
    _github.convert_semver_string_to_semver_tag_array = MagicMock(return_value=[1, 1, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.get_highest_semver_array_snapshot_tag_from_base = MagicMock(return_value=[1, 1, 0, 0])
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')
    _github.calculate_next_semver = MagicMock(return_value=[1,1,0,1])

    _config = MagicMock(BuildConfig)
    _config.json_config = mock_build_config_minimal
    _config.version_strategy = 'manual'
    _config.artifact_category = 'snapshot'

    _args = Namespace(
        release_notes_output_path=MagicMock(TextIOWrapper),
        no_publish=True,
        version='v1.1.0.0'
    )
    _args.release_notes_output_path.write = MagicMock(return_value=None)

    flow.aggregator.call_github_version(_github, None, _config, args=_args)

    print(str(_github.method_calls))

    _github.add_tag_and_release_notes_to_github.assert_not_called()
    _args.release_notes_output_path.write.assert_called_once_with('No Release Notes')


def test_aggregator_sonar_version_manual_release(mocker):
    with patch('sys.argv', ['flow', 'sonar', '--version', '1.0.0.0', 'scan', 'development']):
        mocker.patch.object(GitHub, '__init__')
        GitHub.__init__.return_value = None
        mocker.patch.object(GitHub, 'get_git_last_tag')
        GitHub.get_git_last_tag.return_value = '1.0.0.0'
        mocker.patch.object(SonarQube, '__init__')
        SonarQube.__init__.return_value = None
        mocker.patch.object(SonarQube, 'scan_code')
        SonarQube.scan_code.return_value = None

        flow.aggregator.main()

def test_aggregator_tracker_version_manual_release(mocker):
    with patch('sys.argv', ['flow', 'tracker', '--version', '1.0.0.0', 'label-release', 'development']):
        mocker.patch.object(GitHub, '__init__')
        GitHub.__init__.return_value = None
        mocker.patch.object(GitHub, 'get_git_last_tag')
        GitHub.get_git_last_tag.return_value = '1.0.0.0'
        mocker.patch.object(Tracker, '__init__')
        Tracker.__init__.return_value = None
        mocker.patch.object(flow.aggregator, 'get_git_commit_history')
        flow.aggregator.get_git_commit_history.return_value = None
        mocker.patch.object(flow.utils.commons, 'extract_story_id_from_commit_messages')
        flow.utils.commons.extract_story_id_from_commit_messages.return_value = None
        mocker.patch.object(Tracker, 'tag_stories_in_commit')
        Tracker.tag_stories_in_commit.return_value = None
        
        flow.aggregator.main()
def test_aggregator_artifactory_version_manual_release(mocker):
    with patch('sys.argv', ['flow', 'artifactory', '--version', '1.0.0.0', 'upload', 'development']):
        mocker.patch.object(GitHub, '__init__')
        GitHub.__init__.return_value = None
        mocker.patch.object(GitHub, 'get_git_last_tag')
        GitHub.get_git_last_tag.return_value = '1.0.0.0'
        mocker.patch.object(ArtiFactory, '__init__')
        ArtiFactory.__init__.return_value = None
        mocker.patch.object(ArtiFactory, 'publish_build_artifact')
        ArtiFactory.publish_build_artifact.return_value = None
        
        flow.aggregator.main()
        
def test_aggregator_zipit_version_manual_release(mocker):
    with patch('sys.argv', ['flow', 'zipit', '--version', '1.0.0.0', '-z', 'somefile', '-c', 'somedir', 'development']):
        mocker.patch.object(GitHub, '__init__')
        GitHub.__init__.return_value = None
        mocker.patch.object(GitHub, 'get_git_last_tag')
        GitHub.get_git_last_tag.return_value = '1.0.0.0'
        mocker.patch.object(flow.aggregator, 'ZipIt')
        flow.aggregator.ZipIt.return_value = None
        
        
        flow.aggregator.main()        

def test_aggregator_github_outputs_version():
    _github = MagicMock(GitHub)
    _github.get_highest_semver_tag = MagicMock(return_value=[1, 0, 0, 0])
    _github.get_all_git_commit_history_between_provided_tags = MagicMock(return_value=['blah1 [#12345678]', 'blah2 [#987654321]'])
    _github.calculate_next_semver = MagicMock(return_value=[1, 1, 0, 0])
    _github.convert_semver_tag_array_to_semver_string = MagicMock(return_value='v1.1.0')
    _github.format_github_specific_release_notes_from_tracker_story_details = MagicMock(return_value='No Release Notes')

    _tracker = MagicMock(Tracker)
    _tracker.get_details_for_all_stories = MagicMock(return_value=[])

    _config = MagicMock(BuildConfig)

    _config.version_strategy = 'tracker'
    _config.artifact_category = 'release'

    _open_mock = mock_open()
    with patch('__main__.open', _open_mock, create=True):
        flow.aggregator.call_github_version(_github, _tracker, _config, file_path='somefilepath', open_func=_open_mock)

    print('Mock Call Stack\n' + str(_github.method_calls))

    _tracker.get_details_for_all_stories.assert_called_with(['12345678', '987654321'])
    _github.add_tag_and_release_notes_to_github.assert_called_with([1, 1, 0, 0], 'No Release Notes')
    _open_mock.assert_called_once_with('somefilepath', 'a')
    _file_mock = _open_mock()
    _file_mock.write.assert_called_once_with('v1.1.0')

def test_aggregator_github_without_output_getversion():
    _github = MagicMock(GitHub)
    _github.get_git_last_tag = MagicMock(return_value='v1.1.0')

    with patch('flow.utils.commons.Commons.quiet', new_callable=PropertyMock, return_value=True):
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            flow.aggregator.call_github_getversion(_github)

        assert fake_stdout.getvalue() == "v1.1.0\n"

def test_aggregator_github_outputs_getversion():
    _github = MagicMock(GitHub)
    _github.get_git_last_tag = MagicMock(return_value='v1.1.0')

    _open_mock = mock_open()
    with patch('__main__.open', _open_mock, create=True):
        flow.aggregator.call_github_getversion(_github, file_path='somefilepath', open_func=_open_mock)

    print('Mock Call Stack\n{}'.format(str(_github.method_calls)))

    _open_mock.assert_called_once_with('somefilepath', 'w')
    _file_mock = _open_mock()
    _file_mock.write.assert_called_once_with('v1.1.0')

# this causes flow to throw an error and log to slack when it really does 
# indeed call call_github_getversion - need to figure out how to mock this 
# to not throw the error. Commenting out for now.
# def test_aggregator_github_outputs_getversion_fails():
#     _github = MagicMock(GitHub)
#     _github.get_git_last_tag = MagicMock(return_value='v1.1.0')
# 
#     _open_mock = mock_open()
#     with patch('__main__.open', _open_mock, create=True):
#         with pytest.raises(SystemExit):
#             _open_mock.side_effect = IOError
#             flow.aggregator.call_github_getversion(_github, file_path='somefilepath', open_func=_open_mock)
# 
#     print('Mock Call Stack\n{}'.format(str(_github.method_calls)))

from unittest.mock import mock_open
from unittest.mock import patch

import flow.utils.commons as commons


def test_extract_story_id_with_empty_list():
    story_list = commons.extract_story_id_from_commit_messages([])
    assert len(story_list) == 0

commit_example = [
"223342f Adding ability to specify artifactory user [#134082057]",
"4326d00 Adding slack channel option for errors [#130798449]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_two_stories():
    story_list = commons.extract_story_id_from_commit_messages(commit_example)
    assert len(story_list) == 2

commit_example_nested_brackets = [
"223342f Adding ability to specify artifactory user [#134082057, [bubba]]",
"4326d00 Adding slack channel option for errors [#130798449]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_nested_brackets():
    story_list = commons.extract_story_id_from_commit_messages(commit_example_nested_brackets)
    print(str(story_list))
    assert len(story_list) == 1


commit_example_multiple_per_brackets = [
"223342f Adding ability to specify artifactory user [#134082057,#134082058]",
"4326d00 Adding slack channel option for errors [#130798449,123456]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_multiple_per_brackets():
    story_list = commons.extract_story_id_from_commit_messages(commit_example_multiple_per_brackets)
    print(str(story_list))
    assert len(story_list) == 4



commit_example_dedup = [
"223342f Adding ability to specify artifactory user [#134082057,#134082057]",
"4326d00 Adding slack channel option for errors [#134082057,134082057]",
"09c1983 Merge pull request #25 from ci-cd/revert-18-github-version-fix",
"445fd02 Revert \"GitHub version fix\""
]

def test_extract_story_id_with_dedup():
    story_list = commons.extract_story_id_from_commit_messages(commit_example_dedup)
    print(str(story_list))
    assert len(story_list) == 1


def test_write_to_file():
    open_mock = mock_open()
    with patch('__main__.open', open_mock, create=True):
        commons.write_to_file("somefilepath", "test_write_to_file", open_func=open_mock)

    open_mock.assert_called_once_with("somefilepath", "a")
    file_mock = open_mock()
    file_mock.write.assert_called_once_with("test_write_to_file")

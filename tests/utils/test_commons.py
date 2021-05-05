from unittest.mock import mock_open
from unittest.mock import patch

import flow.utils.commons as commons

def test_write_to_file():
    open_mock = mock_open()
    with patch('__main__.open', open_mock, create=True):
        commons.write_to_file("somefilepath", "test_write_to_file", open_func=open_mock)

    open_mock.assert_called_once_with("somefilepath", "a")
    file_mock = open_mock()
    file_mock.write.assert_called_once_with("test_write_to_file")

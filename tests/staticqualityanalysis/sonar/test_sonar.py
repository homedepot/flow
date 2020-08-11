import configparser
import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from flow.staticqualityanalysis.sonar.sonarmodule import SonarQube

from flow.buildconfig import BuildConfig


def test_scan_code_single_jar_executable_path(monkeypatch):
    monkeypatch.setenv('SONAR_HOME','FAKEHOME')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('flow.utils.commons.get_files_of_type_from_directory') as mock_getfiletypefromdir_fn:
            with pytest.raises(SystemExit):
                mock_getfiletypefromdir_fn.return_value = ['sonar-scanner.jar']
                _b = MagicMock(BuildConfig)
                parser = configparser.ConfigParser()
                parser.add_section('sonar')
                _b.settings = parser

                _sonar = SonarQube(config_override=_b)
                _sonar.scan_code()

    mock_getfiletypefromdir_fn.assert_called_with('jar', 'FAKEHOME')


def test_scan_code_settings_executable_path(monkeypatch):
    monkeypatch.setenv('SONAR_HOME','FAKEHOME')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('flow.utils.commons.get_files_of_type_from_directory') as mock_getfiletypefromdir_fn:
            with pytest.raises(SystemExit):
                mock_getfiletypefromdir_fn.return_value = []
                _b = MagicMock(BuildConfig)
                parser = configparser.ConfigParser()
                parser.add_section('sonar')
                parser.set('sonar', 'sonar_runner', 'sonar-runner-dist-2.4.jar')
                _b.settings = parser

                _sonar = SonarQube(config_override=_b)
                _sonar.scan_code()

    mock_getfiletypefromdir_fn.assert_called_with('jar', 'FAKEHOME')


def test_scan_code_missing_executable_path(monkeypatch):
    monkeypatch.setenv('SONAR_HOME','FAKEHOME')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('flow.utils.commons.get_files_of_type_from_directory') as mock_getfiletypefromdir_fn:
            with pytest.raises(SystemExit):
                mock_getfiletypefromdir_fn.return_value = []
                _b = MagicMock(BuildConfig)
                parser = configparser.ConfigParser()
                parser.add_section('sonar')
                _b.settings = parser

                _sonar = SonarQube(config_override=_b)
                _sonar.scan_code()

    mock_printmsg_fn.assert_called_with('SonarQube', '_submit_scan', 'Sonar runner undefined.  Please define path to '
                                                                  'sonar '
                                                              'runner in settings.ini.', 'ERROR')


def test_scan_retry_logic(monkeypatch):
    monkeypatch.setenv('SONAR_HOME','FAKEHOME')

    def _submit_scan_failure():
        raise Exception

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('flow.staticqualityanalysis.sonar.sonarmodule.SonarQube._submit_scan', new=_submit_scan_failure):
            with patch('os.path.isfile', return_value=True):
                with pytest.raises(SystemExit):
                    _b = MagicMock(BuildConfig)
                    parser = configparser.ConfigParser()
                    parser.add_section('sonar')
                    parser.set('sonar', 'sonar_runner', 'sonar-runner-dist-2.4.jar')
                    parser.add_section('project')
                    parser.set('project', 'retry_sleep_interval', '0')
                    _b.settings = parser
                    
                    _sonar = SonarQube(config_override=_b)
                    _sonar.scan_code()

    mock_printmsg_fn.assert_called_with('SonarQube', 'scan_code', 'Could not connect to Sonar.  Maximum number of retries reached.', 'ERROR')


def test_scan_code_missing_sonar_home(monkeypatch):
    if os.getenv('SONAR_HOME'):
        monkeypatch.delenv('SONAR_HOME')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with pytest.raises(SystemExit):
            _b = MagicMock(BuildConfig)
            parser = configparser.ConfigParser()
            parser.add_section('sonar')
            parser.set('sonar', 'sonar_runner', 'sonar-runner-dist-2.4.jar')
            _b.settings = parser

            _sonar = SonarQube(config_override=_b)
            _sonar.scan_code()

    mock_printmsg_fn.assert_called_with('SonarQube', '_submit_scan', '\'SONAR_HOME\' environment variable must be '
                                                                  'defined', 'ERROR')


def test_scan_code_missing_sonar_project_properties(monkeypatch):
    monkeypatch.setenv('SONAR_HOME','FAKEHOME')

    with patch('flow.utils.commons.print_msg') as mock_printmsg_fn:
        with patch('flow.utils.commons.get_files_of_type_from_directory') as mock_getfiletypefromdir_fn:
            with patch('os.path.isfile', return_value=False):
                with pytest.raises(SystemExit):
                    mock_getfiletypefromdir_fn.return_value = ['sonar-scanner.jar']
                    _b = MagicMock(BuildConfig)
                    parser = configparser.ConfigParser()
                    parser.add_section('sonar')
                    parser.set('sonar', 'sonar_runner', 'sonar-runner-dist-2.4.jar')
                    _b.settings = parser

                    _sonar = SonarQube(config_override=_b)
                    _sonar.scan_code()

    mock_printmsg_fn.assert_called_with('SonarQube', '_submit_scan', 'No sonar-project.properties file was found.  Please include in the root of your project with a valid value for \'sonar.host.url\'', 'ERROR')

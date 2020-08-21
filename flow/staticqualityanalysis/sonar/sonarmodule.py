#!/usr/bin/python
# sonarmodule.py

import os
import subprocess
import time

from flow.buildconfig import BuildConfig
from flow.staticqualityanalysis.static_quality_analysis_abc import Static_Quality_Analysis

import flow.utils.commons as commons


class SonarQube(Static_Quality_Analysis):
    clazz = 'SonarQube'
    config = BuildConfig

    def __init__(self, config_override=None):
        method = '__init__'
        commons.print_msg(SonarQube.clazz, method, 'begin')

        if config_override is not None:
            self.config = config_override

        commons.print_msg(SonarQube.clazz, method, 'end')

    def scan_code(self):
        method = 'scan_code'
        commons.print_msg(SonarQube.clazz, method, 'begin')

        retries = 0

        keep_retrying = True

        while keep_retrying:
            try:
                sleep_timer = 0

                if self.config.settings.has_section('project') and self.config.settings.has_option('project',
                                                                                                   'retry_sleep_interval'):
                    sleep_timer = int(self.config.settings.get('project', 'retry_sleep_interval'))

                if retries > 0:
                    time.sleep(sleep_timer * retries)

                self._submit_scan()
                keep_retrying = False
            except Exception:
                retries += 1

                if retries > 3:
                    commons.print_msg(SonarQube.clazz, method, 'Could not connect to Sonar.  Maximum number of retries '
                                                              'reached.', "ERROR")
                    keep_retrying = False
                    exit(1)
                else:
                    commons.print_msg(SonarQube.clazz, method, "Attempting retry number {}".format(retries), "WARN")

        commons.print_msg(SonarQube.clazz, method, 'end')

    # noinspection PyUnboundLocalVariable
    def _submit_scan(self):
        method = '_submit_scan'
        commons.print_msg(SonarQube.clazz, method, 'begin')

        process_failed = False

        sonar_user = os.environ.get('SONAR_USER')
        sonar_pwd = os.environ.get('SONAR_PWD')

        if sonar_user is None or sonar_pwd is None or len(sonar_user.strip()) == 0 or len(sonar_pwd.strip()) == 0:
            commons.print_msg(SonarQube.clazz, method, 'No sonar name/pwd supplied. If your sonar instance does not '
                                                      'support anonymous access then this operation may fail', 'WARNING')

        if not os.getenv("SONAR_HOME"):
            commons.print_msg(SonarQube.clazz, method, '\'SONAR_HOME\' environment variable must be defined', 'ERROR')
            exit(1)

        sonar_jar_files = commons.get_files_of_type_from_directory('jar', os.environ.get('SONAR_HOME'))
        if len(sonar_jar_files) > 0:
            sonar_jar_files.sort(reverse=True)
            sonar_runner_executable = sonar_jar_files[0]
        elif not self.config.settings.has_section('sonar') or not self.config.settings.has_option('sonar',
                                                                                                'sonar_runner'):
            commons.print_msg(SonarQube.clazz, method, 'Sonar runner undefined.  Please define path to sonar '
                                                      'runner in settings.ini.', 'ERROR')
            exit(1)
        else:
            sonar_runner_executable = self.config.settings.get('sonar', 'sonar_runner')

        if not os.path.isfile('sonar-project.properties'):
            commons.print_msg(SonarQube.clazz, method, 'No sonar-project.properties file was found.  Please include in the root of your project with a valid value for \'sonar.host.url\'', 'ERROR')
            exit(1)

        if 'sonar' in self.config.json_config and 'propertiesFile' in self.config.json_config['sonar']:
            custom_sonar_file = self.config.json_config['sonar']['propertiesFile']

            if sonar_user is not None and sonar_pwd is not None:
                sonar_cmd = 'java -Dsonar.projectKey="' + self.config.sonar_project_key + '" -Dsonar.projectName="' + self.config.sonar_project_key + '" -Dsonar.projectVersion="' + self.config.version_number + '" -Dsonar.login=$SONAR_USER -Dsonar.password=$SONAR_PWD -Dproject.settings="' + custom_sonar_file + '" -Dproject.home="$PWD" -jar $SONAR_HOME/' + sonar_runner_executable + ' -e -X'
            else:
                sonar_cmd = 'java -Dsonar.projectKey="' + self.config.sonar_project_key + '" -Dsonar.projectName="' + self.config.sonar_project_key + '" -Dsonar.projectVersion="' + self.config.version_number + '" -Dproject.settings="' + custom_sonar_file + '" -Dproject.home="$PWD" -jar $SONAR_HOME/' + sonar_runner_executable + ' -e -X'
            commons.print_msg(SonarQube.clazz, method, sonar_cmd)
        else:
            if sonar_user is not None and sonar_pwd is not None:
                sonar_cmd = 'java -Dsonar.projectKey="' + self.config.sonar_project_key + '" -Dsonar.projectName="' + self.config.sonar_project_key + '" -Dsonar.projectVersion="' + self.config.version_number + '" -Dsonar.login=$SONAR_USER -Dsonar.password=$SONAR_PWD -Dproject.home="$PWD" -jar $SONAR_HOME/' + sonar_runner_executable + ' -e -X'
            else:
                sonar_cmd = 'java -Dsonar.projectKey="' + self.config.sonar_project_key + '" -Dsonar.projectName="' + self.config.sonar_project_key + '" -Dsonar.projectVersion="' + self.config.version_number + '" -Dproject.home="$PWD" -jar $SONAR_HOME/' + sonar_runner_executable + ' -e -X'
            commons.print_msg(SonarQube.clazz, method, sonar_cmd)

        p = subprocess.Popen(sonar_cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while p.poll() is None:
            line = p.stdout.readline().decode('utf-8').strip(' \r\n')

            commons.print_msg(SonarQube.clazz, method, line)

            if 'ERROR:' in line:
                commons.print_msg(SonarQube.clazz, method, "Failed to execute Sonar: {}".format(line), 'ERROR')
                process_failed = True

        p_output, errs = p.communicate(timeout=120)

        for line in p_output.splitlines():
            commons.print_msg(SonarQube.clazz, method, line.decode('utf-8'))

        if p.returncode != 0:
            commons.print_msg(SonarQube.clazz, method, "Failed calling sonar runner. Return code of {}"
                              .format(p.returncode),
                             'ERROR')
            process_failed = True

        if process_failed:
            raise Exception('Failed uploading')

        commons.print_msg(SonarQube.clazz, method, 'end')

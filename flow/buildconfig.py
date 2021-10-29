#!/usr/bin/python
# buildconfig.py

import configparser
import json
import os.path

import flow.utils.commons as commons


class BuildConfig:
    clazz = 'BuildConfig'
    json_config = None
    build_env = None
    build_env_info = None
    version_number = None
    project_name = None
    artifact_category = None
    calver_bump_type = None
    calver_year_format = None
    settings = None
    language = None
    version_strategy = None
    artifact_extension = None
    artifact_extensions = None
    push_location = 'fordeployment'
    sonar_project_key = None
    project_tracker = None

    def __init__(self, args):
        method = '__init__'

        commons.print_msg(BuildConfig.clazz, method, 'begin')
        commons.print_msg(BuildConfig.clazz, method, "environment is set to: {}".format(args.env))

        BuildConfig.build_env = args.env

        BuildConfig.settings = configparser.ConfigParser()

        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
        rel_path = 'settings.ini'
        abs_file_path = os.path.join(script_dir, rel_path)
        commons.print_msg(BuildConfig.clazz, method, abs_file_path)
        BuildConfig.settings.read(abs_file_path)

        self._load_build_config()

        BuildConfig.build_env_info = BuildConfig.json_config['environments'][args.env]

        BuildConfig.language = BuildConfig.json_config['projectInfo']['language'].lower()

        if 'artifactoryConfig' in BuildConfig.json_config:
            commons.print_msg(self.clazz, method, 'Detected artifactoryConfig block.  Retrieving artifactType.')
            # TODO get rid of artifact_extension in place of artifact_extensions if possible.
            BuildConfig.artifact_extension = BuildConfig.json_config['artifactoryConfig'].get("artifactType", None)
            BuildConfig.artifact_extensions = BuildConfig.json_config['artifactoryConfig'].get("artifactTypes", None)
        elif 'artifact' in BuildConfig.json_config:
            commons.print_msg(self.clazz, method, 'Detected artifactory block.  Retrieving artifactType.')
            BuildConfig.artifact_extension = BuildConfig.json_config['artifact'].get("artifactType", None)
            BuildConfig.artifact_extensions = BuildConfig.json_config['artifact'].get("artifactTypes", None)

        projectTrackers = []
        if 'tracker' in BuildConfig.json_config:
            projectTrackers.append('tracker')
        if 'projectTracking' in BuildConfig.json_config:
            if 'tracker' in BuildConfig.json_config['projectTracking']:
                if 'tracker' not in projectTrackers:
                    projectTrackers.append('tracker')
            if 'jira' in BuildConfig.json_config['projectTracking']:
                if 'jira' not in projectTrackers:
                    projectTrackers.append('jira')

        if len(projectTrackers) > 1:
            trackers = ','.join(projectTrackers)
            commons.print_msg(BuildConfig.clazz, method, "The build config json contains configuration for "
                                                         "multiple project tracking tools: {}"
                                                         "Please remove all but one project tracker from the "
                                                         "configuration".format(trackers), 'ERROR')
            exit(1)
        elif len(projectTrackers) == 1:
            BuildConfig.project_tracker = projectTrackers[0]

        try:
            BuildConfig.version_strategy = BuildConfig.json_config['projectInfo']['versionStrategy']
        except KeyError:
            commons.print_msg(BuildConfig.clazz, method, "The build config json does not contain projectInfo => "
                                                        "versionStrategy.  'manual', 'calver_year', 'tracker' or 'jira' values can be "
                                                        "used.", 'ERROR')
            exit(1)

        if BuildConfig.version_strategy != 'manual' and BuildConfig.version_strategy != 'calver_year' and BuildConfig.version_strategy != projectTrackers[0]:
            commons.print_msg(BuildConfig.clazz, method, "The versionStrategy in build config json is not "
                                                         "manual or calver_year and does not match the "
                                                         "defined project tracking tool: {}.".format(projectTrackers[0]), 'ERROR')
            exit(1)

        commons.print_msg(BuildConfig.clazz, method, 'end')

    def _load_build_config(self):
        method = 'loadBuildConfig'
        commons.print_msg(BuildConfig.clazz, method, 'begin')
        commons.print_msg(BuildConfig.clazz, method, "The run time environment {}".format(BuildConfig.build_env))

        if BuildConfig.build_env is None:
            commons.print_msg(BuildConfig.clazz, method, 'Environment was not passed in.', 'ERROR')
            exit(1)

        if BuildConfig.json_config is None:
            self.__check_file_exists(commons.build_config_file)
            build_config = json.loads(open(commons.build_config_file).read())

            if build_config == '':
                commons.print_msg(BuildConfig.clazz, method, 'Environment was not passed in.', 'ERROR')
                exit(1)

            BuildConfig.json_config = build_config

        try:
            BuildConfig.project_name = BuildConfig.json_config['projectInfo']['name']
            BuildConfig.artifact_category = BuildConfig.json_config['environments'][BuildConfig.build_env][
                'artifactCategory'].lower()
            if ('versionStrategy' in BuildConfig.json_config['projectInfo'].keys() and
                BuildConfig.json_config['projectInfo']['versionStrategy'] == 'calver_year'):
                bump_type = BuildConfig.json_config['environments'][BuildConfig.build_env]['calverBumpType'].lower()
                commons.print_msg(BuildConfig.clazz, method, "The calver bump type is {}".format(bump_type))
                BuildConfig.calver_bump_type = bump_type
                #check if year format is defined
                if 'calverYearFormat' in BuildConfig.json_config['environments'][BuildConfig.build_env].keys():
                    calver_year_format = BuildConfig.json_config['environments'][BuildConfig.build_env]['calverYearFormat'].lower()
                    if calver_year_format != 'short' and calver_year_format != 'long':
                        commons.print_msg(BuildConfig.clazz, method, "The calverYearFormat in build config json must be either 'short' "
                                                                     "or 'long'.", 'ERROR')
                        exit(1)
                    commons.print_msg(BuildConfig.clazz, method, "The calver year format is {}".format(calver_year_format))
                    BuildConfig.calver_year_format = calver_year_format
                #else:
                    # Not Implemented here. It's possible that the short_year flag was passed instead of
                    # the build config, should that flag be removed in favor of the build config?
        except KeyError as e:
            commons.print_msg(BuildConfig.clazz, method, "The buildConfig.json is missing a key. {}".format(e),
                             'ERROR')
            exit(1)

        commons.print_msg(BuildConfig.clazz, method, 'end')

        return BuildConfig.json_config

    def __check_file_exists(self, file):
        method = "checkFileExists"

        if not os.path.isfile(file):
            for f in os.listdir('.'):
                commons.print_msg(BuildConfig.clazz, method, 'Listing files found.')
                commons.print_msg(BuildConfig.clazz, method, f)
            commons.print_msg(BuildConfig.clazz, method, 'Cannot find buildConfig.json.  Only the files above were '
                                                        'found in the current directory.', 'ERROR')

            exit(1)

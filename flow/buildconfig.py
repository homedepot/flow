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
    settings = None
    language = None
    version_strategy = None
    artifact_extension = None
    artifact_extensions = None
    push_location = 'fordeployment'

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

        try:
            BuildConfig.version_strategy = BuildConfig.json_config['projectInfo']['versionStrategy']
        except KeyError:
            commons.print_msg(BuildConfig.clazz, method, "The build config json does not contain projectInfo => "
                                                         "versionStrategy.  'manual' or 'tracker' values can be "
                                                         "used.", 'ERROR')
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

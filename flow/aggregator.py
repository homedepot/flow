#!/usr/bin/python
# aggregator.py

import os
import sys
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from argparse import FileType
from flow import pluginloader
import flow.utils.commons as commons
from flow.buildconfig import BuildConfig
from flow.cloud.cloudfoundry.cloudfoundry import CloudFoundry
from flow.cloud.gcappengine.gcappengine import GCAppEngine
from flow.coderepo.github.github import GitHub
from flow.communications.slack.slack import Slack
from flow.metrics.graphite.graphite import Graphite
from flow.projecttracking.tracker.tracker import Tracker
from flow.projecttracking.jira.jira import Jira
from pydispatch import dispatcher
from flow.staticqualityanalysis.sonar.sonarmodule import SonarQube
from flow.utils.commons import Commons
from flow.zipit.zipit import ZipIt
import pkg_resources


from flow.artifactstorage.artifactory.artifactory import Artifactory


def main():
    clazz = 'aggregator'
    method = 'main'
    tasks_requiring_github = []

    try:
        version = pkg_resources.require("THD-Flow")[0].version
    except:
        version = 'UNKNOWN'

    parser = ArgumentParser(prog='version {} \n flow'.format(version))

    subparsers = parser.add_subparsers(help='Task types', dest='task')

    parser.add_argument('env', help="An environment that is defined in buildConfig.json environments section.")

    parser.add_argument('-q', '--quiet', help="Silence the logging to stdout", default='False')

    load_task_parsers(subparsers)

    plugins = []

    for i in pluginloader.get_plugins():
        plugin = pluginloader.load_plugin(i)

        new_parser = subparsers.add_parser(plugin.parser, formatter_class=RawTextHelpFormatter)
        plugin.register_parser(new_parser)
        plugins.append(plugin)

        if hasattr(plugin, 'require_version') and plugin.require_version is True:
            tasks_requiring_github.append(plugin.parser)

    args = parser.parse_args()

    task = args.task.lower()

    if 'quiet' in args and args.quiet.lower() in ['yes', 'true', 'off', 'y']:
        Commons.quiet = True
    elif task == 'github' and args.action == 'getversion' and args.output is None:
        Commons.quiet = True
    # elif task == 'github' and args.action == 'version' and args.output is None:
    #     Commons.quiet = True

    commons.print_msg(clazz, method, "THD-Flow Version: {}".format(version))

    BuildConfig(args)

    if 'deploy_directory' in args and args.deploy_directory is not None:
        commons.print_msg(clazz, method, "Setting deployment directory to {}".format(args.deploy_directory))
        BuildConfig.push_location = args.deploy_directory

    connect_error_dispatcher()

    github = None

    # TODO check if there are any registered metrics endpoints defined in settings.ini. This is optional.
    metrics = Graphite()

    commons.print_msg(clazz, method, "Task {}".format(task))

    tasks_requiring_github.extend(['sonar', 'slack', 'artifactory', 'cf', 'zipit', 'gcappengine'])
    if BuildConfig.project_tracker == 'tracker':
        tasks_requiring_github.append('tracker')
    elif BuildConfig.project_tracker == 'jira':
        tasks_requiring_github.append('jira')

    if task != 'github' and task in tasks_requiring_github:
        github = GitHub()

        if 'version' in args and args.version is not None and len(args.version.strip()) > 0 and args.version.strip(
                                                                                                ).lower() != 'latest':
            # The only time a user should be targeting a snapshot environment and specifying a version
            # number without a "+" should be if they were manually versioning and passing in a base
            # version number.  Although technically this could be used outside of the manually versioned
            # experience.
            #
            # i.e. flow cf deploy -v 1.0.1 development
            #      this would deploy the latest snapshot version of 1.0.1, 1.0.1+3
            # if however, they supplied the "+" it would target that specific snapshot version and not the latest
            # i.e. flow cf deploy -v 1.0.1+2
            #      this would deploy the version 1.0.1+2 even though there is a snapshot available with +3
            if BuildConfig.artifact_category == 'snapshot' and '+' not in args.version:
                commons.print_msg(clazz, method, ('Base version passed in.  Looking for latest snapshot version '
                                                  'determined by base', args.version))
                # TODO it doesn't appear that this is actually returning the latest snapshot, but instead returning
                #      what was passed in.  even in the older version of code.
                BuildConfig.version_number = github.get_git_last_tag(args.version.strip())
            else:
                BuildConfig.version_number = BuildConfig.version_number = github.get_git_last_tag(args.version.strip())
            # validate after processing what the version_number is set to.
            commons.print_msg(clazz, method, "Setting version number based on argument {}"
                              .format(BuildConfig.version_number))

        else:
            BuildConfig.version_number = github.get_git_last_tag()

    if task == 'github':
        github = GitHub()
        if args.action == 'version':
            if BuildConfig.project_tracker == 'tracker':
                _tracker = Tracker()
                call_github_version(github, _tracker, file_path=args.output, args=args)
            elif BuildConfig.project_tracker == 'jira':
                _jira = Jira()
                call_github_version(github, _jira, file_path=args.output, args=args)
            else:
                call_github_version(github, None, file_path=args.output, args=args)
            metrics.write_metric(task, args.action)
        elif args.action == 'getversion':
            if 'output' in args:
                call_github_getversion(github, file_path=args.output)
            else:
                call_github_getversion(github)
            metrics.write_metric(task, args.action)
    elif task == 'tracker':
        tracker = Tracker()

        commits = get_git_commit_history(github, args)

        story_list = tracker.extract_story_id_from_commit_messages(commits)

        tracker.tag_stories_in_commit(story_list)
        metrics.write_metric(task, args.action)
    elif task == 'jira':
        jira = Jira()

        commits = get_git_commit_history(github, args)

        story_list = jira.extract_story_id_from_commit_messages(commits)

        jira.tag_stories_in_commit(story_list)
        metrics.write_metric(task, args.action)
    elif task == 'slack':
        slack = Slack()

        if args.action == 'release':
            if BuildConfig.project_tracker == 'tracker':
                _project_tracker_instance = Tracker()
            elif BuildConfig.project_tracker == 'jira':
                _project_tracker_instance = Jira()
            commits = get_git_commit_history(github, args)

            story_list = _project_tracker_instance.extract_story_id_from_commit_messages(commits)
            story_details = _project_tracker_instance.get_details_for_all_stories(story_list)
            story_details = _project_tracker_instance.flatten_story_details(story_details)

            slack.publish_deployment(story_details)
        elif args.action == 'message':
            channel = args.channel if args.channel else None
            user = args.user if args.user else None
            icon = args.icon if args.icon else None
            emoji = args.emoji if args.emoji else None
            attachment_color = args.attachment_color if args.attachment_color else None
            slack_url = args.slack_url

            slack.publish_custom_message(message=args.message, channel=channel, user=user, icon=icon, emoji=emoji,
                                         attachment_color=attachment_color, slack_url=slack_url)
        metrics.write_metric(task, args.action)
    elif task == 'sonar':
        if 'sonar_project_key' in args and args.sonar_project_key is not None:
            BuildConfig.sonar_project_key = args.sonar_project_key
        else:
            BuildConfig.sonar_project_key = BuildConfig.project_name
        sonar = SonarQube()
        sonar.scan_code()
        metrics.write_metric(task, args.action)
    elif task == 'artifactory':
        artifactory = Artifactory()

        if args.action == 'upload':
            artifactory.publish_build_artifact()
            metrics.write_metric(task, args.action)
        elif args.action == 'download':
            create_deployment_directory()
            artifactory.download_and_extract_artifacts_locally(BuildConfig.push_location + '/', extract=args.extract in ['y', 'yes', 'true'] or args.extract is None)
    elif task == 'cf':
        if BuildConfig.build_env_info['cf']:
            if 'version' not in args:
                commons.print_msg(clazz, method, 'Version number not passed in for deployment. Format is: v{'
                                                 'major}.{minor}.{bug}+{buildnumber} ', 'ERROR')
                exit(1)

        cf = CloudFoundry()

        is_script_run_successful = True

        if args.action == 'deploy':

            if args.script is not None:
                commons.print_msg(clazz, method, 'Custom deploy script detected')
                cf.download_cf_cli()
                cf.download_custom_deployment_script(args.script)
                is_script_run_successful = cf.run_deployment_script(args.script)
            else:
                commons.print_msg(clazz, method, 'No custom deploy script passed in.  Cloud Foundry detected in '
                                                'buildConfig.  Calling standard CloudFoundry deployment.')

                if not args.no_download:
                    create_deployment_directory()

                    if BuildConfig.artifact_extension is None and BuildConfig.artifact_extensions is None:
                        commons.print_msg(clazz, method, 'Attempting to retrieve and deploy from GitHub.')

                        github.download_code_at_version()
                    else:
                        commons.print_msg(clazz, method, 'Attempting to retrieve and deploy from Artifactory.')
                        artifactory = Artifactory()

                        artifactory.download_and_extract_artifacts_locally(BuildConfig.push_location + '/')

                force = False

                if args.force is not None and args.force.strip().lower() != 'false':
                    force = True

                manifest = None

                if args.manifest is not None:
                    commons.print_msg(clazz, method, "Setting manifest to {}".format(args.manifest))
                    manifest = args.manifest

                delete_on_fail = args.delete_on_fail

                cf.deploy(force_deploy=force, manifest=manifest, delete_on_fail=delete_on_fail)

            commons.print_msg(clazz, method, 'Checking if we can attach the output to the CR')

            # noinspection PyPep8Naming
            SIGNAL = 'publish-deploy-complete'
            sender = {}
            dispatcher.send(signal=SIGNAL, sender=sender)
        elif args.action == 'rollback':
            cf.rollback_to_previous()

        if is_script_run_successful is False:
            exit(1)

        metrics.write_metric(task, args.action)

    elif task == 'gcappengine':
        app_engine = GCAppEngine()

        is_script_run_successful = True

        create_deployment_directory()

        if BuildConfig.artifact_extension is None and BuildConfig.artifact_extensions is None:
            commons.print_msg(clazz, method, 'Attempting to retrieve and deploy from GitHub.')

            github.download_code_at_version()
        else:
            commons.print_msg(clazz, method, 'Attempting to retrieve and deploy from Artifactory.')
            artifactory = Artifactory()

            artifactory.download_and_extract_artifacts_locally(BuildConfig.push_location + '/')

        app_yaml = None

        if args.app_yaml is not None:
            commons.print_msg(clazz, method, "Setting app yaml to {}".format(args.app_yaml))
            app_yaml = args.app_yaml

        if args.promote is not None and args.promote.lower() != 'true':
            app_engine.deploy(app_yaml=app_yaml, promote=False)
        else:
            app_engine.deploy(app_yaml=app_yaml)

        # noinspection PyPep8Naming
        SIGNAL = 'publish-deploy-complete'
        sender = {}
        dispatcher.send(signal=SIGNAL, sender=sender)

        if is_script_run_successful is False:
            exit(1)

        metrics.write_metric(task, args.action)

    elif task == 'zipit':
        ZipIt('artifactory', args.zipfile, args.contents)

    else:
        for i in plugins:
            if i.parser == task:
                i.run_action(args)
                metrics.write_metric(task, args.action)
                continue


def load_task_parsers(subparsers):
    github_parser = subparsers.add_parser("github", help="Github task", formatter_class=RawTextHelpFormatter)
    github_parser.add_argument('action', help="Github task to execute. Possible values: \n "
                                              "version    - create new version and tag repository with version number.  "
                                              "Also append release notes to version information. \n"
                                              "getversion - returns the latest version number.")
    github_parser.add_argument('-v', '--version', help='(optional) If manually versioning, this is passed in by the '
                                                       'user.  Note: versionStrategy in buildConfig should be set to '
                                                       '"manual"')
    github_parser.add_argument('-o', '--output', help='(optional) Writes the version number to a file. Use only if '
                                                      'you need to persist the version number in a file.')
    github_parser.add_argument('-sy', '--short-year', help='(optional) causes flow to create a calver_year version '
                                                           'with a 2 digit year instead of a 4 digit year.  Note: '
                                                           'versionStrategy in buildConfig should be set to "calver_year"',
                                                           action='store_true')
    github_parser.add_argument('--no-publish', help='(optional) Stops publish to GitHub releases', action='store_true')
    github_parser.add_argument('-rnop', '--release-notes-output-path',
                               type=FileType('w'), help='(optional) Writes the release notes to a file. Use only if '
                                                        'you need to persist the release notes in a file.')
    tracker_parser = subparsers.add_parser("tracker", help="Tracker task", formatter_class=RawTextHelpFormatter)
    tracker_parser.add_argument('action', help="Tracker task to execute. Possible Values: "
                                               "\n label-release - lookup stories in commit history and tag each story "
                                               "with the current version number")
    tracker_parser.add_argument('-v', '--version', help='(optional) If manually versioning, this is passed in by the '
                                                        'user.  Note: versionStrategy in buildConfig should be set to '
                                                        '"manual"')
    jira_parser = subparsers.add_parser("jira", help="Jira task", formatter_class=RawTextHelpFormatter)
    jira_parser.add_argument('action', help="Jira task to execute. Possible Values: "
                                            "\n label-release - lookup stories in commit history and tag each story "
                                            "with current version number")
    jira_parser.add_argument('-v', '--version', help='(optional) If manually versioning, this is passed in by the '
                                                     'user.  Note: versionStrategy in buildConfig should be set to '
                                                     '"manual"')
    slack_parser = subparsers.add_parser("slack", help="Slack task", formatter_class=RawTextHelpFormatter)
    slack_parser.add_argument('action', help='Slack task to execute. Possible values: \n '
                                             'release - ship release notes to slack after a deployment has completed \n'
                                             'message - Sends custom slack messages.  One use case is for sending flow '
                                             'deprecation messages to teams during their deployment.')
    slack_parser.add_argument('-c', '--channel', help="Slack channel to post in.")
    slack_parser.add_argument('-v', '--version', help='(optional) Defaults to latest version.  If upload is for a '
                                                      'previous version, pass in the version number here. ')
    slack_parser.add_argument('-m', '--message', help="For use with message action. Message to be published.")
    slack_parser.add_argument('-s', '--user', help="(optional) For use with message action. User name for message.")
    slack_parser.add_argument('-i', '--icon', help="(optional) For use with message action. Icon to be displayed in footer.")
    slack_parser.add_argument('-e', '--emoji', help="(optional) For use with message action. Emoji for message.")
    slack_parser.add_argument('-a', '--attachment-color', help="(optional) For use with message action. Color for "
                                                               "attachment "
                                                               "bar.")
    slack_parser.add_argument('-u', '--slack_url', help="(optional) For use with message action. Slack webhook url.")

    artifactory_parser = subparsers.add_parser("artifactory", help="Artifactory task",
                                               formatter_class=RawTextHelpFormatter)
    artifactory_parser.add_argument('action', help='Used to interact with and upload to Artifactory. Possible values: '
                                                   '\n upload - upload an artifact to artifactory')
    artifactory_parser.add_argument('-x', '--extract', help='(optional) Only used for download action. Specifies whether the downloaded artifact should be extracted (only '
                                                            'applies to .tar .tar.gz .zip file formats). Default True.')
    artifactory_parser.add_argument('-v', '--version', help='(optional) If manually versioning, this is passed in by the '
                                                            'user.  Note: versionStrategy in buildConfig should be set to '
                                                            '"manual"')

    sonar_parser = subparsers.add_parser("sonar", help="Sonar task", formatter_class=RawTextHelpFormatter)
    sonar_parser.add_argument('action', help='Upload to Sonar for analysis. Possible values: \n '
                                             'upload - uploads artifact to artifactory. location is based on settings in '
                                             'buildConfig.json.  \n '
                                             'download - downloads artifact from artifactory. location is based on '
                                             'settings in buildConfig.json and optional version number passed in.')
    sonar_parser.add_argument('-v', '--version', help='(optional) If manually versioning, this is passed in by the '
                                                      'user.  Note: versionStrategy in buildConfig should be set to '
                                                      '"manual"')
    sonar_parser.add_argument('-pk', '--sonar-project-key', help='(optional) If passed then this value is used for sonar.projectKey and sonar.projectName '
                                                          'otherwise buildConfig projectInfo.name is used.')

    cf_parser = subparsers.add_parser("cf", help="Cloud Foundry task",
                                            formatter_class=RawTextHelpFormatter)
    cf_parser.add_argument('action', help='CF task. Possible values: \n '
                                                'deploy   - deploy application to Cloud Foundry \n'
                                                'rollback - Route traffic to and restart the most '
                                                'recent stopped version while stopping and deleting the current version')
    cf_parser.add_argument('-v', '--version', help='(optional) Defaults to latest version.  If deployment is '
                                                         'for a previous version, pass in the version number here. ')
    cf_parser.add_argument('-f', '--force', help='(optional) Force the deploy even if the same version number is '
                                                       'already running.  \n '
                                                       'Note: Zero-downtime deployment will not occur if forcing a '
                                                       'deploy on the same version number.')
    cf_parser.add_argument('-s', '--script', help='(optional) If you choose to use a custom deploy script '
                                                        'instead of the default zero-downtime, pass in the path to '
                                                        'deploy script here.')
    cf_parser.add_argument('-d', '--delete-on-fail', help='(optional) Whether or not to delete the deployed application if the deployment fails. Default False.')
    cf_parser.add_argument('-metrics', '--manifest', help='(optional) Custom manifest name if you choose not to '
                                                                ' follow standard pattern of {environment}.manifest.yml')
    cf_parser.add_argument('--no-download', help='(optional) Skips downloading and extraction of artifact.'
                                                       'Useful if the artifact was downloaded previously.',
                                 action='store_true')

    zipship_parser = subparsers.add_parser('zipit', help='Support for zipping directory contents and shipping it '
                                                         'somewhere', formatter_class=RawTextHelpFormatter)
    zipship_parser.add_argument('-c', '--contents', help='Path to directory or file to be zipped', required=True)
    zipship_parser.add_argument('-z', '--zipfile', help='Name of the zipfile to create and ship', required=True)
    zipship_parser.add_argument('-r', '--recursive', help='(optional) Zip directory recursively if sub-directories '
                                                          'exist.')
    zipship_parser.add_argument('-v', '--version', help='(optional) If manually versioning, this is passed in by the '
                                                        'user.  Note: versionStrategy in buildConfig should be set to '
                                                        '"manual"')

    gc_appengine_parser = subparsers.add_parser('gcappengine', help='Deployment to Google Cloud App Engine',
                                                formatter_class=RawTextHelpFormatter)
    gc_appengine_parser.add_argument('action', help='Google Cloud App Engine. Possible values: \n '
                                                    'deploy - deploy to GC App Engine')
    gc_appengine_parser.add_argument('-v', '--version', help='(optional) Defaults to latest version.  If deployment is '
                                                             'for a previous version, pass in the version number '
                                                             'here. ')
    gc_appengine_parser.add_argument('-d', '--deploy-directory', help='(optional) Directory to download artifact to. '
                                                                      'By default it\'s downloaded to a new directory '
                                                                      'called \'fordeployment\'')
    gc_appengine_parser.add_argument('-y', '--app-yaml', help='(optional) Custom app manifest.  Default is app-{'
                                                              'environment}.yaml')
    gc_appengine_parser.add_argument('-p', '--promote', help='(optional) Automatically promote new version and stop '
                                                             'routing traffic to the older version.  Default is true.')


def connect_error_dispatcher():
    clazz = 'aggregator'
    method = 'connect_error_dispatcher'
    # Load dispatchers for communicating error messages to slack (or somewhere else)

    # noinspection PyPep8Naming
    SIGNAL = 'publish-error-signal'
    if 'slack' in BuildConfig.json_config:
        commons.print_msg(clazz, method, 'Detected slack in buildConfig. Connecting error dispatcher to slack.')
        dispatcher.connect(Slack.publish_error, signal=SIGNAL, sender=dispatcher.Any)
    elif BuildConfig.settings.has_section('slack'):
        commons.print_msg(clazz, method, 'Detected slack in global settings.ini.  Connecting error dispatcher to slack.')
        dispatcher.connect(Slack.publish_error, signal=SIGNAL, sender=dispatcher.Any)
    else:
        commons.print_msg(clazz, method, 'No event dispatcher detected. The only place errors will show up is in this '
                                         'log.', 'WARN')


def get_git_commit_history(git_hub_instance, args):
    if 'version' in args and args.version is not None and len(args.version.strip()) > 0 and args.version.strip(
                                                                                            ).lower() != 'latest':
        commits = git_hub_instance.get_all_git_commit_history_between_provided_tags(
            git_hub_instance.convert_semver_string_to_semver_tag_array(git_hub_instance.get_git_previous_tag(
                                                                       BuildConfig.version_number)),
            git_hub_instance.convert_semver_string_to_semver_tag_array(BuildConfig.version_number))
    else:
        commits = git_hub_instance.get_all_git_commit_history_between_provided_tags(
            git_hub_instance.convert_semver_string_to_semver_tag_array(git_hub_instance.get_git_previous_tag()),
            git_hub_instance.convert_semver_string_to_semver_tag_array(BuildConfig.version_number))

    return commits


def create_deployment_directory():
    clazz = 'aggregator'
    method = 'create_deployment_directory'
    commons.print_msg(clazz, method, 'begin')

    try:
        os.makedirs(BuildConfig.push_location)
    except FileExistsError as e:
        commons.print_msg(clazz, method, "Directory {dir} already exists. {error}".format(
            dir=BuildConfig.push_location, error=e), 'WARN')
    except Exception as e:
        commons.print_msg(clazz, method, "Failed making directory {dir}. {error}".format(
            dir=BuildConfig.push_location, error=e), 'ERROR')
        exit(1)

    commons.print_msg(CloudFoundry.clazz, method, 'end')


def call_github_getversion(git_hub_instance, file_path=None, open_func=open):
    commons.print_msg('aggregator', 'call_github_getversion', 'begin')
    clazz = 'aggregator'
    method = 'call_github_getversion'
    commons.print_msg(clazz, method, 'begin')

    my_version = git_hub_instance.get_git_last_tag()
    if file_path:
        try:
            commons.write_to_file(file_path, my_version, mode='w', open_func=open_func)
        except Exception as e:
            commons.print_msg(clazz, method, 'Failed creating file {file}.  {error}'.format(
                file=file_path, error=e), 'ERROR')
            exit(1)
    else:
        print(my_version)

    commons.print_msg(clazz, method, 'end')


# noinspection PyUnboundLocalVariable
def call_github_version(github_instance, project_tracker_instance, config=None, file_path=None, open_func=open, args=None):
    clazz = 'aggregator'
    method = 'call_github_version'
    commons.print_msg(clazz, method, 'begin')

    if config is None:
        config = BuildConfig

    release_notes = None

    if config.version_strategy == 'manual':
        try:
            if 'version' not in args:
                commons.print_msg(clazz, method, 'Version number required for release but not passed in.', 'ERROR')
                exit(1)
        except:
            commons.print_msg(clazz, method, 'Version number required for release but not passed in.', 'ERROR')
            exit(1)

        # find the highest existing tag that matches the base release that was passed in.
        base_semver_tag_array = github_instance.convert_semver_string_to_semver_tag_array(args.version.strip())
        highest_semver_tag_array = github_instance.get_highest_semver_tag()
        highest_semver_release_tag_array = github_instance.get_highest_semver_release_tag()

        # default the bump stategy to None.
        if config.artifact_category == 'snapshot':
            if highest_semver_release_tag_array == base_semver_tag_array:
                commons.print_msg(clazz, method, "Version number {} already has release build associated.".format(highest_semver_release_tag_array),
                                  'ERROR')
                exit(1)

            highest_semver_tag_array_from_base = github_instance.get_highest_semver_array_snapshot_tag_from_base(
                    base_semver_tag_array)
            # - Fetch all commit history.  Either from the last valid tag that includes base or the last tag if the base
            # doesn't exist in tags yet       if
            commits = github_instance.get_all_git_commit_history_between_provided_tags(highest_semver_tag_array if
                                                                                       highest_semver_tag_array_from_base
                                                                                       is None else
                                                                                       highest_semver_tag_array_from_base)

            next_semver_tag_array = github_instance.calculate_next_semver(tag_type=config.artifact_category,
                                                                          bump_type=None,
                                                                          highest_version_array=base_semver_tag_array if highest_semver_tag_array_from_base is None else highest_semver_tag_array_from_base)
        else:  # release, so use the base
            # - Fetch all commit history.  Either from the last valid tag that includes base or the last tag if the base
            # doesn't exist in tags yet
            commits = github_instance.get_all_git_commit_history_between_provided_tags(highest_semver_release_tag_array)

            next_semver_tag_array = base_semver_tag_array

        # - Dig through the story list to fetch some meta data about each story.
        if project_tracker_instance is None:
            story_details = None
        else:
            # - Dig through commits to find story list.
            story_list = project_tracker_instance.extract_story_id_from_commit_messages(commits)
            story_details = project_tracker_instance.get_details_for_all_stories(story_list)
            # need to ensure expected keys exist on story details for release notes formatting
            story_details = project_tracker_instance.flatten_story_details(story_details)

        # - Tag the version
        # - Update the release notes on the new version number with the stories meta data.
        release_notes = github_instance.format_github_specific_release_notes_from_project_tracker_story_details(story_details)

        my_version = github_instance.convert_semver_tag_array_to_semver_string(next_semver_tag_array)
        if file_path:
            commons.write_to_file(file_path, my_version, open_func=open_func)
        commons.print_msg(clazz, method, 'end')

    elif config.version_strategy == 'calver_year':
        #This version strategy is using a calver variant that looks like: year.major.patch+snapshot.
        # find the highest existing tag that matches the base release that was passed in.
        # functionality for fetching versions from github is identical for semver so re-using existing functions.
        if config.artifact_category == 'snapshot':
            # - Find the highest sem ver tag (not latest), doesn't matter if snapshot or release or beginning of time
            highest_calver_tag_array = github_instance.get_highest_semver_tag()
            highest_calver_tag_array_history = github_instance.get_highest_semver_snapshot_tag()

        elif config.artifact_category == 'release':
            # - Find the last semantic version release tag or beginning of time
            highest_calver_tag_array = github_instance.get_highest_semver_release_tag()
            highest_calver_tag_array_history = highest_calver_tag_array
        else:
            raise Exception("Invalid artifact_category provided.  Must be 'snapshot' or 'release'")

        short_year = False
        if args.short_year:
            short_year = True
        # This is a calver scheme, but leaving name as semver for compatibility with shared
        # code that comes after this if/else.
        next_semver_tag_array = github_instance.calculate_next_calver(tag_type=config.artifact_category,
                                                                        bump_type=config.calver_bump_type,
                                                                        highest_version_array=highest_calver_tag_array,
                                                                        short_year=short_year)

        # - Dig through the story list to fetch some meta data about each story.
        commits = github_instance.get_all_git_commit_history_between_provided_tags(highest_calver_tag_array_history)
        if project_tracker_instance is None:
            story_details = None
        else:
            # - Dig through commits to find story list.
            story_list = project_tracker_instance.extract_story_id_from_commit_messages(commits)
            story_details = project_tracker_instance.get_details_for_all_stories(story_list)
            # need to ensure expected keys exist on story details for release notes formatting
            story_details = project_tracker_instance.flatten_story_details(story_details)

        # - Tag the version
        # - Update the release notes on the new version number with the stories meta data.
        release_notes = github_instance.format_github_specific_release_notes_from_project_tracker_story_details(story_details)

        my_version = github_instance.convert_semver_tag_array_to_semver_string(next_semver_tag_array)
        if file_path:
            commons.write_to_file(file_path, my_version, open_func=open_func)
        commons.print_msg(clazz, method, 'end')

    elif config.version_strategy == 'tracker' or config.version_strategy == 'jira':
        if args and 'version' in args and args.version is not None:
            commons.print_msg(clazz, method, 'Version strategy set to automated in buildConfig but version flag was '
                                             'passed in.  Either change version strategy to manual or remove -v flag.',
                              'ERROR')
            exit(1)

        if config.artifact_category == 'snapshot':
            # - Find the highest sem ver tag (not latest), doesn't matter if snapshot or release or beginning of time
            highest_semver_tag_array = github_instance.get_highest_semver_tag()
            highest_semver_tag_array_history = github_instance.get_highest_semver_snapshot_tag()

        elif config.artifact_category == 'release':
            # - Find the last semantic version release tag or beginning of time
            highest_semver_tag_array = github_instance.get_highest_semver_release_tag()
            highest_semver_tag_array_history = highest_semver_tag_array
        else:
            raise Exception("Invalid artifact_category provided.  Must be 'snapshot' or 'release'")

        # - Fetch all commit history from that tag to now
        commits = github_instance.get_all_git_commit_history_between_provided_tags(highest_semver_tag_array_history)

        story_details = None
        if  config.project_tracker == 'tracker' or config.project_tracker == 'jira':
            # - Dig through commits to find story list.
            story_list = project_tracker_instance.extract_story_id_from_commit_messages(commits)
            # - Dig through the story list to fetch some meta data about each story.
            story_details = project_tracker_instance.get_details_for_all_stories(story_list)

        # default the bump strategy to None.
        if config.artifact_category == 'snapshot':
            next_semver_tag_array = github_instance.calculate_next_semver(tag_type=config.artifact_category,
                                                                          bump_type=None,
                                                                          highest_version_array=highest_semver_tag_array)
        else:  # release
            # New Release build
            # - Find the last semantic version release tag or beginning of time
            # - Based upon the story meta data, decided on the bump strategy.
            bump_strategy = project_tracker_instance.determine_semantic_version_bump(story_details)

            # - Increment the build number + 1
            next_semver_tag_array = github_instance.calculate_next_semver(tag_type=config.artifact_category,
                                                                          bump_type=bump_strategy,
                                                                          highest_version_array=highest_semver_tag_array)

        # - Tag the version
        # - Update the release notes on the new version number with the stories meta data.
        story_details = project_tracker_instance.flatten_story_details(story_details)
        release_notes = github_instance.format_github_specific_release_notes_from_project_tracker_story_details(story_details)
        my_version = github_instance.convert_semver_tag_array_to_semver_string(next_semver_tag_array)

        if file_path:
            commons.write_to_file(file_path, my_version, open_func=open_func)
        commons.print_msg(clazz, method, 'end')

    if args is not None and args.release_notes_output_path is not None:
        if release_notes is None:
            commons.print_msg(clazz, method, 'No release notes found to save to file', 'ERROR')
            exit(1)
        try:
            args.release_notes_output_path.write(release_notes)
        except Exception as e:
            commons.print_msg(clazz, method, 'Failed creating file {file}.  {error}'.format(
                file=args.release_notes_output_path, error=e), 'ERROR')
            exit(1)

    if args is None or not args.no_publish:
        github_instance.add_tag_and_release_notes_to_github(next_semver_tag_array, release_notes)

    print(my_version)


if __name__ == "__main__":
    main()
    sys.exit(0)

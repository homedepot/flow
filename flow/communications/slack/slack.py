#!/usr/bin/python
#slack.py

import os
import urllib.parse

import requests
from flow.buildconfig import BuildConfig
from flow.communications.communications_abc import communications

import flow.utils.commons as commons
from flow.utils.commons import Object


class Slack(communications):
    clazz = 'Slack'
    slack_url = os.getenv('SLACK_WEBHOOK_URL')
    config = BuildConfig
    http_timeout = 30

    def __init__(self, config_override=None):
        method = '__init__'
        commons.print_msg(Slack.clazz, method, 'begin')

        Slack.slack_url = os.getenv('SLACK_WEBHOOK_URL')

        if config_override is not None:
            self.config = config_override

        commons.print_msg(Slack.clazz, method, 'end')

    def publish_deployment(self, story_details):
        method = 'publish_deployment'
        commons.print_msg(Slack.clazz, method, 'begin')

        if Slack.slack_url is None:
            commons.print_msg(Slack.clazz, method, 'No Slack URL was found in the environment.  Did you set  '
                                                  'SLACK_WEBHOOK_URL in your pipeline?', 'ERROR')
            exit(1)

        commons.verify_version(self.config)

        icon = None
        emoji = None
        slack_channel = None
        user_name = None

        if 'slack' in self.config.json_config and 'emoji' in self.config.json_config['slack']:
            emoji = self.config.json_config['slack']['emoji']
        elif self.config.settings.has_section('slack') and self.config.settings.has_option('slack', 'emoji'):
            emoji = self.config.settings.get('slack', 'emoji')

        if 'slack' in self.config.json_config and 'icon' in self.config.json_config['slack']:
            icon = self.config.json_config['slack']['icon']
        elif self.config.settings.has_section('slack') and self.config.settings.has_option('slack', 'icon'):
            icon = self.config.settings.get('slack', 'icon')

        if 'slack' in self.config.json_config and 'channel' in self.config.json_config['slack']:
            slack_channel = self.config.json_config['slack']['channel']
        elif self.config.settings.has_section('slack') and self.config.settings.has_option('slack', 'channel'):
            slack_channel = self.config.settings.get('slack', 'channel')

        if 'slack' in self.config.json_config and 'botName' in self.config.json_config['slack']:
            user_name = self.config.json_config['slack']['botName']
        elif self.config.settings.has_section('slack') and self.config.settings.has_option('slack', 'bot_name'):
            user_name = self.config.settings.get('slack', 'bot_name')

        app_version = self.config.version_number
        environment = self.config.build_env
        app_name = self.config.json_config['projectInfo']['name']

        slack_message = Object()
        if icon:
            slack_message.icon_url = icon
        else:
            slack_message.icon_emoji = emoji
        if slack_channel:
            slack_message.channel = slack_channel
        slack_message.username = user_name
        slack_message.attachments = []

        # Application information
        attachment = Object()
        attachment.mrkdwn_in = ['pretext', 'fields']
        attachment.fallback = "{name} {version} has been deployed to {env}".format(name=app_name,
                                                                                   version=app_version,
                                                                                   env=environment)

        attachment.pretext = ":package: *{app}* _{version}_ has been deployed to *{env}*".format(app=app_name,
                                                                                                 version=app_version,
                                                                                                 env=environment)

        attachment.fields = []

        manual_deploy_environment_links = self._get_manual_deploy_links()

        # deploy links
        for key, value in enumerate(manual_deploy_environment_links):
            attachment_field = Object()
            attachment_field.value = "Deploy to <{link}|{title}>".format(link=manual_deploy_environment_links[value],
                                                                         title=value)
            attachment.fields.append(attachment_field)

        slack_message.attachments.append(attachment)

        # no stories defined
        if len(story_details) == 0:
            attachment = Object()
            attachment.mrkdwn_in = ['pretext', 'fields']
            attachment.pretext = '*No Release Notes*'
            slack_message.attachments.append(attachment)

        # story details
        for i, release_note in enumerate(story_details):
            if release_note.get('story_type') == 'release':
                story_emoji = ':checkered_flag:'
            elif release_note.get('story_type') == 'bug':
                story_emoji = ':beetle:'
            elif release_note.get('story_type') == 'chore':
                story_emoji = ':wrench:'
            else:
                story_emoji = ':star:'

            attachment = Object()
            attachment.fallback = release_note.get('name')
            attachment.mrkdwn_in = ['pretext', 'fields']
            if (BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack',
                                                                                              'release_note_attachment_color')):
                attachment.color = BuildConfig.settings.get('slack', 'release_note_attachment_color')
            else:
                attachment.color = '#0000ff'
            attachment.footer = 'Flow'
            if (BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack',
                                                                                              'footer_icon_url')):
                attachment.footer_icon = BuildConfig.settings.get('slack', 'footer_icon_url')

            if i == 0:
                attachment.pretext = '*Release Notes*'

            attachment.fields = []

            attachment_field = Object()
            attachment_field.value = "*" + str(release_note.get('id')) + "*                                                                                                             " + story_emoji + ' _' + release_note.get('story_type') + "_"
            attachment_field.short = True
            attachment.fields.append(attachment_field)
            attachment_field = Object()
            attachment_field.value = '*<' + release_note.get('url') + '|' + release_note.get('name') + '>*'
            attachment.fields.append(attachment_field)
            attachment_field = Object()
            if release_note.get('description') is None or len(release_note.get('description').strip()) == 0:
                attachment_field.value = '_No description_'
            else:
                attachment_field.value = (release_note.get('description')[:150] + '..') if len(release_note.get('description')) > 150 else release_note.get('description')
            attachment.fields.append(attachment_field)
            attachment_field = Object()
            attachment_field.value = '*Status*: ' + release_note.get('current_state')
            attachment_field.short = True
            attachment.fields.append(attachment_field)

            slack_message.attachments.append(attachment)

        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        commons.print_msg(Slack.clazz, method, Slack.slack_url)
        commons.print_msg(Slack.clazz, method, slack_message.to_JSON())

        resp = None  # instantiated so it can be logged outside of the try below the except

        try:
            resp = requests.post(Slack.slack_url, slack_message.to_JSON(), headers=headers, timeout=self.http_timeout)
        except requests.ConnectionError:
            commons.print_msg(Slack.clazz, method, "Request to Slack timed out.", "ERROR")
            exit(1)
        except Exception as e:
            commons.print_msg(Slack.clazz, method, "Failed sending slack message to {url}. {exception}".format(
                url=Slack.slack_url, exception=e))

            # has to be defined here too in order to exit properly during the exception but still log appropriate
            # messages when there is a status code available
            if hasattr('resp', 'status_code') and resp.status_code != 200:
                commons.print_msg(Slack.clazz, method, "Failed sending slack message to {url}.  \r\n Response: {resp}"
                                  .format(url=Slack.slack_url,
                                         resp=resp.text))

            exit(1)

        if hasattr('resp', 'status_code') and resp.status_code != 200:
            commons.print_msg(Slack.clazz, method, "Failed sending slack message to {url}.  \r\n Response: {resp}"
                              .format(url=Slack.slack_url,
                                     resp=resp.text))
            exit(1)

        commons.print_msg(Slack.clazz, method, 'end')

    def _get_manual_deploy_links(self):
        method = '_get_manual_deploy_links'
        manual_deploy_environment_links = {}

        # Look for manual deploy links in the current environment stanza
        if 'manualDeployEnvs' in self.config.build_env_info:
            manual_deploy_links = self.config.build_env_info['manualDeployEnvs']

            commons.print_msg(Slack.clazz, method, "Publishing build links: {}".format(manual_deploy_links))

            # For each manual deploy environment, lookup the corresponding link for that environment stanza
            for manually_deploy_to_env in manual_deploy_links:
                try:
                    manual_deploy_environment_links[manually_deploy_to_env] = self.config.json_config['environments'][manually_deploy_to_env]['manualDeployLink']
                    if "?" in manual_deploy_environment_links:
                        manual_deploy_environment_links[manually_deploy_to_env] = manual_deploy_environment_links[manually_deploy_to_env] + "&"
                    else:
                        manual_deploy_environment_links[manually_deploy_to_env] = manual_deploy_environment_links[manually_deploy_to_env] + "?"

                    manual_deploy_environment_links[manually_deploy_to_env] = manual_deploy_environment_links[manually_deploy_to_env] + "VERSION=" + urllib.parse.quote_plus(self.config.version_number)
                except KeyError as e:
                    commons.print_msg(Slack.clazz, method, "Could not find manual deploy link: {}".format(e),
                                     'ERROR')

        else:
            commons.print_msg(Slack.clazz, method, 'No manual build links specified')

        return manual_deploy_environment_links

    def publish_error(sender, message, class_name, method_name):
        method = 'publish_error'
        commons.print_msg(Slack.clazz, method, 'begin')

        if Slack.slack_url is None:
            commons.print_msg(Slack.clazz, method, 'No Slack URL was found in the environment.  Did you set SLACK_WEBHOOK_URL in your pipeline?', 'WARN')
        else:
            icon = None
            emoji = None
            slack_channel = None
            user_name = None

            if 'slack' in BuildConfig.json_config and 'emoji' in BuildConfig.json_config['slack']:
                emoji = BuildConfig.json_config['slack']['emoji']
            elif BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'emoji'):
                emoji = BuildConfig.settings.get('slack', 'emoji')

            if 'slack' in BuildConfig.json_config and 'icon' in BuildConfig.json_config['slack']:
                icon = BuildConfig.json_config['slack']['icon']
            elif BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'icon'):
                icon = BuildConfig.settings.get('slack', 'icon')

            if 'slack' in BuildConfig.json_config and 'channel' in BuildConfig.json_config['slack']:
                slack_channel = BuildConfig.json_config['slack']['channel']
            elif BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'channel'):
                slack_channel = BuildConfig.settings.get('slack', 'channel')

            if 'slack' in BuildConfig.json_config and 'botName' in BuildConfig.json_config['slack']:
                user_name = BuildConfig.json_config['slack']['botName']
            elif BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'bot_name'):
                user_name = BuildConfig.settings.get('slack', 'bot_name')

            app_version = BuildConfig.version_number
            environment = BuildConfig.build_env
            app_name = BuildConfig.json_config['projectInfo']['name']

            slack_message = Object()
            if icon:
                slack_message.icon_url = icon
            else:
                slack_message.icon_emoji = emoji
            if slack_channel:
                slack_message.channel = slack_channel

            slack_message.username = user_name
            slack_message.attachments = []

            # Application information
            attachment = Object()
            attachment.pretext = attachment.fallback = "CI/CD for {} has failed".format(app_name)

            if (BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack',
                                                                                              'error_attachment_color')):
                attachment.color = BuildConfig.settings.get('slack', 'error_attachment_color')
            else:
                attachment.color = '#ff0000'

            attachment.author_name = environment + " " + (str(app_version) if str(app_version) is not None else 'Unknown Version')
            attachment.title = "Build " + (os.environ.get('BUILD_ID') if os.environ.get('BUILD_ID') is not None else 'Unknown')
            attachment.title_link = (os.environ.get('BUILD_URL') if os.environ.get('BUILD_URL') is not None else '')
            attachment.footer = 'Flow'
            attachment.text = message

            attachment.fields = []

            attachment_field = Object()
            attachment_field.value = class_name
            attachment_field.title = 'Class'
            attachment.fields.append(attachment_field)

            attachment_field = Object()
            attachment_field.value = method_name
            attachment_field.title = 'Method'
            attachment.fields.append(attachment_field)

            slack_message.attachments.append(attachment)

            commons.print_msg(Slack.clazz, method, slack_message.to_JSON())

            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

            commons.print_msg(Slack.clazz, method, Slack.slack_url)

            try:
                resp = requests.post(Slack.slack_url, slack_message.to_JSON(), headers=headers,
                                     timeout=Slack.http_timeout)

                if resp.status_code == 200:
                    commons.print_msg(Slack.clazz, method,
                                      "Successfully sent to slack. \r\n resp: {}".format(resp.text),
                                      "DEBUG")
                else:
                    commons.print_msg(Slack.clazz, method,
                                      "Failed sending slack message to {url} \r\n Resp: {resp} \r\n "
                                      "Status: {stat}".format(url=Slack.slack_url, resp=resp.text,
                                                              stat=resp.status_code), "WARN")

            except requests.ConnectionError:
                commons.print_msg(Slack.clazz, method, "Request to Slack timed out.", "ERROR")
            except Exception as e:
                commons.print_msg(Slack.clazz, method, "Failed sending slack message to {url} with exception {ex}"
                                  .format(url=Slack.slack_url,
                                          ex=e))

        commons.print_msg(Slack.clazz, method, 'end')

    def publish_custom_message(self, message, channel=None, user='Flow', icon=None, emoji=None,
                               attachment_color=None, slack_url=None):
        method = 'publish_custom_message'
        commons.print_msg(Slack.clazz, method, 'begin')

        slack_message = Object()

        if slack_url is not None:
            Slack.slack_url = slack_url

        if slack_url is None and Slack.slack_url is None and BuildConfig.settings.has_section('slack') and \
                BuildConfig.settings.has_option('slack', 'generic_message_slack_url'):
            Slack.slack_url = BuildConfig.settings.get('slack', 'generic_message_slack_url')
        elif slack_url is None and Slack.slack_url is None:
            commons.print_msg(Slack.clazz, method, 'No Slack URL was found in the environment or settings.ini.  Failed to send message', 'ERROR')
            exit(1)

        if emoji is None and 'slack' in BuildConfig.json_config and 'emoji' in BuildConfig.json_config['slack']:
            emoji = BuildConfig.json_config['slack']['emoji']
            slack_message.icon_emoji = emoji
        elif emoji is None and BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'emoji'):
            emoji = BuildConfig.settings.get('slack', 'emoji')
            slack_message.icon_emoji = emoji

        if icon is None and 'slack' in BuildConfig.json_config and 'icon' in BuildConfig.json_config['slack']:
            icon = BuildConfig.json_config['slack']['icon']
            slack_message.icon_url = icon
        elif icon is None and BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'icon'):
            icon = BuildConfig.settings.get('slack', 'icon')
            slack_message.icon_url = icon

        if channel is not None:
            slack_message.channel = channel
        elif 'slack' in BuildConfig.json_config and 'channel' in BuildConfig.json_config['slack']:
            slack_channel = BuildConfig.json_config['slack']['channel']
            slack_message.channel = slack_channel
        elif BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'channel'):
            slack_channel = BuildConfig.settings.get('slack', 'channel')
            slack_message.channel = slack_channel

        if user is None and 'slack' in BuildConfig.json_config and 'botName' in BuildConfig.json_config['slack']:
            user = BuildConfig.json_config['slack']['botName']
        elif user is None and BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack', 'bot_name'):
            user = BuildConfig.settings.get('slack', 'bot_name')

        app_version = BuildConfig.version_number
        environment = BuildConfig.build_env
        app_name = BuildConfig.json_config['projectInfo']['name']

        slack_message.username = user
        slack_message.attachments = []

        # Application information
        attachment = Object()
        attachment.pretext = attachment.fallback = message

        if attachment_color is not None:
            attachment.color = attachment_color
        elif (BuildConfig.settings.has_section('slack') and BuildConfig.settings.has_option('slack',
                                                                                  'release_note_attachment_color')):
            attachment.color = BuildConfig.settings.get('slack', 'release_note_attachment_color')
        else:
            attachment.color = '#0000ff'

        attachment.author_name = app_name + ' ' + environment + " " + (str(app_version) if str(app_version) is not
                                                                                           None else 'Unknown Version')
        if 'github' in self.config.json_config and 'org' in self.config.json_config['github']:
            attachment.author_name = "{msg} \n org: {org} \n repo: {repo}".format(msg=attachment.author_name,
                                                                    org=self.config.json_config['github']['org'],
                                                              repo=self.config.json_config['github']['repo'])
        # attachment.title = app_name
        attachment.title_link = (os.environ.get('BUILD_URL') if os.environ.get('BUILD_URL') is not None else '')
        attachment.footer = 'Flow'
        # attachment.text = message

        slack_message.attachments.append(attachment)

        commons.print_msg(Slack.clazz, method, slack_message.to_JSON())

        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        commons.print_msg(Slack.clazz, method, Slack.slack_url)

        try:
            resp = requests.post(Slack.slack_url, slack_message.to_JSON(), headers=headers,
                                 timeout=Slack.http_timeout)
            if resp.status_code == 200:
                commons.print_msg(Slack.clazz, method, "Successfully sent to slack. \r\n resp: {}".format(resp.text),
                                 "DEBUG")
            else:
                commons.print_msg(Slack.clazz, method, "Failed sending slack message to {url} \r\n Resp: {resp} \r\n "
                                                      "Status: {stat}".format(url=Slack.slack_url, resp=resp.text,
                                                                              stat=resp.status_code), "WARN")

        except requests.ConnectionError:
            commons.print_msg(Slack.clazz, method, "Request to Slack timed out.", "ERROR")
        except Exception as e:
            commons.print_msg(Slack.clazz, method, "Failed sending slack message to {url} with exception {ex}"
                              .format(url=Slack.slack_url,
                                     ex=e))

        commons.print_msg(Slack.clazz, method, 'end')

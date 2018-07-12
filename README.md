# Flow
A CLI tool for common Continuous Integration/Continuous Delivery Tasks

[![Build Status](https://travis-ci.org/homedepot/flow.svg?branch=master)](https://travis-ci.org/homedepot/flow)
[![Coverage Status](https://coveralls.io/repos/github/homedepot/flow/badge.svg?branch=master)](https://coveralls.io/github/homedepot/flow?branch=master)
[![PyPI version](https://badge.fury.io/py/THD-Flow.svg)](https://badge.fury.io/py/THD-Flow)


**Current Integrations:**
* GitHub
* Pivotal Tracker
* Sonar
* Artifactory
* Cloud Foundry
* Google AppEngine
* Slack
* Grafana

## Join Us
* Backlog: [Pivotal Tracker](https://www.pivotaltracker.com/n/projects/2135573#)
* Docker: 
* Chat: [gitter.im](https://gitter.im/thd-flow)

## Development

For instructions on contributing, please see [CONTRIBUTING.md](CONTRIBUTING.md).


## Usage


### Github
Generates version numbers (using semantic versioning), attaches release notes and retrieves the latest version number.

**Actions:**

version - create new version, tag repo with version number and append build notes
getversion - returns the latest version number.

**Usage:** `flow github [Flags] [Action] [Environment]`


**Flags:**

-v VERSION, --version VERSION (optional) If manually versioning, this is passed in by the user.  Note: versionStrategy in buildConfig should be set to "manual"

-o OUTPUT, --output OUTPUT (optional) Writes the version number to a file. Use only if you need to persist the version number in a file.

--no-publish (optional) Stops publish to GitHub releases

-rnop RELEASE_NOTES_OUTPUT_PATH, --release-notes-output-path RELEASE_NOTES_OUTPUT_PATH (optional) Writes the release notes to a file. Use only if you need to persist the release notes in a file.

**Environment Variables:**

TRACKER_TOKEN (Required) to access Pivotal Tracker story information when building release notes

GITHUB_TOKEN (Required) for access to your project API _NOTE: Requires repo access only._

SLACK_WEBHOOK_URL (optional) for sending error messages from Flow to your slack channel


For the help documentation, please check `flow github -h`


### Tracker
Label stories with the version number.

**Actions:**

label-release - lookup stories in commit history and tag each story with the current version number

**Usage:** `flow tracker [Flags] [Action] [Environment]`

**Flags:**

-v VERSION, --version VERSION (optional) If manually versioning, this is passed in by the user.  Note: versionStrategy in buildConfig should be set to "manual"

**Environment Variables:**

GITHUB_TOKEN (Required) for access to your project API _NOTE: Requires repo access only._

TRACKER_TOKEN (Required) for accessing story information and labeling stories

SLACK_WEBHOOK_URL (optional) for sending error messages from Flow to your slack channel

**Settings.ini (Global Settings):**

url (required) to the tracker server. Priority is given if a value in buildConfig.json is specified.


For the help documentation, please check `flow tracker -h`


### Slack
Publishes release notes after a deployment.

**Actions:**

release - ship release notes to slack after a deployment has completed

message - Sends custom slack messages.  One use case is for sending flow deprecation messages to teams during their deployment.

**Notes:**
If no channel is defined in buildConfig.json, this will publish to the default channel for the webhook. It also provides links for manually publishing to other environments specified in the buildConfig.json.

**Usage:** `flow slack [Flags] [Action] [Environment]`

**Flags:**

-c CHANNEL, --channel CHANNEL Slack channel to post in.

-v VERSION, --version VERSION (optional) Defaults to latest version.  If upload is for a previous version, pass in the version number here.

-m MESSAGE, --message MESSAGE For use with message action. Message to be published.

-s USER, --user USER  (optional) For use with message action. User name for message.

-i ICON, --icon ICON  (optional) For use with message action. Icon to be displayed in footer.

-e EMOJI, --emoji EMOJI (optional) For use with message action. Emoji for message.

-a ATTACHMENT_COLOR, --attachment-color ATTACHMENT_COLOR (optional) For use with message action. Color for attachment bar.

-u SLACK_URL, --slack_url SLACK_URL (optional) For use with message action. Slack webhook url.

**Environment Variables:**

SLACK_WEBHOOK_URL (required) for sending release notes to slack

TRACKER_TOKEN (Required) to access Pivotal Tracker story information when building release notes

GITHUB_TOKEN (Required) for access to your project API _NOTE: Requires repo access only._

**Settings.ini (Global Settings):**
bot_name (required) default bot name.  Can be overridden by users in their buildConfig.json.

emoji (required) default emoji.  Can be overridden by users in their buildConfig.json.

release_note_attachment_color (required) default bar color for release notes.  Can be overridden by users in their buildConfig.json.

error_attachment_color (required) default bar color for errors sent to slack.  Can be overridden by users in their buildConfig.json.

generic_message_slack_url (optional) sets generic channel when using the custom message feature of slack


For the help documentation, please check `flow slack -h`


### Sonar
Triggers a sonar scan of your project.

**Notes:**
Project configuration should be defined in sonar-project.properties.  For an example, see [this](sonar-project.properties).

The sonar task requires installation of sonar-runner.  The name of the local sonar runner executable needs to be defined in settings.ini.

The sonar task requires an environment variable, called SONAR_HOME that points to your sonar runner directory.

**Actions:**

scan - submit code to sonar for code quality scan

**Usage:** `flow sonar [Flags] [Action] [Environment]`

**Flags:**

-v VERSION, --version VERSION (optional) If manually versioning, this is passed in by the user.

**Environment Variables:**

SLACK_WEBHOOK_URL (optional) for sending error messages from Flow to your slack channel

**Settings.ini (Global Settings):**

sonar_runner (required) path to sonar runner executable


For the help documentation, please check `flow sonar -h`


### Artifactory
Task used to upload/download artifacts to/from artifactory.

**Actions:**

upload - uploads artifact to artifactory. location is based on settings in buildConfig.json.

download - downloads artifact from artifactory. location is based on settings in buildConfig.json and optional version number passed in.

_NOTE:_ To include a POM in the upload, set `includePom` in your buildConfig.json, `artifact` stanza.

**Usage:** `flow artifactory [Flags] [Action] [Environment]`

**Flags:**

-x EXTRACT, --extract EXTRACT (optional) Only used for download action. Specifies whether the downloaded artifact should be extracted (only applies to .tar .tar.gz .zip file formats). Default True.

-v VERSION, --version VERSION (optional) If manually versioning, this is passed in by the user.  Note: versionStrategy in buildConfig should be set to "manual"

**Environment Variables:**

SLACK_WEBHOOK_URL (optional) for sending error messages from Flow to your slack channel

ARTIFACTORY_TOKEN (Required) api token to artifactory OR encrypted password for user if used in conjunction with ARTIFACTORY_USER

ARTIFACTORY_USER (optional) user for uploading to artifactory

ARTIFACT_BUILD_DIRECTORY (required) directory location where artifact is built


For the help documentation, please check `flow artifactory -h`


### CF (Pivotal Cloud Foundry)
Performs a zero-downtime deployment to cloud foundry expecting a manifest named after your environment (e.g. development.manifest.yml). The version for the deployed application defaults to the latest release in GitHub but can be overwritten with the `-v` or `--version` flag. This currently (12-07-16) requires an artifact in artifactory to function.

**Actions:**

deploy - push application to Pivotal Cloud Foundry

**Usage:** `flow cf [Flags] [Action] [Environment]`

**Flags:**

-v VERSION, --version VERSION (optional) Defaults to latest version.  If deployment is for a previous version, pass in the version number here.

-f FORCE, --force FORCE (optional) Force the deploy even if the same version number is already running. Note: Zero-downtime deployment will not occur if forcing a deploy on the same version number.

-s SCRIPT, --script SCRIPT (optional) If you choose to use a custom deploy script instead of the default zero-downtime, pass in the path to deploy script here.

-metrics MANIFEST, --manifest MANIFEST (optional) Custom manifest name if you choose not to  follow standard pattern of{environment}.manifest.yml

**Environment Variables:**

GITHUB_TOKEN (Required) for access to your project API _NOTE: Requires repo access only._

ARTIFACTORY_TOKEN (Required) api token to artifactory OR encrypted password for user if used in conjunction with ARTIFACTORY_USER (api token is preferred over password)

DEPLOYMENT_USER (Required) for logging into PCF

DEPLOYMENT_PWD (Required) for logging into PCF

SLACK_WEBHOOK_URL (optional) for sending error messages from Flow to your slack channel

ARTIFACTORY_USER (optional) user for uploading to artifactory

CF_BUILDPACK (optional)  Custom build packs should typically be indicated in your manifest; however, sometimes URLs for build packs may contains sensitive information, such as a github oauth token.  You can use this environment variable to avoid exposing this in your manifest.

**Settings.ini (Global Settings):**

cli_download_path (required) path to download cf cli


For the help documentation, please check `flow cf -h`


### Google Cloud App Engine
Performs a deployment to Google App Engine expecting an application yaml named after your environment (e.g. app-development.yaml/yml) or a custom app-yml name to be passed in. The version for the deployed application defaults to the latest release in GitHub but can be overwritten with the `-v` or `--version` flag. This currently (12-07-16) requires an artifact in artifactory to function.

**Actions:**

deploy - ship version of code to Google Cloud App Engine

**Usage:** `flow gcappengine [Flags] [Action] [Environment]`

**Flags:**

-v VERSION, --version VERSION (optional) Defaults to latest version.  If deployment is for a previous version, pass in the version number here.

-d DEPLOY_DIRECTORY, --deploy-directory DEPLOY_DIRECTORY (optional) Directory to download artifact to. By default it's downloaded to a new directory called 'fordeployment'

-y APP_YAML, --app-yaml APP_YAML (optional) Custom app manifest.  Default is app-{environment}.yaml

-p PROMOTE, --promote PROMOTE (optional) Automatically promote new version and stop routing traffic to the older version.  Default is true.

**Environment Variables:**

GCAPPENGINE_USER_JSON (Required)  the contents of a service account json created from Google's Instructions [here](https://cloud.google.com/iam/docs/service-accounts)  NOTE: this is json content, not a uri to a file.

CLOUDSDK_CORE_PROJECT (Required)  project name as displayed in google cloud

**Settings.ini (Global Settings):**

cloud_sdk_path (required) path to download gcloud cli


For the help documentation, please check `flow gcappengine -h`


## License
Licensed under the [Apache License](LICENSE)


## Key Contributors

Andrew Turner
[@aturnerbulldawg](https://github.com/aturnerbulldawg)

Cade Thacker

Jeff Billimek

Corbett Waddingham

Jimmy Joy

Jermaine Davis

Nick Bunn

Preston Turner

Chris Leatherwood

Notable Mentions: 
Jeff Anderson,
Patrick Baggett,
Micahel Celeste,
Mark Dedula,
Adam Edelman,
Chris Gruel,
Joey Guerra,
Nolan Hedstrom,
Muhammad Ikram,
John Jimenez,
Shane Keels,
David Kowis,
John Mckenna,
Winston Milling,
Dhakshna Munusamy,
Sanjay Nair,
Nikeshbhai Patel,
Priyesh Patel,
Cody Stamps,
Ian Stansbury,
Alvaro Ramirez-del Villar   

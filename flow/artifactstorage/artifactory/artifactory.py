#!/usr/bin/python
# artifactory.py

import json
import os
import os.path
import tarfile
import zipfile

import requests
from flow.artifactstorage.artifact_storage_abc import Artifact_Storage
from flow.buildconfig import BuildConfig

import flow.utils.commons as commons


class ArtifactDownloadException(Exception): pass


class ArtifactException(Exception): pass


class ArtiFactory(Artifact_Storage):
    clazz = 'ArtiFactory'

    repo_key = None
    artifactory_domain = None
    artifactory_group = None
    artifactory_files = []
    artifactory_extensions = []
    pom_filename = None
    pom_file = None
    config = BuildConfig
    http_timeout = 30

    def __init__(self, config_override=None):
        method = '__init__'
        commons.printMSG(ArtiFactory.clazz, method, 'begin')

        if config_override is not None:
            self.config = config_override

        try:
            # below line is to maintain backwards compatibility since stanza was renamed
            if 'artifactoryConfig' in self.config.json_config:
                artifactory_json_config = self.config.json_config['artifactoryConfig']
            else:
                artifactory_json_config = self.config.json_config['artifact']

            ArtiFactory.artifactory_domain = artifactory_json_config['artifactoryDomain']
            ArtiFactory.artifactory_group = artifactory_json_config['artifactoryGroup']

            if self.config.build_env_info['artifactCategory'] == 'release':
                ArtiFactory.repo_key = artifactory_json_config['artifactoryRepoKey']
            else:
                ArtiFactory.repo_key = artifactory_json_config['artifactoryRepoKeySnapshot']

            if self.config.artifact_extensions:
                for extensions in self.config.artifact_extensions:
                    self.artifactory_extensions.append(extensions)
            else:
                self.artifactory_extensions.append(self.config.artifact_extension)

        except KeyError as e:
            commons.printMSG(ArtiFactory.clazz,
                             method,
                             "The build config associated with artifactory is missing key {}".format(str(e)), 'ERROR')
            exit(1)

        commons.printMSG(ArtiFactory.clazz, method, 'end')

    def publish(self, file, file_name):
        method = 'publish'
        commons.printMSG(ArtiFactory.clazz, method, 'begin')

        headers = {'Content-type': commons.content_oct_stream, 'Accept': commons.content_json}

        try:
            with open(file, 'rb') as zip_file:
                file_url = "{artifact_home}/{file}".format(artifact_home=self.get_artifact_home_url(), file=file_name)
                commons.printMSG(ArtiFactory.clazz, method, "Publishing to {}".format(file_url))

                # token and user env variables
                if os.getenv('ARTIFACTORY_TOKEN') and os.getenv('ARTIFACTORY_USER'):
                    commons.printMSG(ArtiFactory.clazz, method, 'Found artifactory token and user.')
                    resp = requests.put(file_url,
                                        auth=(os.getenv('ARTIFACTORY_USER'), os.getenv('ARTIFACTORY_TOKEN')),
                                        headers=headers,
                                        data=zip_file,
                                        timeout=self.http_timeout)

                # token environment var and user defined in settings.ini
                elif os.getenv('ARTIFACTORY_TOKEN') and BuildConfig.settings.has_section('artifactory') and \
                        BuildConfig.settings.has_option('artifactory', 'user'):
                    commons.printMSG(ArtiFactory.clazz, method, 'Found artifactory token.  Using default user '
                                                                'specified in settings.ini.')
                    resp = requests.put(file_url,
                                        auth=(BuildConfig.settings.get('artifactory', 'user'),
                                              os.getenv('ARTIFACTORY_TOKEN')),
                                        headers=headers,
                                        data=zip_file,
                                        timeout=self.http_timeout)

                # token only and assumed to be api key
                elif os.getenv('ARTIFACTORY_TOKEN'):
                    commons.printMSG(ArtiFactory.clazz, method, 'Found artifactory token.  Assuming it\'s API key.')

                    headers = {'X-Api-Key': os.getenv('ARTIFACTORY_TOKEN'),
                               'Content-type': commons.content_oct_stream,
                               'Accept': commons.content_json}

                    resp = requests.put(file_url,
                                        headers=headers,
                                        data=zip_file,
                                        timeout=self.http_timeout)

                else:
                    commons.printMSG(ArtiFactory.clazz, method, 'No artifactory user specified.  This operation may '
                                                                'fail if anonymous access is not allowed. To specify '
                                                                'user, set environment variable \'ARTIFACTORY_TOKEN\' '
                                                                'and \'ARTIFACTORY_USER\'.',
                                     'WARN')
                    resp = requests.put(file_url, headers=headers, data=zip_file, timeout=self.http_timeout)
        except requests.ConnectionError:
            commons.printMSG(ArtiFactory.clazz, method, "Request to Artifactory timed out.", "ERROR")
            exit(1)
        except Exception as ex:
            commons.printMSG(ArtiFactory.clazz, method, "Failed publishing to artifactory: {}. Sometimes this can be "
                                                        "due to an invalid user name/password.".format(ex), 'ERROR')

            exit(1)

        commons.printMSG(ArtiFactory.clazz, method, "resp status code: {}".format(resp.status_code))
        commons.printMSG(ArtiFactory.clazz, method, "response: {}".format(resp.text))

        if resp.status_code != 201:
            commons.printMSG(ArtiFactory.clazz,
                             method,
                             "Publish to artifactory failed to {home}{fwdslash}{file} Response: {"
                             "response}".format(home=self.get_artifact_home_url(), fwdslash=commons.forward_slash,
                                                file=file_name, response=resp.text), 'ERROR')
            exit(1)
        else:
            commons.printMSG(ArtiFactory.clazz, method, resp.text)

        commons.printMSG(ArtiFactory.clazz, method, 'end')

    def publish_build_artifact(self):
        method = 'publish_build_artifact'
        commons.printMSG(ArtiFactory.clazz, method, 'begin')

        self._get_artifactory_files_name_from_build_dir()
        for file in ArtiFactory.artifactory_files:
            self.publish(file["artifactory_file"], file["artifactory_filename"])

        if 'artifactoryConfig' in self.config.json_config:
            artifactory_json_config = self.config.json_config['artifactoryConfig']
        else:
            artifactory_json_config = self.config.json_config['artifact']

        if 'includePom' in artifactory_json_config:
            commons.printMSG(ArtiFactory.clazz, method, 'POM needed, publishing to artifactory')
            self.publish(ArtiFactory.pom_file, ArtiFactory.pom_filename)

        commons.printMSG(ArtiFactory.clazz, method, 'end')

    def _get_artifactory_files_name_from_build_dir(self):
        method = '_get_artifactory_files_name_from_build_dir'
        commons.printMSG(ArtiFactory.clazz, method, 'begin')

        if 'ARTIFACT_BUILD_DIRECTORY' in os.environ:
            artifactory_build_dir = os.getenv('ARTIFACT_BUILD_DIRECTORY')
        else:
            commons.printMSG(ArtiFactory.clazz,
                             method,
                             'Missing artifact build path. Did you forget to define the environment variable '
                             '\'ARTIFACT_BUILD_DIRECTORY\'? ', 'ERROR')
            exit(1)

        for extension in self.artifactory_extensions:
            try:
                out = commons.get_files_of_type_from_directory(extension.lower(), artifactory_build_dir)

                commons.printMSG(ArtiFactory.clazz, method, out)

                if len(out) != 1:
                    commons.printMSG(ArtiFactory.clazz, method, "Found {number} artifacts of type {type} in {"
                                                                "builddir}".format(number=len(out),
                                                                                   type=extension.lower(),
                                                                                   builddir=
                                                                                   os.getenv('ARTIFACT_BUILD_DIRECTORY')),
                                     'ERROR')
                    raise IOError('Found more than 1 artifact')

                artifactory_file = os.path.join(artifactory_build_dir, out[0])
                artifactory_filename = out[0]
                ArtiFactory.artifactory_files.append(
                    {"artifactory_file": artifactory_file, "artifactory_filename": artifactory_filename})
                commons.printMSG(ArtiFactory.clazz, method, "artifactoryfile: {}".format(artifactory_file))
                commons.printMSG(ArtiFactory.clazz, method,
                                 "artifactoryfilename: {}".format(artifactory_filename))

            except Exception as ex:
                print(ex)
                commons.printMSG(ArtiFactory.clazz,
                                 method, "Failed to find artifact of type {type} in {builddir}".format(
                        type=extension.lower(), builddir=os.getenv('ARTIFACT_BUILD_DIRECTORY')), 'ERROR')
                exit(1)

        ArtiFactory.pom_file = os.path.join('', "pom.xml")
        ArtiFactory.pom_filename = "pom.xml"

        commons.printMSG(ArtiFactory.clazz, method, 'end')

    def get_artifact_home_url(self):
        method = 'get_artifact_home_url'
        commons.printMSG(ArtiFactory.clazz, method, 'begin')

        commons.verify_version(self.config)

        url = ArtiFactory.artifactory_domain + commons.forward_slash + \
              ArtiFactory.repo_key + commons.forward_slash + \
              ArtiFactory.artifactory_group + commons.forward_slash + \
              self.config.project_name + commons.forward_slash + \
              self.config.version_number

        commons.printMSG(ArtiFactory.clazz, method, ("Artifactory url:", url))

        commons.printMSG(ArtiFactory.clazz, method, "end")
        return url

    def get_artifact_url(self):
        method = "get_artifact_url"
        if len(self.artifactory_extensions) > 1:
            commons.printMSG(ArtiFactory.clazz, method, "You have more then one extension declared. Use 'get_urls_of "
                                                        "artifacts' to get more then one url")
        return self._get_artifact_url(self.artifactory_extensions[0])

    def get_urls_of_artifacts(self):
        urls = []
        for extension in self.artifactory_extensions:
            urls.append(self._get_artifact_url(extension))
        return urls

    def _get_artifact_url(self, extension):
        method = "get_artifact_url"
        commons.printMSG(ArtiFactory.clazz, method, "begin")

        arti_api_url = self.artifactory_domain + \
                       "/api/storage/" + \
                       self.repo_key + \
                       "/" + self.artifactory_group + \
                       "/" + self.config.project_name + \
                       "/" + self.config.version_number

        try:
            resp = requests.get(arti_api_url, timeout=self.http_timeout)
        except requests.ConnectionError as e:
            commons.printMSG(ArtiFactory.clazz, method, "Request to Artifactory timed out.", "ERROR")
            raise ArtifactException(e)
        except Exception as e:
            commons.printMSG(ArtiFactory.clazz,
                             method,
                             ("Unable to locate artifactory path {arti_api_url}".format(arti_api_url=arti_api_url)),
                             "ERROR")
            raise ArtifactException(e)

        if resp.status_code != 200:
            commons.printMSG(ArtiFactory.clazz,
                             method,
                             ("Unable to locate artifactory path {arti_api_url}\r\n Response: {resp}".format(arti_api_url=arti_api_url, resp=resp.text)),
                             "ERROR")
            raise ArtifactException("Unable to locate artifactory path {arti_api_url}\r\n Response: {resp}".format(arti_api_url=arti_api_url, resp=resp.text))

        json_data = json.loads(resp.text)

        matching_file_count = 0

        for child in json_data['children']:
            child_uri = child['uri']
            if child_uri.endswith("." + extension):
                matching_file_count += 1
                artifact_to_deploy = child['uri']
                commons.printMSG(ArtiFactory.clazz, method, ("Found match ", artifact_to_deploy))

        if matching_file_count == 1:
            return "%s/%s/%s/%s/%s%s" % (self.artifactory_domain,
                                         self.repo_key,
                                         self.artifactory_group,
                                         self.config.project_name,
                                         self.config.version_number,
                                         artifact_to_deploy)
        elif matching_file_count > 1:
            commons.printMSG(ArtiFactory.clazz, method, "Found more than 1 artifact in {}".format(arti_api_url), 'ERROR')
            raise ArtifactException("Found more than 1 artifact in {}".format(arti_api_url))

        else:
            commons.printMSG(ArtiFactory.clazz,
                             method,
                             "Could not locate artifact {}".format(extension),
                             "ERROR")
            raise ArtifactException("Could not locate artifact {}".format(extension))

    def download_artifact(self, artifact_url, download_path):
        """
        Download the artifact from artifactory. Really just a save a url to a file method.
        :param artifact_url: obviously, the artifact url
        :param download_path: Where you want the file to go
        :return: nothing, exceptions raised if it fails
        """
        method = "download_artifact"
        try:
            with open(download_path, 'wb') as handle:
                response = requests.get(artifact_url, stream=True)
                if not response.ok:
                    response.raise_for_status()

                for block in response.iter_content(1024):
                    handle.write(block)

        except Exception as e:
            commons.printMSG(ArtiFactory.clazz, method, 'Failed to download {}'.format(artifact_url), 'ERROR')
            commons.printMSG("URLError is {msg}".format(msg=e.message))
            raise ArtifactDownloadException(e.message)

    def download_and_extract_artifacts_locally(self, download_dir, extract=True):
        for extension in self.artifactory_extensions:
            self._download_and_extract_artifact_locally(download_dir, extension, extract=extract)

    def _download_and_extract_artifact_locally(self, download_dir, extension, extract=True):
        method = "_download_and_extract_artifact_locally"

        commons.printMSG(ArtiFactory.clazz, method, 'begin')

        commons.verify_version(self.config)

        artifact_to_download = self.config.project_name + '-' + self.config.version_number + '.' + extension

        try:
            artifact = self.get_artifact_url()
        except ArtifactException:
            exit(1)

        download_path = download_dir + artifact_to_download

        commons.printMSG(ArtiFactory.clazz, method, "artifact_to_download = {a} and download_path is {d}".format(
            a=artifact_to_download, d=download_path))
        commons.printMSG(ArtiFactory.clazz, method, 'Downloading {artifact} to {download_path}'.format(artifact=
                                                                                                       artifact,
                                                                                                       download_path
                                                                                                       =download_path))
        try:
            self.download_artifact(artifact, download_path)
        except ArtifactDownloadException as e:
            commons.printMSG(ArtiFactory.clazz, method, 'Failed to download {}'.format(artifact), 'ERROR')
            commons.printMSG("URLError is {msg}".format(msg=e))
            os.system('stty sane')
            exit(1)

        if extract:
            # Unzip/untar file downloaded from Artifactory if required
            if extension == "tar.gz" or extension == "tar" or extension == "tgz":
                tar = tarfile.open(download_path)
                tar.extractall(download_dir)
                tar.close()
                commons.printMSG(ArtiFactory.clazz, method, 'Deploying a tar from {}'.format(download_path))
            if extension == "zip":
                with zipfile.ZipFile(download_path, "r") as z:
                    z.extractall(download_dir)

                commons.printMSG(ArtiFactory.clazz, method, "Deploying a zip from {}".format(download_path))
        print(download_path)

        commons.printMSG(ArtiFactory.clazz, method, 'end')

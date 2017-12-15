import os
import platform
import subprocess
import tarfile
import urllib
import ssl

from subprocess import TimeoutExpired

from flow.buildconfig import BuildConfig
from flow.cloud.cloud_abc import Cloud

import flow.utils.commons as commons


class GCAppEngine(Cloud):

    clazz = 'GCAppEngine'
    config = BuildConfig

    def __init__(self, config_override=None):
        method = '__init__'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        if config_override is not None:
            self.config = config_override

        if os.environ.get('WORKSPACE'):  # for Jenkins
            GCAppEngine.path_to_google_sdk = os.environ.get('WORKSPACE') + '/'
        else:
            GCAppEngine.path_to_google_sdk = ""

        commons.printMSG(GCAppEngine.clazz, method, 'end')

    def _download_google_sdk(self):
        method = '_download_google_sdk'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        cmd = "where" if platform.system() == "Windows" else "which"
        rtn = subprocess.call([cmd, 'gcloud'])

        gcloud_location = self.config.settings.get('googlecloud', 'cloud_sdk_path') + self.config.settings.get('googlecloud', 'gcloud_version')

        if rtn == 0:
            commons.printMSG(GCAppEngine.clazz, method, 'gcloud already installed')
        else:
            commons.printMSG(GCAppEngine.clazz, method, "gcloud CLI was not installed on this image. "
                                                        "Downloading Google Cloud SDK from {}".format(
                gcloud_location))

            with urllib.request.urlopen(gcloud_location, context=ctx) as u, open(self.config.settings.get('googlecloud', 'gcloud_version'), 'wb') as f:
                f.write(u.read())

            tar = tarfile.open('./' + self.config.settings.get('googlecloud', 'gcloud_version'))
            GCAppEngine.path_to_google_sdk = 'google-cloud-sdk/bin/'
            tar.extractall()
            tar.close()

        commons.printMSG(GCAppEngine.clazz, method, 'end')

    def _verify_required_attributes(self):
        method = '_verfify_required_attributes'

        if not os.getenv('GCAPPENGINE_USER_JSON'):
            commons.printMSG(GCAppEngine.clazz, method, 'Credentials not loaded.  Please define ''environment variable '
                                                        '\'GCAPPENGINE_USER_JSON\'', 'ERROR')
            exit(1)

    def _write_service_account_json_to_file(self):
        method = '_write_service_account_json_to_file'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        try:
            file = open('gcloud.json', 'w+')

            file.write(os.getenv('GCAPPENGINE_USER_JSON'))

        except Exception as e:
            commons.printMSG(GCAppEngine.clazz, method, "Failed writing gcloud auth json to gcloud.json from "
                                                        "'GCAPPENGINE_USER_JSON'.  Error: {}'".format(e), 'ERROR')
            exit(1)

        commons.printMSG(GCAppEngine.clazz, method, 'end')

    def _gcloud_login(self):
        method = '_gcloud_login'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        cmd = "{path}gcloud auth activate-service-account --key-file {keyfile} --quiet".format(
            path=GCAppEngine.path_to_google_sdk,
            keyfile='gcloud.json')

        gcloud_login = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        login_failed = False

        while gcloud_login.poll() is None:
            line = gcloud_login.stdout.readline().decode('utf-8').strip(' \r\n')

            commons.printMSG(GCAppEngine.clazz, method, line)

            # if 'credentials were rejected' in line.lower():
            #     commons.printMSG(GCAppEngine.clazz, method, "Make sure that your credentials are correct for {"
            #                                                  "}".format(CloudFoundry.cf_user), 'ERROR')
            #     login_failed = True

        try:
            gcloud_login_output, errs = gcloud_login.communicate(timeout=120)

            for line in gcloud_login_output.splitlines():
                commons.printMSG(GCAppEngine.clazz, method, line.decode('utf-8'))

            if gcloud_login.returncode != 0:
                commons.printMSG(GCAppEngine.clazz, method, "Failed calling cloud auth. Return code of {}. Make "
                                                             "sure the user has proper permission to deploy.".format(
                                                                gcloud_login.returncode), 'ERROR')
                login_failed = True

        except TimeoutExpired:
            commons.printMSG(GCAppEngine.clazz, method, "Timed out calling GCLOUD AUTH.", 'ERROR')
            login_failed = True

        if login_failed:
            gcloud_login.kill()
            os.system('stty sane')
            exit(1)

        commons.printMSG(GCAppEngine.clazz, method, 'end')

    def _determine_app_yml(self):
        method = '_determine_app_yml'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        if os.path.isfile("app-{}.yml".format(self.config.build_env)):
            app_yaml = "app-{}.yml".format(self.config.build_env)
        elif os.path.isfile("{dir}/app-{env}.yml".format(dir=self.config.push_location, env=self.config.build_env)):
            app_yaml = "{dir}/app-{env}.yml".format(dir=self.config.push_location, env=self.config.build_env)
        elif os.path.isfile("app-{}.yaml".format(self.config.build_env)):
            app_yaml = "app-{}.yaml".format(self.config.build_env)
        elif os.path.isfile("{dir}/app-{env}.yaml".format(dir=self.config.push_location, env=self.config.build_env)):
            app_yaml = "{dir}/app-{env}.yaml".format(dir=self.config.push_location, env=self.config.build_env)
        else:
            commons.printMSG(GCAppEngine.clazz, method, "Failed to find app_yaml file app-{}.yml/yaml".format(
                self.config.build_env), 'ERROR')
            exit(1)

        commons.printMSG(GCAppEngine.clazz, method, "Using app_yaml {}".format(app_yaml))

        commons.printMSG(GCAppEngine.clazz, method, 'end')

        return app_yaml

    def _gcloud_deploy(self, app_yaml, promote=True):
        method = '_gcloud_deploy'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        promote_flag = "--no-promote" if promote is False else ""
        cmd = "{path}gcloud app deploy {dir}/{env} --quiet --version {ver} {promote}".format(
            path=GCAppEngine.path_to_google_sdk,
            dir=self.config.push_location,
            env=app_yaml,
            ver=((self.config.version_number).replace('+','--')).replace('.','-'),
            promote=promote_flag)


        commons.printMSG(GCAppEngine.clazz, method, cmd)

        gcloud_app_deploy = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        deploy_failed = False

        while gcloud_app_deploy.poll() is None:
            line = gcloud_app_deploy.stdout.readline().decode('utf-8').strip(' \r\n')
            commons.printMSG(GCAppEngine.clazz, method, line)

        try:
            gcloud_app_deploy_output, errs = gcloud_app_deploy.communicate(timeout=300)

            if gcloud_app_deploy.returncode != 0:
                commons.printMSG(GCAppEngine.clazz, method, "Failed calling {command}.  Return code of {"
                                                             "rtn}.".format(command=cmd,
                                                                            rtn=gcloud_app_deploy.returncode),
                                 'ERROR')
                deploy_failed = True

        except TimeoutExpired:
            commons.printMSG(GCAppEngine.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
            deploy_failed = True

        if deploy_failed:
            os.system('stty sane')
            # self._cf_logout()
            exit(1)

        commons.printMSG(GCAppEngine.clazz, method, 'end')

    def deploy(self, app_yaml=None, promote=True):
        method = 'deploy'
        commons.printMSG(GCAppEngine.clazz, method, 'begin')

        self._verify_required_attributes()

        self._write_service_account_json_to_file()

        self._download_google_sdk()

        self._gcloud_login()

        if self.config.artifact_extension is not None:
            self.find_deployable(self.config.artifact_extension, self.config.push_location)

        if app_yaml is None:
            app_yaml = self._determine_app_yml()

        self._gcloud_deploy(app_yaml, promote)

        commons.printMSG(GCAppEngine.clazz, method, 'DEPLOYMENT SUCCESSFUL')

        commons.printMSG(GCAppEngine.clazz, method, 'end')
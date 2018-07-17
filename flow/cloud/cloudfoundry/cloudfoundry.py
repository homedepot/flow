import os
import subprocess
import tarfile
import urllib.request
from subprocess import TimeoutExpired
import platform

from flow.buildconfig import BuildConfig
from flow.cloud.cloud_abc import Cloud

import flow.utils.commons as commons


class CloudFoundry(Cloud):

    clazz = 'CloudFoundry'
    cf_org = None
    cf_space = None
    cf_api_endpoint = None
    cf_domain = None
    cf_user = None
    cf_pwd = None
    path_to_cf = None
    stopped_apps = None
    started_apps = None
    config = BuildConfig
    http_timeout = 30

    def __init__(self, config_override=None):
        method = '__init__'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        if config_override is not None:
            self.config = config_override

        if os.environ.get('WORKSPACE'):  # for Jenkins
            CloudFoundry.path_to_cf = os.environ.get('WORKSPACE') + '/'
        else:
            CloudFoundry.path_to_cf = ""

        commons.print_msg(CloudFoundry.clazz, method, 'end')


    def download_cf_cli(self):
        method = '_download_cf_cli'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd = "where" if platform.system() == "Windows" else "which"
        rtn = subprocess.call([cmd, 'cf'])

        if rtn == 0:
            commons.print_msg(CloudFoundry.clazz, method, 'cf cli already installed')
        else:
            commons.print_msg(CloudFoundry.clazz, method, "cf CLI was not installed on this image. "
                                                        "Downloading CF CLI from {}".format(
                self.config.settings.get('cloudfoundry', 'cli_download_path')))

            urllib.request.urlretrieve(self.config.settings.get('cloudfoundry', 'cli_download_path'), # nosec
                                           './cf-linux-amd64.tgz')
            tar = tarfile.open('./cf-linux-amd64.tgz')
            CloudFoundry.path_to_cf = "./"
            tar.extractall()
            tar.close()

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _verify_required_attributes(self):
        method = '_verify_required_attributes'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        commons.print_msg(CloudFoundry.clazz, method, "workspace {}".format(CloudFoundry.path_to_cf))

        if os.environ.get('DEPLOYMENT_USER') is None:
            commons.print_msg(CloudFoundry.clazz, method, "No User Id. Did you forget to define environment variable "
                                                         "'DEPLOYMENT_USER?", 'ERROR')
            exit(1)
        else:
            CloudFoundry.cf_user = os.environ.get('DEPLOYMENT_USER')

        if os.environ.get('DEPLOYMENT_PWD') is None:
            commons.print_msg(CloudFoundry.clazz, method, "No User Password. Did you forget to define environment "
                                                         "variable 'DEPLOYMENT_PWD'?", 'ERROR')
            exit(1)
        else:
            CloudFoundry.cf_pwd = os.environ.get('DEPLOYMENT_PWD')

        try:
            # noinspection PyStatementEffect
            self.config.json_config['projectInfo']['name']
            CloudFoundry.cf_org = self.config.build_env_info['cf']['org']
            CloudFoundry.cf_space = self.config.build_env_info['cf']['space']
            CloudFoundry.cf_api_endpoint = self.config.build_env_info['cf']['apiEndpoint']
            if 'domain' in self.config.build_env_info['cf']:  # this is not required bc could be passed in via manifest
                CloudFoundry.cf_domain = self.config.build_env_info['cf']['domain']

            commons.print_msg(CloudFoundry.clazz, method, "CloudFoundry.cf_org {}".format(CloudFoundry.cf_org))
            commons.print_msg(CloudFoundry.clazz, method, "CloudFoundry.cf_space {}".format(CloudFoundry.cf_space))
            commons.print_msg(CloudFoundry.clazz, method, "CloudFoundry.cf_api_endpoint {}"
                              .format(CloudFoundry.cf_api_endpoint))
            commons.print_msg(CloudFoundry.clazz, method, "CloudFoundry.cf_domain {}".format(CloudFoundry.cf_domain))
        except KeyError as e:
            commons.print_msg(CloudFoundry.clazz,
                              method,
                             "The build config associated with cloudfoundry is missing key {}".format(str(e)), 'ERROR')
            exit(1)

    def _check_cf_version(self):
        method = '_check_cf_version'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd = "{}cf --version".format(CloudFoundry.path_to_cf)
        cf_version = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        try:
            cf_version_output, errs = cf_version.communicate(timeout=30)

            for line in cf_version_output.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, line.decode('utf-8'))

            if cf_version.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}".format(
                    command=cmd, rtn=cf_version.returncode), 'ERROR')

                os.system('stty sane')
                self._cf_logout()
                exit(1)

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
            cf_version.kill()
            os.system('stty sane')
            self._cf_logout()
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _get_stopped_apps(self):
        method = '_get_stopped_apps'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd = "{path}cf apps | grep {proj}*-v\d*\.\d*\.\d* | grep stopped | awk '{{print $1}}'".format(
            path=CloudFoundry.path_to_cf,
            proj=self.config.project_name)

        stopped_apps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) # nosec

        get_stopped_apps_failed = False

        try:
            CloudFoundry.stopped_apps, errs = stopped_apps.communicate(timeout=60)

            for line in CloudFoundry.stopped_apps.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, "App Already Stopped: {}".format(line.decode('utf-8')))

            if stopped_apps.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}".format(
                    command=cmd, rtn=stopped_apps.returncode), 'ERROR')
                get_stopped_apps_failed = True

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
            get_stopped_apps_failed = True

        if get_stopped_apps_failed:
            stopped_apps.kill()
            os.system('stty sane')
            self._cf_logout()
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _get_started_apps(self, force_deploy=False):
        method = '_get_started_apps'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd = "{path}cf apps | grep {proj}*-v\d*\.\d*\.\d* | grep started | awk '{{print $1}}'".format(
            path=CloudFoundry.path_to_cf,
            proj=self.config.project_name)

        started_apps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) # nosec

        get_started_apps_failed = False

        try:
            CloudFoundry.started_apps, errs = started_apps.communicate(timeout=60)

            for line in CloudFoundry.started_apps.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, "Started App: {}".format(line.decode('utf-8')))
                version_to_look_for = "{proj}-{ver}".format(proj=self.config.project_name,
                                                            ver=self.config.version_number)

                if line.decode('utf-8') == version_to_look_for and not force_deploy:
                    commons.print_msg(CloudFoundry.clazz, method, "App version {} already exists and is running. "
                                                                 "Cannot perform zero-downtime deployment.  To "
                                                                 "override, set force flag = 'true'".format(
                        version_to_look_for), 'ERROR')
                    get_started_apps_failed = True

                elif line.decode('utf-8') == version_to_look_for and force_deploy:
                    commons.print_msg(CloudFoundry.clazz, method, "Already found {} but force_deploy turned on. "
                                                                 "Continuing with deployment.  Downtime will occur "
                                                                 "during deployment.".format(version_to_look_for))
            if started_apps.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}".format(
                    command=cmd, rtn=started_apps.returncode), 'ERROR')

                get_started_apps_failed = True

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
            get_started_apps_failed = True

        if get_started_apps_failed:
            started_apps.kill()
            # started_apps.communicate()
            os.system('stty sane')
            self._cf_logout()
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _determine_manifests(self):
        method = '_determine_manifests'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        if os.path.isfile("{}.manifest.yml".format(self.config.build_env)):
            manifest = self.config.build_env + '.manifest.yml'
        elif os.path.isfile("{dir}/{env}.manifest.yml".format(dir=self.config.push_location,
                                                              env=self.config.build_env)):
            manifest = "{dir}/{env}.manifest.yml".format(dir=self.config.push_location,
                                                         env=self.config.build_env)
        else:
            commons.print_msg(CloudFoundry.clazz, method, "Failed to find manifest file {}.manifest.yml".format(
                self.config.build_env), 'ERROR')
            exit(1)

        # noinspection PyUnboundLocalVariable
        commons.print_msg(CloudFoundry.clazz, method, "Using manifest {}".format(manifest))

        commons.print_msg(CloudFoundry.clazz, method, 'end')

        return manifest

    def _cf_push(self, manifest):
        method = '_cf_push'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        commons.print_msg(CloudFoundry.clazz, method, "Using manifest {}".format(manifest))

        if self.config.artifact_extension is None or self.config.artifact_extension in ('zip', 'tar', 'tar.gz'):
            # deployed from github directly or it's a zip, tar, tar.gz file
            file_to_push = self.config.push_location
        else:
            file_to_push = "{dir}/{file}".format(dir=self.config.push_location, file=self.find_deployable(
                self.config.artifact_extension, self.config.push_location))

        buildpack = "-b {}".format(os.getenv('CF_BUILDPACK')) if os.getenv('CF_BUILDPACK') else ""

        cmd = CloudFoundry.path_to_cf + "cf push {project_name}-{version} -p {pushlocation} -f {manifest} {buildpack} ".format(project_name=self.config.project_name,
                                            version=self.config.version_number,
                                            pushlocation=file_to_push,
                                            manifest=manifest,
                                            buildpack=buildpack)

        commons.print_msg(CloudFoundry.clazz, method, cmd.split())
        cf_push = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        push_failed = False

        while cf_push.poll() is None:
            line = cf_push.stdout.readline().decode('utf-8').strip(' \r\n')
            commons.print_msg(CloudFoundry.clazz, method, line)

        try:
            cf_push.communicate(timeout=300)

            if cf_push.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}.  Return code of {rtn}."
                                  .format(command=cmd,
                                         rtn=cf_push.returncode),
                                  'ERROR')
                push_failed = True

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
            push_failed = True

        if push_failed:
            os.system('stty sane')
            self._cf_logout()
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    # noinspection PyUnboundLocalVariable
    def _stop_old_app_servers(self):
        method = '_stop_old_app_servers'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        stop_old_apps_failed = False

        for line in CloudFoundry.started_apps.splitlines():
            version_to_look_for = self.config.project_name+'-'+self.config.version_number

            if line.decode("utf-8") != version_to_look_for:
                commons.print_msg(CloudFoundry.clazz, method, "Scaling down {}".format(line.decode("utf-8")))

                cmd = "{path}cf scale {app} -i 1".format(path=CloudFoundry.path_to_cf,
                                                         app=line.decode("utf-8"))

                cf_scale = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                try:
                    cf_scale_output, errs = cf_scale.communicate(timeout=60)

                    for scale_line in cf_scale_output.splitlines():
                        commons.print_msg(CloudFoundry.clazz, method, scale_line.decode('utf-8'))

                    if cf_scale.returncode != 0:
                        commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}"
                                                                     "".format(command=cmd, rtn=cf_scale.returncode),
                                         'WARN')
                        stop_old_apps_failed = True

                except TimeoutExpired:
                    commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'WARN')
                    stop_old_apps_failed = True

                stop_cmd = "{path}cf stop {project}".format(path=CloudFoundry.path_to_cf,
                                                            project=line.decode("utf-8"))

                commons.print_msg(CloudFoundry.clazz, method, stop_cmd)
                cf_stop = subprocess.Popen(stop_cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                try:
                    cf_stop_output, errs = cf_stop.communicate(timeout=60)

                    for stop_line in cf_stop_output.splitlines():
                        commons.print_msg(CloudFoundry.clazz, method, stop_line.decode("utf-8"))

                    if cf_scale.returncode != 0:
                        commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}"
                                                                     "".format(command=cmd, rtn=cf_stop.returncode),
                                         'WARN')
                        stop_old_apps_failed = True

                except TimeoutExpired:
                    commons.print_msg(CloudFoundry.clazz, method, "Timed out calling".format(cmd), 'WARN')
                    stop_old_apps_failed = True
            else:
                commons.print_msg(CloudFoundry.clazz, method, "Skipping scale down for {}".format(line.decode("utf-8")))

        if stop_old_apps_failed:
            cf_stop.kill()
            # cf_stop.communicate()
            os.system('stty sane')
            self._cf_logout()

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _unmap_delete_previous_versions(self):
        method = '_unmap_delete_previous_versions'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        unmap_delete_previous_versions_failed = False

        for line in CloudFoundry.stopped_apps.splitlines():
            if "{proj}-{ver}".format(proj=self.config.project_name,
                                     ver=self.config.version_number).lower() == line.decode("utf-8").lower():
                commons.print_msg(CloudFoundry.clazz, method, "{} exists. Not removing routes for it.".format(
                    line.decode("utf-8").lower()))
            else:
                cmd1 = "{}cf routes".format(CloudFoundry.path_to_cf)
                cmd2 = "grep {}".format(line.decode("utf-8"))
                cmd3 = ["awk", "{{print $2}}"]

                cmd_string = cmd1+cmd2+str(cmd3)
                commons.print_msg(CloudFoundry.clazz, method, cmd_string)
                run1 = subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                run2 = subprocess.Popen(cmd2.split(), stdin=run1.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                existing_routes = subprocess.Popen(cmd3, stdin=run2.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                if CloudFoundry.cf_domain is not None:
                    try:
                        run1.stdout.close()
                        run2.stdout.close()
                        existing_routes_output, err = existing_routes.communicate(timeout=120)

                        cmd_string = cmd1+cmd2+str(cmd3)
                        if existing_routes.returncode != 0:
                            commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}"
                                              .format(command=cmd_string,
                                                     rtn=existing_routes.returncode),
                                             'ERROR')

                        for route_line in existing_routes_output.splitlines():
                            commons.print_msg(CloudFoundry.clazz, method, "Removing route {route} from {line}".format(
                                route=route_line.decode("utf-8"), line=line.decode("utf-8")))

                            cmd = "{path}cf unmap-route {old_app} {cf_domain} -n {route_line}".format(
                                path=CloudFoundry.path_to_cf,
                                old_app=line.decode("utf-8"),
                                cf_domain=CloudFoundry.cf_domain,
                                route_line=route_line.decode("utf-8"))

                            commons.print_msg(CloudFoundry.clazz, method, cmd)

                            unmap_route = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE,
                                                           stderr=subprocess.STDOUT)

                            try:
                                unmap_route_output, errs = unmap_route.communicate(timeout=120)

                                for unmapped_route in unmap_route_output.splitlines():
                                    commons.print_msg(CloudFoundry.clazz, method, unmapped_route.decode("utf-8"))

                                if unmap_route.returncode != 0:
                                    unmap_delete_previous_versions_failed = True
                                    commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return "
                                                                                 "code of {rtn}".format(
                                                                                    command=cmd,
                                                                                    rtn=unmap_route.returncode),
                                                     'ERROR')

                            except TimeoutExpired:
                                unmap_delete_previous_versions_failed = True
                                commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')

                    except TimeoutExpired:
                        commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
                        unmap_delete_previous_versions_failed = True

                if unmap_delete_previous_versions_failed is False:
                    delete_cmd = "{path}cf delete {project} -f".format(project=line.decode("utf-8"),
                                                                       path=CloudFoundry.path_to_cf)

                    commons.print_msg(CloudFoundry.clazz, method, delete_cmd)

                    delete_app = subprocess.Popen(delete_cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    try:
                        delete_app_output, errs = delete_app.communicate(timeout=120)

                        for deleted_app in delete_app_output.splitlines():
                            commons.print_msg(CloudFoundry.clazz, method, deleted_app.decode("utf-8"))

                        if delete_app.returncode != 0:
                            commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}"
                                              .format(command=cmd,
                                                     rtn=delete_app.returncode),
                                             'ERROR')

                    except TimeoutExpired:
                        commons.print_msg(CloudFoundry.clazz, method, "Timed out calling".format(delete_cmd), 'ERROR')
                        delete_app.kill()
                        delete_app.communicate()
                        os.system('stty sane')

                if unmap_delete_previous_versions_failed:
                    existing_routes.kill()
                    # existing_routes.communicate()
                    os.system('stty sane')
                    self._cf_logout()
                    exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _cf_logout(self):
        method = '_cf_logout'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd = "{}cf logout".format(CloudFoundry.path_to_cf)

        cf_logout = subprocess.Popen(cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        logout_failed = False

        try:
            cf_logout_output, errs = cf_logout.communicate(timeout=30)

            for line in cf_logout_output.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, line.decode('utf-8'))

            if cf_logout.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}"
                                  .format(command=cmd,
                                         rtn=cf_logout.returncode),
                                 'ERROR')
                logout_failed = True

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd), 'ERROR')
            logout_failed = True

        if logout_failed:
            cf_logout.kill()
            os.system('stty sane')
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _cf_login(self):
        method = 'cf_login'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd = "{path}cf login -a {cf_api_endpoint} -u {cf_user} -p {cf_pwd} -o \"{cf_org}\" -s \"{cf_space}\" --skip-ssl-validation".format(
            path=CloudFoundry.path_to_cf,
            cf_api_endpoint=CloudFoundry.cf_api_endpoint,
            cf_user=CloudFoundry.cf_user,
            cf_pwd=CloudFoundry.cf_pwd,
            cf_org=CloudFoundry.cf_org,
            cf_space=CloudFoundry.cf_space
        )

        cmd_array = "{path}cf login -a {cf_api_endpoint} -u {cf_user} -p {cf_pwd} -o".format(
            path=CloudFoundry.path_to_cf,
            cf_api_endpoint=CloudFoundry.cf_api_endpoint,
            cf_user=CloudFoundry.cf_user,
            cf_pwd=CloudFoundry.cf_pwd
        ).split()
        cmd_array.append(CloudFoundry.cf_org)
        cmd_array.append("-s")
        cmd_array.append(CloudFoundry.cf_space)
        cmd_array.append("--skip-ssl-validation")

        cf_login = subprocess.Popen(cmd_array, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        login_failed = False

        while cf_login.poll() is None:
            line = cf_login.stdout.readline().decode('utf-8').strip(' \r\n')

            commons.print_msg(CloudFoundry.clazz, method, line)

            if 'credentials were rejected' in line.lower():
                commons.print_msg(CloudFoundry.clazz, method, "Make sure that your credentials are correct for {}"
                                  .format(CloudFoundry.cf_user), 'ERROR')
                login_failed = True

        try:
            cf_login_output, errs = cf_login.communicate(timeout=120)

            for line in cf_login_output.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, line.decode('utf-8'))

            if cf_login.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling cf login. Return code of {rtn}. Make "
                                                             "sure the user {usr} has proper permission to deploy.",
                                 'ERROR')
                login_failed = True

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling CF LOGIN.  Make sure that your "
                                                         "credentials are correct for {}".format(CloudFoundry.cf_user),
                             'ERROR')
            login_failed = True

        if login_failed:
            cf_login.kill()
            os.system('stty sane')
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def _cf_login_check(self):
        method = 'cf_login_check'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        cmd_api = "{path}cf api {api}".format(path=CloudFoundry.path_to_cf,
                                          api=CloudFoundry.cf_api_endpoint)

        cf_api = subprocess.Popen(cmd_api.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        try:
            cf_api_output, cf_api_err = cf_api.communicate(timeout=30)

            for api_line in cf_api_output.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, api_line.decode('utf-8'))

            if cf_api.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}".format(
                                 command=cmd_api, rtn=cf_api.returncode), 'ERROR')
                exit(1)

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd_api), 'ERROR')

        # Test user/pwd login
        cmd_auth = "{path}cf auth {cf_user} {cf_pwd}".format(path=CloudFoundry.path_to_cf,
                                                         cf_user=CloudFoundry.cf_user,
                                                         cf_pwd=CloudFoundry.cf_pwd)

        cf_login = subprocess.Popen(cmd_auth.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        try:
            cf_login_output, cf_login_err = cf_login.communicate(timeout=30)

            for cf_login_line in cf_login_output.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, cf_login_line.decode('utf-8'))

            if cf_login.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Make sure that your credentials are correct for {usr}. "
                                                             "\r\n Return Code: {rtn}".format(usr=CloudFoundry.cf_user,
                                                                                              rtn=cf_login.returncode),
                                 'ERROR')
                exit(1)

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling login for {}".format(
                CloudFoundry.cf_user), 'ERROR')

        cmd_target_array = '{path}cf target -o'.format(path=CloudFoundry.path_to_cf).split()
        cmd_target_array.append(CloudFoundry.cf_org)
        cmd_target_array.append("-s")
        cmd_target_array.append(CloudFoundry.cf_space)
        
        print(cmd_target_array)
        cf_target = subprocess.Popen(cmd_target_array, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        try:
            cf_target_output, cf_target_err = cf_target.communicate(timeout=30)

            for cf_target_line in cf_target_output.splitlines():
                commons.print_msg(CloudFoundry.clazz, method, cf_target_line.decode('utf-8'))

            if cf_target.returncode != 0:
                commons.print_msg(CloudFoundry.clazz, method, "Failed calling {command}. Return code of {rtn}".format(
                                 command=cmd_target_array, rtn=cf_target.returncode), 'ERROR')
                exit(1)

        except TimeoutExpired:
            commons.print_msg(CloudFoundry.clazz, method, "Timed out calling {}".format(cmd_target_array), 'ERROR')
            exit(1)

        commons.print_msg(CloudFoundry.clazz, method, 'end')

    def deploy(self, force_deploy=False, manifest=None):
        method = 'deploy'
        commons.print_msg(CloudFoundry.clazz, method, 'begin')

        self._verify_required_attributes()

        self.download_cf_cli()

        self._cf_login_check()

        self._cf_login()

        self._check_cf_version()

        self._get_stopped_apps()

        self._get_started_apps(force_deploy)

        if manifest is None:
            manifest = self._determine_manifests()

        self._cf_push(manifest)

        if not os.getenv("AUTO_STOP"):
            self._stop_old_app_servers()

        if not force_deploy:
            # don't delete if force bc we want to ensure that there is always 1 non-started instance
            # for backup and force_deploy is used when you need to redeploy/replace an instance
            # that is currently running
            self._unmap_delete_previous_versions()

        commons.print_msg(CloudFoundry.clazz, method, 'DEPLOYMENT SUCCESSFUL')

        commons.print_msg(CloudFoundry.clazz, method, 'end')
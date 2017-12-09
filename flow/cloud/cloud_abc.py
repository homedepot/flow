import os
import subprocess
import zipfile
from abc import ABCMeta, abstractmethod

import requests

from flow.utils import commons


class Cloud(metaclass=ABCMeta):
    clazz = 'Cloud'

    def download_custom_deployment_script(self, custom_deploy_script):
        method = 'download_custom_deployment_script'
        commons.printMSG(Cloud.clazz, method, 'begin')

        if custom_deploy_script is None or len(custom_deploy_script.strip()) == 0:
            return

        if 'github' in custom_deploy_script:
            commons.printMSG(Cloud.clazz, method, "Looking for deploy script from GitHub {"
                                                  "}".format(custom_deploy_script))

            try:
                if os.getenv("GITHUB_TOKEN"):
                    headers = {'Authorization': ("Bearer " + os.getenv("GITHUB_TOKEN"))}

                    resp = requests.get(custom_deploy_script, headers=headers, verify=False, timeout=self.http_timeout)
                else:
                    commons.printMSG(Cloud.clazz, 'No GITHUB_TOKEN detected in environment. Attempting to access '
                                                  'deploy script anonymously.', 'WARN')
                    resp = requests.get(custom_deploy_script, verify=False, timeout=self.http_timeout)

            except:
                commons.printMSG(Cloud.clazz, method, "Failed retrieving custom deploy script from GitHub {}".format(
                    custom_deploy_script), 'ERROR')
                exit(1)

            if resp.status_code == 200:
                with os.fdopen(os.open('custom_deploy.sh', os.O_WRONLY | os.O_CREAT), 'w') as handle:
                    handle.write(resp.text)
                commons.printMSG(Cloud.clazz, method, resp.text)
            else:
                commons.printMSG(Cloud.clazz, method, "Failed retrieving custom web deploy script from {script}. "
                                                       "\r\n Response: {response}".format(script=custom_deploy_script,
                                                                                          response=resp.text), 'ERROR')
                exit(1)

        elif 'http' in custom_deploy_script or 'www' in custom_deploy_script:
            commons.printMSG(Cloud.clazz, method, "Looking for deploy script from web at {"
                                                  "}".format(custom_deploy_script))

            try:
                resp = requests.get(custom_deploy_script, verify=False, timeout=self.http_timeout)
            except:
                commons.printMSG(Cloud.clazz, method, "Failed retrieving custom web deploy script from {script}. "
                                                       "\r\n Response: {response}".format(script=custom_deploy_script,
                                                                                          response=resp.text), 'ERROR')
                exit(1)

            if resp.status_code == 200:
                with os.fdopen(os.open('custom_deploy.sh', os.O_WRONLY | os.O_CREAT), 'w') as handle:
                    handle.write(resp.text)
                commons.printMSG(Cloud.clazz, method, resp.text)
            else:
                commons.printMSG(Cloud.clazz, method, "Failed retrieving custom web deploy script from {script}. "
                                                       "\r\n Response: {response}".format(script=custom_deploy_script,
                                                                                          response=resp.text), 'ERROR')
                exit(1)

        elif custom_deploy_script is not None and len(custom_deploy_script.strip()) > 0:
            commons.printMSG(Cloud.clazz, method, ("Looking for deploy script locally", custom_deploy_script))

            if not os.path.isfile(custom_deploy_script.strip()):
                commons.printMSG(Cloud.clazz, method, ("Failed retrieving custom deploy script locally from {}"
                                                       .format(custom_deploy_script), 'ERROR'))
                exit(1)

        commons.printMSG(Cloud.clazz, method, 'end')

    def find_deployable(self, file_ext, dir_to_look_in):
        method = 'find_deployable'
        commons.printMSG(Cloud.clazz, method, 'begin')

        commons.printMSG(Cloud.clazz, method, "Looking for a {ext} in {dir}".format(ext=file_ext, dir=dir_to_look_in))

        deployable_files = commons.get_files_of_type_from_directory(file_ext.lower(), dir_to_look_in)

        if len(deployable_files) > 1:
            commons.printMSG(Cloud.clazz, method, "Found more than 1 artifact in {}".format(dir_to_look_in), 'ERROR')
            # raise IOError('Found more than 1 artifact')
            exit(1)
        elif len(deployable_files) == 0:
            commons.printMSG(Cloud.clazz, method, "Could not find file of type {ext} in {dir}".format(
                ext=file_ext, dir=dir_to_look_in), 'ERROR')
            # raise IOError('Found 0 artifacts')
            exit(1)

        commons.printMSG(Cloud.clazz, method, 'end')

        return deployable_files[0]

    def run_deployment_script(self, custom_deploy_script):
        method = 'run_deployment_script'
        commons.printMSG(Cloud.clazz, method, 'begin')

        cmd = "./" + custom_deploy_script

        execute_custom_script = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while execute_custom_script.poll() is None:
            line = execute_custom_script.stdout.readline().decode('utf-8').strip(' \r\n')
            commons.printMSG(Cloud.clazz, method, line)

        execute_custom_script_output, execute_custom_script_error = execute_custom_script.communicate(timeout=120)

        for line in execute_custom_script_output.splitlines():
            commons.printMSG(Cloud.clazz, method, line.decode("utf-8"))

        if execute_custom_script.returncode != 0:
            commons.printMSG(Cloud.clazz, method, "Failed calling {command}. Return code of {rtn}".format(
                    command=cmd, rtn=execute_custom_script.returncode), 'ERROR')
            return False

        commons.printMSG(Cloud.clazz, method, 'end')

        return True

    @abstractmethod
    def deploy(self):
        pass

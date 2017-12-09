#!/usr/bin/python
# graphite.py

import socket
from time import time

from flow.buildconfig import BuildConfig
from flow.metrics.metrics_abc import Metrics
from requests import post

import flow.utils.commons as commons


class Graphite(Metrics):
    clazz = 'Graphite'
    endpoint = None
    config = BuildConfig
    prefix = None

    def __init__(self):
        method = '__init__'

        self.endpoint = self.config.settings.get('metrics', 'endpoint')
        commons.printMSG(self.clazz, method, "Metrics Endpoint {}".format(self.endpoint))

        self.prefix = self.config.settings.get('metrics', 'prefix')
        commons.printMSG(self.clazz, method, "Metrics Prefix {}".format(self.prefix))

    def write_metric(self, task, action):
        method = 'write_metric'
        commons.printMSG(self.clazz, method, 'begin')
        try:
            message = "{0}.{1}.{2}.{3}.count {4} {5}\n".format(self.prefix, task, action, self.config.project_name,
                                                               1, int(time()))
            # resp = post(self.endpoint, message)
            #
            # if resp.status_code == 200:
            #     commons.printMSG(self.clazz, method, "Metrics Write {}".format(message))
            # else:
            #     commons.printMSG(self.clazz, method, 'Metrics Write Failed', 'ERROR')

        except socket.error as e:
            commons.printMSG(self.clazz, method, "Metrics Write Failed ()".format(e), 'ERROR')

        commons.printMSG(self.clazz, method, 'end')

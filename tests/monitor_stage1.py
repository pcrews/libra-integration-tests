# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

""" monitor_stage1
    e2e tests for basic haproxy/lb monitoring via atlas lbaas

"""

import ast
import time
import unittest
import requests
import commands

import lbaas_utils

class testMonitorStage1(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=200
                ):
        super(testMonitorStage1, self).__init__(testname)
        self.test_description = test_description
        self.args = args
        self.logging = logging
        self.driver = driver
        self.algorithm = algorithm
        self.bad_statuses = ['500','413','400']
        if type(lb_name) is int:
            self.lb_name = str(lb_name)
        else:
            self.lb_name = lb_name
        self.nodes = nodes
        self.lb_id = lb_id
        self.expected_status = expected_status

    def report_info(self):
        """ function for dumping info on test failures """
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
        msg_data = ['']
        for report_value in report_values:
            msg_data.append("%s: %s" %(report_value, getattr(self,report_value)))
        msg_data.append('')
        return '\n'.join(msg_data)

    def setUp(self):
        ###########################
        # test create load balancer
        ###########################
        print ''
        self.logging.info("Setting up for testcase:")
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    

    def test_monitorLoadBalancer(self):
        """ test monitoring of loadbalancers for libra
        """
        # Create our loadbalancer
        self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer id: %s' %self.lb_id)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)
        lbaas_utils.validate_loadBalancer(self)
        # use fabric to stop libra_worker
        self.logging.info("Stopping libra_worker on lb: %s address: %s" %(self.lb_id, self.lb_addr))
        cmd = "sudo fab --no-pty -H %s stop_libra_worker" %(self.lb_addr)
        status, output = commands.getstatusoutput(cmd)
        #if self.args.verbose:
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)
        # check api to see if ERROR state is set / libra_worker failure is detected
        self.logging.info("Wait / poll api server for loadbalancer to be set to ERROR status...")
        lbaas_utils.wait_for_active_status(self, self.lb_id, active_wait_time=240, desired_status='ERROR')
        # restart libra_worker
        self.logging.info("Starting libra_worker on lb: %s address: %s" %(self.lb_id, self.lb_addr))
        cmd = "sudo fab --no-pty -H %s start_libra_worker" %(self.lb_addr)
        status, output = commands.getstatusoutput(cmd)
        #if self.args.verbose:
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)
        # check api to ensure lb state is properly reset
        self.logging.info("Wait / poll api server for loadbalancer to be set to ACTIVE status...")
        lbaas_utils.wait_for_active_status(self, self.lb_id, active_wait_time=240, desired_status='ACTIVE')
        # one final lb validation
        lbaas_utils.validate_loadBalancer(self)
        
    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
        result = self.driver.delete_lb(self.lb_id)






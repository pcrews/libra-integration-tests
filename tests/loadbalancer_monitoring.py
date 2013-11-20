# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

""" create_loadbalancer
    e2e tests for creating loadbalancers via atlas lbaas

"""

import ast
import time
import commands
import unittest
import requests

import lbaas_utils

class testMonitoring(unittest.TestCase):

    def __init__( self
                , test_description
                , args
                , logging
                , driver
                , testname
                , lb_name
                , nodes
                , lb_id=None
                , algorithm = None
                , monitor_data=None
                , expected_status=200
                ):
        super(testMonitoring, self).__init__(testname)
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
        self.swift_user = self.args.osusername
        self.swift_tenant_name = self.args.ostenantname
        self.swift_pass = self.args.ospassword
        self.auth_url = self.args.osauthurl
        self.default_monitor = {'delay': 30, 'attemptsBeforeDeactivation': 2, 'type': 'CONNECT', 'timeout': 30}
        self.monitor_data = monitor_data
        # we override defaults if command line options given.
        if self.args.swiftuser:
            self.swift_user = self.args.swiftuser
        if self.args.swiftpw:
            self.swift_pass = self.args.swiftpw
        if self.args.swifttenantname:
            self.swift_tenant_name = self.args.swifttenantname
        self.swift_auth_token, self.swift_endpoint, self.swift_tenant_id = lbaas_utils.get_auth_token_endpoint(self.auth_url, self.swift_user, self.swift_pass, self.swift_tenant_name, verbose = args.verbose)


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
        # test healing a load balancer
        ###########################
        print ''
        self.logging.info("Setting up for testcase:")
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    

    def test_Monitoring(self):
        """ multiple clients beat on a loadbalancer
        """
        
        # Create our loadbalancer
        if not self.args.lbid:
            self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
            self.logging.info('load balancer id: %s' %self.lb_id)
            self.logging.info('load balancer ip addr: %s' %self.lb_addr)
            lbaas_utils.validate_loadBalancer(self)
        else:
            self.logging.info("Using user-supplied loadbalancer: %s" %self.args.lbid)
            self.lb_id = self.args.lbid
            self.lb_addr = self.get_floating_ip(self.lb_id)

        # validate the loadbalancer
        lbaas_utils.validate_loadBalancer(self)
        self.logging.info("Getting monitor data for default monitor...")
        output, status = self.driver.get_monitor(self.lb_id)
        self.assertEqual(status,'200',msg="ERROR: problem w/ loadbalancer: %s monitor.  Received status: %s: %s" %(self.lb_id, status, output))
        self.assertEqual(output, self.default_monitor, msg="ERROR: problem with default monitor.  Expected: %s, Actual: %s" %(self.default_monitor, output))

        # updating the monitor...
        for description, monitor in self.monitor_data:
            self.logging.info("Testing monitor variant: %s..." %description)
            output, status = self.driver.update_monitor(self.lb_id, monitor)
            self.logging.info("Status: %s || output: %s" %(status, output))
            current_monitor, current_status = self.driver.get_monitor(self.lb_id)
            self.assertEqual(status,'200',msg="ERROR: problem w/ loadbalancer: %s monitor.  Received status: %s: %s" %(self.lb_id, current_status, current_monitor))
            self.assertEqual(current_monitor, monitor, msg= "Loadbalancer: %s monitor not matching expected value:  Expected: %s || Actual %s" %(self.lb_id, monitor, current_monitor)
        lbaas_utils.wait_for_active_status(self)
        
    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        if not self.args.lbid:
            self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
            result = self.driver.delete_lb(self.lb_id)
        else:
            self.logging.info("Used user-specified loadbalancer: %s, not attempting to cleanup..." %self.lb_id)


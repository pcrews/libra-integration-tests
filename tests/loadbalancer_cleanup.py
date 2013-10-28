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

""" loadbalancer_cleanup
    lazy man's way to clean up a lot of test lb's...

"""
import sys
import ast
import copy
import time
import unittest
import requests
import lbaas_utils

class testLoadBalancerCleanup(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname):
        super(testLoadBalancerCleanup, self).__init__(testname)
        self.test_description = test_description
        self.args = args
        self.logging = logging
        self.driver = driver

    def report_info(self):
        """ function for dumping info on test failures """
        report_values = ['test_description']
        msg_data = ['']
        for report_value in report_values:
            msg_data.append("%s: %s" %(report_value, getattr(self,report_value)))
        msg_data.append('')
        return '\n'.join(msg_data)

    def setUp(self):
        ###########################
        # test cleanup loadbalancers
        ###########################
        print ''
        self.logging.info("Setting up for testcase:")
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    

    def test_loadBalancerCleanup(self):
        """ delete all available loadbalancers for provided user
        """
        # Get list of loadbalancers
        self.lb_list = self.driver.list_lbs()
        # delete them all
        for lb in self.lb_list:
            self.logging.info(lb)






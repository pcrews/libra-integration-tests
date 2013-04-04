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

""" modify_nodes:
    tests to validate modify_node lb functionality

"""

import ast
import unittest
import requests

import lbaas_utils

class testMultiLoadBalancer(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name1, lb_name2, nodes1, nodes2, lb_id=None
                , algorithm = None, expected_status=200
                ):
        super(testMultiLoadBalancer, self).__init__(testname)
        self.test_description = test_description
        self.args = args
        self.logging = logging
        self.driver = driver
        self.algorithm = algorithm
        self.bad_statuses = ['500','413','400']
        self.lb_name1 = lb_name1
        self.lb_name2 = lb_name2
        self.nodes1 = nodes1
        self.nodes2 = nodes2
        self.lb_id1 = lb_id
        self.lb_id2 = None
        self.expected_status = expected_status

    def report_info(self):
        """ function for dumping info on test failures """
        report_values = ['test_description', 'expected_status']
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
        report_values = ['test_description', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name1: %s" %self.lb_name1)
            self.logging.info("nodes1: %s" %self.nodes1) 
            self.logging.info("name2: %s" %self.lb_name2)  
            self.logging.info("nodes2: %s" %self.nodes2)  
        # Create our loadbalancer
        self.create_result, self.actual_status, self.lb_id1, self.lb_addr = self.driver.create_lb(self.lb_name1, self.nodes1, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer1 id: %s' %self.lb_id1)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)

    def test_multiLB(self):
        """ test of multiple lb's per haproxy device
        """

        # wait until our lb is ACTIVE before trying to update it
        # test / validate lb1
        lbaas_utils.wait_for_active_status(self, self.lb_id1)
        lbaas_utils.validate_loadBalancer( self
                                         , multi=True
                                         , multi_id=self.lb_id1
                                         , multi_name=self.lb_name1
                                         , multi_nodes=self.nodes1)
        result_data = self.driver.list_lb_detail(self.lb_id1)
        if 'virtualIps' in result_data:
            self.vip = result_data['virtualIps'][0]['id']
        else: # client has different key
            self.vip = ast.literal_eval(result_data['ips'])[0]['id']
        # create lb2
        self.logging.info('Creating load balancer2...')
        self.create_result, self.actual_status, self.lb_id2, self.lb_addr = self.driver.create_lb(self.lb_name2, self.nodes2, self.algorithm, self.bad_statuses, self.vip)
        lbaas_utils.wait_for_active_status(self, self.lb_id2)
        self.logging.info('load balancer2 id: %s' %(self.lb_id2))
        lbaas_utils.validate_loadBalancer( self
                                         , multi=True
                                         , multi_id=self.lb_id2
                                         , multi_name=self.lb_name2
                                         , multi_nodes=self.nodes2)


    def tearDown(self):
        ##########################
        # modify the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id1)
        result = self.driver.delete_lb(self.lb_id1)
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id2)
        result = self.driver.delete_lb(self.lb_id2)

 

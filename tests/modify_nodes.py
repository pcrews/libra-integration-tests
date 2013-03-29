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

class testModifyNode(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=200
                ):
        super(testModifyNode, self).__init__(testname)
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
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    
        # Create our loadbalancer
        self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer id: %s' %self.lb_id)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)

    def test_modifyNodes(self):
        """ test modifying loadbalancer nodes for libra
        """

        # wait until our lb is ACTIVE before trying to update it
        lbaas_utils.wait_for_active_status(self)
        # modify/disable a node on our loadbalancer
        self.logging.info("Testing node disable...")
        nodes = self.driver.list_lb_nodes(self.lb_id)
        mod_node = nodes['nodes'][0]
        mod_node_id = mod_node['id']
        mod_node_addr = mod_node['address']
        mod_node_data = {'condition':'DISABLED'}
        self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        lbaas_utils.validate_loadBalancer(self, [mod_node_addr])

        # re-enable the node
        self.logging.info("Testing re-enable of node...")
        mod_node_data = {'condition':'ENABLED'}
        self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        lbaas_utils.validate_loadBalancer(self)

        # modify ip / address
        self.logging.info("Testing update of node ip...")
        mod_node_data = {'address': '127.0.0.1'}
        expected_status = '400'
        self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update node ip address succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))
        
        # modify port
        self.logging.info("Testing update of node port...")
        mod_node_data = {'port': '443'}
        expected_status = '400'
        self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update node port succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))

        # update of non-existent node
        self.logging.info("Testing update of non-existent node...")
        mod_node_data = {'condition':"DISABLED"}
        expected_status = '404'
        self.actual_status = self.driver.modify_node(self.lb_id, '0', mod_node_data)
        self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update node port succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))

        # lower-case condition
        #self.logging.info("Testing lowercase condition...")
        #mod_node_data = {'condition':'disabled'}
        #self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        #lbaas_utils.validate_loadBalancer(self, [mod_node_addr])
        #self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        #lbaas_utils.validate_loadBalancer(self, [mod_node_addr])

        # lower-case condition
        self.logging.info("Testing bad condition...")
        mod_node_data = {'condition':'TASERED_BADLY'}
        expected_status = '400'
        self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
        self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update to bad condition succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))
 

    def tearDown(self):
        ##########################
        # modify the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
        result = self.driver.delete_lb(self.lb_id)

 

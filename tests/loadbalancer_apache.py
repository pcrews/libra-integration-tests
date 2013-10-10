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

""" loadbalancer_functions
    e2e tests for creating loadbalancers via atlas lbaas

"""

import os
import sys
import ast
import copy
import time
import unittest
import requests
import commands
import lbaas_utils

class testLoadBalancerApache(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None
                , expected_status=202):
        super(testLoadBalancerApache, self).__init__(testname)
        self.test_description = test_description
        self.args = args
        self.logging = logging
        self.driver = driver
        self.algorithm = algorithm
        self.good_algorithms = ['LEAST_CONNECTIONS','ROUND_ROBIN']
        self.bad_statuses = ['500','413','400']
        if type(lb_name) is int:
            self.lb_name = str(lb_name)
        else:
            self.lb_name = lb_name
        self.node_pool = nodes
        self.main_lb_id = None
        # we have a pool of N nodes we can use, but set initial set to just 1 backend node
        self.nodes = [self.node_pool[0]]
        self.lb_id = lb_id
        self.expected_status = expected_status
        self.first_run_done = False

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

    def test_loadBalancerFuncs(self):
        """ test libra loadbalancers via siege
        """
        # Create our loadbalancer w/ one node to start
        self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer id: %s' %self.lb_id)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)
        lbaas_utils.validate_loadBalancer(self)

        # iterate through backend node sets and run siege
        for node_count in [1,3,5,10]:
            self.logging.info("Testing with %s nodes" %node_count)
            self.logging.info("*"*80)
            if node_count != 1:
                # we have nodes[0] already, we add subsequent nodes to it
                add_nodes = self.node_pool[len(self.nodes):node_count]
                # add nodes to our loadbalancer
                self.add_node_result, self.actual_status = self.driver.add_nodes(self.lb_id, add_nodes)
                if self.actual_status =='202': 
                    # good update, we need to update our expected nodes
                    self.nodes += add_nodes
                    self.logging.info("Current node list:")
                    nodes = self.driver.list_lb_nodes(self.lb_id)
                    self.logging.info(nodes)
                    lbaas_utils.validate_loadBalancer(self)
                else:
                    self.assertEqual(self.actual_status, '202', msg = "Adding nodes to loadbalancer %s failed with status: %s" %(self.lb_id, self.actual_status))
            # now we run apache-bench!
            self.logging.info("Beginning apache-bench tests...")
            pages = [ ('cgi-bin/1k-random.py','1k randomly generated text')
                    , ('1k-static','1k static data')
                    , ('starry-night-vincent-van-go1.jpg','jpeg file')
                    #, ('csj.mp4','mp4 video')
                    ]
            for page_file, page_desc in pages:
                page_path = os.path.join(self.lb_addr, page_file)
                self.logging.info("Testing page: %s, %s" %(page_path, page_desc))
                cmd = 'ab -q -r -c50 -n1000 http://%s' %(page_path)
                self.logging.info("test command: %s" %cmd)
                status, output = commands.getstatusoutput(cmd)
                self.logging.info("status: %s" %status)
                self.logging.info("output: %s" %output)       

    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        if self.main_lb_id:
            self.lb_id = self.main_lb_id
        if self.args.cleanupoff:
            self.logging.info("NOT deleting loadbalancer: %s per user-specified flag..." %self.lb_id)
        else:
            self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
            result = self.driver.delete_lb(self.lb_id)





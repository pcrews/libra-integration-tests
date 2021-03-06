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

    def __init__( self
                , test_description
                , args
                , logging
                , driver
                , testname
                , lb_name
                , nodes
                , concurrency=100
                , requests=100000
                , node_counts=[1,3,5,10]
                , pages = None
                , lb_id=None
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
        self.concurrency = concurrency
        self.requests = requests
        self.node_counts = node_counts
        self.pages = pages
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
        report_values = [ 'test_description'
                        , 'lb_name'
                        , 'nodes'
                        , 'expected_status'
                        , 'node_counts'
                        , 'pages'
                        , 'concurrency'
                        , 'requests']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    

    def test_loadBalancerFuncs(self):
        """ test libra loadbalancers via apachebench
        """
        # Create our loadbalancer w/ one node to start
        self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer id: %s' %self.lb_id)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)
        lbaas_utils.validate_loadBalancer(self)

        # iterate through backend node sets and run apachebench
        for node_count in self.node_counts:
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
            for page_set in self.pages:
                page_file = page_set['path']
                page_desc = page_set['description']
                page_path = os.path.join(self.lb_addr, page_file)
                self.logging.info("Testing page: %s, %s" %(page_path, page_desc))
                self.logging.info("Testing with %s nodes" %node_count)
                cmd = 'ab -q -r -c%s -n%s http://%s' %(self.concurrency, self.requests, page_path)
                self.logging.info("test command: %s" %cmd)
                status, output = commands.getstatusoutput(cmd)
                self.logging.info("status: %s" %status)
                self.logging.info("output: %s" %output)       
            # determine if we want to wait for m&b testing or not
            self.logging.info(self.args.testmab)
            if self.args.testmab == True:
                report_wait = 180
                self.logging.info("Waiting %s seconds for metering testing..." %report_wait)
                time.sleep(report_wait)
                # delete the lb
                if self.args.cleanupoff:
                    self.logging.info("NOT deleting loadbalancer: %s per user-specified flag..." %self.lb_id)
                else:
                    self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
                    result = self.driver.delete_lb(self.lb_id)
                # get total html bytes and total bytes
                total_bytes = 0
                total_requests = 0
                for line in output.split('\n'):
                    line = line.replace('bytes','')
                    if line.strip().startswith('Complete requests:'):
                        total_requests = int(line.split(':')[1].strip())
                        self.logging.info("Complete requests: %s" %(total_requests))
                    if line.strip().startswith('Total transferred:'):
                        total_bytes = int(line.split(':')[1].strip())
                        self.logging.info("Total bytes: %s" %(total_bytes))
                # get total bytes / messages from metering server
                metering_result = lbaas_utils.validate_metering(self, total_requests, total_bytes)
                self.assertTrue(metering_result)

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





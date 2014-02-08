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
import sys
import ast
import copy
import time
import unittest
import requests
import lbaas_utils

class testLoadBalancerFuncs(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=202
                , functional_inputs = None
                , test_nodes = None):
        super(testLoadBalancerFuncs, self).__init__(testname)
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
        self.nodes = nodes
        self.main_lb_id = None
        self.original_nodes = None
        self.lb_id = lb_id
        self.expected_status = expected_status
        self.functional_inputs = functional_inputs
        self.test_nodes = test_nodes

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
        """ test creation of loadbalancers and their functions for libra
        """
        # Create our loadbalancer
        self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer id: %s' %self.lb_id)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)
        lbaas_utils.validate_loadBalancer(self)

        ##############
        # test updates
        ##############
        self.logging.info("Testing update variants...")
        if self.functional_inputs and 'update_variants' in self.functional_inputs and self.actual_status not in self.bad_statuses:
            for update_variant in self.functional_inputs['update_variants']:
                self.logging.info("Update variant description: %s" %update_variant['description'])
                self.update_data = update_variant['update_data']
                if 'expected_status' in update_variant:
                    self.expected_status = update_variant['expected_status']
                else:
                    self.expected_status = 202
                if 'algorithm' in update_variant and update_variant['algorithm'] in self.good_algorithms:
                    self.algorithm = update_variant['algorithm']
                # wait until our lb is ACTIVE before trying to update it
                lbaas_utils.wait_for_active_status(self)
                # update our loadbalancer
                self.actual_status = self.driver.update_lb(self.lb_id, self.update_data)
                if 'name' in self.update_data and self.actual_status not in self.bad_statuses:
                    self.lb_name = self.update_data['name']
                lbaas_utils.validate_loadBalancer(self)

        ################
        # test add_nodes
        ################
        self.expected_status='202'
        if self.functional_inputs and 'add_node_variants' in self.functional_inputs:
            # get list of original lb nodes (each node = dict)
            original_nodes = self.driver.list_lb_nodes(self.lb_id)['nodes']
            self.original_nodes = copy.deepcopy(self.nodes)
            for variant in self.functional_inputs['add_node_variants']:
                self.logging.info("Testing add / remove node functionality...")
                self.logging.info("Add node variant: %s" %(variant['description']))
                add_nodes = []
                if 'nodes' in variant:
                    add_nodes = variant['nodes']
                else:
                    node_count = variant['node_count']
                    if str(variant['node_count']).startswith('MAX_BACKEND_COUNT'):
                        node_count = int(self.args.maxbackendnodes) - len(self.nodes)
                        if str(variant['node_count']).endswith('+1'):
                            node_count += 1
                    node_pool = self.test_nodes
                    # we have a node_count value and pull from default_values['nodes']
                    if node_count < len(node_pool):
                        add_nodes = node_pool[:node_count]
                    else:
                        add_nodes = []
                        idx = 0
                        while len(add_nodes) < node_count:
                            add_nodes.append(node_pool[idx])
                            idx += 1
                            if idx == len(node_pool):
                                idx = 0
                # add nodes to our loadbalancer
                if self.args.verbose:
                    self.logging.info("Pre-add node list:")
                    nodes = self.driver.list_lb_nodes(self.lb_id)
                self.logging.info(nodes)
                self.add_node_result, self.actual_status = self.driver.add_nodes(self.lb_id, add_nodes)
                disabled_list = []
                if self.actual_status =='202': 
                    # good update, we need to update our expected nodes
                    self.nodes += add_nodes
                    for node in self.nodes:
                        if 'condition' in node and node['condition'] == 'DISABLED':
                            if 'address' in node:
                                disabled_list.append(node['address'])
                    self.logging.info("Post-add node list:")
                    nodes = self.driver.list_lb_nodes(self.lb_id)
                    self.logging.info(nodes)
                    # maybe delete this wait!
                    lbaas_utils.wait_for_active_status(self)
                    lbaas_utils.validate_loadBalancer(self, disabled_list)
                    # remove nodes / reset to original set up
                    current_nodes = self.driver.list_lb_nodes(self.lb_id)['nodes']
                    for orig_node in original_nodes:
                        if orig_node in current_nodes:
                            current_nodes.remove(orig_node)
                    for current_node in current_nodes:
                        attempts_remain = 60
                        time_wait = 1
                        node_exists = True
                        node_id = current_node['id']
                        if self.args.verbose:
                            self.logging.info("Removing node id: %s" %node_id)
                        while attempts_remain and node_exists:
                            result = self.driver.delete_lb_node(self.lb_id, node_id)
                            if result != '202':
                                attempts_remain -= 1
                                time.sleep(time_wait)
                            else:
                                node_exists = False
                        self.assertEqual(result, '202', msg="ERROR: Node id: %s deletion on loadbalancer id: %s failed" %(node_id, self.lb_id))
                    self.nodes = copy.deepcopy(self.original_nodes)
                

        ###################	
        # test modify_nodes
        ###################
        if self.original_nodes:
            self.nodes = self.original_nodes
        if self.functional_inputs and 'modify_variants' in self.functional_inputs:
            self.logging.info("Testing modify nodes")
            # wait until our lb is ACTIVE before trying to update it
            lbaas_utils.wait_for_active_status(self)
            # modify/disable a node on our loadbalancer
            self.logging.info("Testing node disable...")
            self.expected_status=202
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

            # DISABLED - 
            # libra currently does not actually update ip addrs or ports of nodes
            # but it does return a 202 / incorrect status code
            """
            # modify ip / address
            self.logging.info("Testing update of node ip...")
            mod_node_data = {'address': '127.0.0.1'}
            expected_status = '400'
            if self.args.badstatus:
                expected_status = self.args.badstatus
            self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
            nodes = self.driver.list_lb_nodes(self.lb_id)
            self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update node ip address succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))
        
            # modify port
            self.logging.info("Testing update of node port...")
            mod_node_data = {'port': '443'}
            expected_status = '400'
            if self.args.badstatus:
                expected_status = self.args.badstatus
            self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
            self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update node port succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))
            """

            # update of non-existent node
            self.logging.info("Testing update of non-existent node...")
            mod_node_data = {'condition':"DISABLED"}
            expected_status = '404'
            if self.args.badstatus:
                expected_status = self.args.badstatus
            self.actual_status = self.driver.modify_node(self.lb_id, '0', mod_node_data)
            self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Attempt to update non-existent node succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))

            # lower-case condition
            expected_status='400'
            if self.args.badstatus:
                expected_status = self.args.badstatus
            self.logging.info("Testing lowercase condition...")
            mod_node_data = {'condition':'disabled'}
            self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
            self.assertEqual(str(self.actual_status), expected_status, msg = "ERROR: Usage of lowercase node condition succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_status))
            self.expected_status='202'

            # negative / bad node condition
            self.logging.info("Testing bad condition...")
            mod_node_data = {'condition':'TASERED_BADLY'}
            expected_statuses = ['400','512', '404']
            self.actual_status = self.driver.modify_node(self.lb_id, mod_node_id, mod_node_data)
            self.assertTrue(str(self.actual_status) in expected_statuses, msg = "ERROR: Attempt to update to bad condition succeeded with status: %s.  Expected status: %s" %(self.actual_status, expected_statuses))

        ################
        # test multi_lb
        ################
        """ test of multiple lb's per haproxy device
        """
        if self.functional_inputs and 'multiLB_variants' in self.functional_inputs:
            self.logging.info("Testing multiple loadbalancers on one device...")
            self.expected_status = '202'
            self.main_lb_id = copy.deepcopy(self.lb_id)
            for multi_variant in self.functional_inputs['multiLB_variants']: 
                self.lb_name2 = multi_variant['name2']
                self.nodes2 = multi_variant['nodes2']
                # wait until our lb is ACTIVE before trying to update it
                # test / validate lb1
                self.actual_status='202'
                lbaas_utils.wait_for_active_status(self, self.lb_id)
                lbaas_utils.validate_loadBalancer( self
                                                 , multi=True
                                                 , multi_id=self.lb_id
                                                 , multi_name=self.lb_name
                                                 , multi_nodes=self.nodes)
                result_data = self.driver.list_lb_detail(self.lb_id)
                if 'virtualIps' in result_data:
                    self.vip = result_data['virtualIps'][0]['id']
                else: # client has different key
                    self.vip = ast.literal_eval(result_data['ips'])[0]['id']
                # create lb2
                self.logging.info('Creating load balancer2...')
                self.create_result, self.actual_status, self.lb_id2, self.lb_addr = self.driver.create_lb(self.lb_name2, self.nodes2, self.algorithm, self.bad_statuses, self.vip)
                if self.args.verbose:
                    self.logging.info("STATUS: %s" %self.actual_status)
                    self.logging.info("RESULT: %s" %self.create_result.text)
                lbaas_utils.wait_for_active_status(self, self.lb_id2)
                self.logging.info('load balancer2 id: %s' %(self.lb_id2))
                lbaas_utils.validate_loadBalancer( self
                                                 , multi=True
                                                 , multi_id=self.lb_id2
                                                 , multi_name=self.lb_name2
                                                 , multi_nodes=self.nodes2)
                self.logging.info("Deleting loadbalancer: %s" %self.lb_id2)
                result = self.driver.delete_lb(self.lb_id2)

        
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





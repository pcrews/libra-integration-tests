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

""" create_loadbalancer
    e2e tests for creating loadbalancers via atlas lbaas

"""

import ast
import unittest

class testCreateLoadBalancer(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=200):
        super(testCreateLoadBalancer, self).__init__(testname)
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
        self.create_result, self.actual_status, self.lb_id = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        if self.args.verbose:
            self.logging.info('load balancer id: %s' %self.lb_id)
            self.logging.info("")

    def test_createLoadBalancer(self):
        """ test loadbalancer creation
        """
        #####################
        # test create result
        #####################

        http_validation = self.driver.validate_status(self.expected_status, self.actual_status)
        self.assertEqual(http_validation, True
                        , msg = "ERROR: load balancer create failed.  Expected: %s || Actual: %s" \
                        %(self.expected_status, self.create_result)
                        )
        if self.actual_status not in self.bad_statuses:
            ###############
            # test lb list
            ###############
            self.logging.info('Validating load balancer list...')
            loadbalancers = self.driver.list_lbs()
            lb_match = self.driver.validate_lb_list(self.lb_name, loadbalancers)
            self.assertEqual(lb_match, True, msg= "ERROR: load balancer: %s has no match in api loadbalancer list:\n %s" %(self.lb_name, loadbalancers))
            if self.args.verbose:
                self.logging.info("")
        
            ################
            # test detail
            ################
            self.logging.info('Validating load balancer detail...')
            result_data = self.driver.list_lb_detail(self.lb_id)
            if self.args.verbose:
                for key, item in result_data.items():
                    self.logging.info('%s: %s' %(key, item))
            # check name
            self.assertEqual(self.lb_name.strip(), result_data['name'].strip(), msg="ERROR: lb name: %s || system name: %s" %(self.lb_name, result_data['name']))
            # check nodes
            system_nodes = result_data['nodes']
            error, error_list = self.driver.validate_lb_nodes(self.nodes, system_nodes)
            self.assertEqual(error, 0, msg= '\n'.join(error_list))
            # check algorithm
            # check protocol
            # check status
            # check updated time
            # check created time
            if self.args.verbose:
                self.logging.info("")

            ###################
            # test nodes list
            ###################
            self.logging.info('Validating load balancer nodes url...')
            result_data = self.driver.list_lb_nodes(self.lb_id)
            if self.args.verbose:
                for key, item in result_data.items():
                    self.logging.info('%s: %s' %(key, item))
            error, error_list = self.driver.validate_lb_nodes(self.nodes, result_data['nodes'])
            self.assertEqual(error, 0, msg= '\n'.join(error_list))

    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
        result = self.driver.delete_lb(self.lb_id)


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

class testUpdateLoadBalancer(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, update_data, lb_id=None
                , algorithm = None, expected_status=200
                , backend_nodes = None):
        super(testUpdateLoadBalancer, self).__init__(testname)
        self.test_description = test_description
        self.args = args
        self.logging = logging
        self.driver = driver
        self.algorithm = algorithm
        self.update_data = update_data
        self.bad_statuses = ['500','413','400']
        if type(lb_name) is int:
            self.lb_name = str(lb_name)
        else:
            self.lb_name = lb_name
        self.nodes = nodes
        self.lb_id = lb_id
        self.expected_status = expected_status
        self.backend_nodes = backend_nodes

    def report_info(self):
        """ function for dumping info on test failures """
        report_values = ['test_description', 'update_data', 'expected_status']
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
        report_values = ['test_description', 'update_data', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    
        # Create our loadbalancer
        self.create_result, self.actual_status, self.lb_id = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        if self.args.verbose:
            self.logging.info('load balancer id: %s' %self.lb_id)
            self.logging.info("")

    def test_updateLoadBalancer(self):
        """ test update of loadbalancers for libra
        """
        # update our loadbalancer
        self.update_result, self.actual_status = self.driver.update_lb(self.lb_id, self.update_data)
        if 'name' in self.update_data:
            self.lb_name = self.update_data['name']
        self.validate_loadBalancer()
        
    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
        result = self.driver.delete_lb(self.lb_id)

    def validate_loadBalancer(self):
        """ The various things we do to validate a loadbalancer
            This includes:
                - testing various READ API methods against provided values
                - testing the loadbalancer itself
                  (we expect backend nodes to be formatted to help us test
                - testing the status returned by the API server against expected status
        """

        #####################
        # test create result
        #####################

        status_validation = self.driver.validate_status(self.expected_status, self.actual_status)
        self.assertEqual(status_validation, True
                        , msg = self.report_info() + "ERROR: load balancer update failed.  Expected: %s || Actual: %s" \
                        %(self.expected_status, self.update_result)
                        )
        if self.actual_status not in self.bad_statuses:
            ###############
            # test lb list
            ###############
            self.logging.info('Validating load balancer list...')
            loadbalancers = self.driver.list_lbs()
            lb_match = self.driver.validate_lb_list(self.lb_name, loadbalancers)
            self.assertEqual(lb_match, True, msg = self.report_info() + "ERROR: load balancer: %s has no match in api loadbalancer list:\n %s" %(self.lb_name, loadbalancers))
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
            self.assertEqual(self.lb_name.strip(), result_data['name'].strip(), msg = self.report_info() + "ERROR: lb name: %s || system name: %s" %(self.lb_name, result_data['name']))
            # check nodes
            system_nodes = result_data['nodes']
            error, error_list = self.driver.validate_lb_nodes(self.nodes, system_nodes)
            self.assertEqual(error, 0, msg = self.report_info() + '\n'.join(error_list))
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
            self.assertEqual(error, 0, msg = self.report_info() + '\n'.join(error_list))

            ########################
            # test the loadbalancer
            ########################
            self.logging.info('testing loadbalancer function...')
            result_data = self.driver.list_lb_detail(self.lb_id)
            ip_list = ast.literal_eval(result_data['ips'])
            lb_ip = ip_list[0]['address']
            expected_etags = {}
            actual_etags = {}
            self.logging.info('gathering backend node etags...')
            for backend_node in self.nodes:
                node_addr = 'http://%s' %backend_node['address']
                result = requests.get(node_addr)
                expected_etags[node_addr] = result.headers['etag']
            self.logging.info('testing lb for function...')
            request_count = 20
            for request_iter in range(request_count):
                result = requests.get('http://%s' %lb_ip)
                if result.headers['etag'] in actual_etags:
                    actual_etags[result.headers['etag']] += 1
                else:
                    actual_etags[result.headers['etag']] = 1
            for actual_etag in actual_etags.keys():
                self.assertTrue(actual_etag in expected_etags.values(), msg = "Received bad etag: %s.  Expected etags: %s" %(actual_etag, expected_etags))
            expected_hit_count = request_count/len(self.nodes)
            for actual_etag, count in actual_etags.items():
                self.assertTrue(count <= expected_hit_count, msg = "loadbalancing appears off.  Executed requests: %d.  Actual request counts: %s" %(request_count, actual_etags))




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

""" utils.py
    common code shared among test cases
"""

import ast
import requests
import time

def validate_loadBalancer(lb_test_case):
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

        status_validation = lb_test_case.driver.validate_status(lb_test_case.expected_status, lb_test_case.actual_status)
        lb_test_case.assertEqual(status_validation, True
                        , msg = lb_test_case.report_info() + "ERROR: load balancer create failed.  Expected: %s || Actual: %s" \
                        %(lb_test_case.expected_status, lb_test_case.actual_status)
                        )
        if lb_test_case.actual_status not in lb_test_case.bad_statuses:
            ###############
            # test lb list
            ###############
            lb_test_case.logging.info('Validating load balancer list...')
            loadbalancers = lb_test_case.driver.list_lbs()
            lb_match = lb_test_case.driver.validate_lb_list(lb_test_case.lb_name, loadbalancers)
            lb_test_case.assertEqual(lb_match, True, msg = lb_test_case.report_info() + "ERROR: load balancer: %s has no match in api loadbalancer list:\n %s" %(lb_test_case.lb_name, loadbalancers))
            if lb_test_case.args.verbose:
                lb_test_case.logging.info("")
        
            ################
            # test detail
            ################
            lb_test_case.logging.info('Validating load balancer detail...')
            result_data = lb_test_case.driver.list_lb_detail(lb_test_case.lb_id)
            if lb_test_case.args.verbose:
                for key, item in result_data.items():
                    lb_test_case.logging.info('%s: %s' %(key, item))
            # check name
            lb_test_case.assertEqual(lb_test_case.lb_name.strip(), result_data['name'].strip(), msg = lb_test_case.report_info() + "ERROR: lb name: %s || system name: %s" %(lb_test_case.lb_name, result_data['name']))
            # check nodes
            system_nodes = result_data['nodes']
            error, error_list = lb_test_case.driver.validate_lb_nodes(lb_test_case.nodes, system_nodes)
            lb_test_case.assertEqual(error, 0, msg = lb_test_case.report_info() + '\n'.join(error_list))
            # check algorithm
            # check protocol
            # check status
            active_wait_time = 30
            time_decrement = 3
            status_pass = False
            while active_wait_time and not status_pass:
                if result_data['status'] != 'ACTIVE':
                    time.sleep(time_decrement)
                    active_wait_time -= time_decrement
                    result_data = lb_test_case.driver.list_lb_detail(lb_test_case.lb_id)
                else:
                    status_pass = True
            lb_test_case.assertEqual(result_data['status'], 'ACTIVE', msg = 'loadbalancer: %s not in ACTIVE status after %d seconds' %(lb_test_case.lb_id, active_wait_time))
            # check updated time
            # check created time
            if lb_test_case.args.verbose:
                lb_test_case.logging.info("")

            ###################
            # test nodes list
            ###################
            lb_test_case.logging.info('Validating load balancer nodes url...')
            result_data = lb_test_case.driver.list_lb_nodes(lb_test_case.lb_id)
            if lb_test_case.args.verbose:
                for key, item in result_data.items():
                    lb_test_case.logging.info('%s: %s' %(key, item))
            error, error_list = lb_test_case.driver.validate_lb_nodes(lb_test_case.nodes, result_data['nodes'])
            lb_test_case.assertEqual(error, 0, msg = lb_test_case.report_info() + '\n'.join(error_list))

            ########################
            # test the loadbalancer
            ########################
            lb_test_case.logging.info('testing loadbalancer function...')
            result_data = lb_test_case.driver.list_lb_detail(lb_test_case.lb_id)
            if 'ips' in result_data:
                ip_list = ast.literal_eval(result_data['ips'])
            else:
                ip_list = result_data['virtualIps']
            lb_ip = ip_list[0]['address']
            expected_etags = {}
            actual_etags = {}
            url_base='http'
            lb_test_case.logging.info('gathering backend node etags...')
            for backend_node in lb_test_case.nodes:
                if str(backend_node['port']) == '443':
                    url_base='https'
                node_addr = '%s://%s' %(url_base, backend_node['address'])
                result = requests.get(node_addr, verify= False)
                expected_etags[node_addr] = result.headers['etag']
            lb_test_case.logging.info('testing lb for function...')
            request_count = 5*len(expected_etags)
            for request_iter in range(request_count):
                lb_url = '%s://%s' %(url_base, lb_ip)
                result = requests.get(lb_url, verify= False)
                if result.headers['etag'] in actual_etags:
                    actual_etags[result.headers['etag']] += 1
                else:
                    actual_etags[result.headers['etag']] = 1
            for actual_etag in actual_etags.keys():
                lb_test_case.assertTrue(actual_etag in expected_etags.values(), msg = "Received bad etag: %s.  Expected etags: %s" %(actual_etag, expected_etags))
            # ensure our backend nodes were all used
            for node, expected_etag in expected_etags.items():
                lb_test_case.assertTrue(expected_etag in actual_etags.keys(), msg = "Backend node: %s, etag: %s did not receive any traffic from the loadbalancer.  Actual etags received: %s" %(node, expected_etag, actual_etags))
            expected_hit_count = request_count/len(lb_test_case.nodes)
            # This is temporarily disabled
            """
            for actual_etag, count in actual_etags.items():
                lb_test_case.assertTrue(count <= expected_hit_count, msg = "loadbalancing appears off.  Executed requests: %d.  Actual request counts: %s" %(request_count, actual_etags))
            """

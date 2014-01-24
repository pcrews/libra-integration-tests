# Copyright 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
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

import sys
import ast
import json
import math
import time
import requests

def get_auth_token_endpoint(auth_url, username, password, tenant_name, desired_service_name='Object Storage', verbose = False):
    """ Used for testing the lbaas log archiving feature """
        
    endpoint = None
    headers = {"Content-Type": "application/json"}
    request_data = {'auth':{ 'tenantName': tenant_name
                           , 'passwordCredentials':{'username': username
                                                   , 'password': password}
                           }
                   }
    request_data = json.dumps(request_data)
    request_result = requests.post(auth_url, data=request_data, headers=headers, verify=False)
    if verbose:
        print 'Status: %s' %request_result.status_code
        print 'Output:\n%s' %(request_result.text)
    request_data = ast.literal_eval(request_result.text)
    for service_data in request_data['access']['serviceCatalog']:
        if service_data['name'] == desired_service_name:
            endpoint = service_data['endpoints'][0]['publicURL'].replace('\\','')
    auth_token = request_data['access']['token']['id']
    tenant_id = request_data['access']['token']['tenant']['id']
    return auth_token, endpoint, tenant_id

def wait_for_active_status(lb_test_case, lb_id=None, active_wait_time=None, desired_status='ACTIVE',must_pass=True):
    total_wait_time = 0
    time_decrement = 3
    status_pass = False
    if not active_wait_time:
        active_wait_time = int(lb_test_case.args.activewaittime)
    print 
    if not lb_id:
        lb_id = lb_test_case.lb_id
    result_data = lb_test_case.driver.list_lb_detail(lb_id)
    while total_wait_time != active_wait_time and not status_pass:
        if 'status' not in result_data:
            lb_test_case.logging.info('WARNING: no status in result data...')
            lb_test_case.logging.info('result_data:')
            lb_test_case.logging.info(result_data)
            result_data['status'] = None
        if result_data['status'] != desired_status:
            time.sleep(time_decrement)
            total_wait_time += time_decrement
            result_data = lb_test_case.driver.list_lb_detail(lb_id)
        else:
            status_pass = True
            if lb_test_case.args.activepause:
                lb_test_case.logging.info("Waiting %d seconds from %s status..." %(lb_test_case.args.activepause, desired_status))
                time.sleep(lb_test_case.args.activepause)
    if must_pass:
        lb_test_case.assertEqual(result_data['status'], desired_status, msg = 'loadbalancer: %s not in %s status after %d seconds' %(lb_id, desired_status, active_wait_time))

def validate_loadBalancer( lb_test_case
                         , disabled_node_list=[]
                         , multi=False
                         , multi_id=None
                         , multi_name=None
                         , multi_nodes=None):
        """ The various things we do to validate a loadbalancer
            This includes:
                - testing various READ API methods against provided values
                - testing the loadbalancer itself
                  (we expect backend nodes to be formatted to help us test
                - testing the status returned by the API server against expected status
        """
        if multi:
            lb_test_case.lb_id = multi_id
            lb_test_case.lb_name = multi_name
            lb_test_case.nodes = multi_nodes
        #####################
        # test create result
        #####################

        status_validation = lb_test_case.driver.validate_status(lb_test_case.expected_status, lb_test_case.actual_status)
        lb_test_case.assertEqual(status_validation, True
                        , msg = lb_test_case.report_info() + "ERROR: load balancer create failed.  Expected: %s || Actual: %s" \
                        %(lb_test_case.expected_status, lb_test_case.actual_status)
                        )
        if lb_test_case.actual_status not in lb_test_case.bad_statuses:
            result_data = lb_test_case.driver.list_lb_detail(lb_test_case.lb_id)
            ################
            # test detail
            ################
            lb_test_case.logging.info('Validating load balancer detail...')
            if lb_test_case.args.verbose:
                for key, item in result_data.items():
                    lb_test_case.logging.info('%s: %s' %(key, item))
            # check status / wait until we are in ACTIVE state
            wait_for_active_status(lb_test_case)
            result_data = lb_test_case.driver.list_lb_detail(lb_test_case.lb_id)
            # check name
            lb_test_case.assertEqual(lb_test_case.lb_name.strip(), result_data['name'].strip(), msg = lb_test_case.report_info() + "ERROR: lb name: %s || system name: %s" %(lb_test_case.lb_name, result_data['name']))
            # check nodes
            system_nodes = result_data['nodes']
            error, error_list = lb_test_case.driver.validate_lb_nodes(lb_test_case.nodes, system_nodes)
            lb_test_case.assertEqual(error, 0, msg = lb_test_case.report_info() + '\n'.join(error_list))
            # check algorithm
            # check protocol
            # check updated time
            # check created time
            if lb_test_case.args.verbose:
                lb_test_case.logging.info("")

            ###############
            # test lb list
            ###############
            lb_test_case.logging.info('Validating load balancer list...')
            loadbalancers = lb_test_case.driver.list_lbs()
            lb_match = lb_test_case.driver.validate_lb_list(lb_test_case.lb_name, loadbalancers)
            lb_test_case.assertEqual(lb_match, True, msg = lb_test_case.report_info() + "ERROR: load balancer: %s has no match in api loadbalancer list:\n %s" %(lb_test_case.lb_name, loadbalancers))
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
                if backend_node['address'] not in disabled_node_list: #skip any explicitly disabled nodes...
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
                size = 0
                for byte in result.iter_content():
                    size += 1
                lb_test_case.logging.info("Result.content size: %s" %size)
                header_size = 0
                alt_header = 0
                for key, value in result.headers.items():
                    header_size += (len(key) + len(value))
                    alt_header += (sys.sizeof(key) + sys.sizeof(value))
                lb_test_case.logging.info("headers size: %s" %(header_size))
                lb_test_case.logging.info("alt headers: %s" %(alt_header))
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

def convert_to_gb(bytes):
    p = math.pow(1024,3)
    gb = round(bytes/p,2)
    return gb

def validate_metering(lb_test_case, requests, total_bytes):
    """ Validation function for metering and billing """
    logging = lb_test_case.logging
    lb_id = lb_test_case.lb_id
    logging.info("Validating metering information for loadbalancer: %s" %(lb_id))
    # get rabbitmq data for the lb
    import rabbit_utils
    bytes, messages, metered_bytes = rabbit_utils.get_metering_data(lb_test_case.args, 
                                                                  lb_test_case.lb_id,
                                                                  lb_test_case.logging)
    logging.info("Message count: %s" %len(messages))
    logging.info("Bytes: %s" %bytes)
    logging.info("Metered bytes: %s" %metered_bytes)
    logging.info("             : %s GB" %convert_to_gb(metered_bytes))
    logging.info("Measured bytes: %s" %total_bytes)
    logging.info("             : %s GB" %convert_to_gb(total_bytes))
    # compare test-detected bytes to metered bytes...
    logging.info("Comparing test-tool received bytes to metered bytes...")
    metered_bytes = float(metered_bytes)
    total_bytes = float(total_bytes)
    byte_diff = float(total_bytes - metered_bytes)
    if byte_diff:
        logging.info("Metered / Measured diff: %s" %byte_diff)
        logging.info("                       : %s GB" %convert_to_gb(byte_diff))
        per_req_diff = float(byte_diff/requests)
        logging.info("Difference per request: %s" %per_req_diff)
        percent_diff = float(byte_diff/total_bytes)*100
        logging.info("Percentage error: %s" %percent_diff)
    # scan messages for format ...
    logging.info("Validating message formatting for loadbalancer: %s" %(lb_id))
    import validictory
    import mab_schemas
    for message in messages:
        schema = None
        if 'event_type' in message:
            event_type = message['event_type']
            logging.info("Validating event_type: %s" %event_type)
            try:
                schema = mab_schemas.message_schemas[event_type]
                validictory.validate(message, schema)
            except Exception, e:
                logging.info("Error in validation of message format")
                logging.info(e)
    # scan messages for type...
    return True

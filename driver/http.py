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

""" http.py
    methods for interacting with the lbaas service via http requests

"""

import sys
import json
import time
import requests


class lbaasDriver:

    """ Driver to handle http interaction with the libra lbaas service
        Contains methods to call the various api methods as well as
        code for validating the actions

    """

    def __init__(self, args, api_user_url, logging):
        """ TODO: put in validation and api-specific whatnot here """
        self.args = args
        self.wait_decrement = 1  # duration of sleep when we wait for things
        self.user_name = args.osusername
        self.auth_url = args.osauthurl
        self.tenant_name = args.ostenantname
        self.region_name = args.osregionname
        self.password = args.ospassword
        self.verbose = args.verbose
        self.logging.info = logging
        self.auth_token, self.api_user_url, self.swift_endpoint, self.tenant_id = self.get_auth_token()
        if api_user_url:  # if the user supplies an api_user_url, we use that vs. service_catalog value
            self.api_user_url = api_user_url
        self.api_headers = {"Content-Type": "application/json",
                            "X-Auth-Token": self.auth_token}
        return

    #------------------
    # utility functions
    #------------------
    def get_auth_token(self):
        """ Get our keystone auth token to work with the api server """

        lbaas_endpoint = None
        swift_endpoint = None
        headers = {"Content-Type": "application/json"}
        request_data = {'auth': {'tenantName': self.tenant_name,
                                 'passwordCredentials': {'username': self.user_name,
                                                          'password': self.password}
                                }
                       }
        request_data = json.dumps(request_data)
        request_result = requests.post(self.auth_url, data=request_data, headers=headers, verify=False)
        if self.verbose:
            self.logging.info('Status: %s' % request_result.status_code)
            self.logging.info('Output:\n%s' % (request_result.text))
        request_data = json.loads(request_result.text)
        for service_data in request_data['access']['serviceCatalog']:
            if service_data['name'] == 'Load Balancer':
                if self.region_name:
                    for endpoint in service_data['endpoints']:
                        if endpoint['region'] == self.region_name:
                            lbaas_endpoint = endpoint['publicURL'].replace('\\', '')
                else:
                    lbaas_endpoint = service_data['endpoints'][0]['publicURL'].replace('\\', '')
                if self.verbose:
                    self.logging.info("LBAAS_ENDPOINT: %s" % lbaas_endpoint)
            if service_data['name'] == 'Object Storage':
                swift_endpoint = service_data['endpoints'][0]['publicURL'].replace('\\', '')
        auth_token = request_data['access']['token']['id']
        tenant_id = request_data['access']['token']['tenant']['id']
        return auth_token, lbaas_endpoint, swift_endpoint, tenant_id

    #-----------------
    # lbaas functions
    #-----------------
    def create_lb(self, name, nodes, algorithm, bad_statuses, vip=None):
        """ Create a load balancer via the requests library
            We expect the url to be the proper, fully constructed base url
            we add the 'loadbalancers suffix to the base

            nodes is expected to be a list of nodes in this format:
            nodes = [{"address": "15.185.227.167","port": "80"},{"address": "15.185.227.165","port": "80"}]

        """

        url = "%s/loadbalancers" % self.api_user_url
        request_data = {"name": name,
                        "nodes": nodes
                       }
        lb_id = None
        lb_addr = None
        tcp_https_flag = False
        for node in nodes:
            if 'port' in node and str(node['port']) == '443':
                tcp_https_flag = True
        if algorithm:
            request_data["algorithm"] = "%s" % algorithm
        if tcp_https_flag:
            request_data['protocol'] = 'TCP'
            request_data['port'] = '443'
        # dual lb stuff
        if vip:
            request_data['virtualIps'] = [{"id":vip}]
        request_data = json.dumps(request_data)
        request_result = requests.post(url, data=request_data, headers=self.api_headers, verify=False)
        result_data = json.loads(request_result.text)
        request_status = str(request_result.status_code)
        if self.verbose:
            self.logging.info("url: %s" % url)
            self.logging.info("status: %s" % request_status)
            self.logging.info("request_data: %s" % request_data)
            self.logging.info("request result: %s" % result_data)
        if request_status not in bad_statuses:
            lb_id = result_data['id']
            lb_addr = result_data['virtualIps'][0]['address']
            attempts_remain = 120
            time_wait = 1
            while not lb_addr and attempts_remain:
                result_data = self.list_lb_detail(lb_id)
                if 'virtualIps' in result_data:
                    lb_addr = result_data['virtualIps'][0]['address']
                    if lb_addr:
                        attempts_remain = 0
                    else:
                        attempts_remain -= 1
                        time.sleep(time_wait)
                else:
                    attempts_remain -= 1
                    time.sleep(time_wait)
        return request_result, request_status, lb_id, lb_addr

    def delete_lb(self, lb_id):
        """ Delete the loadbalancer identified by 'lb_id' """
        url = "%s/loadbalancers/%s" % (self.api_user_url, lb_id)
        request_result = requests.delete(url, headers=self.api_headers, verify=False)
        if self.verbose:
            self.logging.info(request_result.status_code)
            self.logging.info(request_result.text)
        return request_result

    def list_lbs(self):
        """ List all loadbalancers for the given auth token / tenant id """

        url = "%s/loadbalancers" % self.api_user_url
        request_result = self.__get(url, headers=self.api_headers, verify=False)
        return json.loads(request_result.text)['loadBalancers']

    def list_lb_detail(self, lb_id):
        """ Get the detailed info returned by the api server for the specified id """

        url = "%s/loadbalancers/%s" % (self.api_user_url, lb_id)
        request_result = self.__get(url, headers=self.api_headers, verify=False)
        return json.loads(request_result.text)

    def list_lb_nodes(self, lb_id):
        """ Get list of nodes for the specified lb_id """

        url = "%s/loadbalancers/%s/nodes" % (self.api_user_url, lb_id)
        request_result = self.__get(url, headers=self.api_headers, verify=False)
        return json.loads(request_result.text)

    def delete_lb_node(self, lb_id, node_id):
        """ Remove specified node_id from lb_id """
        url = "%s/loadbalancers/%s/nodes/%s" % (self.api_user_url, lb_id, node_id)
        request_result = requests.delete(url, headers=self.api_headers, verify=False)
        return str(request_result.status_code)

    def update_lb(self, lb_id, update_data):
        """ We get a dictionary of update_data
            containing a new name, algorithm, or both
            and we execute an UPDATE API call and see
            what happens
        """
        url = "%s/loadbalancers/%s" % (self.api_user_url, lb_id)
        request_data = json.dumps(update_data)
        request_result = requests.put(url, data=request_data, headers=self.api_headers, verify=False)
        return str(request_result.status_code)

    def add_nodes(self, lb_id, add_node_data):
        """ We get a list of nodes we want to add and
            try to add them :)

        """
        url = "%s/loadbalancers/%s/nodes" % (self.api_user_url, lb_id)
        node_data = {}
        node_data['nodes'] = add_node_data
        node_data = json.dumps(node_data)
        request_result = requests.post(url, data=node_data, headers=self.api_headers, verify=False)
        return json.loads(request_result.text), str(request_result.status_code)

    def modify_node(self, lb_id, node_id, node_data):
        """ Set the node's condition to the value specified """

        url = "%s/loadbalancers/%s/nodes/%s" % (self.api_user_url, lb_id, node_id)
        node_data = json.dumps(node_data)
        request_result = requests.put(url, data=node_data, headers=self.api_headers, verify=False)
        if self.verbose:
            self.logging.info('http driver modify_node()')
            self.logging.info(request_result.status_code)
            self.logging.info(request_result.text)
        return request_result.status_code

    def get_monitor(self, lb_id):
        """ Get health monitor information """
        url = "%s/loadbalancers/%s/healthmonitor" % (self.api_user_url, lb_id)
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return json.loads(request_result.text), str(request_result.status_code)

    def update_monitor(self, lb_id, monitor_data):
        """ Get health monitor information """
        url = "%s/loadbalancers/%s/healthmonitor" % (self.api_user_url, lb_id)
        output = ''
        status = ''
        monitor_data = json.dumps(monitor_data)
        request_result = requests.put(url, data=monitor_data, headers=self.api_headers, verify=False)
        try:
            output = json.loads(request_result.text)
        except ValueError:
            output = request_result.text
        if request_result.status_code:
            status = request_result.status_code
        return output, str(request_result.status_code)

    def get_logs(self, lb_id, auth_token=None, obj_endpoint=None, obj_basepath=None):
        """ Get the logs / archive them for the listed lb_id """

        url = "%s/loadbalancers/%s/logs" % (self.api_user_url, lb_id)
        data = {}
        if auth_token:
            data['authToken'] = auth_token
        else:
            data['authToken'] = self.auth_token
        if obj_endpoint:
            data['objectStoreEndpoint'] = obj_endpoint
        else:
            data['objectStoreEndpoint'] = self.swift_endpoint
        if obj_basepath:
            data['objectStoreBasePath'] = obj_basepath
        if data:
            data = json.dumps(data)
            request_result = requests.post(url, data=data, headers=self.api_headers, verify=False)
        else:
            request_result = requests.post(url, headers=self.api_headers, verify=False)
        if self.verbose:
            self.logging.info('http driver get_logs()')
            self.logging.info(url)
            self.logging.info(data)
            self.logging.info(request_result.status_code)
            self.logging.info(request_result.text)
        return request_result.status_code

    # http functions
    def __get(self, url, headers=None, verify=False, retries=10, caller_info=None):
        good_request = False
        while retries and not good_request:
            request_result = requests.get(url, headers=headers, verify=False)
            if self.verbose:
                self.logging.info('http GET request...')
                self.logging.info('caller: %s' % caller_info)
                self.logging.info('url: %s' % url)
                self.logging.info('status: %s' % request_result.status_code)
                self.logging.info('returned: %s' % request_result.text)
                self.logging.info('+' * 80)
            if str(request_result.status_code) == '401':
                retries -= 1
                time.sleep(self.wait_decrement)
            else:
                good_request = True
        return request_result

    # validation functions
    # these should likely live in a separate file, but putting
    # validation + actions together for now

    def validate_lb_nodes(self, expected_nodes, system_nodes):
        """ We go through our list of expected nodes and compare them
            to our system nodes
        """
        error = 0
        error_list = []
        if len(expected_nodes) != len(system_nodes):
            error_list.append("ERROR: Node mismatch between request and api server detail: %s || %s" % (expected_nodes, system_nodes))
            error = 1
        for node in expected_nodes:
            match = 0
            for sys_node in system_nodes:
                if not match and node['address'] == sys_node['address'] and int(node['port']) == int(sys_node['port']):
                    match = 1
            if not match:
                error_list.append("ERROR: Node: %s has no match from api server" % (node))
                error = 1
        return error, error_list

    def validate_status(self, expected_status, actual_status):
        """ See what the result_dictionary status_code is and
            compare it to our expected result """

        if str(actual_status) == str(expected_status):
            result = True
        else:
            result = False
        return result

    def validate_lb_list(self, lb_name, loadbalancers):
        match = False
        for loadbalancer in loadbalancers:
            """
            if self.args.verbose:
                for key, item in loadbalancer.items():
                    self.logging.info('%s: %s' % (key, item))
            """
            if loadbalancer['name'] == lb_name[0:128]:  # api_server trims whitespace...
                    match = True
        return match

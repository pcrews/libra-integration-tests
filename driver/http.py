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

import ast
import json
import requests

class lbaasDriver:
    """ Driver to handle http interaction with the libra lbaas service
        Contains methods to call the various api methods as well as
        code for validating the actions

    """

    def __init__(self, args, api_user_url):
        """ TODO: put in validation and api-specific whatnot here """
        self.api_user_url = api_user_url
        self.user_name = args.osusername
        self.auth_url = args.osauthurl
        self.tenant_id = args.ostenantid
        self.password = args.ospassword
        self.auth_token = self.get_auth_token()
        self.api_headers = {"Content-Type": "application/json"
              ,"X-Auth-Token": "%s" %(self.auth_token) }
        return

    #------------------
    # utility functions
    #------------------
    def get_auth_token(self):
        """ Get our keystone auth token to work with the api server """
        request_data = {'auth':{ 'tenantId': self.tenant_id
                               , 'passwordCredentials':{'username': self.user_name
                                                       , 'password': self.password}
                               }
                       }
        request_data = json.dumps(request_data)
        headers = {"Content-Type": "application/json"}
        request_result = requests.post(self.auth_url, data=request_data, headers=headers, verify=False)
        request_data = ast.literal_eval(request_result.text)
        auth_token = request_data['access']['token']['id']
        return auth_token

    #-----------------
    # lbaas functions
    #-----------------
    def create_lb(self, name, nodes, algorithm, bad_statuses):
        """ Create a load balancer via the requests library 
            We expect the url to be the proper, fully constructed base url
            we add the 'loadbalancers suffix to the base 

            nodes is expected to be a list of nodes in this format:
            nodes = [{"address": "15.185.227.167","port": "80"},{"address": "15.185.227.165","port": "80"}]

        """
        url = "%s/loadbalancers" %self.api_user_url
        request_data = { "name": "%s" %name
                       , "nodes": nodes 
                       }
        lb_id = None
        if algorithm:
            request_data["algorithm"] = "%s" %algorithm
        request_data = json.dumps(request_data)
        request_result = requests.post(url, data=request_data, headers=self.api_headers, verify= False)
        result_data = ast.literal_eval(request_result.text)
        request_status = str(request_result.status_code)
        if request_status not in bad_statuses:
            lb_id = result_data['id']
        return request_result, request_status, lb_id

    def delete_lb(self, lb_id):
        """ Delete the loadbalancer identified by 'lb_id' """
        url = "%s/loadbalancers/%s" %(self.api_user_url, lb_id)
        request_result = requests.delete(url, headers=self.api_headers, verify=False)
        return request_result

    def list_lbs(self):
        """ List all loadbalancers for the given auth token / tenant id """

        url = "%s/loadbalancers" %self.api_user_url
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return ast.literal_eval(request_result.text)['loadBalancers']
 
    def list_lb_detail(self, lb_id):
        """ Get the detailed info returned by the api server for the specified id """

        url = "%s/loadbalancers/%s" %(self.api_user_url, lb_id)
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return ast.literal_eval(request_result.text)

    def list_lb_nodes(self, lb_id):
        """ Get list of nodes for the specified lb_id """
    
        url = "%s/loadbalancers/%s/nodes" %(self.api_user_url, lb_id)
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return ast.literal_eval(request_result.text)

    def update_lb(self, lb_id, update_data):
        """ We get a dictionary of update_data
            containing a new name, algorithm, or both
            and we execute an UPDATE API call and see
            what happens
        """
        url = "%s/loadbalancers/%s" %(self.api_user_url, lb_id)
        request_data = json.dumps(update_data)
        request_result = requests.put(url, data=request_data, headers=self.api_headers, verify=False)
        return ast.literal_eval(request_result.text), str(request_result.status_code)

    # validation functions
    # these should likely live in a separate file, but putting
    # validation + actions together for now 

    def validate_lb_nodes(self,expected_nodes, system_nodes):
        """ We go through our list of expected nodes and compare them
            to our system nodes
        """
        error = 0
        error_list = []
        if len(expected_nodes) != len(system_nodes):
            error_list.append("ERROR: Node mismatch between request and api server detail: %s || %s" %(nodes, system_nodes))
            error = 1
        for node in expected_nodes:
            match = 0
            for sys_node in system_nodes:
                if not match and node['address'] == sys_node['address'] and int(node['port']) == int(sys_node['port']):
                    match = 1
            if not match:
                error_list.append("ERROR: Node: %s has no match from api server" %(node))
                error_list.append("ERROR: %s" %vars(result))
                error = 1                
        return error, error_list

    def validate_status(self,expected_status, actual_status):
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
                    self.logging.info('%s: %s' %(key, item))
            """
            if loadbalancer['name'] == lb_name[0:128]: # api_server trims whitespace...
                    match = True
        return match


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

""" python-client.py
    methods for interacting with the lbaas service via python-libraclient requests

"""

import os
import ast
import json
import requests
import commands

class lbaasDriver:
    """ Driver to handle http interaction with the libra lbaas service
        Contains methods to call the various api methods as well as
        code for validating the actions

    """

    def __init__(self, args, api_user_url):
        """ TODO: put in validation and api-specific whatnot here """

        self.args = args
        self.api_user_url = api_user_url
        self.supported_algorithms = ['ROUND_ROBIN', 'LEAST_CONNECTIONS', None]
        self.user_name = args.osusername
        self.auth_url = args.osauthurl
        self.tenant_name = args.ostenantname
        self.password = args.ospassword
        self.good_status = args.successstatuscode
        self.verbose = args.verbose
        self.region_name = args.osregionname
        self.base_cmd = ("libra_client --os_auth_url=%s "
                         "--os_username=%s --os_password=%s "
                         "--os_tenant_name=%s  --os_region_name=%s") %(self.auth_url, self.user_name, self.password, self.tenant_name, self.region_name)
        if args. prodhack:
            #self.base_cmd += " --bypass_url=%s --insecure --service_type=compute " %(self.api_user_url)
            self.base_cmd += " --bypass_url=%s --insecure " %(self.api_user_url)
        # bit of a hack to eliminate some saltstack garbage we get with the client
        self.garbage_output = ['/usr/lib/python2.7/getpass.py:83: GetPassWarning: Can not control echo on the terminal.'
                              ,'passwd = fallback_getpass(prompt, stream)'
                              ,'Warning: Password input may be echoed.'
                              ,'Please set a password for your new keyring'
                              ]
        self.get_swift_credentials()
        return

    def get_swift_credentials(self):
        """ Get our keystone auth token to work with the api server """
        
        self.swift_endpoint = None
        headers = {"Content-Type": "application/json"}
        request_data = {'auth':{ 'tenantName': self.tenant_name
                               , 'passwordCredentials':{'username': self.user_name
                                                       , 'password': self.password}
                               }
                       }
        request_data = json.dumps(request_data)
        auth_url = self.auth_url
        if not self.auth_url.endswith('tokens'):
            auth_url = os.path.join(self.auth_url, 'tokens')
        request_result = requests.post(auth_url, data=request_data, headers=headers, verify=False)
        if self.verbose:
            print 'Status: %s' %request_result.status_code
            print 'Output:\n%s' %(request_result.text)
        request_data = ast.literal_eval(request_result.text)
        for service_data in request_data['access']['serviceCatalog']:
            if service_data['name'] == 'Object Storage':
                self.swift_endpoint = service_data['endpoints'][0]['publicURL'].replace('\\','')
        self.auth_token = request_data['access']['token']['id']
        self.tenant_id = request_data['access']['token']['tenant']['id']    
        return 

    def trim_garbage_output(self, output):
        for garbage_item in self.garbage_output:
            output = output.replace(garbage_item,'').strip()
        return output

    def execute_cmd(self, cmd):
        status, output = commands.getstatusoutput(cmd)
        output = self.trim_garbage_output(output)
        if self.verbose:
            print "Command: %s" %cmd
            print "Status: %s" %status
            print "Output:\n%s" %output
        return status, output

    def handle_client_side_errors(self, data, client_action=None, algorithm=None):
        # a bit of a hack for client-side handling of some bad requests
        # python-libraclient appears to detect / check and provide a 
        # 'you used me wrong' type of message vs. a 'from-the-api-server' error code
        status = '512' # default / what brought us here
        error_strings = [ "Invalid IP:port specified for --node"
                        , "Libra command line client %s: error: argument --algorithm: invalid choice: '%s'" %(client_action, algorithm)
                        ]
        for line in data:
            for error_string in error_strings:
                if error_string in line:
                    status = '400'
        return status

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

        lb_id = None
        ip_addr = None
        tcp_https_flag = False
        cmd = self.base_cmd + ' create --name="%s"' %name
        for node in nodes:
            node_info = ''
            address = ''
            port = ''
            if 'address' in node:
                address = node['address']
            if 'port' in node:
                port = node['port']
                if str(port) == '443':
                    tcp_https_flag = True
            cmd += ' --node=%s:%s' %(address, port)
        if algorithm:
            cmd += ' --algorithm=%s' %algorithm
        if tcp_https_flag:
            cmd += ' --protocol=TCP --port=443'
        if vip:
            cmd += ' --vip=%s' %vip
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        if len(data) >= 3 and algorithm in self.supported_algorithms:
            data = data[3]
            lb_data = data.split('|')
            lb_id = lb_data[1].strip()
            lb_stats = ast.literal_eval(lb_data[9].strip())
            lb_addr = lb_stats[0]['address']
            status = self.args.successstatuscode
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
        elif str(status) == '512':
            status = self.handle_client_side_errors(data, 'create', algorithm)
        else:
            data = data[0]
            if 'HTTP' in data:
                status = data.split('(HTTP')[1].strip().replace(')','')
        return output, status, lb_id, lb_addr # TODO detect error statuses!!!!!

    def delete_lb(self, lb_id):
        """ Delete the loadbalancer identified by 'lb_id' """

        if lb_id:
            cmd = self.base_cmd + ' delete --id=%s' %lb_id
            status, output = self.execute_cmd(cmd)
            return output

    def list_lbs(self):
        """ List all loadbalancers for the given auth token / tenant id """

        url = "%s/loadbalancers" %self.api_user_url
        cmd = self.base_cmd + ' list'
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        field_names = []
        for field_name in data[1].split('|')[1:-1]:
            field_names.append(field_name.strip().lower())
        loadbalancers = []
        data = output.split('\n')[3:-1] # get the 'meat' / data
        for lb_row in data:
            loadbalancer = {}
            lb_data = lb_row.split('|')[1:-1]
            for idx, lb_item in enumerate(lb_data):
                loadbalancer[field_names[idx]] = lb_item[1:-1]
            loadbalancers.append(loadbalancer)
        return loadbalancers

    def list_lb_detail(self, lb_id):
        """ Get the detailed info returned by the api server for the specified id """

        cmd = self.base_cmd + ' status --id=%s' %lb_id
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        field_names = []
        for field_name in data[1].split('|')[1:-1]:
            field_names.append(field_name.strip().lower())
        data = output.split('\n')[3:-1][0] # get the 'meat' / data and expect one line
        # expect a single line of detail data
        loadbalancer_detail = {}
        lb_data = data.split('|')[1:-1]
        for idx, lb_item in enumerate(lb_data):
            if field_names[idx] == 'nodes':
                loadbalancer_detail[field_names[idx]] = ast.literal_eval(lb_item.strip())
            else:
                loadbalancer_detail[field_names[idx]] = lb_item[1:-1]
        return loadbalancer_detail


    def list_lb_nodes(self, lb_id):
        """ Get list of nodes for the specified lb_id """
    
        cmd = self.base_cmd + ' node-list --id=%s' %lb_id
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        field_names = []
        for field_name in data[1].split('|')[1:-1]:
            field_names.append(field_name.strip().lower())
        node_dict = {}
        node_list = []
        data = output.split('\n')[3:-1] # get the 'meat' / data
        for node_row in data:
            node = {}
            node_data = node_row.split('|')[1:-1]
            for idx, node_item in enumerate(node_data):
                node[field_names[idx]] = node_item.strip()
            node_list.append(node)
        node_dict['nodes'] = node_list
        return node_dict

    def update_lb(self, lb_id, update_data):
        """ We get a dictionary of update_data
            containing a new name, algorithm, or both
            and we execute an UPDATE API call and see
            what happens
        """
        
        cmd = self.base_cmd + ' modify --id=%s' %(lb_id)
        if 'name' in update_data:
            cmd += ' --name="%s"' %update_data['name']
        if 'algorithm' in update_data:
            cmd += ' --algorithm=%s' %update_data['algorithm']
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        if output.strip() in ['',':']:
            status = self.good_status 
        elif str(status) == '512':
            status = self.handle_client_side_errors(data, 'modify', update_data['algorithm'])
        else:
            data = data[0]
            if 'HTTP' in data:
                status = data.split('(HTTP')[1].strip().replace(')','')
        return status

    def add_nodes(self, lb_id, add_node_data):
        """ We get a list of nodes we want to add and
            try to add them :)

        """
        cmd = self.base_cmd + ' node-add --id=%s' %(lb_id)
        for node in add_node_data:
            node_info = ''
            address = ''
            port = ''
            if 'address' in node:
                address = node['address']
            if 'port' in node:
                port = node['port']
                if str(port) == '443':
                    tcp_https_flag = True
            cmd += ' --node=%s:%s' %(address, port)
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        if 'HTTP' in data[0]:
                status = data[0].split('(HTTP')[1].strip().replace(')','')
        elif str(status) == '512':
            status = self.handle_client_side_errors(data)
        else: 
            status = self.good_status 
        return output, status

    def modify_node(self, lb_id, node_id, node_data):
        """ Set the node's condition to the value specified """

        cmd = self.base_cmd + ' node-modify --id=%s --nodeid=%s' %(lb_id, node_id)
        if 'condition' in node_data:
            cmd += ' --condition=%s' %(node_data['condition'])
        if 'address' in node_data or 'port' in node_data:
            # hack as client only allows node updates of condition...
            return '400'
        status, output = self.execute_cmd(cmd)
        data = output.split('\n')
        if 'HTTP' in data[0]:
                status = data[0].split('(HTTP')[1].strip().replace(')','')
        elif str(status) == '512':
            status = self.handle_client_side_errors(data)
        else: 
            status = '204' 
        return status

    def get_logs(self, lb_id, auth_token=None, obj_endpoint=None, obj_basepath=None):
        """ Get the logs / archive them for the listed lb_id """
        
        if auth_token:
            use_token = auth_token
        else:
            use_token = self.auth_token
        if obj_endpoint:
            use_endpoint = obj_endpoint
        else:
            use_endpoint = self.swift_endpoint
        if obj_basepath:
            use_basepath = obj_basepath
        cmd = self.base_cmd + ' logs --id=%s --token=%s --endpoint=%s --basepath=%s' %(lb_id, use_token, use_endpoint, use_basepath)
        status, output = self.execute_cmd(cmd)
        if not status:
            status='204'
        return status


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
            # This is a bit bobo, but we have variable whitespace
            # padding in client output depending on other names
            # that exist in the lb list and we test with whitespace
            # names.  Time to make this perfect isn't available, so
            # this works for the most part.
            if lb_name.strip() == loadbalancer['name'].strip():
                    match = True
        return match

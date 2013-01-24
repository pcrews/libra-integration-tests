""" python-client.py
    methods for interacting with the lbaas service via python-libraclient requests

"""

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
        self.api_user_url = api_user_url
        self.user_name = args.osusername
        self.auth_url = args.osauthurl
        self.tenant_name = args.ostenantname
        self.password = args.ospassword
        self.region_name = args.osregionname
        self.base_cmd = ("libra_client --os_auth_url=%s "
                         "--os_username=%s --os_password=%s "
                         "--os_tenant_name=%s  --os_region_name=%s") %(self.auth_url, self.user_name, self.password, self.tenant_name, self.region_name)
        return

    #-----------------
    # lbaas functions
    #-----------------
    def create_lb(self, name, nodes, algorithm):
        """ Create a load balancer via the requests library 
            We expect the url to be the proper, fully constructed base url
            we add the 'loadbalancers suffix to the base 

            nodes is expected to be a list of nodes in this format:
            nodes = [{"address": "15.185.227.167","port": "80"},{"address": "15.185.227.165","port": "80"}]

        """

        cmd = self.base_cmd + ' create --name=%s' %name
        for node in nodes:
            cmd += ' --node=%s:%s' %(node['address'], node['port'])
        if algorithm:
            cmd += ' --algorithm=%s' %algorithm
        status, output = commands.getstatusoutput(cmd)
        print cmd
        print status
        print output
        print '&'*80 
        return output

    def delete_lb(self, lb_id):
        """ Delete the loadbalancer identified by 'lb_id' """
        cmd = self.base_cmd + ' delete --id=%s' %lb_id
        status, output = commands.getstatusoutput(cmd)
        print status
        print output
        return output

    def list_lbs(self):
        """ List all loadbalancers for the given auth token / tenant id """

        url = "%s/loadbalancers" %self.api_user_url
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return request_result

    def list_lb_detail(self, lb_id):
        """ Get the detailed info returned by the api server for the specified id """

        url = "%s/loadbalancers/%s" %(self.api_user_url, lb_id)
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return request_result

    def list_lb_nodes(self, lb_id):
        """ Get list of nodes for the specified lb_id """
    
        url = "%s/loadbalancers/%s/nodes" %(self.api_user_url, lb_id)
        request_result = requests.get(url, headers=self.api_headers, verify=False)
        return request_result

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

    def validate_status(self,expected_status, result):
        """ See what the result_dictionary status_code is and
            compare it to our expected result """
        
        actual_status = str(vars(result)['status_code'])
        if actual_status == str(expected_status):
            result = True
        else:
            result = False
        return actual_status, result


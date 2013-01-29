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
        self.supported_algorithms = ['ROUND_ROBIN', 'LEAST_CONNECTIONS', None]
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
    def create_lb(self, name, nodes, algorithm, bad_statuses):
        """ Create a load balancer via the requests library 
            We expect the url to be the proper, fully constructed base url
            we add the 'loadbalancers suffix to the base 

            nodes is expected to be a list of nodes in this format:
            nodes = [{"address": "15.185.227.167","port": "80"},{"address": "15.185.227.165","port": "80"}]

        """

        lb_id = None
        cmd = self.base_cmd + ' create --name="%s"' %name
        for node in nodes:
            node_info = ''
            address = ''
            port = ''
            if 'address' in node:
                address = node['address']
            if 'port' in node:
                port = node['port']
            cmd += ' --node=%s:%s' %(address, port)
        if algorithm:
            cmd += ' --algorithm=%s' %algorithm
        status, output = commands.getstatusoutput(cmd)
        data = output.split('\n')
        if len(data) >= 3 and algorithm in self.supported_algorithms:
            data = data[3]
            lb_id = data.split('|')[1].strip()
            status = '200' 
        elif algorithm not in self.supported_algorithms:
            status = 'bad status: algorithm'
            # a bit of a hack for client-side handling of bad algorithms
            # python-libraclient appears to detect / check and provide a 
            # 'you used me wrong' type of message vs. a 'from-the-api-server' error code
            algo_error_string = "Libra command line client create: error: argument --algorithm: invalid choice: '%s'" %algorithm
            for line in data:
                if algo_error_string in line:
                    status = '400'   
        else:
            data = data[0]
            if 'HTTP' in data:
                status = data.split('(HTTP')[1].strip().replace(')','')
        return output, status, lb_id # TODO detect error statuses!!!!!

    def delete_lb(self, lb_id):
        """ Delete the loadbalancer identified by 'lb_id' """

        if lb_id:
            cmd = self.base_cmd + ' delete --id=%s' %lb_id
            status, output = commands.getstatusoutput(cmd)
            return output

    def list_lbs(self):
        """ List all loadbalancers for the given auth token / tenant id """

        url = "%s/loadbalancers" %self.api_user_url
        cmd = self.base_cmd + ' list'
        status, output = commands.getstatusoutput(cmd)
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
        status, output = commands.getstatusoutput(cmd)
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
        status, output = commands.getstatusoutput(cmd)
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


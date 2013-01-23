""" http.py
    methods for interacting with the lbaas service via http requests

"""
import json
import requests

class lbaasDriver:
    """ Driver to handle http interaction with the libra lbaas service
        Contains methods to call the various api methods as well as
        code for validating the actions

    """

    def __init__(self):
        """ TODO: put in validation and api-specific whatnot here """
        return

    #-----------------
    # lbaas functions
    #-----------------
    def create_lb(self, url, name, nodes, headers):
        """ Create a load balancer via the requests library 
            We expect the url to be the proper, fully constructed base url
            we add the 'loadbalancers suffix to the base 

            nodes is expected to be a list of nodes in this format:
            nodes = [{"address": "15.185.227.167","port": "80"},{"address": "15.185.227.165","port": "80"}]

        """
        url = "%s/loadbalancers" %url
        request_data = { "name": "%s" %name
                       , "nodes": nodes 
                       }
        request_data = json.dumps(request_data)
        request_result = requests.post(url, data=request_data, headers=headers, verify= False)
        return request_result

    def delete_lb(self,url, lb_id, headers):
        """ Delete the loadbalancer identified by 'lb_id' """
        url = "%s/loadbalancers/%s" %(url, lb_id)
        request_result = requests.delete(url, headers=headers, verify=False)
        return request_result

    def list_lbs(self,url, headers):
        """ List all loadbalancers for the given auth token / tenant id """

        url = "%s/loadbalancers" %url
        request_result = requests.get(url, headers=headers, verify=False)
        return request_result

    def list_lb_detail(self,url, lb_id, headers):
        """ Get the detailed info returned by the api server for the specified id """

        url = "%s/loadbalancers/%s" %(url, lb_id)
        request_result = requests.get(url, headers=headers, verify=False)
        return request_result

    def list_lb_nodes(self,url, lb_id, headers):
        """ Get list of nodes for the specified lb_id """
    
        url = "%s/loadbalancers/%s/nodes" %(url, lb_id)
        request_result = requests.get(url, headers=headers, verify=False)
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


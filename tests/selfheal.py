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
import time
import commands
import unittest
import requests

import lbaas_utils

class testRecreateLoadBalancer(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=200
                ):
        super(testRecreateLoadBalancer, self).__init__(testname)
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

    def report_info(self):
        """ function for dumping info on test failures """
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
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
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    

    def test_createLoadBalancer(self):
        """ test creation of loadbalancers for libra
        """
        # Create our loadbalancer
        self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
        self.logging.info('load balancer id: %s' %self.lb_id)
        self.logging.info('load balancer ip addr: %s' %self.lb_addr)
        lbaas_utils.validate_loadBalancer(self)

        # get the device id for our loadbalancer
        cmd = 'salt --output=pprint \%s mysql.query lbaas "SELECT devices.name from devices JOIN loadbalancers_devices on devices.id = loadbalancers_devices.device WHERE loadbalancers_devices.loadbalancer=%s"' %(self.args.lbaasdbserver, self.lb_id)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)
        data = ast.literal_eval(output)
        nova_name = data[self.args.lbaasdbserver]['results'][0][0].strip()
        self.logging.info("Loadbalancer: %s nova name: %s" %(self.lb_id, nova_name))

        cmd ='nova --insecure --os-username=%s --os-tenant-id=%s --os-region-name=%s --os-password=%s --os-auth-url=%s list' %(self.args.nodesusername, self.args.nodestenantid, self.args.nodesregionname, self.args.nodespassword, self.args.nodesauthurl)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        #self.logging.info("Output: %s" %output)
        node_list = output.split('\n')[3:-1]
        for node_line in node_list:
            node_data = node_line.split('|')
            id =  node_data[1].strip()
            name =  node_data[2].strip()
            status =  node_data[3].strip()
            task_state = node_data[4].strip()
            if name == nova_name:
                self.logging.info(node_line)
                nova_id = id
                break

        self.logging.info("Nova id for lb: %s: %s" %(self.lb_id, nova_id))
        self.logging.info("Deleting nova node for lb: %s..." %(self.lb_id))
        cmd ='nova --insecure --os-username=%s --os-tenant-id=%s --os-region-name=%s --os-password=%s --os-auth-url=%s delete %s' %(self.args.nodesusername, self.args.nodestenantid, self.args.nodesregionname, self.args.nodespassword, self.args.nodesauthurl, nova_id)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)
        self.logging.info("Sleeping 30 seconds...")
        time.sleep(30)
        time_wait = 1
        attempts_remain = 100
        max_time = 3000
        lb_ready = False
        suspected_bad = False
        start_time = time.time()
        self.logging.info("Testing loadbalancer, expecting no results / will wait for repair...")
        while not lb_ready and attempts_remain and ((time.time()-start_time) <= max_time):
                try:
                    if attempts_remain%10 ==0:
                        self.logging.info("Attempts remaining: %d" %attempts_remain)
                    lb_url = 'http://%s' %(self.lb_addr)
                    result = requests.get(lb_url, verify= False)
                    if result:
                        lb_ready=True
                except Exception, e:
                    if not suspected_bad:
                        suspected_bad = True
                        self.logging.info(Exception)
                        self.logging.info(e)
                        self.logging.info("Will try up to: %d times for the loadbalancer to be functional (~10 minutes), please be patient..." %(attempts_remain*time_wait))
                    time.sleep(time_wait)
                    attempts_remain -= 1
        stop_time = time.time()
        expended_time = stop_time - start_time
        self.logging.info("Time for loadbalancer: %s to be ready: %f" %(self.lb_id, expended_time))


    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
        result = self.driver.delete_lb(self.lb_id)






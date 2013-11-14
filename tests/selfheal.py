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

    def grep_for_info(self, lb_id=None, device_name=None):
        cmd = 'sudo salt \%s cmd.run "cat /var/log/libra/admin*log | grep %s"'
        cmd = 'sudo salt \%s cmd.run "cat /var/log/libra/pool*log | grep %s"'
        return

    def get_nova_name(self, quiet=False):
        cmd = 'salt --output=pprint \%s mysql.query lbaas "SELECT devices.name from devices JOIN loadbalancers_devices on devices.id = loadbalancers_devices.device WHERE loadbalancers_devices.loadbalancer=%s"' %(self.args.lbaasdbserver, self.lb_id)
        status, output = commands.getstatusoutput(cmd)
        if not quiet:
            self.logging.info("")
            self.logging.info("Getting nova id for loadbalancer: %s..." %(self.lb_id))
            self.logging.info("Command: %s" %cmd)
            self.logging.info("Status: %s" %status)
            self.logging.info("Output: %s" %output)
        data = ast.literal_eval(output)
        nova_name = data[self.args.lbaasdbserver]['results'][0][0].strip()
        if not quiet:
            self.logging.info("Loadbalancer: %s nova name: %s" %(self.lb_id, nova_name))
            self.logging.info("")
        return nova_name

    def get_nova_id(self, nova_name, quiet=False):
        nova_id = None
        cmd ='nova --insecure --os-username=%s --os-tenant-id=%s --os-region-name=%s --os-password=%s --os-auth-url=%s list' %(self.args.nodesusername, self.args.nodestenantid, self.args.nodesregionname, self.args.nodespassword, self.args.nodesauthurl)
        status, output = commands.getstatusoutput(cmd)
        if not quiet:
            self.logging.info("")
            self.logging.info("Getting nova id for nova node: %s..." %(nova_name))
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
                if not quiet:
                    self.logging.info(node_line)
                    self.logging.info("")
                nova_id = id
                break
        return nova_id

    def check_floating_ip(self, quiet=False):
        cmd ='nova --insecure --os-username=%s --os-tenant-id=%s --os-region-name=%s --os-password=%s --os-auth-url=%s floating-ip-list | grep %s' %(self.args.nodesusername, self.args.nodestenantid, self.args.nodesregionname, self.args.nodespassword, self.args.nodesauthurl, self.lb_addr)
        status, output = commands.getstatusoutput(cmd)
        if not quiet:
            self.logging.info("")
            self.logging.info("Nova info for floating ip: %s, lb_id: %s..." %(self.lb_addr, self.lb_id))
            self.logging.info("Command: %s" %cmd)
            self.logging.info("Status: %s" %status)
            self.logging.info("Output: %s" %output)
            self.logging.info("")
        return output

    def get_floating_ip(self, lb_id, quiet=False):
        ip_addr = None
        cmd = 'salt --output=pprint \%s mysql.query lbaas "select inet_ntoa(ip) from loadbalancers_devices JOIN vips ON loadbalancers_devices.device = vips.device WHERE loadbalancer=%s"' %(self.args.lbaasdbserver, self.lb_id)
        status, output = commands.getstatusoutput(cmd)
        if not quiet:
            self.logging.info("="*80)
            self.logging.info("")
            self.logging.info("Getting floating ip for loadbalancer: %s..." %(self.lb_id))
            self.logging.info("Command: %s" %cmd)
            self.logging.info("Status: %s" %status)
            self.logging.info("Output: %s" %output)
        data = ast.literal_eval(output)
        ip_addr = data[self.args.lbaasdbserver]['results'][0][0].strip()
        self.logging.info("Floating ip for loadbalancer: %s: %s" %(lb_id, ip_addr))
        self.logging.info("="*80)
        return ip_addr

    def setUp(self):
        ###########################
        # test healing a load balancer
        ###########################
        print ''
        self.logging.info("Setting up for testcase:")
        report_values = ['test_description','lb_name', 'nodes', 'expected_status']
        for report_value in report_values:
            self.logging.info("  - %s: %s" %(report_value, getattr(self,report_value)))
        if self.args.verbose:
            self.logging.info("name: %s" %self.lb_name)
            self.logging.info("nodes: %s" %self.nodes)    

    def test_healLoadBalancer(self):
        """ test creation of loadbalancers for libra
        """
        
        # Create our loadbalancer
        if not self.args.lbid:
            self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
            self.logging.info('load balancer id: %s' %self.lb_id)
            self.logging.info('load balancer ip addr: %s' %self.lb_addr)
            lbaas_utils.validate_loadBalancer(self)
        else:
            self.logging.info("Using user-supplied loadbalancer: %s" %self.args.lbid)
            self.lb_id = self.args.lbid
            self.lb_addr = self.get_floating_ip(self.lb_id)

        # wait a bit if we want to show off
        if self.args.demowaittime:
            self.logging.info("Sleeping %s seconds for demo / manual testing" %self.args.demowaittime)
            time.sleep(self.args.demowaittime)

        # get the nova name for our loadbalancer
        orig_nova_name = self.get_nova_name()

        # get nova id
        orig_nova_id = self.get_nova_id(orig_nova_name)

        # check floating_ip
        floating_ip_output = self.check_floating_ip()

        # use our nova info and delete the haproxy vm
        nova_sleep = 15
        self.logging.info("-"*80)
        self.logging.info("Nova info for loadbalancer: %s, ip_addr: %s" %(self.lb_id, self.lb_addr))
        self.logging.info("Nova name: %s" %orig_nova_name)
        self.logging.info("Nova id: %s" %orig_nova_id)
        self.logging.info("Floating ip data: %s" %floating_ip_output)
        self.logging.info("-"*80)
        self.logging.info("")
        self.logging.info("Deleting nova node for lb: %s..." %(self.lb_id))
        cmd ='nova --insecure --os-username=%s --os-tenant-id=%s --os-region-name=%s --os-password=%s --os-auth-url=%s delete %s' %(self.args.nodesusername, self.args.nodestenantid, self.args.nodesregionname, self.args.nodespassword, self.args.nodesauthurl, orig_nova_id)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)
        self.logging.info("Sleeping %s seconds for nova delete to take effect..." %nova_sleep)
        # TODO: add in nova list verification of no node (?)
        # TODO: test the database for the device?
        time.sleep(nova_sleep)
        time_wait = 1
        attempts_remain = 100
        max_time = 600
        lb_ready = False
        suspected_bad = False
        first_run = True
        start_time = time.time()
        new_nova_name = orig_nova_name
        new_nova_id = orig_nova_id
        self.logging.info("Scanning nova and libra database for vm / loadbalancer status...")
        while not lb_ready and attempts_remain and ((time.time()-start_time) <= max_time):
            # get new nova name
            new_nova_name = self.get_nova_name(quiet=True)
            # get new nova id / check floating ip
            new_nova_id = self.get_nova_id(new_nova_name, quiet=True)
            # check floating ip
            floating_ip_output = self.check_floating_ip(quiet=True)
            if attempts_remain%10 ==0 and not first_run:
                self.logging.info("-"*80)
                self.logging.info("Status check:")
                self.logging.info("Attempts remaining: %d" %attempts_remain)
                self.logging.info("Time waited: %f" %(time.time() - start_time))
                self.logging.info("Nova name: %s" %new_nova_name)
                self.logging.info("Nova id: %s" %new_nova_id)
                self.logging.info("Floating ip data: %s" %floating_ip_output)
                self.logging.info("-"*80)
                self.logging.info("")
            if new_nova_name != orig_nova_name and new_nova_id and new_nova_id in floating_ip_output:
                self.logging.info("-"*80)
                self.logging.info("New nova node has been assigned loadbalancer: %s's floating ip" %(self.lb_id))
                self.logging.info("-"*80)
                self.logging.info("")
                lb_ready = True
            else:
                suspected_bad = True
                if first_run:
                    self.logging.info("Will try up to: %d times for the loadbalancer to be functional (~%d minutes), please be patient..." %(attempts_remain*time_wait, (max_time/60)))
                    first_run = False
            time.sleep(time_wait)
            attempts_remain -= 1
        stop_time = time.time()
        expended_time = stop_time - start_time
        self.logging.info("Time for loadbalancer: %s to be ready: %f" %(self.lb_id, expended_time))
        self.logging.info("-")*80
        self.logging.info("New nova attributes:")
        # list new nova name
        new_nova_name = self.get_nova_name()
        self.logging.info("Original nova name: %s" %orig_nova_name)
        # get new nova id / check floating ip
        new_nova_id = self.get_nova_id(new_nova_name)
        self.logging.info("Original nova id: %s" %orig_nova_id)
        # check floating ip
        self.check_floating_ip()
        self.logging.info("-")*80
        self.logging.info("")
        self.logging.info("")
        self.assertTrue(lb_ready, msg = "WARNING: loadbalancer %s not ready in %f seconds" %(self.lb_id, expended_time))
        if not self.args.lbid:
            lbaas_utils.validate_loadBalancer(self)
        # wait a bit if we want to show off
        if self.args.demowaittime:
            self.logging.info("Sleeping %s seconds for demo / manual testing" %self.args.demowaittime)
            time.sleep(self.args.demowaittime)

    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        if not self.args.lbid:
            self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
            result = self.driver.delete_lb(self.lb_id)
        else:
            self.logging.info("Used user-specified loadbalancer: %s, not attempting to cleanup..." %self.lb_id)






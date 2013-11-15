# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

class testBetaRayBill(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=200
                ):
        super(testBetaRayBill, self).__init__(testname)
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

    def test_BetaRayBill(self):
        """ multiple clients beat on a loadbalancer
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
        # create our hammer-time minions
        self.logging.info("Creating salt minions...")
        cmd = 'salt-cloud -C%s -m%s -y' %(self.args.cloudconfig, self.args.cloudmap)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)

        # configure them
        self.logging.info("Configuring our hellish minions...mwa ha ha")
        cmd = 'salt *lbaas-hellraiser* state.highstate'
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)

        # start the hammer-storm!
        self.logging.info("Stop!")
        self.logging.info("Hammer time!")
        self.logging.info("Beginning test runs on minions...")
       
        test_url = 'https://%s/cgi-bin/wait_wait.py' %(self.lb_addr)
        cmd = 'salt *lbaas-hellraiser* cmd.run cwd=/home/ubuntu "python hellraiser.py %s"' %(test_url)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)

        # validate the loadbalancer
        lbaas_utils.validate_loadBalancer(self)


    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        if not self.args.lbid:
            self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
            result = self.driver.delete_lb(self.lb_id)
        else:
            self.logging.info("Used user-specified loadbalancer: %s, not attempting to cleanup..." %self.lb_id)
        # wipe out our cloud minions
        self.logging.info("Cleaning up cloud minions...")
        cmd = 'salt-cloud -d -C%s -m%s -y' %(self.args.cloudconfig, self.args.cloudmap)
        status, output = commands.getstatusoutput(cmd)
        self.logging.info("Command: %s" %cmd)
        self.logging.info("Status: %s" %status)
        self.logging.info("Output: %s" %output)





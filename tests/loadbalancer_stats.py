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
import unittest
import requests
import lbaas_utils

class testLoadBalancerStats(unittest.TestCase):

    def __init__( self, test_description, args, logging, driver
                , testname, lb_name, nodes, lb_id=None
                , algorithm = None, expected_status=200
                ):
        super(testLoadBalancerStats, self).__init__(testname)
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
        """ gathering time until we have a good loadbalancer and counting bad devices
        """
        iterations = []
        bad_iterations = []
        failed_iterations = []
        bad_count = 0
        fail_count = 0
        test_iterations=100
        for i in range(test_iterations):
            self.logging.info("Iteration: %d" %i)
            # Create our loadbalancer
            lb_ready = False
            suspected_bad = False
            time_wait = 1
            attempts_remain = 100
            max_time = 300
            start_time = time.time()
            self.create_result, self.actual_status, self.lb_id, self.lb_addr = self.driver.create_lb(self.lb_name, self.nodes, self.algorithm, self.bad_statuses)
            self.logging.info('load balancer id: %s' %self.lb_id)
            self.logging.info('load balancer ip addr: %s' %self.lb_addr)
            lbaas_utils.wait_for_active_status(self, must_pass=False)
            # make sure we can get traffic from our loadbalancer
            self.logging.info(time.time()-start_time)
            self.logging.info((time.time()-start_time) < max_time)
            while not lb_ready and attempts_remain and ((time.time()-start_time) <= max_time):
                try:
                    if attempts_remain%10 ==0:
                        self.logging.info("Attempts remaining: %d" %attempts_remain)
                    lb_url = 'http://%s' %(self.lb_addr)
                    result = requests.get(lb_url, verify= False)
                    result.connection.close()
                    if result:
                        lb_ready=True
                except Exception, e:
                    if not suspected_bad:
                        self.logging.info(Exception)
                        self.logging.info(e)
                        self.logging.info("loadbalancer id: %s not yet ready.  Suspected bad haproxy device" %(self.lb_id))
                        self.logging.info("Will try up to: %d times for the loadbalancer to be functional (~10 minutes), please be patient..." %(attempts_remain*time_wait))
                        suspected_bad = True
                        bad_count += 1
                    time.sleep(time_wait)
                    attempts_remain -= 1
            stop_time = time.time()
            expended_time = stop_time - start_time
            self.logging.info("Time for loadbalancer: %s to be ready: %f" %(self.lb_id, expended_time))
            if suspected_bad:
                if ((expended_time) <= max_time):
                    bad_iterations.append(expended_time)
                else:
                    failed_iterations.append(expended_time)
            else:
                iterations.append(expended_time)
            if attempts_remain and ((expended_time) <= max_time):
                lbaas_utils.validate_loadBalancer(self)
            else:
                self.logging.info("WARN: loadbalancer: %s suspected still not ready after %d seconds" %(self.lb_id, expended_time))
                fail_count += 1
            self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
            result = self.driver.delete_lb(self.lb_id)
            time.sleep(10)


        self.logging.info('#'*80)
        self.logging.info("Run stats:")
        self.logging.info(iterations)
        self.logging.info(bad_iterations)
        self.logging.info("Bad loadbalancers: %d" %bad_count)
        self.logging.info("Failed (bad) loadbalancers: %d" %fail_count)

        self.logging.info("Iterations: %d" %(len(iterations)))
        avg_value = 0
        for iteration in iterations:
            avg_value += iteration
        avg_value = float(avg_value)/float(len(iterations))
        self.logging.info("All iterations average: %f" %(avg_value))
        self.logging.info("All iterations max: %f" %(max(iterations)))
        self.logging.info("All iterations min: %f" %(min(iterations)))

        avg_value = 0
        self.logging.info("Bad iterations: %d" %(len(bad_iterations)))
        for iteration in bad_iterations:
            avg_value += iteration
        if avg_value:
            avg_value = float(avg_value)/float(len(bad_iterations))
        self.logging.info("Bad iterations average: %f" %(avg_value))
        self.logging.info("Bad iterations max: %f" %(max(bad_iterations)))
        self.logging.info("Bad iterations min: %f" %(min(bad_iterations)))

        avg_value = 0
        self.logging.info("Failed iterations: %d" %(len(failed_iterations)))
        for iteration in failed_iterations:
            avg_value += iteration
        if avg_value:
            avg_value = float(avg_value)/float(len(failed_iterations))
        self.logging.info("Failed iterations average: %f" %(avg_value))
        self.logging.info("Failed iterations max: %f" %(max(failed_iterations)))
        self.logging.info("Failed iterations min: %f" %(min(failed_iterations)))

    def tearDown(self):
        ##########################
        # delete the load balancer
        ##########################
        self.logging.info("Deleting loadbalancer: %s" %self.lb_id)
        result = self.driver.delete_lb(self.lb_id)






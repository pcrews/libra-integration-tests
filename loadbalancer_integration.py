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

""" test_loadbalancer.py
    a test to put a loadbalancer node through its paces
    in an end-to-end system.

"""

import os
import sys
import ast
import imp
import yaml
import unittest
import logging
import requests
import argparse

from tests.loadbalancer_functions import testLoadBalancerFuncs
from tests.create_loadbalancer import testCreateLoadBalancer
from tests.update_loadbalancer import testUpdateLoadBalancer
from tests.add_nodes import testAddNodes
from tests.modify_nodes import testModifyNode
from tests.multi_loadbalancer import testMultiLoadBalancer
from tests.loadbalancer_logs import testLoadBalancerLogs
from tests.monitor_stage1 import testMonitorStage1
from tests.loadbalancer_siege import testLoadBalancerSiege
from tests.loadbalancer_apache import testLoadBalancerApache

##########
# parser
##########
parser = argparse.ArgumentParser(description='test_loadbalancer_operations.py - integration test suite for libra lbaas service')
parser.add_argument( '--verbose'
                   , action = 'count'
                   , dest = 'verbose'
                   , default = 0
                   , help = 'Controls internal output.  Utilize multiple times to increase output'
                   )
parser.add_argument( '--driver'
                   , choices=['http','python-client']
                   , dest = 'driver'
                   , default = 'http'
                   , help = 'Method for interacting with the lbaas service'
                   )
parser.add_argument( '--variants_module'
                   , dest = 'variant_module'
                   , default = 'combined_inputs.dat'
                   , help = 'Module containing test inputs'
                   )
parser.add_argument( '--os_username'
                   , action = 'store'
                   , dest ='osusername'
                   , default = None
                   , help = 'OpenStack username to use for testing.'
                   )
parser.add_argument( '--os_password'
                   , action = 'store'
                   , dest = 'ospassword'
                   , default = None
                   , help = 'OpenStack password for os-username'
                   )
parser.add_argument( '--os_tenant_name'
                   , action = 'store'
                   , dest = 'ostenantname'
                   , default = None
                   , help = 'OpenStack tenant name'
                   )
parser.add_argument( '--os_region_name'
                   , action = 'store'
                   , dest = 'osregionname'
                   , default = None
                   , help = 'OpenStack region name (for python-libraclient).  Ex: region-b.geo-1 (no az.)'
                   )
parser.add_argument( '--os_auth_url'
                   , action = 'store'
                   , dest = 'osauthurl'
                   , default = 'https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/tokens'
                   , help = 'OpenStack auth url (keystone endpoint)'
                   )
parser.add_argument( '--lbaas_api_url'
                   , action = 'store'
                   , dest = 'lbaasapiurl'
                   , default = None
                   , help = 'url for the lbaas api server'
                   )
parser.add_argument( '--lbaas_admin_port'
                   , action = 'store'
                   , dest = 'lbaasadminport'
                   , default = '8889'
                   , help = 'lbaas admin port'
                   )
parser.add_argument( '--lbaas_user_port'
                   , action = 'store'
                   , dest = 'lbaasuserport'
                   , default = '443'
                   , help = 'lbaas user port'
                   )
parser.add_argument( '--lbaas_admin_version'
                   , action = 'store'
                   , dest = 'lbaasadminversion'
                   , default = 'v1'
                   , help = 'version string for admin api'
                   )
parser.add_argument( '--lbaas_user_version'
                   , action = 'store'
                   , dest = 'lbaasuserversion'
                   , default = 'v1.1'
                   , help = 'version string for user api'
                   )
parser.add_argument( '--prod_hack'
                   , action = 'store_true'
                   , dest = 'prodhack'
                   , default = False
                   , help = 'flag to use with test / dev systems'
                   )
parser.add_argument( '--max_backend_nodes'
                   , action = 'store'
                   , dest = 'maxbackendnodes'
                   , default = 50
                   , help = 'maximum number of backend nodes allowed per load balancer'
                   , type = int
                   )
parser.add_argument( '--success_status_code'
                   , action = 'store'
                   , dest = 'successstatuscode'
                   , default = 202
                   , help = 'Status code we expect on success'
                   )
parser.add_argument( '--bad_status'
                   , action = 'store'
                   , dest = 'badstatus'
                   , default =  None
                   , help = 'hack to set an expected bad status - implemented due to bug returning 500s vs. expected bad statuses'
                   )
parser.add_argument( '--active_wait_time'
                   , action = 'store'
                   , type=int
                   , dest = 'activewaittime'
                   , default = 60
                   , help = 'seconds to wait for a loadbalancer to achieve ACTIVE status'
                   )
parser.add_argument( '--active_pause'
                   , action = 'store'
                   , type=int
                   , dest = 'activepause'
                   , default = 0
                   , help = 'seconds to wait *after* a loadbalancer has achieved ACTIVE status before proceeding with testing'
                   )
parser.add_argument( '--swift_user'
                   , action = 'store'
                   , dest = 'swiftuser'
                   , default = None
                   , help = 'username for object storage (for haproxy log archiving).  Defaults to lbaas_user'
                   )
parser.add_argument( '--swift_pw'
                   , action = 'store'
                   , dest = 'swiftpw'
                   , default = None
                   , help = 'username for object storage (for haproxy log archiving).  Defaults to lbaas_pw'
                   )
parser.add_argument( '--swift_tenant_name'
                   , action = 'store'
                   , dest = 'swifttenantname'
                   , default = None
                   , help = 'username for object storage (for haproxy log archiving).  Defaults to lbaas_tenant_name'
                   )
parser.add_argument( '--swift_basepath'
                   , action = 'store'
                   , dest = 'swiftbasepath'
                   , default = 'libra_test_logs'
                   , help = 'username for object storage (for haproxy log archiving).  Defaults to lbaas_tenant_name'
                   )
parser.add_argument( '--cleanup_off'
                   , action = 'store_true'
                   , dest = 'cleanupoff'
                   , default = False
                   , help = 'Turns off post-test cleanup (for some tests).  Used to automate workloads on vms we want to study afterwards'
                   )

#######
# main
#######  
args = parser.parse_args(sys.argv[1:])
if args.verbose:
    logging.info("VERBOSE: argument values:")
    for key, item in vars(args).items():
        logging.info("VERBOSE: %s || %s" %(key, item))

# configure logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y%m%d-%H%M%S %p', level=logging.INFO)
# disable INFO-level logging for the requests library...it is noise here
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

############
# variables:
############
driver_path = 'driver'
api_base_url = args.lbaasapiurl
api_admin_url = None
api_user_url = None
if api_base_url:
    api_admin_url = "%s:%s/%s" %(api_base_url, args.lbaasadminport, args.lbaasadminversion)
    api_user_url = "%s:%s/%s" %(api_base_url, args.lbaasuserport, args.lbaasuserversion)

# load our specific driver
driver_module = imp.load_source( args.driver
                        , os.path.join(driver_path, args.driver+'.py'))
driver = driver_module.lbaasDriver( args, api_user_url)



##################################
# test away!
##################################

testloader = unittest.TestLoader()
suite = unittest.TestSuite()

# get our test input variants (nodes, names, etc)
inputs_file = open(args.variant_module,'r')
test_inputs = yaml.load(inputs_file)
inputs_file.close()

#########################
# full functional tests
#########################

# testing full functional test variants 
testnames = testloader.getTestCaseNames(testLoadBalancerFuncs)
for test_name in testnames:
    if 'full_func_variants' in test_inputs:
        for test_variant in test_inputs['full_func_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testLoadBalancerFuncs( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_variant['name']
                                                , test_inputs['default_values']['default_nodes']
                                                , expected_status = expected_status
                                                , functional_inputs = test_inputs['functional_inputs']
                                                , test_nodes = test_inputs['default_values']['nodes']))

#####################
# create lb variants
#####################

testnames = testloader.getTestCaseNames(testCreateLoadBalancer)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'lb_name_variants' in test_inputs:
        for test_variant in test_inputs['lb_name_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testCreateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_variant['name']
                                                , test_inputs['default_values']['default_nodes']
                                                , expected_status = expected_status))

    # testing lb node variants
    if 'node_variants' in test_inputs:
        for test_variant in test_inputs['node_variants']:
            if 'nodes' in test_variant:
                nodes = test_variant['nodes']
            else:
                node_count = test_variant['node_count']
                if str(test_variant['node_count']).startswith('MAX_BACKEND_COUNT'):
                    node_count = int(args.maxbackendnodes)
                    if str(test_variant['node_count']).endswith('+1'):
                        node_count += 1
                node_pool = test_inputs['default_values']['nodes']
                # we have a node_count value and pull from default_values['nodes']
                if node_count < len(node_pool):
                    nodes = node_pool[:node_count]
                else:
                    nodes = []
                    idx = 0
                    should_continue = True
                    while len(nodes) < node_count:
                        nodes.append(node_pool[idx])
                        idx += 1
                        if idx == len(node_pool):
                            idx = 0
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testCreateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , nodes
                                                , expected_status = expected_status))
    # algorithm variants
    if 'algorithm_variants' in test_inputs:
        for test_variant in test_inputs['algorithm_variants']:
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testCreateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , test_inputs['default_values']['default_nodes']
                                                , algorithm = test_variant['algorithm']
                                                , expected_status = expected_status))
#########################
# update operation tests
#########################
testnames = testloader.getTestCaseNames(testUpdateLoadBalancer)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'update_variants' in test_inputs:
        for test_variant in test_inputs['update_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testUpdateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , test_inputs['default_values']['default_nodes']
                                                , test_variant['update_data']
                                                , expected_status = expected_status))


###################
# add node tests
###################
testnames = testloader.getTestCaseNames(testAddNodes)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'add_node_variants' in test_inputs:
        for test_variant in test_inputs['add_node_variants']:
          if 'skip_test' not in test_variant or test_variant['skip_test'] != args.driver:
            nodes = []
            if 'nodes' in test_variant:
                nodes = test_variant['nodes']
            else:
                node_count = test_variant['node_count']
                if str(test_variant['node_count']).startswith('MAX_BACKEND_COUNT'):
                    node_count = int(args.maxbackendnodes) - len(test_inputs['default_values']['default_nodes'])
                    if str(test_variant['node_count']).endswith('+1'):
                        node_count += 1
                node_pool = test_inputs['default_values']['nodes']
                # we have a node_count value and pull from default_values['nodes']
                if node_count < len(node_pool):
                    nodes = node_pool[:node_count]
                else:
                    nodes = []
                    idx = 0
                    should_continue = True
                    while len(nodes) < node_count:
                        nodes.append(node_pool[idx])
                        idx += 1
                        if idx == len(node_pool):
                            idx = 0
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testAddNodes( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , test_inputs['default_values']['default_nodes']
                                                , nodes
                                                , expected_status = expected_status))
######################
# modify node tests
######################
testnames = testloader.getTestCaseNames(testModifyNode)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'modify_variants' in test_inputs:
        for test_variant in test_inputs['modify_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testModifyNode( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , test_inputs['default_values']['default_nodes']
                                                , expected_status = expected_status))

# multi_loadbalancer tests:
testnames = testloader.getTestCaseNames(testMultiLoadBalancer)
for test_name in testnames:
    # testing lb name variants 
    if 'multiLB_variants' in test_inputs:
        for test_variant in test_inputs['multiLB_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testMultiLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_variant['name1']
                                                , test_variant['name2']
                                                , test_variant['nodes1']
                                                , test_variant['nodes2']
                                                , expected_status = expected_status))

# log archive tests
testnames = testloader.getTestCaseNames(testLoadBalancerLogs)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'log_variants' in test_inputs:
        for test_variant in test_inputs['log_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testLoadBalancerLogs( test_variant['description'], args, logging, driver
                                              , test_name
                                              , test_variant['name']
                                              , test_variant['nodes']
                                              , expected_status = expected_status))

# monitor stage 1 tests
testnames = testloader.getTestCaseNames(testMonitorStage1)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'monitor1_variants' in test_inputs:
        for test_variant in test_inputs['monitor1_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testMonitorStage1( test_variant['description'], args, logging, driver
                                              , test_name
                                              , test_variant['name']
                                              , test_variant['nodes']
                                              , expected_status = expected_status))

#########################
# siege tests
#########################
testnames = testloader.getTestCaseNames(testLoadBalancerSiege)
for test_name in testnames:
    if 'siege_variants' in test_inputs:
        for test_variant in test_inputs['siege_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testLoadBalancerSiege( test_variant['description'], args, logging, driver
                                               , test_name
                                               , test_variant['name']
                                               , test_inputs['default_values']['nodes']
                                               , expected_status = expected_status))

#########################
# apache tests
#########################
testnames = testloader.getTestCaseNames(testLoadBalancerApache)
for test_name in testnames:
    if 'apache_variants' in test_inputs:
        for test_variant in test_inputs['apache_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            if 'expected_status' in test_variant:
                expected_status = test_variant['expected_status']
            else:
                expected_status = args.successstatuscode 
            suite.addTest(testLoadBalancerApache( test_variant['description'], args, logging, driver
                                               , test_name
                                               , test_variant['name']
                                               , test_inputs['default_values']['nodes']
                                               , expected_status = expected_status))

result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())



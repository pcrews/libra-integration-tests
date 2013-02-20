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

from tests.create_loadbalancer import testCreateLoadBalancer
from tests.update_loadbalancer import testUpdateLoadBalancer

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
                   , default = 'test_inputs.dat'
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
                   , default = 'https://lbapi.paas.hpcloud.net'
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
                   , help = 'version string for user api'
                   )
parser.add_argument( '--max_backend_nodes'
                   , action = 'store'
                   , dest = 'maxbackendnodes'
                   , default = 5
                   , help = 'version string for user api'
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
# create operation tests
#########################

testnames = testloader.getTestCaseNames(testCreateLoadBalancer)
# lb_name variants
for test_name in testnames:
    # testing lb name variants 
    if 'lb_name_variants' in test_inputs:
        for test_variant in test_inputs['lb_name_variants']:
          if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
            suite.addTest(testCreateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_variant['name']
                                                , test_inputs['default_values']['default_nodes']
                                                , expected_status = test_variant['expected_status']))

    # testing lb node variants
    if 'node_variants' in test_inputs:
        for test_variant in test_inputs['node_variants']:
            if 'nodes' in test_variant:
                nodes = test_variant['nodes']
            else:
                node_count = test_variant['node_count']
                if str(test_variant['node_count']).startswith('MAX_BACKEND_COUNT'):
                    node_count = args.maxbackendnodes
                    if '+' in test_variant['node_count']:
                        additional_node_count = test_variant['node_count'].split('+')[1]
                        node_count += int(additional_node_count)
                node_pool = test_inputs['default_values']['nodes']
                # we have a node_count value and pull from default_values['nodes']
                if node_count < len(node_pool):
                    nodes = test_inputs['default_values']['nodes'][:node_count]
                else:
                    nodes = []
                    idx = 0
                    while len(nodes) < node_count:
                        nodes.append(node_pool[idx])
                        idx += 1
                        if idx >= len(node_pool):
                            idx = 0
            suite.addTest(testCreateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , nodes
                                                , expected_status = test_variant['expected_status']))
    # algorithm variants
    if 'algorithm_variants' in test_inputs:
        for test_variant in test_inputs['algorithm_variants']:
            suite.addTest(testCreateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , test_inputs['default_values']['default_nodes']
                                                , algorithm = test_variant['algorithm']
                                                , expected_status = test_variant['expected_status']))
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
            suite.addTest(testUpdateLoadBalancer( test_variant['description'], args, logging, driver
                                                , test_name
                                                , test_inputs['default_values']['default_name']
                                                , test_inputs['default_values']['default_nodes']
                                                , test_variant['update_data']
                                                , expected_status = test_variant['expected_status']))

result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())



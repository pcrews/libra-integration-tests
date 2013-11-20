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

""" lbaas_test_loader:
    Module for handling the ugly work of
    sifting through variants + loading them into the test suite
    Probably a better way exists...I should find it :/

"""
import os
import yaml
import unittest

from tests.loadbalancer_functions import testLoadBalancerFuncs
from tests.loadbalancer_stats import testLoadBalancerStats
from tests.create_loadbalancer import testCreateLoadBalancer
from tests.update_loadbalancer import testUpdateLoadBalancer
from tests.add_nodes import testAddNodes
from tests.modify_nodes import testModifyNode
from tests.multi_loadbalancer import testMultiLoadBalancer
from tests.loadbalancer_logs import testLoadBalancerLogs
from tests.monitor_stage1 import testMonitorStage1
from tests.loadbalancer_siege import testLoadBalancerSiege
from tests.loadbalancer_apache import testLoadBalancerApache
from tests.loadbalancer_cleanup import testLoadBalancerCleanup
from tests.selfheal import testRecreateLoadBalancer
from tests.multiple_client_stress import testBetaRayBill
from tests.loadbalancer_monitoring import testMonitoring

def load_lbaas_test_suite(args, variant_module, logging, driver):
    testloader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # get our test input variants (nodes, names, etc)
    if 'variants' not in os.path.dirname(variant_module):
        variant_module = os.path.join('variants', variant_module)
    inputs_file = open(variant_module,'r')
    test_inputs = yaml.load(inputs_file)
    inputs_file.close()

    #########################
    # stats / probe tests
    #########################
    testnames = testloader.getTestCaseNames(testLoadBalancerStats)
    for test_name in testnames:
        if 'stat_variants' in test_inputs:
            for test_variant in test_inputs['stat_variants']:
              if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
                if 'expected_status' in test_variant:
                    expected_status = test_variant['expected_status']
                else:
                    expected_status = args.successstatuscode 
                suite.addTest(testLoadBalancerStats( test_variant['description'], args, logging, driver
                                                    , test_name
                                                    , test_variant['name']
                                                    , test_inputs['default_values']['default_nodes']
                                                    , expected_status = expected_status))

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
                                                   , test_variant['concurrency']
                                                   , test_variant['requests']
                                                   , test_variant['node_counts']
                                                   , test_variant['pages']
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
                                                   , test_variant['concurrency']
                                                   , test_variant['requests']
                                                   , test_variant['node_counts']
                                                   , test_variant['pages']
                                                   , expected_status = expected_status))

    #####################
    # selfheal variants
    #####################

    testnames = testloader.getTestCaseNames(testRecreateLoadBalancer)
    for test_name in testnames:
        if 'selfheal_variants' in test_inputs:
            for test_variant in test_inputs['selfheal_variants']:
              if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
                if 'expected_status' in test_variant:
                    expected_status = test_variant['expected_status']
                else:
                    expected_status = args.successstatuscode 
                suite.addTest(testRecreateLoadBalancer( test_variant['description'], args, logging, driver
                                                    , test_name
                                                    , test_variant['name']
                                                    , test_inputs['default_values']['default_nodes']
                                                    , expected_status = expected_status))

    ##############################
    # multiclient stress variants
    ##############################
    testnames = testloader.getTestCaseNames(testBetaRayBill)
    for test_name in testnames:
        if 'betaraybill_variants' in test_inputs:
            for test_variant in test_inputs['betaraybill_variants']:
              if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
                if 'expected_status' in test_variant:
                    expected_status = test_variant['expected_status']
                else:
                    expected_status = args.successstatuscode 
                suite.addTest(testBetaRayBill( test_variant['description']
                                                      , args
                                                      , logging
                                                      , driver
                                                      , test_name
                                                      , test_variant['name']
                                                      , test_inputs['default_values']['default_nodes']
                                                      , expected_status = expected_status))

    ##############################
    # monitor variants
    ##############################
    testnames = testloader.getTestCaseNames(testMonitoring)
    for test_name in testnames:
        if 'monitor_variants' in test_inputs:
              if 'disabled' not in test_variant: # bit of a hack to help us skip tests that we know will fail
                if 'expected_status' in test_variant:
                    expected_status = test_variant['expected_status']
                else:
                    expected_status = args.successstatuscode 
                suite.addTest(testMonitoring( test_variant['description']
                                                      , args
                                                      , logging
                                                      , driver
                                                      , test_name
                                                      , test_inputs['default_values']['default_name']
                                                      , test_inputs['default_values']['default_nodes']
                                                      , monitor_data = test_input['monitor_variants']
                                                      , expected_status = expected_status))

    #########################
    # cleanup tests
    #########################
    testnames = testloader.getTestCaseNames(testLoadBalancerCleanup)
    for test_name in testnames:
        if 'cleanup_variants' in test_inputs:
            for test_variant in test_inputs['cleanup_variants']:
                suite.addTest(testLoadBalancerCleanup( test_variant['description'], args, logging, driver
                                                    , test_name))

    return suite

""" test_loadbalancer.py
    a test to put a loadbalancer node through its paces
    in an end-to-end system.

"""

import os
import sys
import ast
import imp
import json
import unittest
import logging
import requests
import argparse

from tests.create_loadbalancer import testCreateLoadBalancer

############
# functions
############

#------------------
# utility functions
#------------------
def get_auth_token(auth_url, user_name, tenant_id, password):
    """ Get our keystone auth token to work with the api server """
    request_data = {'auth':{ 'tenantId': tenant_id
                           , 'passwordCredentials':{'username': user_name
                                                   , 'password': password}
                           }
                   }
    request_data = json.dumps(request_data)
    headers = {"Content-Type": "application/json"}
    request_result = requests.post(auth_url, data=request_data, headers=headers, verify=False)
    request_data = ast.literal_eval(request_result._content)
    auth_token = request_data['access']['token']['id']
    return auth_token

#######
# main
#######
parser = argparse.ArgumentParser(description='test_loadbalancer_operations.py - integration test suite for libra lbaas service')
parser.add_argument( '--verbose'
                   , action = 'count'
                   , dest = 'verbose'
                   , default = 0
                   , help = 'Controls internal output.  Utilize multiple times to increase output'
                   )
parser.add_argument( '--driver'
                   , choices=['http','client']
                   , dest = 'driver'
                   , default = 'http'
                   , help = 'Method for interacting with the lbaas service'
                   )
parser.add_argument( '--os-username'
                   , action = 'store'
                   , dest ='osusername'
                   , default = None
                   , help = 'OpenStack username to use for testing.'
                   )
parser.add_argument( '--os-password'
                   , action = 'store'
                   , dest = 'ospassword'
                   , default = None
                   , help = 'OpenStack password for os-username'
                   )
parser.add_argument( '--os-tenant-id'
                   , action = 'store'
                   , dest = 'ostenantid'
                   , default = None
                   , help = 'OpenStack tenant id (not name) for os-username'
                   )
parser.add_argument( '--os-auth-url'
                   , action = 'store'
                   , dest = 'osauthurl'
                   , default = 'https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/tokens'
                   , help = 'OpenStack auth url (keystone endpoint)'
                   )
parser.add_argument( '--lbaas-api-url'
                   , action = 'store'
                   , dest = 'lbaasapiurl'
                   , default = 'https://lbapi.paas.hpcloud.net'
                   , help = 'url for the lbaas api server'
                   )
parser.add_argument( '--lbaas-admin-port'
                   , action = 'store'
                   , dest = 'lbaasadminport'
                   , default = '8889'
                   , help = 'lbaas admin port'
                   )
parser.add_argument( '--lbaas-user-port'
                   , action = 'store'
                   , dest = 'lbaasuserport'
                   , default = '443'
                   , help = 'lbaas user port'
                   )
parser.add_argument( '--lbaas-admin-version'
                   , action = 'store'
                   , dest = 'lbaasadminversion'
                   , default = 'v1'
                   , help = 'version string for admin api'
                   )
parser.add_argument( '--lbaas-user-version'
                   , action = 'store'
                   , dest = 'lbaasuserversion'
                   , default = 'v1.1'
                   , help = 'version string for user api'
                   )
# TODO: add --seed option
# This option must take values such as 'time' to allow for easier 
# use of random seed values
              
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
user_name = args.osusername
tenant_id = args.ostenantid
password = args.ospassword
auth_url = args.osauthurl
auth_token = get_auth_token(auth_url, user_name, tenant_id, password)
api_base_url = args.lbaasapiurl
api_admin_port = args.lbaasadminport
api_user_port = args.lbaasuserport
api_admin_version = args.lbaasadminversion
api_user_version = args.lbaasuserversion
api_admin_url = "%s:%s/%s" %(api_base_url, api_admin_port, api_admin_version)
api_user_url = "%s:%s/%s" %(api_base_url, api_user_port, api_user_version)
api_headers = {"Content-Type": "application/json"
              ,"X-Auth-Token": "%s" %(auth_token) }
# load our specific driver
driver_module = imp.load_source( args.driver
                        , os.path.join(driver_path, args.driver+'.py'))
driver = driver_module.lbaasDriver()

######################################
# variable inputs
######################################
lb_name_variants = [ ('basic_positive_name','the quick, brown fox jumps over the lazy dog.', 200)
                   , ('too_long_name', 'a'*129, 500) 
                   #, ('utf_name', unichr(9911).format(u'')*10, 200)
                   , ('null_name','', 200)
                   , ('whitespace_name',' ', 200)
                   , ('long_whitespace_name',' '*128, 200)
                   , ('long_positive_name','a'*128, 200)
                   , ('nonalpha_name','!@#@!', 200)
                   , ('overlong_utf8_name', unichr(9911).format(u'')*1000, 500)
                   #, ('overlong_whitespace_name', ' '*150, 500)
                   ]

default_lb_name = 'Lbaas_test_node'
default_nodes = [{"address": "15.185.227.167","port": "80"}
                ,{"address": "15.185.227.165","port": "80"}
                ]

node_variants = [#one node
                 ('one_node',[{"address": "15.185.227.167","port": "80"}],200)
                 #two nodes
                ,('two_nodes', [{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}],200)
                 #three nodes
                ,('three_nodes',[{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.167","port": "80"}],200)
                 #five nodes
                ,('five_nodes',[{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.167","port": "80"}],200)
                 # > five nodes
                ,('over_five_nodes',[{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.167","port": "80"}],413)
                 # bad_ip
                ,('bad_ip_address', [{"address": "ImmaBadIP7","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}],400)
                 #no nodes
                ,('no_nodes', [{}],400)
                 # no ip
                ,('no_ip_value',[{"address": "","port": "80"}],400)
                 # no address
                ,('no_address',[{"port": "80"}],400)
                 # no port value
                ,('no_port_value',[{"address": "15.185.227.165","port": ""}],400)
                 # no port entry
                ,('no_port_entry',[{"address": ""}],400)
                 # garbage value
                ,('garbage_value',[{"address": "15.185.227.165","port": "80",'ikeelyou':'boomGoesTheDynamite!'}],200)
                 # duplicate address value
                ,('duplicate_address_value',[{"address": "15.185.227.165", "port": "80", "address": "15.185.227.167"}],400)
                 # bad port value
                ,('bad_port_value',[{"address": "15.185.227.165","port": "iKeelYou"}],400)
                ]
      

##################################
# test away!
##################################

testloader = unittest.TestLoader()
suite = unittest.TestSuite()

# create operation tests
testnames = testloader.getTestCaseNames(testCreateLoadBalancer)
# lb_name variants
for test_name in testnames:
    # testing lb name variants
    for test_description, lb_name, test_expected_status in lb_name_variants:
        suite.addTest(testCreateLoadBalancer( test_description, args, logging, driver
                                            , api_user_url, api_headers
                                            , test_name, lb_name, default_nodes
                                            , expected_status = test_expected_status))
    for test_description, node_set, expected_status in node_variants:
        suite.addTest(testCreateLoadBalancer( test_description, args, logging, driver
                                            , api_user_url, api_headers
                                            , test_name, default_lb_name, node_set
                                            , expected_status = expected_status))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())



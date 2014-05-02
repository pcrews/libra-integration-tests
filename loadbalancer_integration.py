# Copyright 2012, 2013 Hewlett-Packard Development Company, L.P.
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

from lbaas_test_loader import load_lbaas_test_suite
from lbaas_parser import get_parser


#######
# main
#######
parser = get_parser()
args = parser.parse_args(sys.argv[1:])
if args.verbose:
    logging.info("VERBOSE: argument values:")
    for key, item in vars(args).items():
        logging.info("VERBOSE: %s || %s" % (key, item))

# configure logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y%m%d-%H%M%S %p', level=logging.INFO)
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
    api_admin_url = "%s:%s/%s" % (api_base_url,
                                  args.lbaasadminport,
                                  args.lbaasadminversion)
    api_user_url = "%s:%s/%s" % (api_base_url,
                                 args.lbaasuserport,
                                 args.lbaasuserversion)

# load our specific driver
driver_module = imp.load_source(args.driver,
                                os.path.join(driver_path, args.driver + '.py'))
driver = driver_module.lbaasDriver(args, api_user_url, logging)

##################################
# test away!
##################################
suite = load_lbaas_test_suite(args, args.variant_module, logging, driver)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())

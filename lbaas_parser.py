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

import argparse


def get_parser():    
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
                       , help = 'Module containing test inputs.  Assumed to be in the variants directory'
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
                       , default = 120
                       , help = 'seconds to wait for a loadbalancer to achieve ACTIVE status'
                       )
    parser.add_argument( '--demo_wait_time'
                       , action = 'store'
                       , type=int
                       , dest = 'demowaittime'
                       , default = None
                       , help = 'seconds to wait during certain tests for manual testing, validation, etc'
                       )
    parser.add_argument( '--active_pause'
                       , action = 'store'
                       , type=int
                       , dest = 'activepause'
                       , default = 0
                       , help = 'seconds to wait *after* a loadbalancer has achieved ACTIVE status before proceeding with testing'
                       )
    parser.add_argument( '--lb_id'
                       , action = 'store'
                       , dest = 'lbid'
                       , default = None
                       , help = 'specify an existing loadbalancer id for use in certain specialized test cases'
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
    parser.add_argument( '--lbaas_db'
                       , action = 'store'
                       , dest = 'lbaasdbserver'
                       , default = None
                       , help = 'The server name for the lbaas database (used in higher-level testing)'
                       )
    parser.add_argument( '--nodes_username'
                       , action = 'store'
                       , dest ='nodesusername'
                       , default = None
                       , help = 'Username owning the haproxy devices (for advanced testing)'
                       )
    parser.add_argument( '--nodes_password'
                       , action = 'store'
                       , dest = 'nodespassword'
                       , default = None
                       , help = 'Password for account owning the haproxy devices (for advanced testing)'
                       )
    parser.add_argument( '--nodes_tenant_id'
                       , action = 'store'
                       , dest = 'nodestenantid'
                       , default = None
                       , help = 'tenant_id owning the haproxy devices (for advanced testing)'
                       )
    parser.add_argument( '--nodes_region_name'
                       , action = 'store'
                       , dest = 'nodesregionname'
                       , default = None
                       , help = 'region for the haproxy devices (for advanced testing)'
                       )
    parser.add_argument( '--nodes_auth_url'
                       , action = 'store'
                       , dest = 'nodesauthurl'
                       , default = 'https://region-a.geo-1.identity.hpcloudsvc.com:35357/v2.0/tokens'
                       , help = 'account auth url (keystone endpoint) for the haproxy devices (for advanced testing)'
                       )
    parser.add_argument( '--test_metering'
                       , action = 'store_true'
                       , dest = 'testmab'
                       , default = False
                       , help = 'Activates metering validation for testcases that offer it.  Requires rabbit* options for validation to work'
                       )
    parser.add_argument( '--kombu_user'
                       , action = 'store'
                       , dest ='kombuuser'
                       , default = None
                       , help = 'rabbitmq username for accessing the queue'
                       )
    parser.add_argument( '--kombu_pass'
                       , action = 'store'
                       , dest = 'kombupass'
                       , default = None
                       , help = 'rabbitmq password for kombu_user'
                       )
    parser.add_argument( '--kombu_host'
                       , action = 'store'
                       , dest = 'kombuhost'
                       , default = None
                       , help = 'ip address / hostname of rabbitmq server'
                       )
    parser.add_argument( '--kombu_virthost'
                       , action = 'store'
                       , dest = 'kombuvirthost'
                       , default = None
                       , help = 'virtual host on the rabbitmq server'
                       )
    parser.add_argument( '--kombu_exchange'
                       , action = 'store'
                       , dest = 'kombuexchange'
                       , default = None
                       , help = 'exchange on the rabbitmq server'
                       )
    parser.add_argument( '--kombu_queue'
                       , action = 'store'
                       , dest = 'kombuqueue'
                       , default = None
                       , help = 'queue on the rabbitmq server'
                       )
    parser.add_argument( '--kombu_port'
                       , action = 'store'
                       , dest = 'kombuport'
                       , default = None
                       , help = 'the port for the rabbitmq server'
                       )
    parser.add_argument( '--kombu_routing_key'
                       , action = 'store'
                       , dest = 'komburoutingkey'
                       , default = None
                       , help = 'the routing key for the rabbitmq server'
                       )
    parser.add_argument( '--cloud_config'
                       , action = 'store'
                       , dest = 'cloudconfig'
                       , default = None
                       , help = 'path on the test machine where the cloud config lurks / lives'
                       )
    parser.add_argument( '--cloud_map'
                       , action = 'store'
                       , dest = 'cloudmap'
                       , default = None
                       , help = 'path to the cloud map file to be used in a test'
                       )
    parser.add_argument( '--cleanup_off'
                       , action = 'store_true'
                       , dest = 'cleanupoff'
                       , default = False
                       , help = 'Turns off post-test cleanup (for some tests).  Used to automate workloads on vms we want to study afterwards'
                       )

    return parser

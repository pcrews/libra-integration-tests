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

######################################
# variable inputs
######################################
default_lb_name = 'Lbaas_test_node'
default_nodes = [{"address": "15.185.227.167","port": "80"}
                ,{"address": "15.185.227.165","port": "80"}
                ]

lb_name_variants = [ ('basic_positive_name','the quick, brown fox jumps over the lazy dog.', 200)
                   , ('too_long_name', 'a'*129, 500) 
                   #, ('utf_name', unichr(9911).format(u'')*10, 200)
                   , ('null_name','', 200)
                   , ('whitespace_name',' ', 200)
                   , ('long_whitespace_name',' '*128, 200)
                   , ('long_positive_name','a'*128, 200)
                   , ('nonalpha_name','!@#@!', 200)
                   , ('overlong_utf8_name', unichr(9911).format(u'')*1000, 500)
                   , ('overlong_whitespace_name', ' '*150, 200) # we trim trailing whitespace > MAX_NAME, so this passes
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
                ,('duplicate_address_value',[{"address": "15.185.227.165", "port": "80", "address": "15.185.227.167"}],200)
                 # bad port value
                ,('bad_port_value',[{"address": "15.185.227.165","port": "iKeelYou"}],400)
                ]


algorithm_variants = [('round_robin_algo',"ROUND_ROBIN",200)
                     ,('least_connections_algo',"LEAST_CONNECTIONS",200)
                     ,('bad_algorithm',"IDONOTEXIST",400)
                     ,('fuzzy_good_algo',"ROUND_ROBIN1",400)
                     ]

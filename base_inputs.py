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

lb_name_variants = [ 
                   ('nonalpha_name','!@#@!', 200)
                   , ('overlong_name', 'X'*130, 500)
                   ]

node_variants = [#one node
                 ('one_node',[{"address": "15.185.227.167","port": "80"}],200)
                 # > five nodes
                ,('over_five_nodes',[{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.167","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.165","port": "80"}
                 ,{"address": "15.185.227.167","port": "80"}],413)
                ]

algorithm_variants = [('round_robin_algo',"ROUND_ROBIN",200)
                     ]

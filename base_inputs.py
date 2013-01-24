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
                ]

algorithm_variants = [('round_robin_algo',"ROUND_ROBIN",200)
                     ]

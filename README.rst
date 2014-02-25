libra-integration-tests
=======================

end to end / integration tests for lbaas libra

Info:
-----
These tools are designed to provide a variety of functional tests for the libra LBaaS system.
They vary from basic, user-visibile functionality to validation of administrator-level functions.
Test inputs are defined in the variants module (a command line option).
The input files are in yaml and the types of inputs will define the types of tests to be created.

Requirements:
-------------
python-requests

optional requirements:
----------------------
apachebench (ab)
siege
python-swiftclient
python-novaclient

functional test suite:
----------------------

Using the following command line will execute the basic functional test suite.
This will create a loadbalancer and put it through its paces with a variety of positive and negative test cases.
This includes loadbalancer and node update / modify operations as well as creation of a dual loadbalancer on a single device.
The OS_REGION_NAME value is the loadbalancer region from the service catalog. 

python ./loadbalancer_integration.py \
            --os_username=${OS_USER} \
            --os_password=${OS_PASS} \
            --os_tenant_name=${OS_TENANT_NAME} \
            --os_region_name=${OS_REGION_NAME} \
            --variants_module=canary.dat

benchmark tests:
----------------
The test suite can be used to execute either the apachebench or siege benchmarks.
The variant file defines how many backend servers to use (one may use several sets of backends in a single test)
as well as the test file(s) to be used and the number of concurrent users and requests to make.

apachebench

siege

utilities:
----------

cleanup

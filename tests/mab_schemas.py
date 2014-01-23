# Copyright 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
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

""" mab_schemas.py
    Module containing json schemas for metering and billing (mab)
    testing, using validictory

"""

message_schemas = {"lbaas.instance.create": {"type": "object",
                                             "properties": {"event_type": {"type": "string", "enum":["lbaas.instance.create"]},
                                                            "message_id": {"type": "string"},
                                                            "timestamp": {"type": "string"},
                                                            "payload": {"type": "object",
                                                                       "properties": {"version": {"type":"string"},
                                                                                      "audit_period_beginning":{"type":"string"},
                                                                                      "audit_period_ending": {"type":"string"},
                                                                                      "display_name": {"type":"string"},
                                                                                      "state_description": {"type":"string"},
                                                                                      "tenant_id": {"type":"string"},
                                                                                      "instance_type_id": {"type":"integer"},
                                                                                      "instance_id": {"type":"integer"},
                                                                                      "instance_type": {"type":"string"},
                                                                                      "state": {"type":"string"},
                                                                                      "mab_processing_version": {"type":"string"},
                                                                                      "service_id": {"type":"string"}
                                                                                     }}}
                                            },
                  "lbaas.bandwidth.usage": {"type": "object",
                                             "properties": {"event_type": {"type": "string", "enum":["lbaas.bandwidth.usage"]},
                                                            "message_id": {"type": "string"},
                                                            "timestamp": {"type": "string"},
                                                            "payload": {"type": "object",
                                                                       "properties": {"version": {"type":"string"},
                                                                                      "audit_period_beginning":{"type":"string"},
                                                                                      "audit_period_ending": {"type":"string"},
                                                                                      "display_name": {"type":"string"},
                                                                                      "state_description": {"type":"string"},
                                                                                      "tenant_id": {"type":"string"},
                                                                                      "instance_type_id": {"type":"integer"},
                                                                                      "instance_id": {"type":"integer"},
                                                                                      "instance_type": {"type":"string"},
                                                                                      "state": {"type":"string"},
                                                                                      "mab_processing_version": {"type":"string"},
                                                                                      "service_id": {"type":"string"},
                                                                                      "metrics": {"type": "object",
                                                                                                  "properties": { "metric_type": {"type":"string"},
                                                                                                                  "metric_units": {"type":"string", "enum":["BYTES"]},
                                                                                                                  "metric_name": {"type":"string", "enum":["lbaas.network.outgoing.bytes"]},
                                                                                                                  "metric_value": {"type":"integer"}
                                                                                                                }
                                                                                                 }
                                                                                     }
                                                                        }}
                                            }
                  }

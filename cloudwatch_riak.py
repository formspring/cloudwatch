#!/usr/bin/env python
#
# Copyright 2011 Formspring
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import httplib
import json
import datetime

import socket

#import aws keys, you can do it this way or through env variables (check boto doc)
#or through any means you want. You decide.
aws = open('path_to_aws_key_file')
aws_key = aws.readline().strip()
aws_secret = aws.readline().strip()

import boto
c = boto.connect_cloudwatch(aws_access_key_id=aws_key, aws_secret_access_key=aws_secret)

#get stats
def getstats(host='localhost', port=8098):
    client = httplib.HTTPConnection(host, port)
    client.request('GET', '/stats')
    response = client.getresponse()
    response_body = response.read()
    response.close()
    client.close()
    js = json.loads(response_body)
    return js


def publish(stats):
    tstamp = datetime.time()
    hostname = socket.gethostname()

    #boto does not like 0
    #boto 2.0rc1 has a bug with dimensions, currently (06/29/2011) fixed in trunk.
    #You need version > 2.0.rc1

    for metric in ['node_put_fsm_time_mean', 'node_get_fsm_time_mean']:
        c.put_metric_data('riak', metric,
                          value=int(stats[metric])+1,
                          timestamp=tstamp,
                          dimensions={'Hostname':hostname},
                          unit='Microseconds')

    for metric in ['node_gets_total', 'node_puts_total']:
        c.put_metric_data('riak', metric,
                          value=int(stats[metric])+1,
                          timestamp=tstamp,
                          dimensions={'Hostname':hostname},
                          unit='Count')

    for metric in ['mem_total', 'mem_allocated']:
        c.put_metric_data('riak', metric,
                          value=float(stats[metric]),
                          timestamp=tstamp,
                          dimensions={'Hostname':hostname},
                          unit='Count')

    c.put_metric_data('riak', 'mem_allocated_%',
                      value=int(float(stats['mem_allocated'])*100 / float(stats['mem_total'])),
                      timestamp=tstamp,
                      dimensions={'Hostname':hostname},
                      unit='Percent')

if __name__ == '__main__':
    #seems to work on AWS, if you bind to the internal IP, change at will
    host = socket.gethostbyname_ex(socket.gethostname())[2][0]
    stats = getstats(host=host)
    publish(stats)


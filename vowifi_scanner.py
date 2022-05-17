#!/usr/bin/env python3

# The MIT License (MIT)

# Copyright (c) 2018 Spinlogic S.L., Albacete, Spain

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
# of the Software, and to permit persons to whom the Software is furnished to do 
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.


#################################################################
#
# Module : vowifi_scanner.py
# Author : Juan Noguera
# Purpose: This script goes through the list of operators in 
#          file declared as parameter and finds whether there
#          is a DNS entry for the ePDG of each operator.
#          
# Input:  file generated from http://www.imei.info/operator-codes/
#
# Output: csv file with the following columns:
#
#    Country   Operator_Name  FQDN_for_ePDG   Resolved_IP_Address   Responds to ping?   length of response to IKEv2_SA_INIT
#
#   One entry per IP Address resolved. I.e. if the FQDN of an 
#   operator resolves to multiple IP Addresses, then this 
#   operator has multiple consecutive entries.
#
#################################################################

"""Usage: vowifi_scanner <operators_filename> <output_filename>"""

__version__ = '0.2.0'

import argparse, random, dns.resolver
import ikev2.ikev2_class as ikev2
import csv, json
from multiprocessing import Pool
from scapy.all import sr1, IPv6, IP, ICMP, ICMPv6EchoRequest

TIMEOUT = 1

def nslookup(operator_url: str) -> bool:
    """"Performs DNS lookup for A (IPv4) and AAAA (IPv6) records"""
    dnsres = dns.resolver.Resolver()
    records = []
    try:
        ansv4 = dnsres.resolve(operator_url, dns.rdatatype.A)
        for record in ansv4:
            records.append(record.address)
        ansv6 = dnsres.resolve(operator_url, dns.rdatatype.AAAA)
        for record in ansv6:
            records.append(record.address)
    except:
        pass
    return records

def respondsToPing(address: str, timeout: int = 5) -> bool:
    '''Checks if the machine at "address" responds to ICMP Echo requests'''
    responds_to_ping = False
    if ':' in address:
        icmp_sender = sr1(IPv6(dst = address) / ICMPv6EchoRequest(data="HELLO"), timeout = timeout, verbose = 0)
    else:
        icmp_sender = sr1(IP(dst = address) / ICMP() / "HELLO", timeout = timeout, verbose = 0)

    if icmp_sender != None:
        responds_to_ping = True

    return responds_to_ping

# single-argument for multiprocessing map()
def connect_s(op):
    return connect(op["MCC"], op["MNC"], TIMEOUT)

def connect(mcc: str, mnc: str, timeout: int = 5):
    if len(mcc) != 3 or len(mnc) != 3:
        print(f"Incorrect length for MCC {mcc} or MNC {mnc} (should be 3 characters)")
        return None

    operator_url = f"epdg.epc.mnc{mnc}.mcc{mcc}.pub.3gppnetwork.org"
    result = {
        "mcc": mcc,
        "mnc": mnc,
        "url": operator_url,
        "records": {}
    }

    dns_query_result = nslookup(operator_url)
    if len(dns_query_result) == 0 :
        # lookup failed
        return result

    # lookup successful; try to connect
    for record in dns_query_result:
        result["records"][record] = {
            "Ping Reply": respondsToPing(record, timeout=timeout),
            "SA Init Response Len": 0
        }

        if ':' in record: # ikev2 class does not support IPv6
            continue
    
        # connect regardless of ping response
        ikev2_pack = ikev2.epdg_ikev2(record)
        result["records"][record]["SA Init Response Len"] = ikev2_pack.sa_init(random.randrange(50000, 55000), 500)

    return result

def main(args):
    operators = []
    with open(args.operators_file) as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_NONE)
        for row in reader:
            operators.append(row)

    print(f"Read {len(operators)} networks from file.")

    with Pool(8) as p:
        results = p.map(connect_s, operators)

    with open(args.out_file, "w") as fh:
        print(json.dumps(results, indent=2), file=fh)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operators_file', type = str, help = 'File with list of operators and their data')
    parser.add_argument('out_file', type = str, help = 'output file (CVS)')
    args = parser.parse_args()
    main(args)
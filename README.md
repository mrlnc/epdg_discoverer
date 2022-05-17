# ePDG discoverer
Resolves the IP addresses of ePDGs from most mobile operators in the world and checks if each ePDG responds to ICMP and whether it accepts IKEv2 connection.

---
---
Note: the original code by @Spinlogic is available here: https://github.com/Spinlogic/epdg_discoverer

My repo has a few changes:
- update imports
- JSON output
- multithreading to increase speed
- fetch network list from mcc-mnc.com

---
---

## ePDG address resolution
Mobile networks use a pre-defined pattern for their ePDG:

> epdg.epc.mcc<_mcc_>.mnc<_mnc_>.pub.3gppnetwork.org

For example, Spain has mcc = 214 and Movistar (Telefónica) has mnc = 07 in Spain. Therefore the URI for Movistar ePDG's is:

> epdg.epc.mcc214.mnc007.pub.3gppnetwork.org

The script resolves both IPv4 and IPv6, but supports only IPv4 hosts for IKEv2 discovery.

# Dependencies

Install dependencies:
```
python3 -m venv .venv
source .venv/bin/actiate
pip3 install < requirements.txt
```

Fetch the network list:
```
./get_operator_list.py network-list.txt
```

## Usage
```
sudo .venv/bin/python3 vowifi_scanner.py <network-list> <output-file>
```

Note that the ePDG address of some operators is resolved, but it does not respond to neither ICMP nor IKEv2_SA_INIT messages. This could mean that the ePDG is off, geoblocked, or does not like the received request and drops it (if it is an IKEv2 one, specially). 

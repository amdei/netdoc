__author__     = 'Andrea Dainese'
__contact__    = 'andrea@adainese.it'
__copyright__  = 'Copyright 2022, Andrea Dainese'
__license__    = 'GPLv3'
__date__       = '2022-09-07'
__version__    = '0.9.6'

import sys
from os.path import basename
import logging
import inspect
from slugify import slugify
from . import functions

def ingest(log, force=False):
    """
    Processing show interface.
    """
    function_name = ''.join(basename(__file__).split('.')[0])
    print(f"I'm the ingestor {function_name}!!!", file=sys.stderr)
    if function_name != functions.parsing_function_from_log(log):
        raise functions.WrongParser(f'Cannot use {function_name} for log {log.pk}')
    if not log.parsed:
        raise functions.NotParsed(f'Skipping unparsed log {log.pk}')
    if not log.parsed_output:
        raise functions.NotParsed(f'Skipping empty parsed log {log.pk}')
    if not force and log.ingested:
        raise functions.AlreadyIngested(f'Skipping injested log {log.pk}')
    if not log.discoverable.device:
        # TODO: show version ingest is missing, manual device set is required.
        raise functions.Postponed(f'Device is required, postponing {log.pk}')

    site_o = log.discoverable.site

    print(log.parsed_output, file=sys.stderr)
    print(site_o, file=sys.stderr)
    for item in log.parsed_output:
        # Parsing
        # https://github.com/networktocode/ntc-templates/blob/54a78038a5c2358ca7b6df7e1cdb19a0f6c1ce7f/tests/linux/ip_link_show/linux_ip_link_show.yml
        device_o = log.discoverable.device
        interface_name = item['interface']
        args = {
            'name': interface_name,
            'mac_address': item['address'],
        }
        # TODO: not tested
        # if item['encapsulation'] == '802.1Q Virtual LAN' and item['vlan_id']:
        #     # Interface is configured to read 802.1Q
        #     vlan_o = functions.set_get_vlan(vid=item['vlan_id'], site=site_o)
        #     args['mode'] = functions.normalize_switchport_mode('trunk')
        #     args['untagged_vlan'] = vlan_o

        try:
            args['mtu'] = int(item['mtu'])
        except ValueError:
            pass

        # TODO: not tested
        # interface_parent = functions.parent_interface(interface_name)
        # if interface_parent:
        #     args['parent'] = functions.set_get_interface(label=interface_parent, device=device_o)

        print(device_o, file=sys.stderr)
        print(args, file=sys.stderr)
        # Trusted data: we always update some data
        interface_o = functions.set_get_interface(label=interface_name, device=device_o, create_kwargs=args, update_kwargs=args)
 
    # Update the log
    log.ingested = True
    log.save()

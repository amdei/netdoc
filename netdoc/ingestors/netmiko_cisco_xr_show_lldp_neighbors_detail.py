__author__     = 'Andrea Dainese'
__contact__    = 'andrea@adainese.it'
__copyright__  = 'Copyright 2022, Andrea Dainese'
__license__    = 'GPLv3'
__date__       = '2022-09-07'
__version__    = '0.9.6'

from os.path import basename
import logging
import inspect
from slugify import slugify
from django.db.utils import IntegrityError
from . import functions

def ingest(log, force=False):
    """
    Processing show lldp neighbors detail.
    """
    function_name = ''.join(basename(__file__).split('.')[0])
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

    for item in log.parsed_output:
        # Parsing
        # https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_nxos/show_lldp_neighbors_detail        device_o = log.discoverable.device
        device_o = log.discoverable.device
        discoverable_o = log.discoverable
        interface_name = item['local_interface']
        remote_interface_name = item['neighbor_interface']
        # TODO: missing mgmt_address on template
        # remote_address = item['mgmt_address']
        remote_device_name = item['neighbor']
        site = log.discoverable.site

        # Excluding non physical interfaces
        if not functions.physical_interface(interface_name) and not functions.physical_interface(remote_interface_name):
            logging.warning(f'Excluding non physical interfaces {interface_name} or {remote_interface_name}')
            continue

        remote_device_o = functions.set_get_device(name=remote_device_name, create_kwargs={'site': site})
        interface_o = functions.set_get_interface(label=interface_name, device=device_o, create_kwargs={'name': interface_name})
        remote_discoverable_o = functions.set_get_discoverable(address=remote_address, device=remote_device_o, site=site, mode=discoverable_o.mode, credential=discoverable_o.credential)
        # TODO: missing mgmt_address on template
        #         remote_discoverable_o = functions.set_get_discoverable(address=remote_address, create_kwargs={'site': site, 'mode': discoverable_o.mode, 'credential': discoverable_o.credential}, device=remote_device_o)
        cable_o = functions.set_get_cable(interface_o, remote_interface_o)

    # Update the log
    log.ingested = True
    log.save()

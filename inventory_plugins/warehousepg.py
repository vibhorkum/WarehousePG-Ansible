#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
WarehousePG Inventory Plugin
Enhances inventory with upstream node information and replication details.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: warehousepg
    plugin_type: inventory
    short_description: WarehousePG inventory plugin
    version_added: "2.9"
    description:
        - This plugin extends the base YAML inventory with WarehousePG specific attributes.
        - It extracts upstream_node information from private_ip mappings.
        - Useful for setting up replication relationships between nodes.
    options:
        plugin:
            description: The name of the inventory plugin
            required: true
            choices: ['warehousepg', 'warehousepg_inventory']
        yaml_file:
            description: Path to the YAML inventory file
            required: false
            default: inventory.yml
'''

EXAMPLES = '''
# Enable the plugin in ansible.cfg:
# [inventory]
# enable_plugins = warehousepg, yaml, ini

# Example inventory file (inventory.yml):
# ---
# all:
#   children:
#     primary-coordinator:
#       hosts:
#         whpg1-coordinator:
#           ansible_host: 110.0.0.4
#           private_ip: 10.0.0.4
#     standby-coordinator:
#       hosts:
#         standby-coordinator:
#           ansible_host: 110.0.0.5
#           private_ip: 10.0.0.5
#           upstream_node_private_ip: whpg1-coordinator
#           replication_type: synchronous
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.errors import AnsibleError, AnsibleParserError
import yaml
import os


class InventoryModule(BaseInventoryPlugin, Constructable):
    NAME = 'warehousepg'

    def verify_file(self, path):
        """Verify that the source file can be processed by this plugin."""
        valid = False
        if super(InventoryModule, self).verify_file(path):
            # Check if file ends with .yml or .yaml
            if path.endswith(('.yml', '.yaml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory file and populate the inventory."""
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        
        # Read the YAML file
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise AnsibleParserError(f"Failed to parse {path}: {str(e)}")
        
        if not data:
            raise AnsibleParserError(f"Inventory file {path} is empty")
        
        # Build a mapping of hostname to private_ip
        hostname_to_ip = {}
        
        # First pass: collect all hostnames and their private IPs
        if 'all' in data and 'children' in data['all']:
            for group_name, group_data in data['all']['children'].items():
                if 'hosts' in group_data:
                    for hostname, host_vars in group_data['hosts'].items():
                        if 'private_ip' in host_vars:
                            hostname_to_ip[hostname] = host_vars['private_ip']
        
        # Second pass: add groups and hosts to inventory
        if 'all' in data and 'children' in data['all']:
            for group_name, group_data in data['all']['children'].items():
                # Add the group
                self.inventory.add_group(group_name)
                
                # Add hosts to the group
                if 'hosts' in group_data:
                    for hostname, host_vars in group_data['hosts'].items():
                        # Add host to inventory
                        self.inventory.add_host(hostname, group=group_name)
                        
                        # Set host variables
                        if host_vars:
                            for var_name, var_value in host_vars.items():
                                self.inventory.set_variable(hostname, var_name, var_value)
                        
                        # Resolve upstream_node_private_ip if it's a hostname
                        if 'upstream_node_private_ip' in host_vars:
                            upstream_ref = host_vars['upstream_node_private_ip']
                            
                            # Check if upstream_ref is a hostname (exists in our mapping)
                            if upstream_ref in hostname_to_ip:
                                # Set the actual IP address
                                resolved_ip = hostname_to_ip[upstream_ref]
                                self.inventory.set_variable(
                                    hostname, 
                                    'upstream_node_ip', 
                                    resolved_ip
                                )
                                self.inventory.set_variable(
                                    hostname,
                                    'upstream_node_hostname',
                                    upstream_ref
                                )
                            else:
                                # upstream_ref is already an IP or not found
                                self.inventory.set_variable(
                                    hostname, 
                                    'upstream_node_ip', 
                                    upstream_ref
                                )

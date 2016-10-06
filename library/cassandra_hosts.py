from ansible.module_utils.basic import *
import ast
import json

GROUPS = 'groups'
PUBLIC_ADDRESS = 'public_address'
RACK = "rack"
LOCAL_ADDRESS = 'local_address'
LEAD_GROUP = 'lead_group'


def build_cass_hosts_config(inventory_hostname, hostvars):
    cassandra_groups = extract_cassandra_groups(hostvars[inventory_hostname], hostvars)
    configured_cassandra_racks = configure_cassandra_racks(cassandra_groups, hostvars, inventory_hostname)
    cassandra_lead_found = determine_lead_group(configured_cassandra_racks,inventory_hostname, hostvars[inventory_hostname][GROUPS])
    prioritized_groups = prioritize_cassandra_groups(cassandra_lead_found)
    return ' '.join(prioritized_groups)


def extract_cassandra_groups(inventory_vars, hostvars):
    cassandra_groups = {}
    for name in inventory_vars[GROUPS]:
        if 'dc-' in name and '-ds' in name:
            cassandra_groups[name] = list(inventory_vars[GROUPS][name])

    cassandra_ip_mappings= { 'lead_group': '' }
    for cassandra_group_name in cassandra_groups:
        cassandra_ip_mappings[cassandra_group_name] = {}
        for ds_ip in cassandra_groups[cassandra_group_name]:
            try:
                private_ip = hostvars[ds_ip]['ec2_private_ip_address']
            except:
                private_ip = hostvars[ds_ip]['ansible_eth0']['ipv4']['address']

            cassandra_ip_mappings[cassandra_group_name][ds_ip] = { 'private_ip': private_ip }
    return cassandra_ip_mappings


def configure_cassandra_racks(cassandra_groups):
    for cassandra_group_name in cassandra_groups:
        group_name_parts = cassandra_group_name.split('-')
        for ds_ip in cassandra_groups[cassandra_group_name]:
            cassandra_groups[cassandra_group_name][ds_ip]['private_ip'] = cassandra_groups[cassandra_group_name][ds_ip]['private_ip'] + ":" + group_name_parts[1] + ',1'
    return cassandra_groups


def determine_lead_group(cassandra_groups, inventory_hostname, groups):
    for group_name in groups:
        if 'dc-' in group_name:
            if inventory_hostname in groups[group_name]:
                group_name_split = group_name.split('-')
                cassandra_groups['lead_group'] = group_name_split[0] + '-' + group_name_split[1]
                break
    return cassandra_groups


def prioritize_cassandra_groups(cassandra_groups):
    prioritized_groups = []
    ds_lead_group = cassandra_groups['lead_group'] + '-ds'
    del cassandra_groups['lead_group']

    for ds_ip in cassandra_groups[ds_lead_group]:
            prioritized_groups.append(cassandra_groups[ds_lead_group][ds_ip]['private_ip'])
    del cassandra_groups[ds_lead_group]

    for cassandra_group_name in cassandra_groups:
        for ds_ip in cassandra_groups[cassandra_group_name]:
            prioritized_groups.append(cassandra_groups[cassandra_group_name][ds_ip]['private_ip'])

    return prioritized_groups


def main():
    module = AnsibleModule(
            argument_spec=dict(
                    inventory_hostname=dict(required=True, type='str'),
                    hostvars=dict(required=True, type="str")
            )
    )

    inventory_hostname = module.params['inventory_hostname']
    hostvars = module.params['hostvars']
    hostvars = hostvars.decode('base64')
    # hostvars = ast.literal_eval(hostvars)
    with open('hostvars.json','w') as hostvars_file:
        hostvars_file.write(hostvars)

    hostvars = json.dumps(hostvars)
    hostvars = json.loads(hostvars)

    cass_hosts = build_cass_hosts_config(inventory_hostname, hostvars)
    cass_hosts = json.dumps(cass_hosts)
    cass_hosts = json.loads(cass_hosts)

    module.exit_json(
            changed=True,
            ansible_facts=dict(
                    cassandra_hosts=cass_hosts
            )
    )


if __name__ == '__main__':
    main()

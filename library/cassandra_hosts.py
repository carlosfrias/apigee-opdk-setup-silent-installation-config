from ansible.module_utils.basic import *
import ast
import json
import tempfile
import os

GROUPS = 'groups'
PUBLIC_ADDRESS = 'public_address'
RACK = "rack"
LOCAL_ADDRESS = 'local_address'
NOT_DEFINED = 'NOT DEFINED'
LEAD_GROUP = 'lead_group'


def build_cass_hosts_config(inventory_hostname, hostvars):
    cassandra_groups = extract_cassandra_groups(hostvars[inventory_hostname], hostvars)
    configured_cassandra_racks = configure_cassandra_racks(cassandra_groups)
    cassandra_lead_found = determine_lead_group(configured_cassandra_racks,
                                                inventory_hostname,
                                                hostvars[inventory_hostname][GROUPS])
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
            if ds_ip in hostvars:
                hostvar = hostvars[ds_ip]
                if LOCAL_ADDRESS in hostvar:
                    private_ip = hostvar[LOCAL_ADDRESS]
                else:
                    private_ip = NOT_DEFINED
            cassandra_ip_map = cassandra_ip_mappings[cassandra_group_name]
            cassandra_ip_map[ds_ip] = { 'private_ip': private_ip }
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
    json_file = '/tmp/hostvars_params.json'
    # json_file = tempfile.mkstemp(suffix='json', text=True)
    with open(json_file, 'w') as hostvars_file:
        hostvars_file.write(hostvars)

    # hostvars = hostvars.decode('base64')
    try:
        hostvars = ast.literal_eval(hostvars)
    except SyntaxError as e:
        hostvars = hostvars.replace('{u', '{')
        hostvars = hostvars.replace(", u'", ", '")
        hostvars = hostvars.replace(": u'", ": '")
        hostvars = hostvars.replace("[u'", "['")
        hostvars = hostvars.replace("'", "\"")
        with open(json_file, 'w') as file:
            file.write(hostvars)

        try:
            hostvars = ast.literal_eval(hostvars)
        except SyntaxError as e:
            msg = "ast.literal_eval conversion failed on line {0} with {1}".format(e.lineno, e.msg)
            msg += "This occurred due to an operating system setting. There is a way around."
            msg += "This means that you will need re-run with --tags=apigee-silent-config to generate the silent-install.conf file."
            msg += "Then complete the installation with --skip-tags=os-pre-req,apigee-pre-req."
            module.fail_json(
                changed=False,
                msg=msg,
            )
            return

    hostvars = json.dumps(hostvars)
    with open(json_file, 'w') as hostvars_file:
        hostvars_file.write(hostvars)

    try:
        hostvars = json.loads(hostvars)
    except SyntaxError as e:
        msg = "json.loads conversion failed: {0} {1}".format(e.lineno, e.msg)
        module.fail_json(
            changed=False,
            msg=msg,
        )
        return


    try:
        cass_hosts = build_cass_hosts_config(inventory_hostname, hostvars)
    except SyntaxError as e:
        msg = "build_cass_hosts_config failed on line {0} with {1}".format(e.lineno, e.msg)
        module.fail_json(
            changed=False,
            msg=msg,
        )
        return

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

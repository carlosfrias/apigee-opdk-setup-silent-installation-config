from ansible.module_utils.basic import *
import ast
import json
import tempfile




def main():
    module = AnsibleModule(
        argument_spec=dict(
            inventory_hostname=dict(required=True, type='str'),
            groups=dict(required=True, type="str")
        )
    )

    inventory_hostname = module.params['inventory_hostname']
    groups = module.params['groups']
    json_file_name = '/tmp/hostvars_params.json'
    json_file = tempfile.mkstemp(suffix='json', text=True)
    with open(json_file_name, 'w') as hostvars_file:
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
        with open('hostvars_params.json', 'w') as file:
            file.write(hostvars)

        try:
            hostvars = ast.literal_eval(hostvars)
        except SyntaxError as e:
            msg = "ast.literal_eval conversion failed on line {0} with {1}".format(e.lineno, e.msg)
            module.fail_json(
                changed=False,
                msg=msg,
            )
            return

    hostvars = json.dumps(hostvars)
    with open('hostvars_dumps.json', 'w') as hostvars_file:
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

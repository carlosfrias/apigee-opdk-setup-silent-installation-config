Apigee OPDK Silent Installation Config
=========

The purpose of this role is to construct a configuration file for the Apigee OPDK silent installer. 

Requirements
------------

The installation of Apigee OPDK requires root access. Credentials must also be supplied to override the empty placeholders
provided here. It is recommended that credentials be consolidated into a single credentials.yml file that can be stored 
separately. It is assumed that files containing credentials are stored in the ~/.apigee folder. 

Role Variables
--------------

Variable defaults are managed in the role apigee-opdk-setup-default-settings. 

Apigee silent installation configuration file

    opdk_installation_config_file: "{{ opdk_installer_path }}/silent-install.conf"

Reference to the OPDK user name

    opdk_user_name: ''
    
Reerence to the OPDK user group name
    
    opdk_group_name: ''
    
Reference to an installation file that is provided by the user instead of the generated installation file.

     provided_response_file: ''



Dependencies
------------

This role depends on the following roles:

* apigee-opdk-setup-default-settings
 
Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: apigee-opdk-setup-silent-installation-config }

License
-------

Apache License Version 2.0, January 2004

Author Information
------------------

Carlos Frias
<!-- BEGIN Google Required Disclaimer -->

# Required Disclaimer

This is not an officially supported Google product.
<!-- END Google Required Disclaimer -->

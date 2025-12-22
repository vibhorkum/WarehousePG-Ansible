# WarehousePG Ansible Role

This Ansible role automates the installation and configuration of WarehousePG HA cluster on Rocky Linux 9.3.

## Features

- User and group management (gpadmin)
- Passwordless SSH configuration
- Sudo access setup
- System dependency installation
- EDB repository configuration
- WarehousePG RPM installation
- Cluster initialization (coordinator and segments)
- Standby coordinator setup
- Remote access configuration

## Requirements

- Rocky Linux 9.3
- Ansible 2.9 or higher
- Valid EDB subscription token
- Appropriate network connectivity between nodes

## Role Variables

See `defaults/main.yml` for all available variables.

Key variables:
- `whpg_gpadmin_uid`: UID for gpadmin user (default: 530)
- `whpg_gpadmin_password`: Password for gpadmin user
- `edb_subscription_token`: EDB repository token
- `whpg_coordinator_port`: Coordinator port (default: 6000)
- `whpg_segment_port_base`: Base port for segments (default: 6002)

## Dependencies

None

## Example Playbook

```yaml
- hosts: primary-coordinator
  become: yes
  roles:
    - role: warehousepg
      vars:
        edb_subscription_token: "your_token_here"
        whpg_gpadmin_password: "NewPassword@123"
```

## License

MIT

## Author Information

Created for WarehousePG HA deployment automation.

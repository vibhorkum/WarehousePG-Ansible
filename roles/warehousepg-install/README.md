# WarehousePG Installation Role

This Ansible role handles complete WarehousePG installation including user management, /etc/hosts configuration, passwordless SSH setup, and package installation.

## Features

- **User Management**: Creates gpadmin user and group with proper sudo access
- **/etc/hosts Configuration**: Updates /etc/hosts with all cluster nodes
- **Passwordless SSH**: Configures SSH keys and passwordless authentication for gpadmin user across all nodes
- **EDB Repository Setup**: Configures EDB repository with subscription token
- **Package Installation**: Installs WarehousePG RPM packages
- **Ownership Configuration**: Sets proper ownership for installation directories
- **Installation Verification**: Verifies successful installation

Based on: https://warehouse-pg.io/docs/7x/install_guide/install_whpg.html

## Requirements

- Rocky Linux 9.3
- Valid EDB subscription token
- Internet connectivity to EDB repository
- Root or sudo access

## Role Variables

See `defaults/main.yml` for all available variables.

### User Management
- `whpg_gpadmin_uid`: UID for gpadmin user (default: 530)
- `whpg_gpadmin_gid`: GID for gpadmin group (default: 530)
- `whpg_gpadmin_user`: Username (default: "gpadmin")
- `whpg_gpadmin_password`: Password for gpadmin (override in vault)
- `whpg_gpadmin_home`: Home directory (default: "/home/gpadmin")

### Network Configuration
- `whpg_use_private_ip_for_hosts`: Use private IPs in /etc/hosts (default: false)

### Installation
- `edb_subscription_token`: EDB repository token (required)
- `whpg_version`: WarehousePG major version (default: "7")
- `whpg_rpm_version`: Full RPM version (default: "7.3.0-WHPG")
- `whpg_install_path`: Installation path (default: "/usr/local/greenplum-db")

## Dependencies

None - This role should be run first before other WarehousePG roles

## Example Playbook

```yaml
- hosts: all
  become: yes
  roles:
    - role: warehousepg-install
      vars:
        edb_subscription_token: "your_token_here"
```

## License

MIT

## Author Information

Created for WarehousePG installation automation.

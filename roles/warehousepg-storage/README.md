# WarehousePG Storage Role

This Ansible role creates and configures data storage directories for WarehousePG coordinator and segment hosts.

## Features

- Creates coordinator data directories
- Creates standby coordinator data directories
- Creates primary segment data directories
- Creates mirror segment data directories
- Sets proper ownership and permissions
- Supports custom mount points and storage locations
- Validates storage space requirements

## Requirements

- **warehousepg-install role** must be run first (creates gpadmin user, configures /etc/hosts, sets up passwordless SSH)
- Sufficient disk space on target hosts
- Root or sudo access

## Role Variables

All variables are defined in `defaults/main.yml`:

### Storage Paths

- `whpg_storage_base`: Base directory for all WarehousePG data (default: `/data`)
- `whpg_coordinator_storage`: Coordinator data directory (default: `{{ whpg_storage_base }}/coordinator`)
- `whpg_primary_storage`: Primary segment directory (default: `{{ whpg_storage_base }}/primary`)
- `whpg_mirror_storage`: Mirror segment directory (default: `{{ whpg_storage_base }}/mirror`)

### Ownership

- `whpg_storage_owner`: Directory owner (default: `gpadmin`)
- `whpg_storage_group`: Directory group (default: `gpadmin`)
- `whpg_storage_mode`: Directory permissions (default: `0700`)

### Validation

- `whpg_validate_storage_space`: Enable storage space validation (default: `true`)
- `whpg_min_coordinator_space_gb`: Minimum space for coordinator in GB (default: `10`)
- `whpg_min_segment_space_gb`: Minimum space for segments in GB (default: `50`)

## Dependencies

None

## Example Playbook

```yaml
- hosts: whpg_primary_site
  become: yes
  roles:
    - role: warehousepg-storage
      vars:
        whpg_storage_base: /data
        whpg_min_segment_space_gb: 100
```

## License

MIT

## Author Information

Created for WarehousePG storage provisioning.

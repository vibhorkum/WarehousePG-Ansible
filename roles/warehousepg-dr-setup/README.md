# WarehousePG DR Setup Role

This Ansible role configures disaster recovery (DR) replication for WarehousePG clusters by setting up:
- Standby coordinator on DR site
- Segment mirrors on DR site for cross-site high availability

## Requirements

- WarehousePG cluster must be initialized and running on the primary site
- DR site hosts must have WarehousePG installed and configured
- SSH passwordless authentication configured between all hosts
- Storage directories created on DR site hosts
- Network connectivity between primary and DR sites on required ports

## Role Variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

```yaml
# Enable standby coordinator setup
whpg_dr_enable_standby_coordinator: true

# Enable segment mirrors on DR site
whpg_dr_enable_segment_mirrors: true

# Standby coordinator configuration
whpg_standby_coordinator_port: 5433
whpg_standby_data_directory: "/data/coordinator/gpseg-1"

# Mirror configuration
whpg_mirror_port_base: 7000

# Replication settings
whpg_replication_checkpoint_segments: 8
whpg_replication_timeout: 300

# Verification settings
whpg_verify_replication: true
whpg_replication_lag_threshold_mb: 100
```

## Dependencies

This role depends on:
- `warehousepg-install` - For WarehousePG installation
- `warehousepg-init` - For cluster initialization

## Example Playbook

```yaml
---
- name: Setup WarehousePG DR Site Replication
  hosts: whpg_primary_coordinator
  become: yes
  roles:
    - role: warehousepg-dr-setup
      vars:
        whpg_dr_enable_standby_coordinator: true
        whpg_dr_enable_segment_mirrors: true
```

## Usage

### Setup Complete DR (Standby + Mirrors)

```bash
ansible-playbook -i inventory.yml dr_setup.yml
```

### Setup Only Standby Coordinator

```bash
ansible-playbook -i inventory.yml dr_setup.yml --tags standby
```

### Setup Only Segment Mirrors

```bash
ansible-playbook -i inventory.yml dr_setup.yml --tags mirrors
```

## DR Failover

After DR is configured, you can fail over to the DR site:

### Promote Standby Coordinator

```bash
# On DR coordinator host
gpactivatestandby -d /data/coordinator/gpseg-1
```

### Activate Mirrors as Primary Segments

```bash
# On new primary coordinator (former DR coordinator)
gprecoverseg -a
```

## Verification

Check DR replication status:

```bash
# Standby coordinator status
gpstate -f

# Mirror segment status
gpstate -m

# Full cluster status with mirrors
gpstate -e
```

## Inventory Requirements

Your inventory must have these groups defined:

```yaml
whpg_primary_site:
  children:
    whpg_primary_coordinator:
      hosts:
        whpg-coordinator: ...
    whpg_primary_segments:
      hosts:
        whpg-segment: ...

whpg_dr_site:
  children:
    whpg_dr_coordinator:
      hosts:
        whpg-coordinator: ...  # Same hostname, different site
    whpg_dr_segments:
      hosts:
        whpg-segment: ...  # Same hostname, different site
```

Each host should have:
- `ansible_host`: Public IP for SSH
- `private_ip`: Private IP for cluster communication
- `hostname`: System hostname
- `site_name`: Site identifier (site1, site2)
- `replication_alias`: Cross-site replication identifier
- `replication_server`: (DR hosts only) Primary site host to replicate from

## License

MIT

## Author Information

Created for WarehousePG multi-site disaster recovery deployments.

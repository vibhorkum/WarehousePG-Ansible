# WarehousePG Initialization Role

This Ansible role initializes a WarehousePG cluster using the `gpinitsystem` utility. It handles the complete initialization process including configuration file generation, cluster initialization, timezone setup, and environment variable configuration.

## Overview

The role performs the following tasks:

1. **Configuration File Generation**: Creates `gpinitsystem_config` and `hostfile_gpinitsystem` files
2. **Cluster Initialization**: Runs `gpinitsystem` to initialize the coordinator and segment instances
3. **Timezone Configuration**: Sets the cluster timezone using `gpconfig`
4. **Environment Setup**: Configures gpadmin user's `.bashrc` with WarehousePG environment variables
5. **Cluster Verification**: Verifies the cluster is running properly using `gpstate`

## Requirements

- WarehousePG packages must be installed (use `warehousepg-install` role)
- Storage directories must be created (use `warehousepg-storage` role)
- Passwordless SSH must be configured between all hosts
- Operating system must be properly configured (use `warehousepg-os-config` role)

## Role Variables

### Required Variables

```yaml
# Coordinator data directory - must exist before initialization
whpg_coordinator_directory: "/data/coordinator"

# Primary segment data directories (determines segments per host)
whpg_data_directories:
  - "/data1/primary"
  - "/data2/primary"
```

### Core Configuration Variables

```yaml
# GPHOME directory where WarehousePG is installed
whpg_gphome: "/usr/local/greenplum-db"

# Configuration directory for gpinitsystem files
whpg_config_dir: "/home/gpadmin/gpconfigs"

# Segment prefix for naming (default: gpseg)
whpg_seg_prefix: "gpseg"

# Port base for primary segments (default: 6000)
whpg_port_base: 6000

# Coordinator hostname (auto-detected from inventory)
whpg_coordinator_hostname: "{{ groups['whpg_coordinator'][0] }}"

# Coordinator port (default: 5432)
whpg_coordinator_port: 5432

# Trusted shell for remote operations (default: ssh)
whpg_trusted_shell: "ssh"

# Checkpoint segments (default: 8)
whpg_checkpoint_segments: 8

# Database encoding (default: UNICODE)
whpg_encoding: "UNICODE"
```

### Mirror Segment Configuration

```yaml
# Enable mirror segments (default: false)
whpg_enable_mirrors: false

# Port base for mirror segments (only used if mirrors are enabled)
whpg_mirror_port_base: 7000

# Mirror data directories (only used if mirrors are enabled)
whpg_mirror_data_directories:
  - "/data1/mirror"
  - "/data2/mirror"

# Mirror mode: spread or grouped (default: spread)
# Only used when whpg_use_dr_site_mirrors is false
whpg_mirror_mode: "spread"

# Use DR site for mirrors (default: false)
# When true, mirrors are placed on whpg_dr_segments hosts (cross-site HA)
# When false, mirrors use the same hosts as primaries (spread/grouped)
whpg_use_dr_site_mirrors: false
```

### DR Site Mirror Configuration

For cross-site high availability, you can place mirror segments on a separate DR site:

```yaml
# Enable mirrors on DR site
whpg_enable_mirrors: true
whpg_use_dr_site_mirrors: true

# Mirror configuration
whpg_mirror_port_base: 7000
whpg_mirror_data_directories:
  - "/data1/mirror"
  - "/data2/mirror"
```

When `whpg_use_dr_site_mirrors` is enabled:
- Primary segments run on hosts in `whpg_primary_segments` group
- Mirror segments run on hosts in `whpg_dr_segments` group
- Mirror mode is automatically set to `spread`
- Provides geographic redundancy for disaster recovery

**Inventory Example for DR Site Mirrors:**

```yaml
all:
  children:
    whpg_primary_site:
      children:
        whpg_primary_coordinator:
          hosts:
            whpg-coordinator:
              ansible_host: 192.168.1.10
        whpg_primary_segments:
          hosts:
            whpg-segment1:
              ansible_host: 192.168.1.11
            whpg-segment2:
              ansible_host: 192.168.1.12
    
    whpg_dr_site:
      children:
        whpg_dr_segments:
          hosts:
            dr-segment1:
              ansible_host: 10.20.30.11
            dr-segment2:
              ansible_host: 10.20.30.12
```

### Standby Coordinator Configuration

```yaml
# Standby coordinator hostname (optional - leave empty if not using)
whpg_standby_coordinator_hostname: ""
```

### Timezone and Environment

```yaml
# Timezone setting for WarehousePG (default: US/Pacific)
whpg_timezone: "US/Pacific"

# Default database name for environment variable
whpg_default_database: "gpadmin"

# Default user for environment variable
whpg_default_user: "gpadmin"
```

### Advanced Options

```yaml
# Whether to save cluster configuration during initialization
whpg_save_config: true

# Output configuration file path
whpg_output_config_file: "{{ whpg_config_dir }}/config_template"

# Locale setting (optional - uses system default if not set)
whpg_locale: ""

# Additional parameters for gpinitsystem_config (advanced)
whpg_additional_params: {}
```

## Dependencies

This role depends on:

- `warehousepg-install`: Installs WarehousePG packages
- `warehousepg-storage`: Creates storage directories

Ensure these roles have been executed before running this role.

## Example Inventory

```yaml
all:
  children:
    whpg_cluster:
      children:
        whpg_coordinator:
          hosts:
            whpg-cdw:
              ansible_host: 192.168.1.10
              private_ip: 10.0.1.10
        whpg_segments:
          hosts:
            whpg-sdw1:
              ansible_host: 192.168.1.11
              private_ip: 10.0.1.11
            whpg-sdw2:
              ansible_host: 192.168.1.12
              private_ip: 10.0.1.12
      vars:
        ansible_user: rocky
        ansible_ssh_private_key_file: ~/.ssh/id_rsa
```

## Example Playbook

### Basic Initialization

```yaml
---
- name: Initialize WarehousePG Cluster
  hosts: whpg_coordinator
  roles:
    - warehousepg-init
```

### Initialization with Mirrors

```yaml
---
- name: Initialize WarehousePG Cluster with Mirrors
  hosts: whpg_coordinator
  vars:
    whpg_enable_mirrors: true
    whpg_mirror_mode: "spread"
    whpg_data_directories:
      - "/data1/primary"
      - "/data2/primary"
    whpg_mirror_data_directories:
      - "/data1/mirror"
      - "/data2/mirror"
  roles:
    - warehousepg-init
```

### Initialization with DR Site Mirrors (Cross-Site HA)

For geographic redundancy, place mirrors on DR site:

```yaml
---
- name: Initialize WarehousePG with DR Site Mirrors
  hosts: whpg_primary_coordinator
  vars:
    whpg_enable_mirrors: true
    whpg_use_dr_site_mirrors: true
    whpg_data_directories:
      - "/data1/primary"
      - "/data2/primary"
    whpg_mirror_data_directories:
      - "/data1/mirror"
      - "/data2/mirror"
  roles:
    - warehousepg-init
```

This configuration will:
- Run primary segments on `whpg_primary_segments` hosts
- Run mirror segments on `whpg_dr_segments` hosts
- Provide cross-site redundancy for disaster recovery

### Initialization with Standby Coordinator

```yaml
---
- name: Initialize WarehousePG with Standby
  hosts: whpg_coordinator
  vars:
    whpg_standby_coordinator_hostname: "whpg-scdw"
    whpg_enable_mirrors: true
    whpg_mirror_mode: "spread"
  roles:
    - warehousepg-init
```

### Complete Workflow

```yaml
---
- name: Complete WarehousePG Installation and Initialization
  hosts: whpg_cluster
  roles:
    - warehousepg-os-config
    - warehousepg-install
    - warehousepg-storage

- name: Initialize WarehousePG Cluster
  hosts: whpg_coordinator
  vars:
    whpg_data_directories:
      - "/data1/primary"
      - "/data2/primary"
    whpg_enable_mirrors: false
    whpg_timezone: "UTC"
  roles:
    - warehousepg-init
```

## Usage

### Using the Standalone Playbook

```bash
# Initialize with default settings
ansible-playbook -i inventory.yml init.yml

# Initialize with custom data directories
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_data_directories=['/data1/primary','/data2/primary','/data3/primary']"

# Initialize with mirrors enabled
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread"

# Initialize with standby coordinator
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_standby_coordinator_hostname=whpg-scdw"
```

### Using Tags

The role doesn't define specific tags, but runs sequentially through all initialization steps.

## Idempotency

The role is idempotent:

- If the coordinator data directory (`{{ whpg_coordinator_directory }}/gpseg-1`) already exists, initialization tasks are skipped
- Environment variable setup checks if `.bashrc` is already configured
- The role always verifies cluster status at the end

## Generated Files

The role generates the following files:

```
/home/gpadmin/
├── gpconfigs/
│   ├── gpinitsystem_config       # Cluster configuration
│   ├── hostfile_gpinitsystem     # Segment host list
│   └── config_template           # Saved cluster config (optional)
├── .bashrc                        # Updated with WarehousePG environment
└── gpAdminLogs/                   # Initialization logs
    └── gpinitsystem_*.log
```

## Troubleshooting

### Initialization Fails

If `gpinitsystem` fails:

1. Check the logs in `/home/gpadmin/gpAdminLogs/`
2. Look for a backout script: `~/gpAdminLogs/backout_gpinitsystem_*`
3. Run the backout script to clean up:
   ```bash
   bash ~/gpAdminLogs/backout_gpinitsystem_gpadmin_<timestamp>
   ```
4. Fix the error and re-run the playbook

### Common Issues

**Issue**: Port conflicts
- **Solution**: Adjust `whpg_port_base` and `whpg_mirror_port_base` to use ports outside the range in `net.ipv4.ip_local_port_range`

**Issue**: Insufficient disk space
- **Solution**: Ensure enough space in data directories before initialization

**Issue**: SSH connectivity problems
- **Solution**: Verify passwordless SSH is working: `gpssh-exkeys -f hostfile_gpinitsystem`

**Issue**: Segment hosts not found
- **Solution**: Check `/etc/hosts` file contains all segment hostnames

## Verification

After initialization, verify the cluster:

```bash
# Check cluster status
gpstate -s

# Check configuration summary
gpstate -Q

# Connect to the database
psql -d gpadmin

# List all segments
SELECT * FROM gp_segment_configuration;
```

## Post-Initialization Steps

1. **Configure Client Access**: Edit `pg_hba.conf` to allow remote connections
2. **Create Users**: Create additional database users
3. **Create Databases**: Create application databases
4. **Load Data**: Begin loading data into the cluster
5. **Performance Tuning**: Adjust WarehousePG configuration parameters

## References

- [WarehousePG Documentation](https://warehouse-pg.io/docs/7x/install_guide/init_whpg.html)
- [gpinitsystem Reference](https://warehouse-pg.io/docs/7x/utility_guide/ref/gpinitsystem.html)
- [gpconfig Reference](https://warehouse-pg.io/docs/7x/utility_guide/ref/gpconfig.html)
- [gpstate Reference](https://warehouse-pg.io/docs/7x/utility_guide/ref/gpstate.html)

## License

MIT

## Author

Vibhor Kumar

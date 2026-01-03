# WarehousePG Ansible Playbook Examples

This document provides examples of how to use the WarehousePG Ansible roles for various scenarios.

## Table of Contents

- [Quick Installation](#quick-installation)
- [Step-by-Step Installation](#step-by-step-installation)
- [Cluster Initialization](#cluster-initialization)
- [Running Specific Tasks](#running-specific-tasks)
- [DR Site Setup](#dr-site-setup)
- [Common Operations](#common-operations)

## Quick Installation

For a complete installation in one command:

```bash
ansible-playbook -i inventory.yml quick_install.yml
```

This will:
1. Configure OS settings (sysctl, limits, SELinux, firewall, etc.)
2. Install WarehousePG packages
3. Create storage directories
4. Set up gpadmin user and SSH keys
5. Install dependencies
6. Configure environment
7. Initialize the cluster
8. Set up standby coordinator (if applicable)
9. Configure remote access

## Step-by-Step Installation

For more control over the installation process:

```bash
# Run the complete installation and configuration
ansible-playbook -i inventory.yml install_and_config.yml
```

Or run each phase separately:

```bash
# Phase 1: OS Configuration
ansible-playbook -i inventory.yml install_and_config.yml --tags os-config

# Phase 2: Installation
ansible-playbook -i inventory.yml install_and_config.yml --tags install

# Phase 3: Storage Setup
ansible-playbook -i inventory.yml install_and_config.yml --tags storage

# Phase 4: User and Environment Setup
ansible-playbook -i inventory.yml install_and_config.yml --tags setup

# Phase 5: Cluster Initialization
ansible-playbook -i inventory.yml install_and_config.yml --tags cluster-init

# Phase 6: Access Configuration
ansible-playbook -i inventory.yml install_and_config.yml --tags access-config

# Phase 7: Standby Setup
ansible-playbook -i inventory.yml install_and_config.yml --tags standby-setup

# Phase 8: Validation
ansible-playbook -i inventory.yml install_and_config.yml --tags validate
```

## Cluster Initialization

### Basic Cluster Initialization

Initialize a WarehousePG cluster with default settings:

```bash
ansible-playbook -i inventory.yml init.yml
```

This will:
1. Create gpinitsystem configuration files
2. Run gpinitsystem to initialize the cluster
3. Set the cluster timezone
4. Configure environment variables for gpadmin user
5. Verify the cluster is running

### Initialization with Custom Data Directories

Specify custom primary segment data directories:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_data_directories=['/data1/primary','/data2/primary','/data3/primary']"
```

The number of directories determines the number of segment instances per host.

### Initialization with Mirror Segments

Initialize with mirror segments for high availability:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread" \
  -e "whpg_mirror_data_directories=['/data1/mirror','/data2/mirror']"
```

Mirror modes:
- `spread`: Distributes mirrors across different hosts (recommended)
- `grouped`: Groups mirrors on the same host

### Initialization with DR Site Mirrors (Cross-Site HA)

For geographic redundancy, place mirrors on DR site hosts:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_use_dr_site_mirrors=true" \
  -e "whpg_mirror_data_directories=['/data1/mirror','/data2/mirror']"
```

This configuration:
- Runs primary segments on `whpg_primary_segments` hosts
- Runs mirror segments on `whpg_dr_segments` hosts
- Provides cross-site redundancy for disaster recovery
- Automatically uses `spread` mirror mode

**Requirements:**
- Inventory must have both `whpg_primary_segments` and `whpg_dr_segments` groups
- DR site hosts must be accessible from primary site
- Network latency should be considered for cross-site mirroring

### Initialization with Standby Coordinator

Initialize with a standby coordinator for automatic failover:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_standby_coordinator_hostname=whpg-scdw" \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread"
```

### Full High-Availability Configuration

Initialize a fully redundant cluster with mirrors and standby:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread" \
  -e "whpg_standby_coordinator_hostname=whpg-scdw" \
  -e "whpg_data_directories=['/data1/primary','/data2/primary']" \
  -e "whpg_mirror_data_directories=['/data1/mirror','/data2/mirror']"
```

### Custom Port Configuration

Adjust port settings if default ports conflict:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_port_base=6000" \
  -e "whpg_mirror_port_base=7000" \
  -e "whpg_coordinator_port=5432"
```

**Note**: Ensure ports are outside the range in `net.ipv4.ip_local_port_range`.

### Custom Timezone Configuration

Set a specific timezone for the cluster:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_timezone=UTC"

# Or use a specific timezone
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_timezone='America/New_York'"
```

### Save Cluster Configuration Template

Save cluster configuration during initialization for future reference:

```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_save_config=true" \
  -e "whpg_output_config_file=/home/gpadmin/gpconfigs/my_cluster_config"
```

### Re-initialization After Cleanup

If you need to re-initialize after cleanup or failure:

```bash
# 1. Clean up previous installation
ansible-playbook -i inventory.yml cleanup.yml \
  -e "whpg_cleanup_remove_data=true"

# 2. Recreate storage directories
ansible-playbook -i inventory.yml install_and_config.yml --tags storage

# 3. Re-initialize the cluster
ansible-playbook -i inventory.yml init.yml
```

### Initialization Variables Reference

Common initialization variables:

```yaml
# Core configuration
whpg_coordinator_directory: "/data/coordinator"
whpg_data_directories: 
  - "/data1/primary"
  - "/data2/primary"

# Port configuration
whpg_port_base: 6000
whpg_coordinator_port: 5432
whpg_mirror_port_base: 7000

# Mirror configuration (same-site)
whpg_enable_mirrors: false
whpg_mirror_mode: "spread"
whpg_mirror_data_directories:
  - "/data1/mirror"
  - "/data2/mirror"

# DR site mirror configuration (cross-site HA)
whpg_use_dr_site_mirrors: false  # When true, uses whpg_dr_segments for mirrors

# Standby configuration
whpg_standby_coordinator_hostname: ""

# Cluster settings
whpg_seg_prefix: "gpseg"
whpg_checkpoint_segments: 8
whpg_encoding: "UNICODE"
whpg_timezone: "US/Pacific"

# Environment
whpg_default_database: "gpadmin"
whpg_default_user: "gpadmin"

# Advanced
whpg_save_config: true
whpg_config_dir: "/home/gpadmin/gpconfigs"
```

**DR Site Mirrors Example:**

```yaml
# inventory.yml snippet
whpg_primary_site:
  children:
    whpg_primary_segments:
      hosts:
        segment1: ...
        segment2: ...

whpg_dr_site:
  children:
    whpg_dr_segments:
      hosts:
        dr-segment1: ...
        dr-segment2: ...
```

```bash
# Initialize with DR site mirrors
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_use_dr_site_mirrors=true"
```

# Port configuration
whpg_port_base: 6000
whpg_coordinator_port: 5432
whpg_mirror_port_base: 7000

# Mirror configuration
whpg_enable_mirrors: false
whpg_mirror_mode: "spread"
whpg_mirror_data_directories:
  - "/data1/mirror"
  - "/data2/mirror"

# Standby configuration
whpg_standby_coordinator_hostname: ""

# Cluster settings
whpg_seg_prefix: "gpseg"
whpg_checkpoint_segments: 8
whpg_encoding: "UNICODE"
whpg_timezone: "US/Pacific"

# Environment
whpg_default_database: "gpadmin"
whpg_default_user: "gpadmin"

# Advanced
whpg_save_config: true
whpg_config_dir: "/home/gpadmin/gpconfigs"
```

### Post-Initialization Verification

After initialization, verify the cluster:

```bash
# SSH to coordinator
ssh gpadmin@whpg-coordinator

# Check cluster status
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1
gpstate -s

# View cluster configuration
gpstate -Q

# Connect to database
psql -d gpadmin

# Inside psql, check segments
SELECT * FROM gp_segment_configuration;
```

## Running Specific Tasks

### OS Configuration Only

```bash
ansible-playbook -i inventory.yml install_and_config.yml --tags os-config
```

Specific OS configuration tasks:

```bash
# Configure sysctl only
ansible-playbook -i inventory.yml -e "whpg_os_config_sysctl=true whpg_os_config_limits=false ..." site.yml

# Configure firewall only
ansible-playbook -i inventory.yml install_and_config.yml --tags os-config \
  -e "whpg_os_config_firewall=true"
```

### User Management Only

```bash
ansible-playbook -i inventory.yml install_and_config.yml --tags user
```

### Cluster Initialization Only

```bash
ansible-playbook -i inventory.yml install_and_config.yml --tags cluster-init \
  --limit whpg_primary_coordinator
```

### Storage Creation Only

```bash
ansible-playbook -i inventory.yml install_and_config.yml --tags storage
```

## DR Site Setup

### Install DR Site

```bash
# Install WarehousePG on DR site
ansible-playbook -i inventory.yml quick_install.yml --limit whpg_dr_site
```

### Setup Standby on DR Site

```bash
ansible-playbook -i inventory.yml install_and_config.yml --tags standby-setup \
  --limit whpg_dr_coordinator
```

## Common Operations

### Check Installation Status

```bash
ansible whpg_primary_site -i inventory.yml -m command \
  -a "rpm -qa | grep warehouse-pg" -b
```

### Verify Cluster Status

```bash
ansible whpg_primary_coordinator -i inventory.yml \
  -m command -a "gpstate -Q" -b --become-user=gpadmin
```

### Restart Cluster

```bash
ansible whpg_primary_coordinator -i inventory.yml \
  -m command -a "gpstop -ar" -b --become-user=gpadmin
```

### Stop Cluster

```bash
ansible whpg_primary_coordinator -i inventory.yml \
  -m command -a "gpstop -a" -b --become-user=gpadmin
```

### Start Cluster

```bash
ansible whpg_primary_coordinator -i inventory.yml \
  -m command -a "gpstart -a" -b --become-user=gpadmin
```

### Check gpadmin User

```bash
ansible whpg_primary_site -i inventory.yml -m command -a "id gpadmin" -b
```

### Verify Storage Directories

```bash
# Check coordinator storage
ansible whpg_primary_coordinator -i inventory.yml \
  -m command -a "ls -ld /data/coordinator" -b

# Check segment storage
ansible whpg_primary_segments -i inventory.yml \
  -m shell -a "ls -ld /data/primary /data/mirror" -b
```

### Validate SSH Connectivity

```bash
# Test SSH from coordinator to segments
ansible whpg_primary_coordinator -i inventory.yml \
  -m shell -a "sudo -u gpadmin gpssh-exkeys -f /home/gpadmin/hostfile_segments" -b
```

## Advanced Examples

### Dry Run (Check Mode)

```bash
ansible-playbook -i inventory.yml install_and_config.yml --check
```

### Verbose Output

```bash
ansible-playbook -i inventory.yml install_and_config.yml -v
# or -vv, -vvv, -vvvv for more verbosity
```

### Run on Specific Hosts

```bash
# Only on primary coordinator
ansible-playbook -i inventory.yml install_and_config.yml \
  --limit whpg-primary-coordinator-1

# Only on segments
ansible-playbook -i inventory.yml install_and_config.yml \
  --limit whpg_primary_segments

# Only on specific host
ansible-playbook -i inventory.yml install_and_config.yml \
  --limit 192.168.1.101
```

### Override Variables

```bash
# Use different storage base
ansible-playbook -i inventory.yml install_and_config.yml \
  -e "whpg_storage_base=/mnt/data"

# Skip validation
ansible-playbook -i inventory.yml install_and_config.yml \
  -e "whpg_validate_storage_space=false"

# Use custom EDB token
ansible-playbook -i inventory.yml install_and_config.yml \
  -e "edb_subscription_token=your-token-here"
```

### Run with Different Inventory

```bash
ansible-playbook -i production_inventory.yml install_and_config.yml
```

## Troubleshooting

### View Task Output

```bash
# Show all facts
ansible whpg_primary_site -i inventory.yml -m setup -b

# Check specific variable
ansible whpg_primary_coordinator -i inventory.yml \
  -m debug -a "var=whpg_coordinator_data_directory"
```

### Validate Syntax

```bash
ansible-playbook -i inventory.yml install_and_config.yml --syntax-check
```

### List All Tasks

```bash
ansible-playbook -i inventory.yml install_and_config.yml --list-tasks
```

### List All Tags

```bash
ansible-playbook -i inventory.yml install_and_config.yml --list-tags
```

### List All Hosts

```bash
ansible-playbook -i inventory.yml install_and_config.yml --list-hosts
```

## Variable Customization Examples

Create a custom variables file:

```yaml
# custom_vars.yml
whpg_gpadmin_password: "MySecurePassword123!"
whpg_storage_base: "/mnt/warehousepg"
whpg_coordinator_port: 5433
whpg_validate_storage_space: true
whpg_min_segment_space_gb: 100

# OS Configuration overrides
whpg_os_sysctl_kernel_shmmax: 500000000000
whpg_os_limits_nofile_soft: 524288
whpg_os_limits_nofile_hard: 524288
```

Run with custom variables:

```bash
ansible-playbook -i inventory.yml install_and_config.yml \
  -e "@custom_vars.yml"
```

## Best Practices

1. **Always use version control** - Commit your inventory and variable files to git
2. **Test in development first** - Use `--check` mode before running on production
3. **Use tags for partial runs** - Isolate changes to specific components
4. **Keep sensitive data in vault** - Use `ansible-vault` for passwords and tokens
5. **Document your changes** - Add comments to custom variable files
6. **Backup before major changes** - Backup cluster configuration and data
7. **Monitor disk space** - Ensure sufficient space before installation
8. **Verify SSH connectivity** - Test SSH access before running playbooks
9. **Review logs** - Check `/var/log/messages` and WarehousePG logs after installation
10. **Use idempotent playbooks** - Roles are designed to be run multiple times safely

## Cleanup and Uninstallation

The roles support cleanup/uninstallation through the `cleanup.yml` playbook. This allows you to remove WarehousePG installation and optionally restore system defaults.

### Basic Cleanup (Packages Only)

Removes WarehousePG packages but keeps user account and data:

```bash
ansible-playbook -i inventory.yml cleanup.yml
```

### Cleanup Including User Removal

Removes packages and the gpadmin user account (but keeps data):

```bash
ansible-playbook -i inventory.yml cleanup.yml \
  -e "whpg_cleanup_remove_user=true"
```

### Full Cleanup (INCLUDING DATA DELETION)

⚠️ **DANGER**: This permanently deletes all WarehousePG data!

```bash
ansible-playbook -i inventory.yml cleanup.yml \
  -e "whpg_cleanup_remove_user=true" \
  -e "whpg_cleanup_remove_data=true"
```

### Cleanup Specific Roles Only

```bash
# Only remove packages (skip OS config restoration)
ansible-playbook -i inventory.yml cleanup.yml --tags install-cleanup

# Only remove storage directories
ansible-playbook -i inventory.yml cleanup.yml --tags storage-cleanup \
  -e "whpg_cleanup_remove_data=true"

# Only restore OS defaults
ansible-playbook -i inventory.yml cleanup.yml --tags os-cleanup
```

### Cleanup Control Variables

Control cleanup behavior with these variables:

- `whpg_cleanup_mode`: Enable cleanup mode (set automatically by cleanup.yml)
- `whpg_cleanup_remove_packages`: Remove WarehousePG packages (default: true)
- `whpg_cleanup_remove_user`: Remove gpadmin user and group (default: false)
- `whpg_cleanup_remove_data`: Remove all data directories (default: false)
- `whpg_cleanup_restore_defaults`: Restore OS settings to defaults (default: true)

### Cleanup Safety Features

The cleanup playbook includes several safety features:

1. **Interactive Warning**: Displays warning before starting cleanup
2. **Confirmation Prompts**: Requires confirmation for data deletion
3. **Conditional Execution**: Only runs destructive tasks when explicitly enabled
4. **Graceful Cluster Shutdown**: Attempts to stop cluster before removal
5. **Backup Restoration**: Restores /etc/hosts from backup if available
6. **Summary Report**: Shows what was cleaned up after completion

### Example: Controlled Cleanup

```yaml
# cleanup_vars.yml
whpg_cleanup_remove_packages: true
whpg_cleanup_remove_user: false
whpg_cleanup_remove_data: false
whpg_cleanup_restore_defaults: true
```

```bash
ansible-playbook -i inventory.yml cleanup.yml -e "@cleanup_vars.yml"
```

### Post-Cleanup Actions

After cleanup, consider:

1. **Reboot servers** - To fully restore OS settings
2. **Verify /etc/hosts** - Ensure no orphaned entries remain
3. **Check disk space** - Confirm storage was freed
4. **Review logs** - Check for any errors during cleanup
5. **Update inventory** - Remove cleaned hosts if decommissioned

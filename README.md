# WarehousePG Ansible Automation

Complete Ansible automation for WarehousePG High Availability installation and disaster recovery on Rocky Linux 9.3.

## Table of Contents

- [Quick Start](#quick-start)
- [Playbook Reference](#playbook-reference)
- [Configuration Guide](#configuration-guide)
  - [Inventory Setup](#inventory-setup)
  - [Segment Configuration](#segment-configuration)
  - [Mirror Configuration](#mirror-configuration)
- [Installation Examples](#installation-examples)
- [DR Setup and Verification](#dr-setup-and-verification)
- [Cluster Operations](#cluster-operations)
- [Troubleshooting](#troubleshooting)
- [Role Documentation](#role-documentation)

## Quick Start

### 1. Update Inventory

Edit `test_inventory.yml` with your server details:

```yaml
all:
  children:
    whpg_primary_site:
      children:
        whpg_primary_coordinator:
          hosts:
            whpg-coordinator:
              ansible_host: 10.0.2.40
              private_ip: 10.0.2.40
        whpg_primary_segments:
          hosts:
            whpg-segment:
              ansible_host: 10.0.9.61
              private_ip: 10.0.9.61
```

### 2. Set EDB Token

```bash
# Option 1: Edit quick_install.yml and set edb_subscription_token
# Option 2: Pass as extra var
ansible-playbook -i test_inventory.yml quick_install.yml \
  -e "edb_subscription_token=your_token_here"
```

### 3. Run Installation

```bash
# Complete installation
ansible-playbook -i test_inventory.yml quick_install.yml

# Initialize cluster
ansible-playbook -i test_inventory.yml init.yml

# Setup DR (optional)
ansible-playbook -i test_inventory.yml dr_setup.yml
```

## Playbook Reference

| Playbook | Purpose | Use When |
|----------|---------|----------|
| `quick_install.yml` | Complete installation: OS config, packages, storage | Fresh installation |
| `init.yml` | Cluster initialization with gpinitsystem | After quick_install.yml or to reinitialize |
| `dr_setup.yml` | Setup standby coordinator and segment mirrors on DR site | Adding DR to existing cluster |
| `validate.yml` | Performance testing with gpcheckperf | Validating hardware performance |
| `cleanup_all.yml` | Complete uninstallation and cleanup | Removing WarehousePG for fresh install |

### Playbook Details

#### quick_install.yml
Runs all roles in sequence:
1. OS configuration (sysctl, limits, SELinux, firewall)
2. User creation and package installation
3. Storage directory setup
4. SSH key configuration

**Does NOT** initialize the cluster - run `init.yml` afterward.

#### init.yml
- Creates gpinitsystem configuration files
- Initializes coordinator and segments
- Configures timezone and environment
- Verifies cluster is running

**Can be run multiple times** with `whpg_force_init=true` to reinitialize.

#### dr_setup.yml
- Configures standby coordinator on DR site
- Sets up segment mirrors on DR site
- Configures streaming replication
- Verifies replication status

#### validate.yml
- Network bandwidth tests between segments
- Disk I/O performance validation
- Memory bandwidth testing

#### cleanup_all.yml
- Terminates all WarehousePG processes
- Removes systemd user sessions
- Removes packages and data directories
- Removes gpadmin user
- Provides comprehensive verification output

## Configuration Guide

### Inventory Setup

The automation uses these inventory groups:

- `whpg_primary_coordinator`: Single coordinator host
- `whpg_primary_segments`: Primary segment hosts (1 to N servers)
- `whpg_standby_coordinator`: Standby coordinator (optional)
- `whpg_dr_segments`: DR site segment hosts for mirrors (optional)

### Segment Configuration

**Segment Calculation:**
```
Total Segments = (Number of Segment Servers) × (Directories per Server)
```

**Example 1: Single Segment Server**
```yaml
whpg_primary_segments:
  hosts:
    whpg-segment:
      ansible_host: 10.0.9.61

whpg_data_directories:
  - "/data/primary/seg1"
  - "/data/primary/seg2"
```
Result: **2 segment instances** on 1 server

**Example 2: Multiple Segment Servers**
```yaml
whpg_primary_segments:
  hosts:
    whpg-segment1:
      ansible_host: 192.168.1.11
    whpg-segment2:
      ansible_host: 192.168.1.12
    whpg-segment3:
      ansible_host: 192.168.1.13
    whpg-segment4:
      ansible_host: 192.168.1.14

whpg_data_directories:
  - "/data/primary/seg1"
  - "/data/primary/seg2"
```
Result: **8 segment instances** (4 servers × 2 directories)

**Segments Per Server Recommendations:**

| Cluster Size | Segment Servers | Segments per Server | Total Segments |
|--------------|-----------------|---------------------|----------------|
| Small (Dev/Test) | 1-2 | 2 | 2-4 |
| Medium (Production) | 4-8 | 2-4 | 8-32 |
| Large (Enterprise) | 16-64+ | 4-8 | 64-512+ |

**Guidelines:**
- **CPU cores**: Generally 1 segment per 2-4 cores
- **Memory**: At least 2-4 GB RAM per segment instance
- **Storage**: Separate disks for each data directory (optimal performance)
- **Network**: 10 GbE recommended for 16+ segments

### Mirror Configuration

#### Same-Site Mirrors (Spread Mode)

Distributes mirrors across different segment servers in the same site:

```yaml
whpg_enable_mirrors: true
whpg_mirror_mode: "spread"
whpg_use_dr_site_mirrors: false
whpg_mirror_data_directories:
  - "/data/mirror/seg1"
  - "/data/mirror/seg2"
```

**Distribution Pattern:**
- Primary on server 1 → Mirror on server 2
- Primary on server 2 → Mirror on server 1
- Primary on server 3 → Mirror on server 4
- Primary on server 4 → Mirror on server 3

#### DR Site Mirrors (Cross-Site HA)

Places mirrors on separate DR site servers for geographic redundancy:

```yaml
whpg_enable_mirrors: true
whpg_use_dr_site_mirrors: true
whpg_mirror_data_directories:
  - "/data/mirror/seg1"
  - "/data/mirror/seg2"
```

**Inventory requires matching DR segment hosts:**
```yaml
whpg_primary_segments:
  hosts:
    whpg-segment1:
      ansible_host: 192.168.1.11
    whpg-segment2:
      ansible_host: 192.168.1.12

whpg_dr_segments:
  hosts:
    dr-segment1:
      ansible_host: 10.20.30.11
    dr-segment2:
      ansible_host: 10.20.30.12
```

**Result:**
- Primary segments on whpg-segment1 → Mirrors on dr-segment1
- Primary segments on whpg-segment2 → Mirrors on dr-segment2

## Installation Examples

### Basic Installation

```bash
# Complete installation
ansible-playbook -i test_inventory.yml quick_install.yml

# Initialize cluster
ansible-playbook -i test_inventory.yml init.yml
```

### Installation with Same-Site Mirrors

```bash
ansible-playbook -i test_inventory.yml quick_install.yml

ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread" \
  -e "whpg_mirror_data_directories=['/data/mirror/seg1','/data/mirror/seg2']"
```

### Installation with DR Site Mirrors

```bash
# Install primary site
ansible-playbook -i test_inventory.yml quick_install.yml \
  --limit whpg_primary_site

# Install DR site
ansible-playbook -i test_inventory.yml quick_install.yml \
  --limit whpg_dr_site

# Initialize with DR mirrors
ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_use_dr_site_mirrors=true"
```

### Installation with Standby Coordinator

```bash
ansible-playbook -i test_inventory.yml quick_install.yml

ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_standby_coordinator_hostname=whpg-scdw" \
  -e "whpg_enable_mirrors=true"
```

### Full HA Configuration

```bash
ansible-playbook -i test_inventory.yml quick_install.yml

ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread" \
  -e "whpg_standby_coordinator_hostname=whpg-scdw" \
  -e "whpg_data_directories=['/data/primary/seg1','/data/primary/seg2']" \
  -e "whpg_mirror_data_directories=['/data/mirror/seg1','/data/mirror/seg2']"
```

### Custom Port Configuration

```bash
ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_port_base=6000" \
  -e "whpg_mirror_port_base=7000" \
  -e "whpg_coordinator_port=5432"
```

**Note:** Ensure ports are outside `net.ipv4.ip_local_port_range`.

### Custom Data Directories

```bash
ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_data_directories=['/data1/primary','/data2/primary','/data3/primary']"
```

The number of directories determines segments per server.

### Re-initialization After Cleanup

```bash
# 1. Clean up previous installation
ansible-playbook -i test_inventory.yml cleanup_all.yml

# 2. Reinstall
ansible-playbook -i test_inventory.yml quick_install.yml

# 3. Re-initialize
ansible-playbook -i test_inventory.yml init.yml
```

## DR Setup and Verification

### Setting Up DR

After primary cluster is initialized:

```bash
# Setup standby coordinator and segment mirrors
ansible-playbook -i test_inventory.yml dr_setup.yml
```

This will:
- Configure standby coordinator on DR site
- Setup segment mirrors on DR site
- Establish streaming replication
- Verify replication status

### DR Verification Commands

#### Check Standby Coordinator Status

```bash
# Run on primary coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1
gpstate -f
```

**Expected Output:**
```
Standby address          = dr-coordinator
Standby data directory   = /data/coordinator/gpseg-1
Standby port             = 5433
Standby status           = Standby host passive
WAL Sender State         = streaming
Sync state               = sync
```

#### Check Mirror Segments Status

```bash
gpstate -m
```

**Expected Output:**
```
Mirror               Datadir              Port   Status    Data Status
dr-segment           /data/mirror/seg1    7000   Passive   Synchronized
dr-segment           /data/mirror/seg2    7001   Passive   Synchronized
```

#### Check Complete Cluster Status

```bash
gpstate -s
```

#### Check Replication Lag

```bash
# Standby coordinator lag
psql -d postgres -c "SELECT client_addr, state, sync_state, 
  pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes 
  FROM pg_stat_replication;"

# Mirror segments lag
gpstate -e
```

### DR Failover Procedures

#### Activate Standby Coordinator (Primary Site Failure)

```bash
# Run on DR coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

# Promote standby to primary
gpactivatestandby -d /data/coordinator/gpseg-1 -a

# Verify new coordinator is active
gpstate -s
```

#### Activate Mirror Segments (Primary Segment Failure)

```bash
# Run on coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

# Recover failed segments (mirrors become primaries)
gprecoverseg -a

# Verify mirrors are active
gpstate -m
```

#### Resynchronize After Failover

```bash
# After primary site comes back online

# Option 1: Incremental recovery (if primary was down briefly)
gprecoverseg -a

# Option 2: Full recovery (if primary has stale data)
gprecoverseg -aF

# Rebalance segments to preferred roles
gprecoverseg -r -a
```

## Cluster Operations

### Verify Installation

```bash
# Check cluster status
ansible whpg-coordinator -i test_inventory.yml \
  -m shell \
  -a "source /usr/local/greenplum-db/greenplum_path.sh && \
      export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1 && \
      gpstate -s" \
  --become --become-user gpadmin

# Check package installation
ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "rpm -qa | grep warehouse-pg"
```

### Start/Stop Cluster

```bash
# Stop cluster
ansible whpg-coordinator -i test_inventory.yml \
  -m shell \
  -a "source /usr/local/greenplum-db/greenplum_path.sh && \
      export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1 && \
      gpstop -a" \
  --become --become-user gpadmin

# Start cluster
ansible whpg-coordinator -i test_inventory.yml \
  -m shell \
  -a "source /usr/local/greenplum-db/greenplum_path.sh && \
      export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1 && \
      gpstart -a" \
  --become --become-user gpadmin

# Restart cluster
ansible whpg-coordinator -i test_inventory.yml \
  -m shell \
  -a "source /usr/local/greenplum-db/greenplum_path.sh && \
      export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1 && \
      gpstop -ar" \
  --become --become-user gpadmin
```

### Database Operations

```bash
# Connect to coordinator
ssh gpadmin@whpg-coordinator

# Set environment
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

# Check segment configuration
psql -d postgres -c "SELECT * FROM gp_segment_configuration ORDER BY content, role;"

# Check database size
psql -d postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;"
```

### Performance Validation

```bash
# Run all performance tests
ansible-playbook -i test_inventory.yml validate.yml

# Run specific tests only
ansible-playbook -i test_inventory.yml validate.yml \
  -e "whpg_validate_network=true" \
  -e "whpg_validate_disk=false" \
  -e "whpg_validate_memory=false"
```

## Troubleshooting

### Check Connectivity

```bash
# Test Ansible connectivity
ansible all -i test_inventory.yml -m ping

# Check SSH access
ansible all -i test_inventory.yml -m shell -a "whoami"
```

### Common Issues

#### Package Installation Fails

**Symptom:** RPM shows installed but files missing

**Diagnosis:**
```bash
rpm -qa | grep warehouse-pg
ls -la /usr/local/greenplum-db-7.3.0-WHPG
```

**Solution:**
```bash
# Clean reinstall
ansible-playbook -i test_inventory.yml cleanup_all.yml
ansible-playbook -i test_inventory.yml quick_install.yml
```

#### SSH Key Exchange Fails

**Symptom:** Cannot SSH between hosts as gpadmin

**Diagnosis:**
```bash
ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "id gpadmin"

ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "ls -la /home/gpadmin/.ssh/" \
  --become --become-user gpadmin
```

**Solution:**
```bash
# Regenerate SSH keys
ansible-playbook -i test_inventory.yml quick_install.yml \
  --tags passwordless_ssh
```

#### Cluster Initialization Fails

**Symptom:** gpinitsystem fails with lock file errors

**Diagnosis:**
```bash
ls -la /tmp/.s.PGSQL*
ps aux | grep postgres
```

**Solution:**
```bash
# Clean up lock files
ansible-playbook -i test_inventory.yml cleanup_all.yml

# Reinstall and initialize
ansible-playbook -i test_inventory.yml quick_install.yml
ansible-playbook -i test_inventory.yml init.yml
```

#### Mirrors Showing as "Down" but Processes Running

**Symptom:** `gpstate -s` shows mirrors down but `gpstate -m` shows synchronized

**Diagnosis:**
```bash
# Check mirror processes
ssh dr-segment "ps aux | grep postgres | grep mirror"

# Check actual mirror status
gpstate -m
```

**Resolution:**
- If processes running and `gpstate -m` shows synchronized, this is a detection quirk - mirrors are fine
- If processes died: `gprecoverseg -a`
- If directories empty: `gprecoverseg -aF`

#### Standby Not Streaming

**Diagnosis:**
```bash
# Check standby process
ssh dr-coordinator "ps aux | grep postgres"

# Check replication on primary
psql -d postgres -c "SELECT * FROM pg_stat_replication;"
```

**Resolution:**
```bash
# Reinitialize standby
gpinitstandby -r -a  # Remove current standby
gpinitstandby -s dr-coordinator -P 5433 -a  # Re-add standby
```

### Viewing Logs

```bash
# Check WarehousePG logs
ssh whpg-coordinator
cat /data/coordinator/gpseg-1/log/gpdb-*.csv

# Check DNF logs
ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "tail -100 /var/log/dnf.log"

# Check system logs
ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "journalctl -u sshd -n 50"
```

## Key Variables

Configure in playbooks, `group_vars/all.yml`, or as extra vars:

### Installation Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `edb_subscription_token` | Required | EDB repository access token |
| `whpg_gpadmin_uid` | 530 | UID for gpadmin user |
| `whpg_gpadmin_gid` | 530 | GID for gpadmin group |

### Cluster Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_coordinator_directory` | /data/coordinator | Coordinator data directory |
| `whpg_coordinator_port` | 5432 | Coordinator database port |
| `whpg_data_directories` | [/data/primary/seg1, /data/primary/seg2] | Primary segment data directories |
| `whpg_port_base` | 6000 | Base port for segment instances |

### Mirror Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_enable_mirrors` | false | Enable mirror segments |
| `whpg_mirror_mode` | spread | Mirror distribution (spread/grouped) |
| `whpg_use_dr_site_mirrors` | false | Place mirrors on DR site |
| `whpg_mirror_data_directories` | [/data/mirror/seg1, /data/mirror/seg2] | Mirror segment data directories |
| `whpg_mirror_port_base` | 7000 | Base port for mirror instances |

### DR Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_dr_enable_standby_coordinator` | true | Setup standby coordinator |
| `whpg_dr_enable_segment_mirrors` | true | Setup segment mirrors |
| `whpg_standby_coordinator_hostname` | "" | Standby coordinator hostname |
| `whpg_standby_coordinator_port` | 5433 | Standby coordinator port |

See individual role README files for complete variable lists.

## Project Structure

```
WarehousePG-Ansible/
├── quick_install.yml           # Main installation playbook
├── init.yml                    # Cluster initialization
├── dr_setup.yml                # DR setup playbook
├── cleanup_all.yml             # Complete cleanup
├── validate.yml                # Performance validation
├── inventory.yml               # Production inventory template
├── test_inventory.yml          # Test/dev inventory
├── ansible.cfg                 # Ansible configuration
├── group_vars/
│   └── all/
│       ├── main.yml           # Default variables
│       └── vault.yml.example  # Vault template
└── roles/
    ├── warehousepg-install/    # User, packages, SSH
    ├── warehousepg-os-config/  # OS tuning
    ├── warehousepg-storage/    # Data directories
    ├── warehousepg-init/       # Cluster initialization
    ├── warehousepg-dr-setup/   # DR configuration
    └── warehousepg-validate/   # Performance validation
```

## Role Documentation

Each role has detailed documentation in its README.md:

- [warehousepg-install](roles/warehousepg-install/README.md): User management, package installation, SSH configuration
- [warehousepg-os-config](roles/warehousepg-os-config/README.md): OS tuning (sysctl, limits, SELinux, firewall)
- [warehousepg-storage](roles/warehousepg-storage/README.md): Data directory creation and configuration
- [warehousepg-init](roles/warehousepg-init/README.md): Cluster initialization with gpinitsystem
- [warehousepg-dr-setup](roles/warehousepg-dr-setup/README.md): Disaster recovery configuration
- [warehousepg-validate](roles/warehousepg-validate/README.md): Performance validation with gpcheckperf

## Architecture Support

**Single-Site HA**
```
Coordinator (Primary + Standby)
├── Segment 1 (Primary + Mirror)
└── Segment 2 (Primary + Mirror)
```

**Cross-Site DR**
```
Primary Site                DR Site
├── Coordinator      ←──→  Standby Coordinator
├── Segment 1        ←──→  Segment 1 Mirror
└── Segment 2        ←──→  Segment 2 Mirror
```

## Security Considerations

### Store Tokens Securely

```bash
# Create vault file
ansible-vault create group_vars/all/vault.yml

# Add token to vault
edb_subscription_token: "your_token_here"

# Run playbook with vault
ansible-playbook -i test_inventory.yml quick_install.yml --ask-vault-pass
```

### Use SSH Keys

Configure in inventory:
```yaml
all:
  vars:
    ansible_ssh_private_key_file: ~/.ssh/id_rsa
```

### Restrict Database Access

Edit `pg_hba.conf` after installation for production:
```bash
# On coordinator
vi /data/coordinator/gpseg-1/pg_hba.conf

# Reload configuration
gpstop -u
```

## Prerequisites

- Rocky Linux 9.3 or RHEL 9
- Ansible 2.9+
- Valid EDB subscription token
- SSH access with sudo privileges
- Python 3.6+ on managed nodes
- Minimum 4 GB RAM per host
- 20 GB+ disk space per segment

## License

MIT

## Author

Vibhor Kumar - WarehousePG HA Deployment Automation

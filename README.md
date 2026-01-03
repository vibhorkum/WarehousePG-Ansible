# WarehousePG Ansible Automation

Complete Ansible automation for WarehousePG High Availability installation on Rocky Linux 9.3.

## Project Structure

```
WarehousePG-Ansible/
├── ansible.cfg                 # Ansible configuration
├── inventory.yml               # Inventory file with host definitions
├── site.yml                    # Main playbook
├── quick_install.yml           # Quick installation playbook
├── install_and_config.yml      # Step-by-step installation
├── init.yml                    # Cluster initialization playbook
├── cleanup.yml                 # Cleanup/uninstall playbook
├── validate.yml                # Cluster validation playbook
├── PLAYBOOK_EXAMPLES.md        # Playbook usage examples
└── roles/
    ├── warehousepg-install/    # Installation and prerequisites
    │   ├── README.md
    │   ├── defaults/main.yml
    │   ├── tasks/
    │   │   ├── main.yml
    │   │   ├── user_management.yml
    │   │   ├── configure_hosts.yml
    │   │   ├── passwordless_ssh.yml
    │   │   └── cleanup.yml
    │   └── templates/
    ├── warehousepg-os-config/  # OS configuration and tuning
    │   ├── README.md
    │   ├── defaults/main.yml
    │   ├── tasks/
    │   │   ├── main.yml
    │   │   ├── sysctl.yml
    │   │   ├── limits.yml
    │   │   ├── selinux.yml
    │   │   ├── firewall.yml
    │   │   └── cleanup.yml
    │   └── templates/
    ├── warehousepg-storage/    # Storage directory setup
    │   ├── README.md
    │   ├── defaults/main.yml
    │   ├── tasks/
    │   │   ├── main.yml
    │   │   ├── coordinator_storage.yml
    │   │   ├── segment_storage.yml
    │   │   └── cleanup.yml
    ├── warehousepg-init/       # Cluster initialization
    │   ├── README.md
    │   ├── defaults/main.yml
    │   ├── tasks/
    │   │   ├── main.yml
    │   │   ├── create_config_files.yml
    │   │   ├── run_gpinitsystem.yml
    │   │   ├── configure_timezone.yml
    │   │   ├── setup_environment.yml
    │   │   └── verify_cluster.yml
    │   └── templates/
    │       ├── gpinitsystem_config.j2
    │       ├── hostfile_gpinitsystem.j2
    │       └── gpadmin_bashrc_additions.j2
    └── warehousepg-validate/   # Performance validation
        ├── README.md
        ├── defaults/main.yml
        ├── tasks/
        │   ├── main.yml
        │   ├── prerequisites.yml
        │   ├── network_validation.yml
        │   ├── disk_memory_validation.yml
        │   └── generate_report.yml
        └── templates/
            └── hostfile_gpcheckperf.j2
```

## Features

**Modular Role Architecture**
- Separate roles for installation, OS config, storage, initialization, and validation
- Independent execution or combined workflows
- Idempotent tasks for safe re-runs

**User Management**
- Creates gpadmin user (UID/GID: 530)
- Sets up passwordless SSH between all hosts
- Configures sudo access

**OS Configuration & Tuning**
- Kernel parameter optimization (sysctl)
- Resource limits configuration
- SELinux and firewall management
- Transparent Huge Pages (THP) disabled
- Network tuning for WarehousePG
- NTP/Chrony time synchronization

**WarehousePG Installation**
- RPM-based installation (version 7.3.0)
- EDB repository configuration
- Installs server, clients, and backup tools
- Configures environment variables

**Storage Management**
- Coordinator and segment data directory setup
- XFS filesystem configuration
- Proper permissions and ownership

**Cluster Initialization**
- Automated gpinitsystem execution
- Support for mirror segments (high availability)
- Standby coordinator configuration
- Timezone and environment setup
- Cluster verification

**Performance Validation**
- Network bandwidth testing (gpcheckperf)
- Disk I/O performance validation
- Memory bandwidth testing (STREAM)
- Configurable performance thresholds

**Cleanup & Maintenance**
- Complete uninstallation capability
- Selective cleanup (packages, user, data)
- OS settings restoration
- Safe cleanup with confirmations

**Network Configuration**
- /etc/hosts management
- Per-host IP preference (public vs private)
- Custom hostname configuration

## Prerequisites

- Rocky Linux 9.3
- Ansible 2.9 or higher
- Valid EDB subscription token
- SSH access to all nodes
- Sudo privileges on target hosts

## Quick Start

### 1. Update Inventory

Edit [inventory.yml](inventory.yml) with your server details:

```yaml
all:
  children:
    primary-coordinator:
      hosts:
        whpg1-coordinator:
          ansible_host: 110.0.0.4
          private_ip: 10.0.0.4
```

### 2. Configure Variables

Edit [site.yml](site.yml) or create a `group_vars/all.yml`:

```yaml
edb_subscription_token: "your_token_here"
whpg_gpadmin_password: "YourSecurePassword123"
```

### 3. Run the Playbook

```bash
# Install on all nodes
ansible-playbook site.yml

# Install only on primary coordinator
ansible-playbook site.yml --tags primary-coordinator

# Install only on standby nodes
ansible-playbook site.yml --tags standby-coordinator,standby-segments

# Dry run
ansible-playbook site.yml --check
```

## Usage Examples

### Deploy Complete HA Cluster

```bash
ansible-playbook site.yml
```

### Deploy Only Primary Infrastructure

```bash
ansible-playbook site.yml --limit primary-coordinator,primary-segments
```

### Reconfigure Access Controls

```bash
ansible-playbook site.yml --tags access
```

### Verify Installation

```bash
ansible primary-coordinator -m shell -a "source /usr/local/greenplum-db/greenplum_path.sh && gpstate -v" -u rocky
```

## Inventory Plugin

The custom `warehousepg` inventory plugin automatically resolves `upstream_node_private_ip` references to actual IP addresses. The role tasks use Ansible lookup plugins to retrieve this information dynamically.

**How it works:**

1. Define `upstream_node_private_ip` with a hostname reference in your inventory
2. The plugin automatically resolves it to the actual IP address
3. Tasks use `lookup('vars', 'hostvars')` to retrieve resolved values dynamically

**Before plugin processing:**
```yaml
standby-coordinator:
  upstream_node_private_ip: whpg1-coordinator
  replication_type: synchronous
```

**After plugin processing:**
```yaml
standby-coordinator:
  upstream_node_private_ip: whpg1-coordinator  # Original reference
  upstream_node_ip: 10.0.0.4                   # Resolved IP
  upstream_node_hostname: whpg1-coordinator    # Resolved hostname
  replication_type: synchronous
```

**Usage in tasks with lookup plugins:**
```yaml
# Tasks use Ansible lookup plugins to dynamically retrieve values
- set_fact:
    primary_ip: "{{ lookup('vars', 'hostvars')[inventory_hostname].upstream_node_ip }}"

# This allows for dynamic resolution at runtime
- name: Configure replication
  command: >
    pg_basebackup -h {{ primary_ip }} -p {{ whpg_coordinator_port }}
```

## Role Variables

Key variables in [roles/warehousepg/defaults/main.yml](roles/warehousepg/defaults/main.yml):

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_gpadmin_uid` | 530 | UID for gpadmin user |
| `whpg_gpadmin_gid` | 530 | GID for gpadmin group |
| `whpg_gpadmin_password` | NewPassword@123 | gpadmin password |
| `edb_subscription_token` | "" | EDB repository token (required) |
| `whpg_coordinator_port` | 6000 | Coordinator port |
| `whpg_segment_port_base` | 6002 | Base port for segments |
| `whpg_standby_port` | 6001 | Standby coordinator port |
| `whpg_pg_hba_allowed_cidr` | 10.0.0.0/16 | Allowed network for connections |

## Architecture

The role supports the following WarehousePG HA architecture:

```
Primary Site                    DR/Standby Site
┌─────────────────────┐        ┌─────────────────────┐
│ Primary Coordinator │◄──────►│ Standby Coordinator │
│   (Sync Replica)    │        │   (Async Replica)   │
└─────────────────────┘        └─────────────────────┘
         │                              │
    ┌────┴────┐                    ┌────┴────┐
    ▼         ▼                    ▼         ▼
┌────────┐ ┌────────┐         ┌────────┐ ┌────────┐
│Segment1│ │Segment2│         │Segment1│ │Segment2│
│Primary │ │Primary │         │Standby │ │Standby │
└────────┘ └────────┘         └────────┘ └────────┘
```

## Tags

Use tags to run specific parts of the deployment:

- `warehousepg`: All tasks
- `user`: User management only
- `dependencies`: System dependencies only
- `install`: WarehousePG installation only
- `configure`: Environment configuration only
- `init`: Cluster initialization only
- `cluster`: Cluster initialization only
- `standby`: Standby setup only
- `access`: Access configuration only

## Cluster Initialization

After installation and configuration, initialize the WarehousePG cluster:

### Basic Initialization
```bash
ansible-playbook -i inventory.yml init.yml
```

### Initialization with Mirrors (High Availability)
```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread"
```

### Initialization with Standby Coordinator
```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_standby_coordinator_hostname=whpg-scdw"
```

### Full HA Configuration
```bash
ansible-playbook -i inventory.yml init.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_mirror_mode=spread" \
  -e "whpg_standby_coordinator_hostname=whpg-scdw"
```

For more initialization examples, see:
- [init.yml playbook](init.yml)
- [warehousepg-init role README](roles/warehousepg-init/README.md)
- [PLAYBOOK_EXAMPLES.md - Cluster Initialization](PLAYBOOK_EXAMPLES.md#cluster-initialization)

## Troubleshooting

### Check SSH Connectivity
```bash
ansible all -m ping
```

### Verify gpadmin User
```bash
ansible all -m shell -a "id gpadmin"
```

### Check WarehousePG Version
```bash
ansible all -m shell -a "/usr/local/greenplum-db/bin/postgres --version"
```

### View Cluster Status
```bash
ansible primary-coordinator -m shell -a "source /usr/local/greenplum-db/greenplum_path.sh && gpstate -s" -u rocky
```

## Cleanup and Uninstallation

To remove WarehousePG installation and optionally restore system defaults:

### Basic Cleanup (Packages Only)
```bash
ansible-playbook -i inventory.yml cleanup.yml
```
This removes WarehousePG packages but keeps the gpadmin user and data directories.

### Full Cleanup (Including User)
```bash
ansible-playbook -i inventory.yml cleanup.yml -e "whpg_cleanup_remove_user=true"
```

### Complete Cleanup (Including Data)
⚠️ **WARNING**: This permanently deletes all WarehousePG data!
```bash
ansible-playbook -i inventory.yml cleanup.yml \
  -e "whpg_cleanup_remove_user=true" \
  -e "whpg_cleanup_remove_data=true"
```

### Cleanup Options
- `whpg_cleanup_remove_packages`: Remove packages (default: true)
- `whpg_cleanup_remove_user`: Remove gpadmin user (default: false)
- `whpg_cleanup_remove_data`: Remove data directories (default: false)
- `whpg_cleanup_restore_defaults`: Restore OS settings (default: true)

For more cleanup examples, see [PLAYBOOK_EXAMPLES.md](PLAYBOOK_EXAMPLES.md#cleanup-and-uninstallation).

## Security Considerations

1. **Token Management**: Store EDB token in Ansible Vault
   ```bash
   ansible-vault create group_vars/all/vault.yml
   ```

2. **SSH Keys**: Use SSH key-based authentication
3. **Firewall**: Configure firewall rules for ports 6000-6002
4. **Passwords**: Use strong passwords and Ansible Vault

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT

## Support

For issues and questions:
- Create an issue in the repository
- Refer to WarehousePG documentation
- Check EDB support portal

## Author
- Vibhor Kumar
Created for WarehousePG HA deployment automation.

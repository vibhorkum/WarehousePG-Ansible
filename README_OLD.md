# WarehousePG Ansible Automation

Complete Ansible automation for WarehousePG High Availability installation and disaster recovery on Rocky Linux 9.3.

## Quick Start

### 1. Update Inventory

Edit `test_inventory.yml` or `inventory.yml` with your server details:

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

Update the token in playbooks or use extra vars:

```bash
# Option 1: Edit quick_install.yml and set edb_subscription_token
# Option 2: Pass as extra var
ansible-playbook -i test_inventory.yml quick_install.yml \
  -e "edb_subscription_token=your_token_here"
```

### 3. Run Installation

```bash
# Complete primary site installation
ansible-playbook -i test_inventory.yml quick_install.yml

# Initialize cluster
ansible-playbook -i test_inventory.yml init.yml

# Setup DR (optional)
ansible-playbook -i test_inventory.yml dr_setup.yml
```

## Available Playbooks

| Playbook | Purpose |
|----------|---------|
| `quick_install.yml` | Complete installation: OS config, packages, storage, initialization |
| `init.yml` | Cluster initialization only (run after quick_install.yml) |
| `dr_setup.yml` | Setup disaster recovery: standby coordinator and mirrors |
| `validate.yml` | Performance validation using gpcheckperf |
| `cleanup_all.yml` | Complete cleanup and uninstallation |

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
└── roles/
    ├── warehousepg-install/    # User, packages, SSH
    ├── warehousepg-os-config/  # OS tuning (sysctl, limits, etc)
    ├── warehousepg-storage/    # Data directory setup
    ├── warehousepg-init/       # Cluster initialization
    ├── warehousepg-dr-setup/   # DR configuration
    └── warehousepg-validate/   # Performance validation
```
## Features

- **Modular Roles**: Separate concerns (install, OS config, storage, init, DR, validation)
- **Idempotent**: Safe to re-run playbooks
- **HA Ready**: Built-in support for standby coordinator and mirror segments
- **Cross-Site DR**: Configure disaster recovery across different sites/regions
- **Performance Validation**: Automated testing with gpcheckperf
- **Complete Cleanup**: Remove everything for fresh deployments

## Prerequisites

- Rocky Linux 9.3
- Ansible 2.9+
- Valid EDB subscription token
- SSH access with sudo privileges
- Python 3.6+ on managed nodes

## Common Usage Patterns

### Complete Fresh Installation
```bash
# 1. Clean slate (if reinstalling)
ansible-playbook -i test_inventory.yml cleanup_all.yml

# 2. Install and initialize primary site
ansible-playbook -i test_inventory.yml quick_install.yml

# 3. Setup DR (optional)
ansible-playbook -i test_inventory.yml dr_setup.yml

# 4. Validate performance
ansible-playbook -i test_inventory.yml validate.yml
```

### Installation with Custom Settings
```bash
ansible-playbook -i test_inventory.yml quick_install.yml \
  -e "whpg_enable_mirrors=true" \
  -e "whpg_use_dr_site_mirrors=true"
```

### Reinitialize Cluster Only
```bash
# Stop cluster, remove data, and reinitialize
ansible-playbook -i test_inventory.yml init.yml \
  -e "whpg_force_init=true"
```

## Key Variables

Configure in playbooks or `group_vars/all.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `edb_subscription_token` | Required | EDB repository access token |
| `whpg_gpadmin_uid` | 530 | UID for gpadmin user |
| `whpg_coordinator_port` | 5432 | Coordinator database port |
| `whpg_enable_mirrors` | false | Enable mirror segments |
| `whpg_use_dr_site_mirrors` | false | Place mirrors on DR site |

See individual role README files for complete variable lists.

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
├── Segment 1              └── Segment 1 Mirror
└── Segment 2              └── Segment 2 Mirror
```

## Verification

After installation, verify the cluster:

```bash
# Check cluster status
ansible whpg-coordinator -i test_inventory.yml \
  -m shell \
  -a "source /usr/local/greenplum-db/greenplum_path.sh && \
      export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1 && \
      gpstate -s" \
  --become --become-user gpadmin

# Check mirrors (if configured)
ansible whpg-coordinator -i test_inventory.yml \
  -m shell \
  -a "source /usr/local/greenplum-db/greenplum_path.sh && \
      export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1 && \
      gpstate -m" \
  --become --become-user gpadmin
```

## Cleanup

Complete removal of WarehousePG:

```bash
# Full cleanup (recommended for fresh reinstalls)
ansible-playbook -i test_inventory.yml cleanup_all.yml
```

The cleanup playbook:
- Stops all WarehousePG processes
- Removes data directories (/data/*)
- Removes installation files
- Removes gpadmin user
- Cleans up SSH keys and lock files
- Provides verification output

## Troubleshooting

### Check Connectivity
```bash
ansible all -i test_inventory.yml -m ping
```

### Check Package Installation
```bash
ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "rpm -qa | grep warehouse"
```

### View Installation Logs
```bash
# Check dnf logs on hosts
ansible whpg_primary_site -i test_inventory.yml \
  -m shell -a "tail -100 /var/log/dnf.log"
```

### Common Issues

1. **Package installation fails**: Check EDB token validity
2. **SSH key exchange fails**: Ensure gpadmin user exists on all hosts
3. **Cluster init fails**: Check lock files with `cleanup_all.yml`
4. **Mirror status shows Down**: Check `/data/mirror` permissions and `gpstate -m`

## Security Considerations

1. **Store tokens securely**:
   ```bash
   ansible-vault create group_vars/all/vault.yml
   # Add: edb_subscription_token: "your_token"
   
   # Run with vault
   ansible-playbook -i inventory.yml quick_install.yml --ask-vault-pass
   ```

2. **Use SSH keys**: Configure `ansible_ssh_private_key_file` in inventory

3. **Restrict pg_hba.conf**: Edit after installation for production

## Documentation

- **[PLAYBOOK_EXAMPLES.md](PLAYBOOK_EXAMPLES.md)**: Detailed playbook usage examples
- **[DR_VERIFICATION.md](DR_VERIFICATION.md)**: DR setup and verification guide
- **[SEGMENT_CONFIGURATION.md](SEGMENT_CONFIGURATION.md)**: Segment configuration details
- **Role READMEs**: Each role has detailed documentation in its README.md

## License

MIT

## Author

Vibhor Kumar - WarehousePG HA Deployment Automation

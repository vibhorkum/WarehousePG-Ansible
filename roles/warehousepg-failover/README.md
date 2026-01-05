# WarehousePG Failover Role

This role handles failover from the primary WarehousePG site to the DR site.

## Overview

The failover role performs the following operations:
1. **Pre-flight checks** - Verifies connectivity, replication lag, and mirror status
2. **Stop primary** (planned failover only) - Gracefully stops the primary cluster
3. **Promote standby** - Promotes the DR standby coordinator to primary
4. **Activate mirrors** - Ensures segment mirrors take over as primaries
5. **Post-failover verification** - Validates the new cluster is operational

## Requirements

- DR site must be configured with standby coordinator and segment mirrors
- SSH connectivity to DR site hosts
- `gpadmin` user with passwordless sudo

## Failover Modes

### Planned Failover
Use for scheduled maintenance or controlled switchover:
```yaml
whpg_failover_mode: planned
```
- Gracefully stops primary cluster
- Verifies replication is in sync
- Minimal to no data loss

### Unplanned Failover
Use when primary site is unavailable:
```yaml
whpg_failover_mode: unplanned
```
- Skips primary cluster operations
- Promotes DR immediately
- May have some data loss depending on replication lag

## Usage

### Basic Failover
```bash
ansible-playbook -i inventory.yml failover.yml
```

### Planned Failover (default)
```bash
ansible-playbook -i inventory.yml failover.yml -e "whpg_failover_mode=planned"
```

### Unplanned/Emergency Failover
```bash
ansible-playbook -i inventory.yml failover.yml -e "whpg_failover_mode=unplanned"
```

### Force Failover (skip safety checks)
```bash
ansible-playbook -i inventory.yml failover.yml -e "whpg_failover_force=true"
```

### Skip All Pre-checks
```bash
ansible-playbook -i inventory.yml failover.yml -e "whpg_failover_skip_checks=true"
```

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_failover_mode` | `planned` | `planned` or `unplanned` |
| `whpg_failover_force` | `false` | Skip safety assertions |
| `whpg_failover_skip_checks` | `false` | Skip all pre-flight checks |
| `whpg_failover_verify_replication_lag` | `true` | Check replication lag before failover |
| `whpg_failover_max_lag_mb` | `10` | Maximum allowed replication lag in MB |
| `whpg_coordinator_data_directory` | `/data/coordinator/gpseg-1` | Coordinator data directory |
| `whpg_coordinator_port` | `5432` | Coordinator port |

## Post-Failover Actions

After failover completes:

1. **Update application connection strings** to point to new primary:
   - Host: DR coordinator IP/hostname
   - Port: 5432 (default)

2. **Verify cluster health**:
   ```bash
   gpstate -e  # Check segment status
   gpstate -s  # Check cluster summary
   ```

3. **Plan for failback** (when original primary is recovered):
   - Rebuild old primary as new standby
   - Re-establish segment mirrors

## Example Playbook

Create `failover.yml`:
```yaml
---
- name: WarehousePG Failover to DR Site
  hosts: whpg_dr_coordinator
  become: yes
  gather_facts: yes
  
  vars:
    whpg_failover_mode: planned
    whpg_base_dir: /usr/local/greenplum-db-7.3.0-WHPG
    whpg_coordinator_data_directory: /data/coordinator/gpseg-1
  
  roles:
    - role: warehousepg-failover
```

## Troubleshooting

### Failover fails at pre-checks
- Use `-e "whpg_failover_force=true"` to bypass safety checks
- Or `-e "whpg_failover_skip_checks=true"` to skip all pre-checks

### Standby not responding
1. SSH to DR coordinator
2. Check standby process: `ps aux | grep postgres`
3. Check logs: `cat $COORDINATOR_DATA_DIRECTORY/log/startup.log`

### Segments not activating
1. Check segment status: `gpstate -e`
2. Run manual recovery: `gprecoverseg -a`
3. Check segment logs on DR segment hosts

## Author

EDB - EnterpriseDB

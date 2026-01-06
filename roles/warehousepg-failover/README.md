# WarehousePG Failover Role

This role handles failover from the primary WarehousePG site to the DR site using
the standard Greenplum DR workflow.

## Overview

The failover role uses the **correct industry-standard Greenplum DR workflow**:

1. **Pre-flight checks** - Verifies connectivity and cluster readiness
2. **Stop primary** (planned failover only) - Gracefully stops the primary cluster
3. **Promote standby coordinator** - Uses `gpactivatestandby` to promote DR coordinator
4. **FTS automatic segment failover** - Fault Tolerance Service automatically promotes mirrors
5. **Post-failover verification** - Validates cluster and provides recovery guidance

### Critical Design Principles

- **DO NOT manually rename segment directories** - This corrupts catalog metadata
- **FTS handles segment failover automatically** - No manual intervention needed
- **`gprecoverseg` is for recovery ONLY** - Used after DR is running to rebuild old primary

### How FTS Segment Failover Works

When `gpactivatestandby` promotes the DR coordinator:
1. The new coordinator connects to segments
2. FTS detects that original primary segments are unreachable
3. FTS automatically promotes DR mirror segments to "Acting Primary" (role='m', preferred_role='p')
4. The cluster becomes fully operational automatically

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
- Gracefully stops primary cluster with `gpstop -M fast -a`
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

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_failover_mode` | `planned` | `planned` or `unplanned` |
| `whpg_failover_force` | `false` | Skip safety assertions |
| `whpg_failover_skip_checks` | `false` | Skip all pre-flight checks |
| `whpg_coordinator_data_directory` | `/data/coordinator/gpseg-1` | Coordinator data directory |
| `whpg_coordinator_port` | `5432` | Coordinator port |
| `whpg_fts_wait_timeout` | `120` | Seconds to wait for FTS segment failover |

## Post-Failover Actions

After failover completes:

### 1. Update Application Connections
Point applications to the new primary:
- **Host**: DR coordinator IP/hostname
- **Port**: 5432 (default)

### 2. Verify Cluster Health
```bash
gpstate -s   # Cluster summary
gpstate -e   # Segment status (may show Down segments for old primary)
gpstate -m   # Mirror status
```

### 3. Recover Old Primary Site (When Ready)
When the old primary site is back online and you want to rebuild it as mirrors:

```bash
# Option A: Incremental recovery (faster, if data directories intact)
gprecoverseg -a

# Option B: Full recovery (if data directories corrupted/missing)
gprecoverseg -aF

# After recovery completes, optionally rebalance to original roles
gprecoverseg -ra
```

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

### Segments showing "Acting Primary" (role=m, preferred_role=p)
This is NORMAL after failover. The mirrors have taken over as primaries.
- Cluster is operational - no action required
- Run `gprecoverseg -a` when old primary site is available to rebuild it

### Some segments still Down
If FTS hasn't completed:
1. Wait longer (FTS may take up to 2 minutes)
2. Check: `gpstate -e`
3. The Down segments are the OLD primary site - expected if that site is offline

### Want to recover old primary site as mirrors
```bash
# After old primary site is back online:
gprecoverseg -a         # Incremental recovery
# OR
gprecoverseg -aF        # Full recovery (slower, more reliable)

# Then optionally rebalance to original preferred roles:
gprecoverseg -ra
```

## Architecture Notes

### Why We Don't Rename Directories

The old approach of renaming segment directories is **dangerous** because:
1. Greenplum's `gp_segment_configuration` catalog tracks segments by their data directories
2. Renaming directories causes the catalog to become inconsistent
3. Can lead to split-brain scenarios where old and new primaries both think they're active
4. Corrupts the cluster metadata

### The Correct Approach

1. **gpactivatestandby** - Promotes the standby coordinator, which becomes the new cluster coordinator
2. **FTS (Fault Tolerance Service)** - Automatically detects that old primary segments are unreachable and promotes mirrors
3. **gprecoverseg** - Used ONLY for recovery, not for failover. Rebuilds segments from existing primaries.

## Author

EDB - EnterpriseDB

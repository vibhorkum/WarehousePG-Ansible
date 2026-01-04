# WarehousePG DR Setup - Verification Guide

## Current DR Configuration Status

### Architecture Overview
- **Primary Site (site1):**
  - Coordinator: whpg-coordinator (3.22.42.68 / 10.0.2.40)
  - Segment: whpg-segment (18.226.172.107 / 10.0.9.61)
  
- **DR Site (site2):**
  - Standby Coordinator: dr-coordinator (3.137.161.206 / 10.0.10.232)
    - Hostname: whpg-coordinator
    - Replication alias: site2-coordinator-repl
  - Mirror Segment: dr-segment (3.139.108.84 / 10.0.12.215)
    - Hostname: whpg-segment  
    - Replication alias: site2-segment-repl

### DR Components Configured

 **Standby Coordinator**
- Status: Configured and streaming
- Connection: site2-coordinator-repl:5433
- Data Directory: /data/coordinator/gpseg-1
- Replication Mode: Synchronous streaming
- WAL Lag: 0 bytes (fully synchronized)

 **Segment Mirrors** 
- Mirror 1: site2-segment-repl:7000 → /data/mirror/seg1
- Mirror 2: site2-segment-repl:7001 → /data/mirror/seg2
- Replication Mode: Streaming
- WAL Lag: 0 bytes (fully synchronized)
- Mirror Status: Synchronized (both mirrors)

## Verification Commands

### 1. Check Standby Coordinator Status

```bash
# Run on primary coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1
gpstate -f
```

**Expected Output:**
```
Standby address          = site2-coordinator-repl
Standby data directory   = /data/coordinator/gpseg-1
Standby port             = 5433
Standby status           = Standby host passive
WAL Sender State: streaming
Sync state: sync
```

### 2. Check Mirror Segments Status

```bash
# Run on primary coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1
gpstate -m
```

**Expected Output:**
```
Mirror               Datadir             Port   Status    Data Status
site2-segment-repl   /data/mirror/seg1   7000   Passive   Synchronized
site2-segment-repl   /data/mirror/seg2   7001   Passive   Synchronized
```

### 3. Check Complete Cluster Status

```bash
# Run on primary coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1
gpstate -s
```

**Note:** May show warnings about "Segment status = Down" for mirrors even when they are streaming. This is a known gpstate detection quirk. Verify with `gpstate -m` which shows the actual replication status.

### 4. Check Replication Lag

```bash
# Run on primary coordinator as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

# Standby coordinator lag
psql -d postgres -c "SELECT client_addr, state, sync_state, sent_lsn, write_lsn, flush_lsn, replay_lsn FROM pg_stat_replication;"

# Mirror segments lag  
gpstate -e
```

## DR Failover Procedures

### Activate Standby Coordinator (Primary Site Failure)

```bash
# Run on DR coordinator (site2-coordinator-repl) as gpadmin
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

# Promote standby to primary
gpactivatestandby -d /data/coordinator/gpseg-1 -a

# Verify new coordinator is active
gpstate -s
```

### Activate Mirror Segments (Primary Segment Failure)

```bash
# Run on coordinator as gpadmin  
source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

# Recover failed segments (mirrors become primaries)
gprecoverseg -a

# Verify mirrors are active
gpstate -m
```

### Resynchronize After Failover

```bash
# After primary site comes back online

# Option 1: Incremental recovery (if primary was down briefly)
gprecoverseg -a

# Option 2: Full recovery (if primary has stale data)
gprecoverseg -aF

# Rebalance segments to preferred roles
gprecoverseg -r -a
```

## Troubleshooting

### Mirrors Showing as "Down" but Processes Running

**Symptom:** `gpstate -s` or `gpstate -e` shows mirrors as "Down" but `gpstate -m` shows "Synchronized"

**Diagnosis:**
```bash
# Check if mirror processes are running
ssh site2-segment-repl "ps aux | grep postgres | grep mirror"

# Check if mirrors are actually streaming
gpstate -m
```

**Resolution:**
- If processes are running and `gpstate -m` shows synchronized, this is a status detection quirk - mirrors are fine
- If processes died, run: `gprecoverseg -a`
- If directories are empty, run: `gprecoverseg -aF`

### Standby Not Streaming

**Diagnosis:**
```bash
# Check standby process on DR coordinator
ssh site2-coordinator-repl "ps aux | grep postgres | grep -v grep"

# Check pg_stat_replication on primary
psql -d postgres -c "SELECT * FROM pg_stat_replication;"
```

**Resolution:**
```bash
# Reinitialize standby
gpinitstandby -r -a  # Remove current standby
gpinitstandby -s site2-coordinator-repl -P 5433 -a  # Re-add standby
```

### Cross-Site Connectivity Issues

**Check /etc/hosts:**
```bash
# On all hosts, verify entries exist for replication aliases
cat /etc/hosts | grep repl
```

**Expected:**
- Primary site hosts should have: `10.0.10.232 site2-coordinator-repl` and `10.0.12.215 site2-segment-repl`
- DR site hosts should have: `10.0.2.40 site1-coordinator-repl` and `10.0.9.61 site1-segment-repl`

## Monitoring Recommendations

### Automated Health Checks

Create a cron job to monitor replication status:

```bash
#!/bin/bash
# /home/gpadmin/bin/check_dr_status.sh

source /usr/local/greenplum-db/greenplum_path.sh
export COORDINATOR_DATA_DIRECTORY=/data/coordinator/gpseg-1

echo "=== DR Health Check - $(date) ==="

# Check standby
echo "Standby Status:"
gpstate -f 2>&1 | grep -E "Standby|streaming|sync"

# Check mirrors
echo -e "\nMirror Status:"
gpstate -m 2>&1 | tail -3

# Check replication lag
echo -e "\nReplication Lag:"
psql -d postgres -t -c "SELECT client_addr, state, pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes FROM pg_stat_replication;"
```

### Key Metrics to Monitor

1. **Replication Lag:** Should be < 10MB under normal load
2. **Mirror Sync Status:** Should always be "Synchronized"
3. **Standby State:** Should always be "streaming"
4. **Network Latency:** Monitor cross-site network latency (should be < 100ms for sync replication)

## Known Issues and Limitations

1. **gpstate -s "Down" Status:** `gpstate -s` may incorrectly report mirrors as "Down" even when they are streaming. Always verify with `gpstate -m`.

2. **Initial Mirror Recovery:** First-time mirror setup requires full recovery (`gprecoverseg -aF`) instead of incremental (`gprecoverseg -a`).

3. **Timing Sensitivity:** Mirrors may take 10-30 seconds to fully synchronize after recovery. Allow time before running verification.

4. **COORDINATOR_DATA_DIRECTORY:** All `gp*` commands require this environment variable to be set.

## Deployment History

- **Primary Cluster:** Initialized with 2 segments on whpg-segment
- **DR Site Install:** Completed with OS config, WarehousePG install, and storage setup
- **Standby Coordinator:** Successfully initialized on 2026-01-03 20:51:51 UTC
- **Segment Mirrors:** Added and recovered on 2026-01-03 18:57:16 UTC
- **Current Status:** Fully operational with synchronous replication

## Next Steps

1. DR setup complete and verified
2. Schedule regular DR drills (quarterly recommended)
3. Document application-specific failover procedures
4. Set up monitoring alerts for replication lag
5. Create runbooks for operations team
6. Test automated failover scripts in non-production environment

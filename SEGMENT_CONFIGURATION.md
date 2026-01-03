# WarehousePG Segment Configuration Guide

This document explains how segment configuration works in this Ansible automation.

## Understanding Segments in WarehousePG

### What are Segments?

In WarehousePG (Greenplum-based), segments are the database instances that store and process data. The coordinator distributes queries to segments for parallel processing.

### Segment Calculation

**Total Segment Instances = (Number of Segment Servers) × (Number of Data Directories per Server)**

Example:
- 3 segment servers
- 2 data directories per server (`whpg_data_directories` has 2 entries)
- **Total segments = 3 × 2 = 6 segment instances**

## Inventory Configuration

### Group Names

The automation uses these inventory groups:

- **`whpg_primary_coordinator`**: Single coordinator host
- **`whpg_primary_segments`**: All primary segment hosts (can be 1 to N servers)
- **`whpg_dr_segments`**: All DR segment hosts for mirrors (optional)

### Single Segment Server Example

```yaml
whpg_primary_segments:
  hosts:
    whpg-segment:
      ansible_host: 18.226.172.107
      hostname: whpg-segment
```

With `whpg_data_directories: ["/data1/primary", "/data2/primary"]`:
- **Result**: 2 segment instances on 1 server

### Multiple Segment Servers Example

```yaml
whpg_primary_segments:
  hosts:
    whpg-segment1:
      ansible_host: 192.168.1.11
      hostname: whpg-segment1
    
    whpg-segment2:
      ansible_host: 192.168.1.12
      hostname: whpg-segment2
    
    whpg-segment3:
      ansible_host: 192.168.1.13
      hostname: whpg-segment3
    
    whpg-segment4:
      ansible_host: 192.168.1.14
      hostname: whpg-segment4
```

With `whpg_data_directories: ["/data1/primary", "/data2/primary"]`:
- **Result**: 8 segment instances (4 servers × 2 directories)

### Segments Per Server

The number of segment instances per server is controlled by `whpg_data_directories`:

```yaml
# 1 segment per server
whpg_data_directories:
  - "/data1/primary"

# 2 segments per server
whpg_data_directories:
  - "/data1/primary"
  - "/data2/primary"

# 4 segments per server
whpg_data_directories:
  - "/data1/primary"
  - "/data2/primary"
  - "/data3/primary"
  - "/data4/primary"

# 6 segments per server (for high-performance systems)
whpg_data_directories:
  - "/data1/primary"
  - "/data2/primary"
  - "/data3/primary"
  - "/data4/primary"
  - "/data5/primary"
  - "/data6/primary"
```

## How It Works

### 1. Hostfile Generation

The role generates a hostfile (`hostfile_gpinitsystem`) that lists all segment servers:

```
# Generated from inventory whpg_primary_segments group
whpg-segment1
whpg-segment2
whpg-segment3
whpg-segment4
```

### 2. gpinitsystem Behavior

The `gpinitsystem` utility:
1. Reads the hostfile to get all segment servers
2. Reads `DATA_DIRECTORY` array to know how many segments per server
3. Creates segment instances across all listed servers

For 4 servers with 2 data directories each:

| Server | Segment Instance | Port | Data Directory |
|--------|------------------|------|----------------|
| whpg-segment1 | gpseg0 | 6000 | /data1/primary |
| whpg-segment1 | gpseg1 | 6001 | /data2/primary |
| whpg-segment2 | gpseg2 | 6000 | /data1/primary |
| whpg-segment2 | gpseg3 | 6001 | /data2/primary |
| whpg-segment3 | gpseg4 | 6000 | /data1/primary |
| whpg-segment3 | gpseg5 | 6001 | /data2/primary |
| whpg-segment4 | gpseg6 | 6000 | /data1/primary |
| whpg-segment4 | gpseg7 | 6001 | /data2/primary |

## Mirror Configuration

### Same-Site Mirrors (Spread Mode)

Mirrors are distributed across different segment servers:

```yaml
whpg_enable_mirrors: true
whpg_mirror_mode: "spread"
whpg_use_dr_site_mirrors: false
```

With 4 segment servers:
- Primary for server 1 → Mirror on server 2
- Primary for server 2 → Mirror on server 1
- Primary for server 3 → Mirror on server 4
- Primary for server 4 → Mirror on server 3

### DR Site Mirrors (Cross-Site HA)

Mirrors are placed on separate DR site servers:

```yaml
whpg_enable_mirrors: true
whpg_use_dr_site_mirrors: true
```

Inventory requires matching DR segment servers:

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

Result:
- Primary segments on whpg-segment1 → Mirrors on dr-segment1
- Primary segments on whpg-segment2 → Mirrors on dr-segment2

## Scaling Guidelines

### Small Cluster (Development/Test)
- **Segment servers**: 1-2
- **Segments per server**: 2
- **Total segments**: 2-4

### Medium Cluster (Production)
- **Segment servers**: 4-8
- **Segments per server**: 2-4
- **Total segments**: 8-32

### Large Cluster (Enterprise)
- **Segment servers**: 16-64+
- **Segments per server**: 4-8
- **Total segments**: 64-512+

### Recommendations

1. **CPU Cores**: Segments per server ≈ Number of CPU cores / 2
2. **Memory**: At least 2GB RAM per segment instance
3. **Storage**: Use separate disks for different data directories
4. **Network**: 10Gbps+ recommended for large clusters

## Adding Segment Servers

### Step 1: Update Inventory

Add new servers to `whpg_primary_segments` group:

```yaml
whpg_primary_segments:
  hosts:
    whpg-segment1:
      ansible_host: 192.168.1.11
      hostname: whpg-segment1
    
    # New server
    whpg-segment5:
      ansible_host: 192.168.1.15
      hostname: whpg-segment5
```

### Step 2: Run Installation

```bash
# Install OS config, packages, and storage on new server
ansible-playbook -i inventory.yml install_and_config.yml \
  --limit whpg-segment5 \
  --tags os-config,install,storage
```

### Step 3: Expand Cluster

After initial cluster is running, use `gpexpand` utility to add new segments:

```bash
# SSH to coordinator
sudo su - gpadmin

# Create expansion input file
gpexpand -f hostfile_expansion

# Run expansion
gpexpand -i gpexpand_inputfile_YYYYMMDD_HHMMSS
```

**Note**: Adding segments to an existing cluster requires the `gpexpand` utility, which is separate from initial cluster creation.

## Verification

After cluster initialization, verify segment configuration:

```bash
# SSH to coordinator
sudo su - gpadmin

# Check all segments
gpstate -e

# Query segment configuration
psql -d gpadmin -c "
  SELECT 
    content,
    role,
    preferred_role,
    mode,
    status,
    hostname,
    port,
    datadir
  FROM gp_segment_configuration
  ORDER BY content, role DESC;
"
```

## Common Patterns

### Pattern 1: Symmetric Configuration
All segment servers have identical hardware and configuration:
- Same number of CPU cores
- Same amount of RAM
- Same disk layout
- Same number of data directories

**Recommended**: Yes, this is the standard configuration

### Pattern 2: Multi-Interface Segments
Servers with multiple network interfaces can have segments bound to different interfaces:

```yaml
whpg_primary_segments:
  hosts:
    whpg-segment1:
      ansible_host: 192.168.1.11
      hostname: whpg-segment1
      whpg_segment_interfaces:
        - whpg-segment1-nic1  # First interface
        - whpg-segment1-nic2  # Second interface
```

This creates entries in the hostfile for network redundancy.

### Pattern 3: Heterogeneous Clusters
Different segment servers with different capacities:

**Not Recommended**: WarehousePG performs best with symmetric configuration

## Troubleshooting

### Issue: Wrong Number of Segments

**Problem**: Expected 8 segments but only got 4

**Solution**: Check `whpg_data_directories` length
```yaml
# This creates 2 segments per server
whpg_data_directories:
  - "/data1/primary"
  - "/data2/primary"

# For 4 servers, total = 4 × 2 = 8 segments
```

### Issue: Segments Not Distributed

**Problem**: All segments on one server

**Solution**: Check inventory has multiple hosts in `whpg_primary_segments`
```yaml
# Wrong - only one host
whpg_primary_segments:
  hosts:
    whpg-segment: ...

# Correct - multiple hosts
whpg_primary_segments:
  hosts:
    whpg-segment1: ...
    whpg-segment2: ...
    whpg-segment3: ...
```

### Issue: Mirror Placement

**Problem**: Mirrors on same host as primaries

**Solution**: 
- For same-site mirrors: Need at least 2 segment servers
- For DR site mirrors: Set `whpg_use_dr_site_mirrors: true`

## References

- [WarehousePG Initialization Documentation](https://warehouse-pg.io/docs/7x/install_guide/init_whpg.html)
- [gpinitsystem Reference](https://warehouse-pg.io/docs/7x/utility_guide/ref/gpinitsystem.html)
- [gpexpand Reference](https://warehouse-pg.io/docs/7x/utility_guide/ref/gpexpand.html)
- Role README: [roles/warehousepg-init/README.md](roles/warehousepg-init/README.md)

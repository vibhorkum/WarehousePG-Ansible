# WarehousePG Segment Mirrors Role

This role configures segment mirrors for a WarehousePG cluster. It supports three mirror modes to provide flexibility for different deployment scenarios.

## Mirror Modes

### 1. Same Host Mode (`same_host`)
Mirrors are created on the **same servers** as primary segments using different ports and directories.

- **Use case**: Development, testing, or when hardware is limited
- **Pros**: No additional servers needed
- **Cons**: No protection against host failure

```yaml
whpg_mirror_mode: "same_host"
```

### 2. Spread Mode (`spread`)
Mirrors are distributed across existing segment hosts in a round-robin fashion.

- Host A's primaries → mirrors on Host B
- Host B's primaries → mirrors on Host C
- Host N's primaries → mirrors on Host A (wrap around)

- **Use case**: Production with multiple segment hosts
- **Pros**: Protection against single host failure without additional servers
- **Cons**: Requires at least 2 segment hosts

```yaml
whpg_mirror_mode: "spread"
```

### 3. Remote Hosts Mode (`remote_hosts`)
Mirrors are created on **dedicated separate hosts** defined in `whpg_mirror_segments` inventory group.

- **Use case**: Maximum availability, DR configurations
- **Pros**: Complete isolation of mirrors from primaries
- **Cons**: Requires additional hardware

```yaml
whpg_mirror_mode: "remote_hosts"
```

## Requirements

- WarehousePG cluster initialized and running
- For `remote_hosts` mode: `whpg_mirror_segments` group defined in inventory
- For `spread` mode: At least 2 segment hosts

## Role Variables

### Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_mirror_mode` | `same_host` | Mirror mode: `same_host`, `spread`, or `remote_hosts` |
| `whpg_mirror_port_base` | `7000` | Starting port for mirror segments |
| `whpg_mirror_data_directories` | See defaults | List of mirror data directories |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `whpg_enable_segment_mirrors` | `true` | Enable/disable mirror setup |
| `whpg_mirror_auto_recover` | `true` | Auto-recover mirrors after adding |
| `whpg_mirror_sync_wait_seconds` | `30` | Wait time for sync after recovery |
| `whpg_mirror_full_recovery` | `true` | Use full recovery for new mirrors |

## Inventory Examples

### Same Host Mode
```yaml
all:
  vars:
    whpg_mirror_mode: "same_host"
  children:
    whpg_primary_coordinator:
      hosts:
        coordinator:
          ansible_host: 10.0.1.10
    whpg_primary_segments:
      hosts:
        segment1:
          ansible_host: 10.0.1.11
        segment2:
          ansible_host: 10.0.1.12
```

### Spread Mode
```yaml
all:
  vars:
    whpg_mirror_mode: "spread"
  children:
    whpg_primary_coordinator:
      hosts:
        coordinator:
          ansible_host: 10.0.1.10
    whpg_primary_segments:
      hosts:
        segment1:
          ansible_host: 10.0.1.11
          replication_alias: seg1-repl
        segment2:
          ansible_host: 10.0.1.12
          replication_alias: seg2-repl
```

### Remote Hosts Mode
```yaml
all:
  vars:
    whpg_mirror_mode: "remote_hosts"
  children:
    whpg_primary_coordinator:
      hosts:
        coordinator:
          ansible_host: 10.0.1.10
    whpg_primary_segments:
      hosts:
        segment1:
          ansible_host: 10.0.1.11
        segment2:
          ansible_host: 10.0.1.12
    whpg_mirror_segments:
      hosts:
        mirror1:
          ansible_host: 10.0.2.11
          replication_alias: mirror1-repl
        mirror2:
          ansible_host: 10.0.2.12
          replication_alias: mirror2-repl
```

## Usage

### Basic Playbook

```yaml
---
- name: Setup Segment Mirrors
  hosts: whpg_primary_coordinator
  become: yes
  
  vars:
    whpg_mirror_mode: "same_host"
  
  roles:
    - warehousepg-segment-mirrors
```

### Command Line

```bash
# Same host mode (default)
ansible-playbook -i inventory.yml setup_mirrors.yml

# Spread mode
ansible-playbook -i inventory.yml setup_mirrors.yml -e "whpg_mirror_mode=spread"

# Remote hosts mode
ansible-playbook -i inventory.yml setup_mirrors.yml -e "whpg_mirror_mode=remote_hosts"
```

## Mirror Configuration Format

The role generates a mirror configuration file in the format required by `gpaddmirrors`:

```
content_id|address|port|data_directory
0|segment1-repl|7000|/data/mirror/seg1
1|segment1-repl|7001|/data/mirror/seg2
2|segment2-repl|7000|/data/mirror/seg1
3|segment2-repl|7001|/data/mirror/seg2
```

## Verification Commands

After running the role, verify mirrors:

```bash
# Check mirror status
gpstate -m

# Check segment configuration
psql -d template1 -c "SELECT * FROM gp_segment_configuration ORDER BY content, role;"

# Check for out-of-sync mirrors
gpstate -e
```

## License

Apache-2.0

## Author

EDB (EnterpriseDB)

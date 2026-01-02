# WarehousePG OS Configuration Role

This Ansible role configures operating system parameters and settings required for optimal WarehousePG performance.

## Features

- SELinux configuration (disable or permissive mode)
- Firewall management (firewalld disable/configure)
- System kernel parameters (sysctl.conf)
- System resource limits (limits.conf)
- Transparent Huge Pages (THP) deactivation
- Disk I/O scheduler configuration
- XFS mount options
- Network MTU settings
- SSH connection threshold settings
- IPC object removal configuration
- Core dump settings
- NTP/Chrony time synchronization

## Requirements

- Rocky Linux 9.3 or RHEL 8/9
- Root or sudo access
- XFS filesystem (recommended)

## Role Variables

All variables are defined in `defaults/main.yml` and are highly customizable.

### Key Variables

- `whpg_selinux_state`: SELinux state (disabled/enforcing/permissive)
- `whpg_firewall_state`: Firewall state (stopped/started)
- `whpg_disable_firewall`: Whether to disable firewall entirely
- `whpg_disable_thp`: Disable Transparent Huge Pages
- `whpg_configure_ntp`: Whether to configure NTP/Chrony
- `whpg_disk_scheduler`: Disk I/O scheduler (deadline/mq-deadline/none)
- `whpg_system_memory_gb`: System memory in GB (for calculations)

## Dependencies

None

## Example Playbook

```yaml
- hosts: all
  become: yes
  roles:
    - role: warehousepg-os-config
      vars:
        whpg_system_memory_gb: 128
        whpg_selinux_state: disabled
```

## License

MIT

## Author Information

Created for WarehousePG OS optimization.

# WarehousePG Validation Role

This role validates WarehousePG cluster performance using the `gpcheckperf` utility.

## Description

The `warehousepg-validate` role performs comprehensive validation of your WarehousePG cluster hardware and network performance:

- **Network Performance**: Tests network bandwidth between segment hosts using parallel, serial, or full-matrix modes
- **Disk I/O Performance**: Validates sequential disk read/write throughput using the `dd` command
- **Memory Bandwidth**: Measures sustainable memory bandwidth using the STREAM benchmark

## Requirements

- WarehousePG must be installed (`warehousepg-install` role)
- Passwordless SSH must be configured between all hosts
- gpadmin user must exist
- Write access to test directories

## Role Variables

### Validation Control
```yaml
whpg_validate_network: true    # Enable/disable network tests
whpg_validate_disk: true       # Enable/disable disk I/O tests
whpg_validate_memory: true     # Enable/disable memory tests
```

### Network Test Configuration
```yaml
whpg_network_test_mode: "N"    # N=parallel pairs, n=serial, M=full matrix
whpg_network_test_dir: "/tmp"  # Directory for network test files
whpg_min_network_bandwidth: 100  # Minimum acceptable bandwidth (MB/s)
```

### Disk Test Configuration
```yaml
whpg_disk_test_dirs:
  - "/data/primary"
  - "/data/mirror"
whpg_min_disk_write: 200       # Minimum write speed (MB/s)
whpg_min_disk_read: 300        # Minimum read speed (MB/s)
```

### Memory Test Configuration
```yaml
whpg_min_memory_bandwidth: 5000  # Minimum memory bandwidth (MB/s)
```

### Report Configuration
```yaml
whpg_validation_report_dir: "/home/gpadmin/validation_reports"
```

## Dependencies

- warehousepg-install role (for WarehousePG installation)

## Example Playbook

### Basic validation
```yaml
- hosts: whpg_primary_coordinator
  become: yes
  roles:
    - role: warehousepg-validate
```

### Custom thresholds
```yaml
- hosts: whpg_primary_coordinator
  become: yes
  roles:
    - role: warehousepg-validate
      vars:
        whpg_min_network_bandwidth: 1000
        whpg_min_disk_write: 500
        whpg_min_disk_read: 700
        whpg_min_memory_bandwidth: 10000
```

### Network only validation
```yaml
- hosts: whpg_primary_coordinator
  become: yes
  roles:
    - role: warehousepg-validate
      vars:
        whpg_validate_disk: false
        whpg_validate_memory: false
      tags: [validate-network]
```

### Full matrix network test
```yaml
- hosts: whpg_primary_coordinator
  become: yes
  roles:
    - role: warehousepg-validate
      vars:
        whpg_network_test_mode: "M"  # Full matrix test
```

## Tags

- `validate-prerequisites`: Run prerequisite checks
- `validate-network`: Run network performance tests
- `validate-disk`: Run disk I/O tests
- `validate-memory`: Run memory bandwidth tests
- `validate-report`: Generate validation reports

## Validation Reports

The role generates three reports in `{{ whpg_validation_report_dir }}`:

1. **network_validation_<timestamp>.txt**: Raw network test output
2. **disk_memory_validation_<timestamp>.txt**: Raw disk and memory test output
3. **validation_summary_<timestamp>.txt**: Summary with pass/fail status

## Performance Thresholds

Default minimum thresholds:
- Network: 100 MB/s
- Disk Write: 200 MB/s
- Disk Read: 300 MB/s
- Memory: 5000 MB/s

Adjust these based on your hardware specifications.

## Notes

- Tests run only on the coordinator node against segment hosts
- Network tests can take 5+ seconds per host
- Disk tests can take significant time with large files
- All tests require `gpadmin` user with passwordless SSH
- Tests use `gpcheckperf` utility from WarehousePG installation

## Author

Vibhor Kumar

## License

MIT

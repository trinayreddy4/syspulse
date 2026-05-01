"""
collector.py
-------------
Gathers system health data: CPU, memory, disk, processes, logs, services.
Returns a structured dictionary ready for AI analysis.

Dependencies:
    - psutil: cross-platform system metrics
    - subprocess: for journalctl and systemctl calls (added later)

Author: Trinay Reddy Malireddy
"""
import psutil
import time
import subprocess
from datetime import datetime

def get_cpu_metrics():
    """
        Collect CPU usage, core counts, and load averages.

       Gathers CPU metrics using psutil and transforms them into a
       structured dictionary for AI analysis.

       Returns:
           dict: {
               "usage_percent": float,   # 0-100
               "core_count": int,        # logical cores
               "physical_cores": int,    # physical cores
               "load_average": dict      # 1/5/15 min averages
           }

       Raises:
           Returns {"error": str} on any psutil failure.

    """
    try:
        cpu_useage_percent = psutil.cpu_percent(interval=1)
        cpu_core_count = psutil.cpu_count()
        cpu_physical_cores = psutil.cpu_count(logical=False)
        cpu_load_averages = psutil.getloadavg()
        result = {
            "usage_percent": round(cpu_useage_percent,2),
            "core_count": round(cpu_core_count,2),
            "physical_cores": round(cpu_physical_cores,2),
            "load_average": {
                "1min": round(cpu_load_averages[0],2),
                "5min": round(cpu_load_averages[1],2),
                "15min": round(cpu_load_averages[2],2)
            }
        }
        return result
    except Exception as e:
        return {"error": str(e)}

def bytes_to_gb(bytes_value):
    """Convert bytes to gigabytes, rounded to 2 decimals."""
    return round(bytes_value / (1024 ** 3), 2)

def get_memory_metrics():
    """
    Collect memory usage: total, used, available, and percent used.
    Gathers memory metrics using psutil and transforms them into a
    structured dictionary for AI analysis.
    Returns:
    dict: {
    "total_gb": float,
    "used_gb": float,
    "available_gb": float,
    "percent_used": float,
    }
    Raises:
        Returns {"error": str} on any psutil failure.
    :return:
    """
    try:
        virtual_memory = psutil.virtual_memory()
        total_gb = bytes_to_gb(virtual_memory.total)
        used_gb = bytes_to_gb(virtual_memory.used)
        available_gb = bytes_to_gb(virtual_memory.available)
        percent_used = virtual_memory.percent

        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": available_gb,
            "percent_used": percent_used,
        }

    except Exception as e:
        return {"error": str(e)}

def get_disk_useage(path="/"):
    try:
        disk_usage = psutil.disk_usage(path)
        return {
            "total_gb": bytes_to_gb(disk_usage.total),
            "used_gb": bytes_to_gb(disk_usage.used),
            "available_gb": bytes_to_gb(disk_usage.free),
            "percent_used": disk_usage.percent,
        }
    except Exception as e:
        return {"error": str(e)}

def get_disk_metrics():
    """
    collect disk usage: mount, filesystem, total, used, available, and percent used.
    Gathers disk metrics using psutil and transforms them into a
    list of dictionaries for AI analysis.
    Returns:
    List:[
        Dict:{
            "mount": Str
            "filesystem": Str,
            "total_gb": Float,
            "used_gb": Float,
            "available_gb": Float,
            "percent_used": Float,
        }
    ]
    :return:
    """
    try:
        result = []
        for disk_partition in psutil.disk_partitions(all=False):
            try:
                mount = disk_partition.mountpoint
                filesystem = disk_partition.fstype
                disk_usage_info = get_disk_useage(path=mount)
                if not "error" in disk_usage_info:
                    result.append({
                        "mount": mount,
                        "filesystem": filesystem,
                        **disk_usage_info
                    })
            except (PermissionError, OSError) as e:
                continue
        return result
    except Exception as e:
        return {"error": str(e)}

def get_top_processes(n=5):
    """
    Collect top n processes using psutil and transforms them into a
    structured dictionary for AI analysis.
    Args:
        Number of processes to collect.
    output:
        dictionary:{
            top_cpu:List of processes sorted by cpu,
            top_memory:List of memory sorted processes,
        }
    :param n:
    :return:
    """
    try:
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        time.sleep(0.5)

        procs_data = []
        for proc in psutil.process_iter(['pid','name','memory_percent','cpu_percent','username']):
            try:
                if not proc.cmdline():
                    continue

                cpu_percent = proc.cpu_percent(interval=None)
                procs_data.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": round(cpu_percent,2),
                    "memory_percent": round(proc.info['memory_percent'] or 0,2),
                    "username": proc.info['username'],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        top_cpu_data = sorted(procs_data, key=lambda x: x['cpu_percent'], reverse=True)[:n]
        top_memory_data = sorted(procs_data,key=lambda x: x['memory_percent'], reverse=True)[:n]

        return {"top_cpu": top_cpu_data, "top_memory": top_memory_data}
    except Exception as e:
        return {"error": str(e)}

def format_uptime(seconds):
    """Convert seconds to human-readable uptime string."""
    days = int(seconds // 86400)       # 86400 = seconds in a day
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{days} days, {hours} hours, {minutes} minutes"

def get_uptime():
    """
    This function is used to retrive the uptime of the system.
    in dictionary format
    output:
        dictionary:{
            "boot_time": str,
            "uptime_seconds": int,
            "uptime_human": str
        }
    :return:
    """
    try:
        boot_seconds = psutil.boot_time()
        uptime_seconds = time.time() - boot_seconds
        boot_time_string = datetime.fromtimestamp(boot_seconds).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "boot_time": boot_time_string,
            "uptime_seconds": round(uptime_seconds,2),
            "uptime_human": format_uptime(uptime_seconds)
        }
    except Exception as e:
        return {"error": str(e)}

def check_service_exists(service):
    """Return True if the service unit file exists on this system."""
    try:
        result = subprocess.run(
            ['systemctl', 'cat', service],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_service_status(services=None):
    """Check status of systemd services.

    Returns:
        dict: {
            service_name: {
                "status": "active"|"inactive"|"failed"|"not_found",
                "enabled": bool
            }
        }
    """
    if services is None:
        services = ["sshd", "crond", "firewalld", "rsyslog"]

    try:
        result = {}
        for service in services:
            try:
                # Step 1: Does service exist?
                if not check_service_exists(service):
                    result[service] = {"status": "not_found", "enabled": False}
                    continue

                # Step 2: Get active status
                active_check = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True, text=True, timeout=5
                )
                status = active_check.stdout.strip()

                # Step 3: Get enabled status
                enabled_check = subprocess.run(
                    ['systemctl', 'is-enabled', service],
                    capture_output=True, text=True, timeout=5
                )
                enabled = enabled_check.stdout.strip() == "enabled"

                result[service] = {"status": status, "enabled": enabled}

            except subprocess.TimeoutExpired:
                result[service] = {"status": "timeout", "enabled": False}

        return result
    except FileNotFoundError:
        return {"error": "systemctl not available"}
    except Exception as e:
        return {"error": str(e)}

import json as json_module  # avoid shadowing the outer json import

def parse_log_entry(entry):
    """Extract useful fields from a journalctl JSON entry.

    Args:
        entry (dict): Raw journalctl JSON entry.

    Returns:
        dict: Cleaned log with timestamp, unit, priority, message.
    """
    # journalctl timestamps are microseconds since epoch (as string)
    # Convert to readable format
    ts_micro = entry.get('__REALTIME_TIMESTAMP', '0')
    try:
        ts = datetime.fromtimestamp(int(ts_micro) / 1_000_000)
        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        timestamp = "unknown"

    # Priority number → human name
    priority_num = int(entry.get('PRIORITY', 7))
    priority_names = {0: 'emerg', 1: 'alert', 2: 'crit', 3: 'err',
                      4: 'warning', 5: 'notice', 6: 'info', 7: 'debug'}

    return {
        "timestamp": timestamp,
        "unit": entry.get('_SYSTEMD_UNIT', 'unknown'),
        "priority": priority_names.get(priority_num, 'unknown'),
        "message": entry.get('MESSAGE', '')[:200]  # truncate long messages
    }


def get_logs(hours=1, max_lines=50):
    """Collect recent error/warning logs from systemd journal.

    Args:
        hours (int): How far back to look. Default 1 hour.
        max_lines (int): Max recent_errors entries to return.

    Returns:
        dict: {
            "total_errors": int,
            "total_warnings": int,
            "recent_errors": list,
            "failed_ssh_attempts": int
        }
    """
    try:
        result = subprocess.run(
            ['journalctl',
             '--since', f'{hours} hour ago',
             '-p', 'warning',
             '--output=json',
             '--no-pager'],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            return {"error": f"journalctl failed: {result.stderr.strip()}"}

        # Parse JSON line-by-line
        log_entries = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                log_entries.append(json_module.loads(line))
            except json_module.JSONDecodeError:
                continue

        # Categorize
        errors, warnings = [], []
        ssh_failures = 0
        for entry in log_entries:
            priority = int(entry.get('PRIORITY', 7))
            parsed = parse_log_entry(entry)

            if priority <= 3:
                errors.append(parsed)
            elif priority == 4:
                warnings.append(parsed)

            # Detect SSH brute force attempts
            msg = entry.get('MESSAGE', '')
            if 'Failed password' in msg or 'authentication failure' in msg:
                ssh_failures += 1

        return {
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "recent_errors": errors[:max_lines],
            "failed_ssh_attempts": ssh_failures
        }

    except subprocess.TimeoutExpired:
        return {"error": "journalctl timed out"}
    except FileNotFoundError:
        return {"error": "journalctl not available"}
    except Exception as e:
        return {"error": str(e)}

import socket   # for hostname

def collect_all():
    """Collect all system health data into a single dictionary.

    Returns:
        dict: Complete system health snapshot with metadata
              and all collected metrics/logs.
    """
    return {
        "metadata": {
            "hostname": socket.gethostname(),
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "collector_version": "1.0.0",
        },
        "cpu": get_cpu_metrics(),
        "memory": get_memory_metrics(),
        "disk": get_disk_metrics(),
        "processes": get_top_processes(n=5),
        "uptime": get_uptime(),
        "services": get_service_status(),
        "logs": get_logs(hours=1),
    }



if __name__ == "__main__":
    import json
    print(json.dumps(collect_all(), indent=2))
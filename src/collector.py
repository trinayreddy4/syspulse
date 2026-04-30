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
        top_cpu_data = sorted(procs_data, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:n]
        top_memory_data = sorted(procs_data,key=lambda x: x['memory_percent'] or 0, reverse=True)[:n]

        return {"top_cpu": top_cpu_data, "top_memory": top_memory_data}
    except Exception as e:
        return {"error": str(e)}



def get_uptime():
    pass

if __name__ == "__main__":
    import json
    print("=== CPU ===")
    print(json.dumps(get_cpu_metrics(), indent=2))
    print("\n=== MEMORY ===")
    print(json.dumps(get_memory_metrics(), indent=2))
    print("\n=== DISK ===")
    print(json.dumps(get_disk_metrics(), indent=2))
    print("\n=== TOP PROCESSES ===")
    print(json.dumps(get_top_processes(n=5), indent=2))
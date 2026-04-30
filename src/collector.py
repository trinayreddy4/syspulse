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
        disk_usage = psutil.disk_usage(Path)
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
        for disk_parition in psutil.disk_partitions(all=True):
            try:
                mount = disk_parition.mountpoint
                filesystem = disk_parition.fstype
                disk_useage_info = get_disk_useage(Path=mount)
                if not "error" in disk_useage_info:
                    result.append({
                        "mount": mount,
                        "filesystem": filesystem,
                        **disk_useage_info
                    })
            except (PermissionError, OSError) as e:
                continue
        return result
    except Exception as e:
        return {"error": str(e)}

def get_top_processes(n=5):
    pass

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
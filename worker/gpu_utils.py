import subprocess
import json

def check_gpu_usage():
    """
    Check if GPU is being used and return usage information
    """
    try:
        # Try to run nvidia-smi
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Parse the output
        values = result.stdout.strip().split(', ')
        gpu_info = {
            "gpu_available": True,
            "gpu_utilization": float(values[0]),
            "memory_utilization": float(values[1]),
            "memory_used_mb": float(values[2]),
            "memory_total_mb": float(values[3])
        }
        
        return gpu_info
    except Exception as e:
        return {
            "gpu_available": False,
            "error": str(e)
        }
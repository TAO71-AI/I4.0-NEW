from enum import Enum
import subprocess
import Utilities.logs as logs

class GPUType(Enum):
    NVIDIA = 0
    AMD = 1
    INTEL = 2
    NO_GPU = 3

def DetectGPU() -> GPUType:
    """
    Detect GPU type.

    Returns:
        GPUType
    """
    logs.WriteLog(logs.INFO, "[gpu_utils] Detecting GPU...")

    try:
        result = subprocess.run(["lspci"], capture_output = True, text = True)

        for line in result.stdout.splitlines():
            if ("VGA" in line or "3D" in line or "Display" in line):
                if ("NVIDIA" in line.upper()):
                    return GPUType.NVIDIA
                elif ("AMD" in line.upper() or "ATI" in line.upper() or "RADEON" in line.upper()):
                    return GPUType.AMD
                elif ("INTEL" in line.upper()):
                    return GPUType.INTEL
    except:
        pass
    
    return GPUType.NO_GPU

def GPUHasVulkan() -> bool:
    """
    Detect if the GPU is compatible with Vulkan.

    Returns:
        bool
    """
    logs.WriteLog(logs.INFO, "[gpu_utils] Detecting Vulkan...")

    try:
        result = subprocess.run(["vulkaninfo"], capture_output = True, text = True, timeout = 5)

        if ("GPU id" in result.stdout):
            return True
    except:
        pass
    
    return False
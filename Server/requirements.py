import os
import logging
import json
import Utilities.install_requirements as requirements
import Utilities.gpu_utils as gpu_utils

PYTORCH_WHEELS = {
    # Testing levels:
    # 0: Works out-of-the-box, fully tested, no configuration changes required
    # 1: Works fine, but requires small configuration changes
    # 2: Might be a bit buggy or requires small code changes
    # 3: Not tested, unknown if it works or not
    # 4: Not tested, but probably works
    # 5: Not tested, and probably does not work
    # 6: Does not have support and will not work

    "cuda": "https://download.pytorch.org/whl/cu130",
    "cuda13.2": "https://download.pytorch.org/whl/cu132",  # 0
    "cuda13.0": "https://download.pytorch.org/whl/cu130",  # 0
    "cuda12.8": "https://download.pytorch.org/whl/cu128",  # 4
    "cuda12.6": "https://download.pytorch.org/whl/cu126",  # 4

    "rocm": "https://download.pytorch.org/whl/rocm7.2",
    "rocm7.2": "https://download.pytorch.org/whl/rocm7.2",  # 3
    "rocm6.4": "https://download.pytorch.org/whl/rocm6.4",  # 3
    
    "sycl": "https://download.pytorch.org/whl/xpu",  # 2

    "cpu": "https://download.pytorch.org/whl/cpu"  # 0
}
BASE_REQUIREMENTS = [
    "PyYAML",
    "requests",
    "pydub",
    "websockets>=16.0.0",
    "asyncio",
    "av",
    "cryptography",
    "Pillow",
    "numpy",
    "accelerate",
    "transformers>=4.57.3",
    "torch>=2.10.0",
    "torchvision",
    "torchaudio"
]
OPTIONAL_REQUIREMENTS = [
    "bitsandbytes",
    "flash-attn"
]

def InstallRequirements() -> None:
    import services_manager as servMgr
    logging.info("[requirements] Preparing for installation...")

    upgrade = os.environ.get("I4_UPGRADE", True)
    verbose = os.environ.get("I4_VERBOSE", False)
    installOptional = os.environ.get("I4_INSTALL_OPTIONAL", False)
    pytorchWhlName = os.environ.get("I4_PT_WHL", "auto")
    gpu = os.environ.get("I4_GPU", None)
    gpuHasVulkan = os.environ.get("I4_GPU_VULKAN", None)
    pipArgs = json.loads(os.environ.get("I4_PIP_ARGS", "[]"))

    if (gpu in [None, "auto"]):
        gpu = gpu_utils.DetectGPU()
    elif (gpu in ["nvidia", "cuda"]):
        gpu = gpu_utils.GPUType.NVIDIA
    elif (gpu in ["amd", "radeon", "rocm"]):
        gpu = gpu_utils.GPUType.AMD
    elif (gpu in ["intel", "sycl"]):
        gpu = gpu_utils.GPUType.INTEL
    else:
        gpu = gpu_utils.GPUType.NO_GPU
    
    if (gpuHasVulkan in [None, "auto"]):
        gpuHasVulkan = gpu_utils.GPUHasVulkan()
    elif (gpuHasVulkan in ["1", "true", "True", "TRUE"]):
        gpuHasVulkan = True
    else:
        gpuHasVulkan = False
    
    if (pytorchWhlName == "auto"):
        if (gpu == gpu_utils.GPUType.NVIDIA):
            pytorchWhlName = "nvidia"
        elif (gpu == gpu_utils.GPUType.AMD):
            pytorchWhlName = "rocm"
        elif (gpu == gpu_utils.GPUType.INTEL):
            pytorchWhlName = "sycl"
        else:
            pytorchWhlName = "cpu"
    
    pytorchWhlIndex = PYTORCH_WHEELS.get(pytorchWhlName, PYTORCH_WHEELS["cpu"])

    if (pytorchWhlIndex == PYTORCH_WHEELS["cpu"]):
        pytorchWhlName = "cpu"
    
    logging.info(f"[requirements] Installation parameters:\n- GPU: {gpu.name}\n- Vulkan available: {gpuHasVulkan}\n- PyTorch wheel: {pytorchWhlName}\n- Install optional requirements: {installOptional}\n- Upgrade: {upgrade}\n- Verbose: {verbose}")
    
    if (upgrade):
        pipArgs.append("--upgrade")
    
    if (verbose):
        pipArgs.append("--verbose")

    servMgr.InstallAllRequirements(GPU = gpu, Vulkan = gpuHasVulkan, Services = None, ExtraArgs = pipArgs)

    if (installOptional):
        requirements.InstallPackage(
            Packages = OPTIONAL_REQUIREMENTS,
            EnvVars = os.environ,
            PIPOptions = pipArgs
        )

    requirements.InstallPackage(
        Packages = BASE_REQUIREMENTS,
        EnvVars = os.environ,
        PIPOptions = pipArgs
    )

if (__name__ == "__main__"):
    InstallRequirements()
import os
import Utilities.install_requirements as requirements
import Utilities.gpu_utils as gpu_utils

GENERAL_REQUIREMENTS = [
    "PyYAML",
    "requests",
    "tiktoken",
    "pydub",
    "websockets>=15.0.0,<16.0.0",
    "asyncio",
    "av",
    "cryptography",
    "Pillow",
    "numpy",
    "accelerate",
    "transformers>=4.57.3"
]
OPTIONAL_REQUIREMENTS = [
    "bitsandbytes",
    #"flash-attn"
]
PYTORCH_REQUIREMENTS = [
    "torch>=2.10.0",
    "torchvision",
    "torchaudio"
]

def InstallRequirements() -> None:
    torchIdx = "https://download.pytorch.org/whl/cpu"
    args = []

    if ("FORCE_UPGRADE" in os.environ and len(os.environ["FORCE_UPGRADE"].strip()) > 0):
        args.append("--upgrade")
    
    if ("VERBOSE" in os.environ and len(os.environ["VERBOSE"].strip()) > 0):
        args.append("--verbose")

    if ("BASE_TORCH_CIDX" in os.environ and len(os.environ["BASE_TORCH_CIDX"].strip()) > 0):
        torchIdx = os.environ["BASE_TORCH_CIDX"]
    elif ("BASE_TORCH_IDX" in os.environ and len(os.environ["BASE_TORCH_IDX"].strip()) > 0):
        os.environ["BASE_TORCH_IDX"] = os.environ["BASE_TORCH_IDX"].strip().lower()
    else:
        gpu = gpu_utils.DetectGPU()
        
        if (gpu == gpu_utils.GPUType.NVIDIA):
            os.environ["BASE_TORCH_IDX"] = "cuda"
        elif (gpu == gpu_utils.GPUType.AMD):
            os.environ["BASE_TORCH_IDX"] = "rocm"
        elif (gpu == gpu_utils.GPUType.INTEL):
            os.environ["BASE_TORCH_IDX"] = "sycl"
        else:
            os.environ["BASE_TORCH_IDX"] = "cpu"

    if (os.environ["BASE_TORCH_IDX"] == "cuda13.0"):
        torchIdx = "https://download.pytorch.org/whl/cu130"  # Fully tested
    elif (os.environ["BASE_TORCH_IDX"] == "cuda12.8"):
        torchIdx = "https://download.pytorch.org/whl/cu128"  # Partially tested
    elif (os.environ["BASE_TORCH_IDX"] == "cuda12.6" or os.environ["BASE_TORCH_IDX"] == "cuda"):
        torchIdx = "https://download.pytorch.org/whl/cu126"  # Partially tested
    elif (os.environ["BASE_TORCH_IDX"] == "rocm6.4" or os.environ["BASE_TORCH_IDX"] == "rocm"):
        torchIdx = "https://download.pytorch.org/whl/rocm6.4"  # Not tested
    elif (os.environ["BASE_TORCH_IDX"] == "sycl"):
        torchIdx = "https://download.pytorch.org/whl/xpu"  # Not tested
    elif (os.environ["BASE_TORCH_IDX"] == "disable"):
        torchIdx = None
    elif (os.environ["BASE_TORCH_IDX"] != "cpu"):
        raise ValueError("Invalid PyTorch idx. Please see documentation.")
    
    if ("BASE_FLASH_ATTN_MAX_JOBS" in os.environ):
        faMj = int(os.environ["BASE_FLASH_ATTN_MAX_JOBS"])
    else:
        faMj = None
    
    requirements.InstallPackage(Packages = GENERAL_REQUIREMENTS, PIPOptions = args)

    import services_manager as servMgr
    servMgr.InstallAllRequirements()

    if (torchIdx is not None):
        requirements.InstallPackage(
            Packages = PYTORCH_REQUIREMENTS,
            PIPOptions = ["--index-url", torchIdx] + args
        )
    
    if ("INSTALL_OPTIONAL" in os.environ and len(os.environ["INSTALL_OPTIONAL"].strip()) > 0):
        requirements.InstallPackage(Packages = OPTIONAL_REQUIREMENTS, PIPOptions = args)
        requirements.InstallPackage(
            Packages = ["flash-attn"],
            PIPOptions = ["--no-build-isolation"] + args,
            EnvVars = {"MAX_JOBS": faMj} if (faMj is not None) else {}
        )

if (__name__ == "__main__"):
    InstallRequirements()
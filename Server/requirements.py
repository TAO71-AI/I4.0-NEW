import os
import Utilities.install_requirements as requirements

GENERAL_REQUIREMENTS = [
    "PyYAML",
    "requests",
    "beautifulsoup4",
    "tiktoken",
    "pydub",
    "websockets>=15.0.0,<16.0.0",
    "asyncio",
    "av",
    "cryptography",
    "ddgs"
]
PYTORCH_REQUIREMENTS = [
    "torch",
    "torchvision",
    "torchaudio"
]

def InstallRequirements() -> None:
    torchIdx = "https://download.pytorch.org/whl/cpu"
    forceUpgrade = ["--upgrade"] if ("BASE_FORCE_UPGRADE" in os.environ and bool(os.environ["BASE_FORCE_UPGRADE"])) else []

    if ("BASE_TORCH_CIDX" in os.environ and len(os.environ["BASE_TORCH_CIDX"].strip()) > 0):
        torchIdx = os.environ["BASE_TORCH_CIDX"]
    elif ("BASE_TORCH_IDX" in os.environ and len(os.environ["BASE_TORCH_IDX"].strip()) > 0):
        os.environ["BASE_TORCH_IDX"] = os.environ["BASE_TORCH_IDX"].strip().lower()

        if (os.environ["BASE_TORCH_IDX"] == "cuda13.0"):
            torchIdx = "https://download.pytorch.org/whl/cu130"  # Fully tested
        elif (os.environ["BASE_TORCH_IDX"] == "cuda12.8"):
            torchIdx = "https://download.pytorch.org/whl/cu128"  # Partially tested
        elif (os.environ["BASE_TORCH_IDX"] == "cuda12.6"):
            torchIdx = "https://download.pytorch.org/whl/cu126"  # Partially tested
        elif (os.environ["BASE_TORCH_IDX"] == "rocm6.4"):
            torchIdx = "https://download.pytorch.org/whl/rocm6.4"  # Not tested
        elif (os.environ["BASE_TORCH_IDX"] == "sycl"):
            torchIdx = "https://download.pytorch.org/whl/xpu"  # Not tested
        elif (os.environ["BASE_TORCH_IDX"] == "disable"):
            torchIdx = None
        elif (os.environ["BASE_TORCH_IDX"] != "cpu"):
            raise ValueError("Invalid PyTorch idx. Please see documentation.")

    if (torchIdx is not None):
        requirements.InstallPackage(
            Packages = PYTORCH_REQUIREMENTS,
            PIPOptions = ["--index-url", torchIdx] + forceUpgrade
        )
    
    requirements.InstallPackage(Packages = GENERAL_REQUIREMENTS, PIPOptions = forceUpgrade)

    import services_manager as servMgr
    servMgr.InstallAllRequirements()

if (__name__ == "__main__"):
    InstallRequirements()
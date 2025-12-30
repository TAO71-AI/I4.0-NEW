from typing import Any
import os
import copy
import Utilities.install_requirements as req
import Utilities.gpu_utils as gpu
import Utilities.logs as logs
import services_manager

def Install(Env: dict[str, Any] | None = None) -> None:
    if (Env is None):
        Env = copy.deepcopy(os.environ)
    
    logs.PrintLog(logs.INFO, (
        "Optional dependencies (services):\n"
        "- text_classification - For automatic reasoning support. STATUS: "
        "INSTALLED" if (services_manager.IsServiceInstalled("text_classification")) else "NOT INSTALLED"
    ))

    if ("CHATBOT_NO_GPU" in Env and bool(Env["CHATBOT_NO_GPU"])):
        gpuType = gpu.GPUType.NO_GPU
        vulkanAvailable = False
    else:
        gpuType = gpu.DetectGPU()
        vulkanAvailable = gpu.GPUHasVulkan()
    
    f16 = not ("CHATBOT_NO_F16" in Env and bool(Env["CHATBOT_NO_F16"]))
    gpuType = gpu.GPUType.NO_GPU if ("CHATBOT_NO_GPU" in Env and bool(Env["CHATBOT_NO_GPU"])) else gpu.DetectGPU()
    vulkanAvailable = False if (("CHATBOT_NO_VULKAN" in Env and bool(Env["CHATBOT_NO_VULKAN"])) and gpuType == gpu.GPUType.NO_GPU) else gpu.GPUHasVulkan()
    unifiedMemory = not ("CHATBOT_NO_UNIFIED_MEMORY" in Env and bool(Env["CHATBOT_NO_UNIFIED_MEMORY"]))
    forceCublas = "CHATBOT_FORCE_CUBLAS" in Env and bool(Env["CHATBOT_FORCE_CUBLAS"]) if (gpuType == gpu.GPUType.NVIDIA) else None
    forceMMQ = "CHATBOT_FORCE_MMQ" in Env and bool(Env["CHATBOT_FORCE_MMQ"]) if (gpuType == gpu.GPUType.NVIDIA) else None
    faAllQuants = not ("CHATBOT_NO_FA_ALL_QUANTS" in Env and bool(Env["CHATBOT_NO_FA_ALL_QUANTS"]))

    logs.PrintLog(
        logs.INFO,
        (
            "[service_chatbot] Install parameters:\n"
            f"- GPU: {gpuType.name}\n"
            f"- Vulkan: {vulkanAvailable}\n"
            f"- F16: {f16}\n"
            f"- Unified memory: {unifiedMemory}\n"
            f"- Force CUBLAS: {'No NVIDIA GPU' if (forceCublas is None) else forceCublas}\n"
            f"- Force MMQ: {'No NVIDIA GPU' if (forceMMQ is None) else forceMMQ}\n"
            f"- FA all quants: {faAllQuants}"
        )
    )
    logs.PrintLog(logs.INFO, f"[service_chatbot] Installing for {gpuType.name}!")
    
    if (gpuType == gpu.GPUType.NVIDIA):
        lcppCmake = (
            f"-DGGML_CUDA=1 -DGGML_CUDE_FORCE_CUBLAS={forceCublas} -DGGML_CUDA_FORCE_MMQ={forceMMQ} "
            f"-DGGML_CUDA_F16={f16} -DGGML_CUDA_ENABLE_UNIFIED_MEMORY={unifiedMemory} -DGGML_CUDA_FA_ALL_QUANTS={faAllQuants}"
        )
    elif (gpuType == gpu.GPUType.AMD):
        lcppCmake = (
            f"-DGGML_HIPBLAS=1 -DGGML_CUDA_F16={f16} -DGGML_CUDA_ENABLE_UNIFIED_MEMORY={unifiedMemory} "
            f"-DGGML_CUDA_FA_ALL_QUANTS={faAllQuants}"
        )
    elif (gpuType == gpu.GPUType.INTEL):
        lcppCmake = (
            f"-DGGML_SYCL=1 -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16={f16} "
            f"-DGGML_CUDA_FA_ALL_QUANTS={faAllQuants} -DGGML_CUDA_ENABLE_UNIFIED_MEMORY={unifiedMemory}"
        )
    elif (gpuType == gpu.GPUType.NO_GPU):
        if (vulkanAvailable):
            lcppCmake = f"-DGGML_VULKAN=1 -DGGML_CUDA_FA_ALL_QUANTS={faAllQuants} -DGGML_CUDA_ENABLE_UNIFIED_MEMORY={unifiedMemory}"
        else:
            lcppCmake = "-DGGML_BLAS=1 -DGGML_BLAS_VENDOR=OpenBLAS"
    
    req.InstallPackage(
        Packages = ["git+https://github.com/TAO71-AI/llama-cpp-python-JamePeng.git@main"],
        EnvVars = {
            "CMAKE_ARGS": lcppCmake
        },
        PIPOptions = ["--verbose"]
    )

if (__name__ == "__main__"):
    Install()
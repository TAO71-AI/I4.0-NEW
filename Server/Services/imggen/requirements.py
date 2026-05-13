import logging
from typing import Any
import os
import copy
import Utilities.install_requirements as req
import Utilities.gpu_utils as gpu

def Install(Env: dict[str, Any] | None = None, Args: list[str] = []) -> None:
    if (Env is None):
        Env = copy.deepcopy(os.environ)
    
    f16 = not ("IMGGEN_NO_F16" in Env and bool(Env["IMGGEN_NO_F16"]))
    gpuType = gpu.GPUType.NO_GPU if ("IMGGEN_NO_GPU" in Env and bool(Env["IMGGEN_NO_GPU"])) else gpu.DetectGPU()
    vulkanAvailable = False if (("IMGGEN_NO_VULKAN" in Env and bool(Env["IMGGEN_NO_VULKAN"])) and gpuType == gpu.GPUType.NO_GPU) else gpu.GPUHasVulkan()

    logging.info((
        "[service_imggen] Install parameters:\n"
        f"- GPU: {gpuType.name}\n"
        f"- Vulkan: {vulkanAvailable}\n"
        f"- F16: {f16}"
    ))
    logging.info(f"[service_imggen] Installing for {gpuType.name}!")
    
    sdcppCmake = "-DSD_WEBP=ON -DSD_WEBM=ON"

    if (gpuType == gpu.GPUType.NVIDIA):
        sdcppCmake += (
            f" -DSD_CUDA=ON -DGGML_CUDA_F16={int(f16)} -DGGML_CUDA_BF16={int(f16)}"
        )
    elif (gpuType == gpu.GPUType.AMD):
        sdcppCmake += (
            f" -DSD_HIPBLAS=ON -DGGML_HIPBLAS_F16={int(f16)} -DGGML_HIPBLAS_BF16={int(f16)} "
            "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++"
        )
    elif (gpuType == gpu.GPUType.INTEL):
        sdcppCmake += (
            f" -DSD_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16={int(f16)} -DGGML_SYCL_BF16={int(f16)}"
        )
    elif (gpuType == gpu.GPUType.NO_GPU):
        if (vulkanAvailable):
            sdcppCmake += " -DSD_VULKAN=ON"
        else:
            sdcppCmake += " -DGGML_OPENBLAS=ON"
    
    req.InstallPackage(
        Packages = ["git+https://github.com/william-murray1204/stable-diffusion-cpp-python.git@main"],
        EnvVars = {
            "CMAKE_ARGS": sdcppCmake
        },
        PIPOptions = Args
    )

if (__name__ == "__main__"):
    Install()
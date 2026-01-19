# Hardware requirements

Keep in mind that these requirements may change in the future.

> [!IMPORTANT]
> The server has only been tested using Arch Linux, but it's expected to work using other GNU/Linux distributions.
> Windows, MacOS, and any other OS that is not GNU/Linux-based is **NOT** expected to run the server, but it might be compatible.
> 
> Do not report server-side issues if you are not running the server in a GNU/Linux OS.
> 
> Also, the current compatibility with ARM CPUs is unknown. If you encounter any bugs when running the server with an ARM CPU, please report an issue.

## Minimum hardware requirements

- OS: GNU/Linux
- CPU: x86_64, 2 cores
- RAM: ~256 MB
- GPU: No GPU required
- Disk: 10 GB
- Python: 3.11

## Recommended hardware requirements

- OS: GNU/Linux
- CPU: x86_64, 4 or more cores
- RAM: 4 GB or more
- GPU: CUDA, ROCm, or SYCL compatible
- Disk: 30 GB
- Python: 3.11

# Installing Python

Follow the guide and documentation of your OS to install Python.

# Creating a Python VENV

It is recommended to run the server using a VENV. To create a VENV, run the following command:
```bash
python -m venv .env
```

In some Operating Systems, this command may change.

# Server installation

We recommend using the automatic installation script. This is a script that automatically installs all of the dependencies of the server and modules.

First, you have to make sure that all of the modules that you will run in the server are in the modules directory. Otherwise the requirements for those modules will not be installed.

Second, execute the `requirements.py` script. This will automatically install all the dependencies for the core server and modules.

> [!IMPORTANT]
> If a new module is added to the server after the installation, the script must be run again.

## Environment variables

|Name|Type|Default value|Module|Description|
|----|----|-------------|------|-----------|
|BASE_TORCH_CIDX|string|-|-|Sets a custom PIP index url for installing PyTorch.|
|BASE_TORCH_IDX|string|cpu|-|Sets a pre-defined PIP index url for installing PyTorch. Values: `cuda13.0` for **NVIDIA** cards and CUDA >= 13.0, `cuda12.8` for **NVIDIA** cards and CUDA >= 12.8, < 13.0, `cuda12.6` for **NVIDIA** cards and CUDA >= 12.6, < 12.8, `rocm6.4` for **AMD** cards and ROCm >= 6.4, `sycl` for **INTEL** cards with SYCL, `cpu` (default) for no GPU cards, `disable` to skip PyTorch installation.|
|BASE_FORCE_UPGRADE|bool|false|-|Forces to upgrade PIP packages.|
|CHATBOT_NO_F16|bool|false|chatbot|Disables F16 when compilating *llama.cpp*. NOTE: This has changed in the *llama.cpp* library. It is unknown if this variable changes anything.|
|CHATBOT_NO_GPU|bool|false|chatbot|Forces the chatbot to not install the dependencies for the GPU.|
|CHATBOT_NO_VULKAN|bool|false|chatbot|Forces the chatbot to not install the dependencies for Vulkan-compatible GPUs.|
|CHATBOT_NO_UNIFIED_MEMORY|bool|false|chatbot|Disables the usage of unified memory in *llama.cpp*. [See more details here](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#unified-memory).|
|CHATBOT_FORCE_CUBLAS|bool|false|chatbot|Forces *llama.cpp* to use cuBLAS. [See more details here](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#performance-tuning). Note: Only works with NVIDIA GPUs.|
|CHATBOT_FORCE_MMQ|bool|false|chatbot|Forces *llama.cpp* to use MMQ. [See more details here](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#performance-tuning). Note: Only works with NVIDIA GPUs.|
|CHATBOT_NO_FA_ALL_QUANTS|bool|false|chatbot|Compiles support for all KV cache quantization types for CUDA kernels. [See more details here](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#performance-tuning). Note: Only works with NVIDIA GPUs.|

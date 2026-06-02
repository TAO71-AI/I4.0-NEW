import logging
from stable_diffusion_cpp import StableDiffusion
from typing import Any, Literal
from io import BytesIO
from PIL import Image
import time

def LoadSDModel(Configuration: dict[str, Any]) -> dict[str, StableDiffusion | Any]:
    if ("_private_model_path" not in Configuration or not isinstance(Configuration["_private_model_path"], dict)):
        raise ValueError("Invalid model path.")
    
    fullModelPath = Configuration["_private_model_path"]
    modelPath = fullModelPath["model"] if ("model" in fullModelPath) else ""
    clipLPath = fullModelPath["clip_l"] if ("clip_l" in fullModelPath) else ""
    clipGPath = fullModelPath["clip_g"] if ("clip_g" in fullModelPath) else ""
    clipVisionPath = fullModelPath["clip_vision"] if ("clip_vision" in fullModelPath) else ""
    t5xxlPath = fullModelPath["t5xxl"] if ("t5xxl" in fullModelPath) else ""
    llmPath = fullModelPath["llm"] if ("llm" in fullModelPath) else ""
    llmVisionPath = fullModelPath["llm_vision"] if ("llm_vision" in fullModelPath) else ""
    highNoiseDiffModelPath = fullModelPath["high_noise_diffusion_model"] if ("high_noise_diffusion_model" in fullModelPath) else ""
    vaePath = fullModelPath["vae"] if ("vae" in fullModelPath) else ""
    taesdPath = fullModelPath["taesd"] if ("taesd" in fullModelPath) else ""
    controlNetPath = fullModelPath["control_net"] if ("control_net" in fullModelPath) else ""
    upscalerPath = fullModelPath["upscaler"] if ("upscaler" in fullModelPath) else ""
    diffusionModelPath = fullModelPath["diffusion"] if ("diffusion" in fullModelPath) else ""

    upscaleTileSize = Configuration["_private_upscale_tile_size"] if ("_private_upscale_tile_size" in Configuration) else 128
    vaeDecodeOnly = Configuration["_private_vae_decode_only"] if ("_private_vae_decode_only" in Configuration) else False
    threads = Configuration["_private_threads"] if ("_private_threads" in Configuration) else -1
    wtype = Configuration["wtype"] if ("wtype" in Configuration) else Configuration["ftype"] if ("ftype" in Configuration) else "default"
    offloadParamsToCPU = Configuration["_private_offload_params_to_cpu"] if ("_private_offload_params_to_cpu" in Configuration) else False
    enableMmap = Configuration["_private_mmap"] if ("_private_mmap" in Configuration) else False
    keepClipOnCPU = Configuration["_private_keep_clip_on_cpu"] if ("_private_keep_clip_on_cpu" in Configuration) else False
    keepControlNetOnCPU = Configuration["_private_keep_control_net_on_cpu"] if ("_private_keep_control_net_on_cpu" in Configuration) else False
    keepVaeOnCPU = Configuration["_private_keep_vae_on_cpu"] if ("_private_keep_vae_on_cpu" in Configuration) else False
    flashAttn = Configuration["_private_flash_attn"] if ("_private_flash_attn" in Configuration) else False
    diffusionFlashAttn = Configuration["_private_diffusion_flash_attn"] if ("_private_diffusion_flash_attn" in Configuration) else flashAttn
    taePreviewOnly = Configuration["_private_tae_preview_only"] if ("_private_tae_preview_only" in Configuration) else False
    diffusionConvDirect = Configuration["_private_diffusion_conv_direct"] if ("_private_diffusion_conv_direct" in Configuration) else False
    vaeConvDirect = Configuration["_private_vae_conv_direct"] if ("_private_vae_conv_direct" in Configuration) else False
    circularX = Configuration["_private_circular_x"] if ("_private_circular_x" in Configuration) else False
    circularY = Configuration["_private_circular_y"] if ("_private_circular_y" in Configuration) else False
    forceSDXLVaeConvScale = Configuration["_private_force_sdxl_vae_conv_scale"] if ("_private_force_sdxl_vae_conv_scale" in Configuration) else False
    chromaUseDitMask = Configuration["_private_chroma_use_dit_mask"] if ("_private_chroma_use_dit_mask" in Configuration) else False
    chromaUseT5Mask = Configuration["_private_chroma_use_t5_mask"] if ("_private_chroma_use_t5_mask" in Configuration) else False
    chromaT5MaskPad = Configuration["_private_chroma_t5_mask_pad"] if ("_private_chroma_t5_mask_pad" in Configuration) else 1
    qwenImageZeroCondT = Configuration["_private_qwen_image_zero_cond_t"] if ("_private_qwen_image_zero_cond_t" in Configuration) else False
    maxVRAM = Configuration["_private_max_vram"] if ("_private_max_vram" in Configuration) else 0
    imageResizeMethod = Configuration["_private_image_resize_method"] if ("_private_image_resize_method" in Configuration) else "crop"
    verbose = Configuration["_private_verbose"] if ("_private_verbose" in Configuration) else False

    modelParamsSD = {
        "model_path": modelPath,
        "clip_l_path": clipLPath,
        "clip_g_path": clipGPath,
        "clip_vision_path": clipVisionPath,
        "t5xxl_path": t5xxlPath,
        "llm_path": llmPath,
        "llm_vision_path": llmVisionPath,
        "high_noise_diffusion_model_path": highNoiseDiffModelPath,
        "diffusion_model_path": diffusionModelPath,
        "vae_path": vaePath,
        "taesd_path": taesdPath,
        "control_net_path": controlNetPath,
        "upscaler_path": upscalerPath,
        "upscale_tile_size": upscaleTileSize,
        "vae_decode_only": vaeDecodeOnly,
        "n_threads": threads,
        "wtype": wtype,
        "offload_params_to_cpu": offloadParamsToCPU,
        "enable_mmap": enableMmap,
        "keep_clip_on_cpu": keepClipOnCPU,
        "keep_control_net_on_cpu": keepControlNetOnCPU,
        "keep_vae_on_cpu": keepVaeOnCPU,
        "flash_attn": flashAttn,
        "diffusion_flash_attn": diffusionFlashAttn,
        "tae_preview_only": taePreviewOnly,
        "diffusion_conv_direct": diffusionConvDirect,
        "vae_conv_direct": vaeConvDirect,
        "circular_x": circularX,
        "circular_y": circularY,
        "force_sdxl_vae_conv_scale": forceSDXLVaeConvScale,
        "chroma_use_dit_mask": chromaUseDitMask,
        "chroma_use_t5_mask": chromaUseT5Mask,
        "chroma_t5_mask_pad": chromaT5MaskPad,
        "qwen_image_zero_cond_t": qwenImageZeroCondT,
        "max_vram": maxVRAM,
        "image_resize_method": imageResizeMethod,
        "verbose": verbose
    } | (Configuration["extra_args"] if ("extra_args" in Configuration and isinstance(Configuration["extra_args"], dict)) else {})
    
    logging.info("[sdcpp_utils] Loading model...")
    loadingTime = time.time()
    
    model = StableDiffusion(**modelParamsSD)
    
    loadingTime = time.time() - loadingTime
    loadingTime = round(loadingTime, 3)

    logging.info(f"[sdcpp_utils] Model loaded in {loadingTime} seconds.")
    return {
        "_private_model": model,
        "_private_type": "sdcpp"
    }

def Inference(
    Model: StableDiffusion,
    Type: Literal["image", "video"],
    Prompt: str,
    NegativePrompt: str = "",
    Width: int = 512,
    Height: int = 512,
    ClipSkip: int = -1,
    RefImages: list[bytes | Image.Image] = [],
    CFGScale: float = 7,
    IMGCFGScale: float | None = None,
    Guidance: float = 3.5,
    Steps: int = 20,
    ETA: float = 0,
    TimestepShift: int = 0,
    SLGScale: float = 0,
    Seed: float = -1,
    UpscaleFactor: int = 1,
    Strength: float = 0.75,
    Sampler: str = "default",
    Scheduler: str = "default",
    IMG_Canny: bool = False,
    VID_Frames: int = 1,
    **kwargs: dict[str, Any]
) -> bytes:
    imgs = []

    for img in RefImages:
        if (isinstance(img, Image.Image)):
            imgs.append((None, img))
        elif (isinstance(img, bytes)):
            buffer = BytesIO(img)
            imgs.append((buffer, Image.open(buffer)))

    globalArgs = {
        "prompt": Prompt,
        "negative_prompt": NegativePrompt,
        "width": Width,
        "height": Height,
        "clip_skip": ClipSkip,
        "cfg_scale": CFGScale,
        "image_cfg_scale": IMGCFGScale,
        "guidance": Guidance,
        "sample_steps": Steps,
        "eta": ETA,
        "timestep_shift": TimestepShift,
        "slg_scale": SLGScale,
        "seed": Seed,
        "upscale_factor": UpscaleFactor,
        "strength": Strength,
        "scheduler": Scheduler,
        "sample_method": Sampler
    } | kwargs

    if (Type == "image"):
        result = Model.generate_image(
            batch_count = 1,
            ref_images = imgs,
            canny = IMG_Canny,
            **globalArgs
        )
        
        resultBuffer = BytesIO()
        result[0].save(resultBuffer, format = "WEBP")

        resultBytes = resultBuffer.getvalue()
        resultBuffer.close()
        result[0].close()
    elif (Type == "video"):
        result = Model.generate_video(
            init_image = imgs[0] if (len(imgs) >= 1) else None,
            end_image = imgs[1] if (len(imgs) >= 2) else None,
            video_frames = VID_Frames,
            **globalArgs
        )
        resultBytes = b""  # TODO
    
    for img in imgs:
        if (img[0] is not None):
            img[0].close()

        img[1].close()
    
    return resultBytes
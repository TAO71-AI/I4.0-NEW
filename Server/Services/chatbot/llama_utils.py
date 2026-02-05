# Import libraries
from llama_cpp import (
    # Model
    Llama,

    # Cache types
    LlamaDiskCache,
    LlamaRAMCache,

    # Split modes
    LLAMA_SPLIT_MODE_LAYER as SPM_LAYER,
    LLAMA_SPLIT_MODE_ROW as SPM_ROW,
    LLAMA_SPLIT_MODE_NONE as SPM_NONE,

    # ROPE scaling types
    llama_rope_scaling_type,

    # Pooling types
    LLAMA_POOLING_TYPE_CLS as POOLING_CLS,
    LLAMA_POOLING_TYPE_MEAN as POOLING_MEAN,
    LLAMA_POOLING_TYPE_LAST as POOLING_LAST,
    LLAMA_POOLING_TYPE_NONE as POOLING_NONE,
    LLAMA_POOLING_TYPE_RANK as POOLING_RANK,
    LLAMA_POOLING_TYPE_UNSPECIFIED as POOLING_UNSPECIFIED,

    # Ftypes
    LLAMA_FTYPE_ALL_F32 as FTYPE_F32,
    LLAMA_FTYPE_MOSTLY_BF16 as FTYPE_BF16,
    LLAMA_FTYPE_MOSTLY_F16 as FTYPE_F16,
    LLAMA_FTYPE_MOSTLY_Q8_0 as FTYPE_Q8_0,
    LLAMA_FTYPE_MOSTLY_Q6_K as FTYPE_Q6_K,
    LLAMA_FTYPE_MOSTLY_Q5_K_M as FTYPE_Q5_K_M,
    LLAMA_FTYPE_MOSTLY_Q5_K_S as FTYPE_Q5_K_S,
    LLAMA_FTYPE_MOSTLY_Q4_K_M as FTYPE_Q4_K_M,
    LLAMA_FTYPE_MOSTLY_Q4_K_S as FTYPE_Q4_K_S,
    LLAMA_FTYPE_MOSTLY_Q3_K_L as FTYPE_Q3_K_L,
    LLAMA_FTYPE_MOSTLY_Q3_K_M as FTYPE_Q3_K_M,
    LLAMA_FTYPE_MOSTLY_Q3_K_S as FTYPE_Q3_K_S,
    LLAMA_FTYPE_MOSTLY_Q2_K as FTYPE_Q2_K,

    LLAMA_FTYPE_MOSTLY_Q5_1 as FTYPE_Q5_1,
    LLAMA_FTYPE_MOSTLY_Q5_0 as FTYPE_Q5_0,
    LLAMA_FTYPE_MOSTLY_Q4_1 as FTYPE_Q4_1,
    LLAMA_FTYPE_MOSTLY_Q4_0 as FTYPE_Q4_0,

    LLAMA_FTYPE_MOSTLY_IQ1_S as FTYPE_IQ1_S,
    LLAMA_FTYPE_MOSTLY_IQ1_M as FTYPE_IQ1_M,
    LLAMA_FTYPE_MOSTLY_TQ1_0 as FTYPE_TQ1_0,
    LLAMA_FTYPE_MOSTLY_IQ2_XXS as FTYPE_IQ2_XXS,
    LLAMA_FTYPE_MOSTLY_IQ2_XS as FTYPE_IQ2_XS,
    LLAMA_FTYPE_MOSTLY_IQ2_S as FTYPE_IQ2_S,
    LLAMA_FTYPE_MOSTLY_IQ2_M as FTYPE_IQ2_M,
    LLAMA_FTYPE_MOSTLY_Q2_K_S as FTYPE_Q2_K_S,
    LLAMA_FTYPE_MOSTLY_TQ2_0 as FTYPE_TQ2_0,
    LLAMA_FTYPE_MOSTLY_IQ3_XXS as FTYPE_IQ3_XXS,
    LLAMA_FTYPE_MOSTLY_IQ3_XS as FTYPE_IQ3_XS,
    LLAMA_FTYPE_MOSTLY_IQ3_S as FTYPE_IQ3_S,
    LLAMA_FTYPE_MOSTLY_IQ3_M as FTYPE_IQ3_M,
    LLAMA_FTYPE_MOSTLY_IQ4_XS as FTYPE_IQ4_XS,
    LLAMA_FTYPE_MOSTLY_IQ4_NL as FTYPE_IQ4_NL
)
from llama_cpp.llama_chat_format import (
    Llava15ChatHandler as CH_Llava15,
    Llava16ChatHandler as CH_Llava16,
    MoondreamChatHandler as CH_Moondream,
    NanoLlavaChatHandler as CH_NanoLlava,
    Llama3VisionAlphaChatHandler as CH_Llama3VisionAlpha,
    MiniCPMv26ChatHandler as CH_MiniCPMv26,
    Qwen25VLChatHandler as CH_Qwen25VL,
    Qwen3VLChatHandler as CH_Qwen3VL
)
from typing import Any
import time
import Utilities.logs as logs

__FTYPES__: dict[str | tuple[str, ...], int] = {
    ("f32", "fp32"): FTYPE_F32,
    "bf16": FTYPE_BF16,
    ("f16", "fp16"): FTYPE_F16,
    "q8_0": FTYPE_Q8_0,
    "q6_k": FTYPE_Q6_K,
    ("q5_k_m", "q5_k"): FTYPE_Q5_K_M,
    "q5_k_s": FTYPE_Q5_K_S,
    ("q4_k_m", "q4_k"): FTYPE_Q4_K_M,
    "q4_k_s": FTYPE_Q4_K_S,
    "q3_k_l": FTYPE_Q3_K_L,
    ("q3_k_m", "q3_k"): FTYPE_Q3_K_M,
    "q3_k_s": FTYPE_Q3_K_S,
    "q2_k": FTYPE_Q2_K,

    "q5_1": FTYPE_Q5_1,
    "q5_0": FTYPE_Q5_0,
    "q4_1": FTYPE_Q4_1,
    "q4_0": FTYPE_Q4_0,

    "iq1_s": FTYPE_IQ1_S,
    "iq1_m": FTYPE_IQ1_M,
    "tq1_0": FTYPE_TQ1_0,
    "iq2_xxs": FTYPE_IQ2_XXS,
    "iq2_xs": FTYPE_IQ2_XS,
    "iq2_s": FTYPE_IQ2_S,
    "iq2_m": FTYPE_IQ2_M,
    "q2_k_s": FTYPE_Q2_K_S,
    "tq2_0": FTYPE_TQ2_0,
    "iq3_xxs": FTYPE_IQ3_XXS,
    "iq3_xs": FTYPE_IQ3_XS,
    "iq3_s": FTYPE_IQ3_S,
    "iq3_m": FTYPE_IQ3_M,
    "iq4_xs": FTYPE_IQ4_XS,
    "iq4_nl": FTYPE_IQ4_NL
}
__SPLIT_MODES__: dict[str | tuple[str, ...], int] = {
    "layer": SPM_LAYER,
    "row": SPM_ROW,
    "none": SPM_NONE
}
__ROPE_SCALING_TYPES__: dict[str | tuple[str, ...], int] = {
    "linear": llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_LINEAR,
    "longrope": llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_LONGROPE,
    ("max_value", "max-value", "max value"): llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_MAX_VALUE,
    "none": llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_NONE,
    "unspecified": llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED,
    "yarn": llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_YARN
}
__POOLING_TYPES__: dict[str | tuple[str, ...], int] = {
    "cls": POOLING_CLS,
    "mean": POOLING_MEAN,
    "last": POOLING_LAST,
    "none": POOLING_NONE,
    "rank": POOLING_RANK,
    "unspecified": POOLING_UNSPECIFIED
}

def __get_value_from_dictionary__(Key: Any, Dictionary: dict[Any | list[Any], Any], Default: Any | None = None) -> tuple[Any, int] | (Any | None):
    """
    Retrieves the value associated with a key in a dictionary, where the keys can be either a single object or a list of possible keys.

    Args:
        Key (Any): The key to search for.
        Dictionary (dict[Any | list[Any], Any]): The dictionary to search in.
        Default (Any | None): The default value to return if the key is not found.
    
    Returns:
        tuple[Any, int] | (Any | None)
    """
    # For each item in the dictionary
    for key, value in Dictionary.items():
        # Check the key type
        if (isinstance(key, list)):
            # Check if the key is found
            if (Key in key):
                return (value, list(Dictionary.keys()).index(key))
        elif (isinstance(key, tuple)):
            k = list(key)

            if (Key in k):
                return (value, list(Dictionary.keys()).index(key))
        elif (Key == key):
            return (value, list(Dictionary.keys()).index(key))
    
    # Key not found, return the default value
    return Default

def StringToFtype(Ftype: str) -> int | None:
    """
    Converts a string (ftype name) into an integer value.

    Args:
        Ftype (str): The ftype name.
    
    Returns:
        int | None
    """
    # Lower the ftype name
    ftype = Ftype.lower()

    # Get the value ftype
    ftypeResult = __get_value_from_dictionary__(ftype, __FTYPES__, None)

    # Return the value ftype
    if (ftypeResult is not None):
        return ftypeResult[0]
    
    return ftypeResult

def StringToSplitMode(SplitMode: str) -> int | None:
    """
    Converts a string (split mode name) into an integer value.

    Args:
        SplitMode (str): The split mode name.
    
    Returns:
        int | None
    """
    # Lower the split mode name
    spm = SplitMode.lower()

    # Get the value split mode
    spmResult = __get_value_from_dictionary__(spm, __SPLIT_MODES__, None)

    # Return the value split mode
    if (spmResult is not None):
        return spmResult[0]
    
    return spmResult

def StringToRopeScalingType(RopeScalingType: str) -> int | None:
    """
    Converts a string (rope scaling type name) into an integer value.

    Args:
        RopeScalingType (str): The rope scaling type name.
    
    Returns:
        int | None
    """
    # Lower the rope scaling type name
    rst = RopeScalingType.lower()

    # Get the value rope scaling type
    rstResult = __get_value_from_dictionary__(rst, __ROPE_SCALING_TYPES__, None)

    # Return the value rope scaling type
    if (rstResult is not None):
        return rstResult[0]
    
    return rstResult

def StringToPoolingType(PoolingType: str) -> int | None:
    """
    Converts a string (pooling type name) into an integer value.

    Args:
        PoolingType (str): The pooling type name.
    
    Returns:
        int | None
    """
    # Lower the pooling type name
    pooling = PoolingType.lower()

    # Get the value pooling type
    poolingResult = __get_value_from_dictionary__(pooling, __POOLING_TYPES__, None)

    # Return the value pooling type
    if (poolingResult is not None):
        return poolingResult[0]
    
    return poolingResult

def StringToCacheType(CacheType: str, CapacityInBytes: int = 2 ^ 30) -> LlamaDiskCache | LlamaRAMCache | None:
    """
    Converts a string (cache type name) into a class.

    Args:
        CacheType (str): The cache type name.
        CapacityInBytes (int): The capacity of the cache.
    
    Returns:
        LlamaDiskCache | LlamaRAMCache | None
    """
    # Lower the cache type name
    cache = CacheType.lower()

    # Get and return the cache type
    if (cache == "disk"):
        return LlamaDiskCache(capacity_bytes = CapacityInBytes)
    elif (cache == "ram"):
        return LlamaRAMCache(capacity_bytes = CapacityInBytes)
    
    return None

def StringToChatHandler(
    ChatHandler: str,
    Mmproj: str,
    UseGPU: bool,
    ImageTokens: tuple[int, int],
    Verbose: bool
) -> CH_Llava15 | None:
    """
    Converts a string (chat handler name) into a class.

    Args:
        ChatHandler (str): The chat handler name.
        Mmproj (str): Path to the MMPROJ file.
        UseGPU (bool): Use the GPU for the mmproj.
        ImageTokens (tuple[int, int]): Min and max image tokens.
    
    Returns:
        CH_Llava15 | None
    """
    # Lower the chat handler name
    chatHandler = ChatHandler.lower()
    generalArgs = {
        "clip_model_path": Mmproj,
        "use_gpu": UseGPU,
        "image_min_tokens": ImageTokens[0],
        "image_max_tokens": ImageTokens[1],
        "verbose": Verbose
    }

    if (ImageTokens[1] < ImageTokens[0] and ImageTokens[1] > -1):
        raise ValueError("[llama_utils] `mmproj_max_image_tokens` can't be less than `mmproj_min_image_tokens`.")

    # Get and return the chat handler
    if (chatHandler == "llava15"):
        return CH_Llava15(**generalArgs)
    elif (chatHandler == "llava16"):
        return CH_Llava16(**generalArgs)
    elif (chatHandler == "llama3visionalpha" or chatHandler == "llama-3-vision-alpha" or chatHandler == "llama3-vision-alpha"):
        return CH_Llama3VisionAlpha(**generalArgs)
    elif (chatHandler == "minicpmv2.6" or chatHandler == "mini-cpm-v2.6"):
        return CH_MiniCPMv26(**generalArgs)
    elif (chatHandler == "moondream"):
        return CH_Moondream(**generalArgs)
    elif (chatHandler == "nanollava"):
        return CH_NanoLlava(**generalArgs)
    elif (chatHandler == "qwen2.5vl" or chatHandler == "qwen2.5-vl"):
        return CH_Qwen25VL(**generalArgs)
    elif (chatHandler == "qwen3vl" or chatHandler == "qwen3-vl"):
        if (ImageTokens[0] < 1024):
            logs.PrintLog(logs.WARNING, "[llama_utils] For Qwen3-VL it's recommended to set `mmproj_min_image_tokens` to 1024.")

        return CH_Qwen3VL(**generalArgs, force_reasoning = False, add_vision_id = True)

    return None

def LoadLlamaModel(Configuration: dict[str, Any]) -> dict[str, Llama | Any]:
    """
    Loads a llama.cpp model.

    Args:
        Configuration (dict[str, Any]): Configuration for the model.
    
    Returns:
        dict[str, Llama | Any]
    """
    # Get all the verbose parameters
    verbose = Configuration["_private_verbose"] if ("_private_verbose" in Configuration) else False
    mmprojVerbose = Configuration["_private_mmproj_verbose"] if ("_private_mmproj_verbose" in Configuration) else False

    if (not isinstance(verbose, bool)):
        raise AttributeError("[llama_utils] Invalid `_private_verbose`.")
    
    if (not isinstance(mmprojVerbose, bool)):
        raise AttributeError("[llama_utils] Invalid `_private_mmproj_verbose`.")

    # Get the model path (and mmproj if provided)
    if ("_private_model_path" in Configuration):
        modelPath = None
        mmproj = None
        chatHandler = None

        logs.WriteLog(logs.INFO, "[llama_utils] Checking model path.")

        if (isinstance(Configuration["_private_model_path"], dict)):
            if ("llm" in Configuration["_private_model_path"]):
                modelPath = Configuration["_private_model_path"]["llm"]
            elif ("base" in Configuration["_private_model_path"]):
                modelPath = Configuration["_private_model_path"]["base"]
            
            if ("mmproj" in Configuration["_private_model_path"]):
                mmproj = Configuration["_private_model_path"]["mmproj"]
            
            if ("chat_handler" in Configuration["_private_model_path"]):
                chatHandler = Configuration["_private_model_path"]["chat_handler"]
        elif (isinstance(Configuration["_private_model_path"], str)):
            modelPath = Configuration["_private_model_path"]
        
        if (not isinstance(modelPath, str)):
            raise AttributeError("[llama_utils] Invalid `_private_model_path`.")
        
        if (not isinstance(mmproj, str) and mmproj is not None):
            raise AttributeError("[llama_utils] Invalid `mmproj`.")

        if (not isinstance(chatHandler, str) and chatHandler is not None):
            raise AttributeError("[llama_utils] Invalid `chat_handler`.")
        
        mmprojGPU = Configuration["_private_mmproj_use_gpu"] if ("_private_mmproj_use_gpu" in Configuration) else True

        if (not isinstance(mmprojGPU, bool)):
            raise AttributeError("[llama_utils] Invalid `_private_mmproj_use_gpu`.")
        
        minImageTokens = Configuration["mmproj_min_image_tokens"] if ("mmproj_min_image_tokens" in Configuration) else -1
        maxImageTokens = Configuration["mmproj_max_image_tokens"] if ("mmproj_max_image_tokens" in Configuration) else -1

        if (not isinstance(minImageTokens, int)):
            raise AttributeError("[llama_utils] Invalid `mmproj_min_image_tokens`.")
        
        if (not isinstance(maxImageTokens, int)):
            raise AttributeError("[llama_utils] Invalid `mmproj_max_image_tokens`.")
        
        if (mmproj is not None and chatHandler is not None):
            chatHandler = StringToChatHandler(
                chatHandler,
                mmproj,
                mmprojGPU,
                (minImageTokens, maxImageTokens),
                mmprojVerbose
            )
        
        if (mmproj is not None and chatHandler is None):
            raise AttributeError("[llama_utils] `mmproj` requires a valid `chat_handler`.")
        
        if (mmproj is None and chatHandler is not None):
            chatHandler = None
            logs.WriteLog(logs.INFO, "[llama_utils] `chat_handler` will not be used because `mmproj` is None.")
    else:
        raise AttributeError("[llama_utils] `_private_model_path` must be in the configuration of the model.")
    
    # Get the GPU layers
    if ("_private_gpu_layers" in Configuration):
        gpuLayers = Configuration["_private_gpu_layers"]

        if (not isinstance(gpuLayers, int)):
            raise AttributeError("[llama_utils] Invalid `_private_gpu_layers`.")
    else:
        gpuLayers = -1
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_gpu_layers` not defined. Set to -1.")
    
    # Get the split_mode
    if ("_private_split_mode" in Configuration):
        splitMode = Configuration["_private_split_mode"]

        if (not isinstance(splitMode, str)):
            raise AttributeError("[llama_utils] Invalid `_private_split_mode`.")
        
        splitMode = StringToSplitMode(splitMode)

        if (splitMode is None):
            splitMode = SPM_LAYER
            logs.PrintLog(logs.WARNING, "[llama_utils] `_private_split_mode` not found. Set to `layer`.")
    else:
        splitMode = SPM_LAYER
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_split_mode` not defined. Set to `layer`.")
    
    # Get the main GPU
    if ("_private_main_gpu" in Configuration):
        mainGPU = Configuration["_private_main_gpu"]

        if (not isinstance(mainGPU, int)):
            raise AttributeError("[llama_utils] Invalid `_private_main_gpu`.")
    else:
        mainGPU = 0
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_main_gpu` not defined. Set to 0.")
    
    # Get mmap
    if ("_private_use_mmap" in Configuration):
        mmap = Configuration["_private_use_mmap"]

        if (not isinstance(mmap, bool)):
            raise AttributeError("[llama_utils] Invalid `_private_use_mmap`.")
    else:
        mmap = True
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_use_mmap` not defined. Set to True.")
    
    # Get mlock
    if ("_private_use_mlock" in Configuration):
        mlock = Configuration["_private_use_mlock"]

        if (not isinstance(mlock, bool)):
            raise AttributeError("[llama_utils] Invalid `_private_use_mlock`.")
    else:
        mlock = False
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_use_mlock` not defined. Set to False.")
    
    # Get ctx
    if ("ctx" in Configuration):
        ctx = Configuration["ctx"]

        if (not isinstance(ctx, int)):
            raise AttributeError("[llama_utils] Invalid `ctx`.")
    else:
        ctx = 2048
        logs.WriteLog(logs.INFO, "[llama_utils] `ctx` not defined. Set to 2048.")
    
    # Get batch
    if ("_private_batch" in Configuration):
        batch = Configuration["_private_batch"]

        if (not isinstance(batch, int)):
            raise AttributeError("[llama_utils] Invalid `_private_batch`.")
    else:
        batch = 512
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_batch` not defined. Set to 512.")
    
    # Get ubatch
    if ("_private_ubatch" in Configuration):
        ubatch = Configuration["_private_ubatch"]

        if (not isinstance(ubatch, int)):
            raise AttributeError("[llama_utils] Invalid `_private_ubatch`.")
    else:
        ubatch = 512
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_ubatch` not defined. Set to 512.")
    
    # Get threads
    if ("_private_threads" in Configuration):
        threads = Configuration["_private_threads"]

        if (not isinstance(threads, int) and threads is not None):
            raise AttributeError("[llama_utils] Invalid `_private_threads`.")
    else:
        threads = None
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_threads` not defined. Set to None.")
    
    # Get batch_threads
    if ("_private_batch_threads" in Configuration):
        batchThreads = Configuration["_private_batch_threads"]

        if (not isinstance(batchThreads, int) and batchThreads is not None):
            raise AttributeError("[llama_utils] Invalid `_private_batch_threads`.")
    else:
        batchThreads = None
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_batch_threads` not defined. Set to None.")
    
    # Get rope_scaling_type
    if ("_private_rope_scaling_type" in Configuration):
        ropeScalingType = Configuration["_private_rope_scaling_type"]

        if (not isinstance(ropeScalingType, str)):
            raise AttributeError("[llama_utils] Invalid `_private_rope_scaling_type`.")
        
        ropeScalingType = StringToRopeScalingType(ropeScalingType)

        if (ropeScalingType is None):
            ropeScalingType = llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED
            logs.PrintLog(logs.WARNING, "[llama_utils] `_private_rope_scaling_type` not found. Set to `unspecified`.")
    else:
        ropeScalingType = llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_rope_scaling_type` not defined. Set to `unspecified`.")
    
    # Get rope_freq_base
    if ("_private_rope_freq_base" in Configuration):
        ropeFreqBase = Configuration["_private_rope_freq_base"]

        if (not isinstance(ropeFreqBase, int) and not isinstance(ropeFreqBase, float)):
            raise AttributeError("[llama_utils] Invalid `_private_rope_freq_base`.")
    else:
        ropeFreqBase = 0
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_rope_freq_base` not defined. Set to 0.")
    
    # Get rope_freq_scale
    if ("_private_rope_freq_scale" in Configuration):
        ropeFreqScale = Configuration["_private_rope_freq_scale"]

        if (not isinstance(ropeFreqScale, int) and not isinstance(ropeFreqScale, float)):
            raise AttributeError("[llama_utils] Invalid `_private_rope_freq_scale`.")
    else:
        ropeFreqScale = 0
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_rope_freq_scale` not defined. Set to 0.")
    
    # Get yarn_ext_factor
    if ("_private_yarn_ext_factor" in Configuration):
        yarnExtFactor = Configuration["_private_yarn_ext_factor"]

        if (not isinstance(yarnExtFactor, int) and not isinstance(yarnExtFactor, float)):
            raise AttributeError("[llama_utils] Invalid `_private_yarn_ext_factor`.")
    else:
        yarnExtFactor = -1
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_yarn_ext_factor` not defined. Set to -1.")
    
    # Get yarn_attn_factor
    if ("_private_yarn_attn_factor" in Configuration):
        yarnAttnFactor = Configuration["_private_yarn_attn_factor"]

        if (not isinstance(yarnAttnFactor, int) and not isinstance(yarnAttnFactor, float)):
            raise AttributeError("[llama_utils] Invalid `_private_yarn_attn_factor`.")
    else:
        yarnAttnFactor = 1
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_yarn_attn_factor` not defined. Set to 1.")
    
    # Get yarn_beta_fast
    if ("_private_yarn_beta_fast" in Configuration):
        yarnBetaFast = Configuration["_private_yarn_beta_fast"]

        if (not isinstance(yarnBetaFast, int) and not isinstance(yarnBetaFast, float)):
            raise AttributeError("[llama_utils] Invalid `_private_yarn_beta_fast`.")
    else:
        yarnBetaFast = 32
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_yarn_beta_fast` not defined. Set to 32.")
    
    # Get yarn_beta_slow
    if ("_private_yarn_beta_slow" in Configuration):
        yarnBetaSlow = Configuration["_private_yarn_beta_slow"]

        if (not isinstance(yarnBetaSlow, int) and not isinstance(yarnBetaSlow, float)):
            raise AttributeError("[llama_utils] Invalid `_private_yarn_beta_slow`.")
    else:
        yarnBetaSlow = 1
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_yarn_beta_slow` not defined. Set to 1.")
    
    # Get yarn_orig_ctx
    if ("_private_yarn_orig_ctx" in Configuration):
        yarnOrigCtx = Configuration["_private_yarn_orig_ctx"]

        if (not isinstance(yarnOrigCtx, int)):
            raise AttributeError("[llama_utils] Invalid `_private_yarn_orig_ctx`.")
    else:
        yarnOrigCtx = 0
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_yarn_orig_ctx` not defined. Set to 0.")
    
    # Get pooling_type
    if ("_private_pooling_type" in Configuration):
        poolingType = Configuration["_private_pooling_type"]

        if (not isinstance(poolingType, str)):
            raise AttributeError("[llama_utils] Invalid `_private_pooling_type`.")
        
        poolingType = StringToPoolingType(poolingType)

        if (poolingType is None):
            poolingType = POOLING_UNSPECIFIED
            logs.PrintLog(logs.WARNING, "[llama_utils] `_private_pooling_type` not found. Set to `unspecified`.")
    else:
        poolingType = POOLING_UNSPECIFIED
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_pooling_type` not defined. Set to `unspecified`.")
    
    # Get offload_kqv
    if ("_private_offload_kqv" in Configuration):
        offloadKqv = Configuration["_private_offload_kqv"]

        if (not isinstance(offloadKqv, bool)):
            raise AttributeError("[llama_utils] Invalid `_private_offload_kqv`.")
    else:
        offloadKqv = True
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_offload_kqv` not defined. Set to True.")
    
    # Get offload_op
    if ("_private_offload_op" in Configuration):
        offloadOp = Configuration["_private_offload_op"]

        if (not isinstance(offloadOp, bool) and offloadOp is not None):
            raise AttributeError("[llama_utils] Invalid `_private_offload_op`.")
    else:
        offloadOp = None
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_offload_op` not defined. Set to None.")
    
    # Get flash_attn
    if ("_private_flash_attn" in Configuration):
        flashAttn = Configuration["_private_flash_attn"]

        if (not isinstance(flashAttn, bool)):
            raise AttributeError("[llama_utils] Invalid `_private_flash_attn`.")
    else:
        flashAttn = False
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_flash_attn` not defined. Set to False.")
    
    # Get swa_full
    if ("_private_swa_full" in Configuration):
        swaFull = Configuration["_private_swa_full"]

        if (not isinstance(swaFull, bool) and swaFull is not None):
            raise AttributeError("[llama_utils] Invalid `_private_swa_full`.")
    else:
        swaFull = None
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_swa_full` not defined. Set to None.")
    
    # Set ftype_k
    if ("ftype_k" in Configuration):
        ftypeK = Configuration["ftype_k"]

        if (not isinstance(ftypeK, str)):
            raise AttributeError("[llama_utils] Invalid `ftype_k`.")
        
        ftypeK = StringToFtype(ftypeK)

        if (ftypeK is None or (
            ftypeK != FTYPE_F32 and
            ftypeK != FTYPE_F16 and
            ftypeK != FTYPE_Q8_0 and
            ftypeK != FTYPE_Q5_0 and
            ftypeK != FTYPE_Q4_0
        )):
            ftypeK = None
            logs.PrintLog(logs.WARNING, "[llama_utils] `ftype_k` not found or invalid. Set to None.")
    else:
        ftypeK = None
        logs.WriteLog(logs.INFO, "[llama_utils] `ftype_k` not defined. Set to None.")
    
    # Set ftype_v
    if ("ftype_v" in Configuration):
        ftypeV = Configuration["ftype_v"]

        if (not isinstance(ftypeV, str)):
            raise AttributeError("[llama_utils] Invalid `ftype_v`.")
        
        ftypeV = StringToFtype(ftypeV)

        if (ftypeV is None or (
            ftypeV != FTYPE_F32 and
            ftypeV != FTYPE_F16 and
            ftypeV != FTYPE_Q8_0 and
            ftypeV != FTYPE_Q5_0 and
            ftypeV != FTYPE_Q4_0
        )):
            ftypeV = None
            logs.PrintLog(logs.WARNING, "[llama_utils] `ftype_v` not found or invalid. Set to None.")
    else:
        ftypeV = None
        logs.WriteLog(logs.INFO, "[llama_utils] `ftype_v` not defined. Set to None.")
    
    # Set spm_infill
    if ("_private_spm_infill" in Configuration):
        spmInfill = Configuration["_private_spm_infill"]

        if (not isinstance(spmInfill, bool)):
            raise AttributeError("[llama_utils] Invalid `_private_spm_infill`.")
    else:
        spmInfill = False
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_spm_infill` not defined. Set to False.")
    
    # Set cache_type
    if ("_private_cache_type" in Configuration):
        cacheType = Configuration["_private_cache_type"]

        if (cacheType is not None):
            if (not isinstance(cacheType, str)):
                raise AttributeError("[llama_utils] Invalid `_private_cache_type`.")
            
            cacheType = StringToCacheType(cacheType)

            if (cacheType is None):
                logs.PrintLog(logs.WARNING, "[llama_utils] `_private_cache_type` not found. Set to None.")
    else:
        cacheType = None
        logs.WriteLog(logs.INFO, "[llama_utils] `_private_cache_type` not defined. Set to None.")
    
    # Set multimodal type
    if ("multimodal" in Configuration):
        multimodal = Configuration["multimodal"]

        if (isinstance(multimodal, str)):
            multimodal = multimodal.split(" ")
        elif (not isinstance(multimodal, list)):
            multimodal = ["text"]
    else:
        multimodal = ["text"]
    
    for mul in multimodal:
        if (
            mul != "text" and
            mul != "image" and
            mul != "video" and
            mul != "audio"
        ):
            logs.PrintLog(logs.WARNING, f"[llama_utils] Multimodal type '{mul}' not supported.")
            continue
    
    # Save the parameters in a dictionary
    modelParamsLCPP = {
        "model_path": modelPath,
        "n_gpu_layers": gpuLayers,
        "split_mode": splitMode,
        "main_gpu": mainGPU,
        "vocab_only": False,
        "use_mmap": mmap,
        "use_mlock": mlock,
        "seed": -1,
        "n_ctx": ctx,
        "n_batch": batch,
        "n_ubatch": ubatch,
        "n_threads": threads,
        "n_threads_batch": batchThreads,
        "rope_scaling_type": ropeScalingType,
        "rope_freq_base": ropeFreqBase,
        "rope_freq_scale": ropeFreqScale,
        "yarn_ext_factor": yarnExtFactor,
        "yarn_attn_factor": yarnAttnFactor,
        "yarn_beta_fast": yarnBetaFast,
        "yarn_beta_slow": yarnBetaSlow,
        "yarn_orig_ctx": yarnOrigCtx,
        "pooling_type": poolingType,
        "logits_all": False,
        "embedding": False,
        "offload_kqv": offloadKqv,
        "op_offload": offloadOp,
        "flash_attn": flashAttn,
        "swa_full": swaFull,
        "no_perf": False,
        "type_k": ftypeK,
        "type_v": ftypeV,
        "spm_infill": spmInfill,
        "cache_type": cacheType,
        "chat_handler": chatHandler,
        "verbose": verbose
    }

    # Load the model
    logs.WriteLog(logs.INFO, "[llama_utils] Loading model...")
    loadingTime = time.time()

    model = Llama(**modelParamsLCPP)
    model.set_cache(cacheType)

    loadingTime = time.time() - loadingTime
    loadingTime = round(loadingTime, 3)

    logs.WriteLog(logs.INFO, f"[llama_utils] Model loaded in {loadingTime} seconds.")
    return {
        "_private_model": model,
        "_private_type": "lcpp"
    }
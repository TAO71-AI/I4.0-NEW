from typing import Any
from transformers import BitsAndBytesConfig
import torch

def StringToDType(DType: str) -> torch.dtype:
    DType = DType.lower().strip()

    if (DType == "f64" or DType == "fp64" or DType == "float64"):
        return torch.float64
    elif (DType == "f32" or DType == "fp32" or DType == "float32"):
        return torch.float32
    elif (DType == "f16" or DType == "fp16" or DType == "float16"):
        return torch.float16
    elif (DType == "bf16" or DType == "bfp16" or DType == "bfloat16"):
        return torch.bfloat16
    elif (DType == "f8_e4m3fn" or DType == "fp8_e4m3fn" or DType == "float8_e4m3fn"):
        return torch.float8_e4m3fn
    elif (DType == "f8_e4m3fnuz" or DType == "fp8_e4m3fnuz" or DType == "float8_e4m3fnuz"):
        return torch.float8_e4m3fnuz
    elif (DType == "f8_e5m2" or DType == "fp8_e5m2" or DType == "float8_e5m2"):
        return torch.float8_e5m2
    elif (DType == "f8_e5m2fnuz" or DType == "fp8_e5m2fnuz" or DType == "float8_e5m2fnuz"):
        return torch.float8_e5m2fnuz
    elif (DType == "f8_e8m0fnu" or DType == "fp8_e8m0fnu" or DType == "float8_e8m0fnu"):
        return torch.float8_e8m0fnu
    elif (DType == "f4_e2m1fn_x2" or DType == "fp4_e2m1fn_x2" or DType == "float4_e2m1fn_x2"):
        return torch.float4_e2m1fn_x2
    elif (DType == "i64" or DType == "int64"):
        return torch.int64
    elif (DType == "i32" or DType == "int32"):
        return torch.int32
    elif (DType == "i16" or DType == "int16"):
        return torch.int16
    elif (DType == "i8" or DType == "int8"):
        return torch.int8
    
    raise ValueError("Invalid or unrecognized PyTorch DType.")

def CreateBNBQuantization(Config: dict[str, Any], FromModelConfig: bool = False) -> BitsAndBytesConfig | None:
    if (FromModelConfig):
        conf = Config["bnb_quantization"] if ("bnb_quantization" in Config) else None
    else:
        conf = Config
    
    if (conf is None):
        return None
    
    bnbBits = conf["bits"] if ("bits" in conf) else None

    if (bnbBits is None or (bnbBits != 4 and bnbBits != 8)):
        raise ValueError("Invalid bits in BNB config.")
    
    return BitsAndBytesConfig(
        load_in_8bit = bnbBits == 8,
        load_in_4bit = bnbBits == 4
    )

def GetAttnImpl(ModelConfig: dict[str, Any], ParamName: str = "attn") -> str | None:
    if (ParamName not in ModelConfig):
        return None
    
    attn = ModelConfig[ParamName].lower()

    if (attn == "none"):
        return None
    elif (attn == "eager" or attn == "sdpa"):
        return attn
    elif (attn == "flash" or attn == "flash_attn" or attn == "flash_attn_2"):
        return "flash_attention_2"
    elif (attn == "flash_3" or attn == "flash_attn_3"):
        return "flash_attention_3"
    elif (attn == "flex" or attn == "flex_attn"):
        return "flex_attention"
    
    raise ValueError("Invalid attention implementation.")
from typing import Any
import Utilities.install_requirements as req

def Install(Env: dict[str, Any] | None = None, Args: list[str] = []) -> None:
    req.InstallPackage(
        Packages = ["git+https://github.com/Tps-F/fairseq.git@main"],
        PIPOptions = Args
    )
    req.InstallPackage(
        Packages = [
            "soundfile==0.12.1",
            "librosa==0.10.1",
            "praat-parselmouth==0.4.3",
            "pyworld==0.3.4",
            "torchcrepe==0.0.22",
            "av==12.0.0",  # Requires >=11.0.0,<12.0.0
            "faiss-cpu==1.7.4",
            "python-dotenv==1.0.0",
            "pydub==0.25.1",
            "click==8.1.7",
            "tensorboardx==2.6.2.2",
            "poethepoet==0.24.4",
            "uvicorn==0.26.0",
            "fastapi==0.109.0",
            "python-multipart==0.0.6",
            "numba==0.58.1",
            "numpy==1.26.4",
            "setuptools<82"
        ],
        PIPOptions = Args
    )
    req.InstallPackage(
        Packages = ["git+https://github.com/TAO71-AI/Retrieval-based-Voice-Conversion@develop"],
        PIPOptions = ["--no-deps"] + Args
    )

if (__name__ == "__main__"):
    Install()
from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


AGNES_ENDPOINT = "https://apihub.agnes-ai.com/v1/images/generations"
DOUBAO_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
DEFAULT_AGNES_MODEL = "agnes-image-2.1-flash"
DEFAULT_DOUBAO_MODEL = "doubao-seedream-4-0-250828"


class ImageServiceError(RuntimeError):
    pass


def _download(url: str, target: Path, *, timeout: int) -> None:
    request = Request(url, headers={"User-Agent": "WeWrite/0.1"})
    with urlopen(request, timeout=timeout) as response:
        target.write_bytes(response.read())


def _post_json(*, endpoint: str, api_key: str, payload: dict, timeout: int, provider_name: str) -> dict:
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        lowered = detail.lower()
        if exc.code in {401, 403} or "authenticationerror" in lowered or "unauthorized" in lowered:
            raise ImageServiceError(
                f"{provider_name} API Key 无效或格式不正确。请到设置页重新填写与“{provider_name}”匹配的 API Key。"
            ) from exc
        raise ImageServiceError(f"{provider_name}图片生成失败（{exc.code}）：{detail[:300]}") from exc
    except URLError as exc:
        raise ImageServiceError(f"无法连接{provider_name}生图服务：{exc.reason}") from exc
    except TimeoutError as exc:
        raise ImageServiceError(f"{provider_name}图片生成超时，请稍后重试。") from exc


def _agnes_payload(*, model: str, prompt: str) -> dict:
    return {
        "model": model or DEFAULT_AGNES_MODEL,
        "prompt": prompt,
        "size": "1024x576",
        "return_base64": True,
    }


def _doubao_payload(*, model: str, prompt: str) -> dict:
    return {
        "model": model or DEFAULT_DOUBAO_MODEL,
        "prompt": prompt,
        "size": "2K",
        "sequential_image_generation": "disabled",
        "stream": False,
        "response_format": "url",
        "watermark": False,
    }


def generate_image(
    *,
    provider: str,
    api_key: str,
    prompt: str,
    output_path: Path,
    model: str = "",
    base_url: str = "",
    timeout: int = 180,
) -> dict[str, str]:
    if not api_key.strip():
        raise ImageServiceError("请先在设置中配置 AI 生图 API Key。")
    if not prompt.strip():
        raise ImageServiceError("缺少图片生成描述。")

    provider_name = str(provider or "agnes").strip().lower()
    if provider_name in {"doubao", "volcengine", "ark"}:
        resolved_model = model or DEFAULT_DOUBAO_MODEL
        endpoint = base_url.strip() or DOUBAO_ENDPOINT
        payload = _doubao_payload(model=resolved_model, prompt=prompt.strip())
        result = _post_json(
            endpoint=endpoint,
            api_key=api_key,
            payload=payload,
            timeout=timeout,
            provider_name="豆包",
        )
    elif provider_name in {"agnes", ""}:
        resolved_model = model or DEFAULT_AGNES_MODEL
        endpoint = base_url.strip() or AGNES_ENDPOINT
        payload = _agnes_payload(model=resolved_model, prompt=prompt.strip())
        result = _post_json(
            endpoint=endpoint,
            api_key=api_key,
            payload=payload,
            timeout=timeout,
            provider_name="Agnes",
        )
    else:
        raise ImageServiceError(f"当前暂不支持生图服务：{provider_name}。")

    data = result.get("data")
    first = data[0] if isinstance(data, list) and data else {}
    if not isinstance(first, dict):
        raise ImageServiceError("AI 生图服务返回了无法识别的结果。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_url = str(first.get("url") or "").strip()
    image_base64 = str(first.get("b64_json") or "").strip()
    if image_url:
        try:
            _download(image_url, output_path, timeout=timeout)
        except Exception as exc:
            raise ImageServiceError("图片已经生成，但下载到本机失败，请重试。") from exc
        source = "url"
    elif image_base64:
        try:
            output_path.write_bytes(base64.b64decode(image_base64))
        except Exception as exc:
            raise ImageServiceError("AI 生图服务返回的图片数据无法保存。") from exc
        source = "base64"
    else:
        raise ImageServiceError("AI 生图服务没有返回图片。")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ImageServiceError("生成的图片为空，请重试。")
    return {
        "local_path": str(output_path.resolve()),
        "source": source,
        "provider": provider_name,
        "model": resolved_model,
    }


def generate_cover_image(**kwargs) -> dict[str, str]:
    return generate_image(**kwargs)

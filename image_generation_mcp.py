"""stdio MCP server for AI LB Cloudflare image generation.

Calls /v1/images/generations on the public Bonnate AI LB at
https://lb.bonnate.com/v1. Reference images are read from local paths so the
caller can upload files.
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

PROTOCOL_VERSION = "2024-11-05"
DEFAULT_MODEL = "cloudflare/@cf/black-forest-labs/flux-2-klein-4b"
DEFAULT_BASE_URL = "https://lb.bonnate.com/v1"
REFERENCE_LIMITS = {
    "cloudflare/@cf/black-forest-labs/flux-2-dev": 4,
    "cloudflare/@cf/black-forest-labs/flux-2-klein-4b": 4,
    "cloudflare/@cf/black-forest-labs/flux-2-klein-9b": 4,
    "cloudflare/@cf/bytedance/stable-diffusion-xl-lightning": 1,
    "cloudflare/@cf/stabilityai/stable-diffusion-xl-base-1.0": 1,
    "cloudflare/@cf/lykon/dreamshaper-8-lcm": 1,
}
_TEXT_ONLY = (
    "cloudflare/@cf/black-forest-labs/flux-1-schnell",
    "cloudflare/@cf/leonardo/lucid-origin",
    "cloudflare/@cf/leonardo/phoenix-1.0",
)

def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _api_key() -> str:
    key = os.environ.get("AI_LB_API_KEY", "").strip()
    if key:
        return key
    key_file = os.environ.get("AI_LB_API_KEY_FILE", "").strip()
    if not key_file:
        candidate = _script_dir() / "api-key"
        if candidate.is_file():
            key_file = str(candidate)
    if not key_file:
        raise RuntimeError("Set AI_LB_API_KEY or AI_LB_API_KEY_FILE")
    return Path(key_file).read_text(encoding="utf-8").strip()


def _output_dir() -> Path:
    configured = os.environ.get("AI_LB_IMAGE_DIR", "").strip()
    directory = Path(configured) if configured else _script_dir() / "images"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _base_url() -> str:
    configured = os.environ.get("AI_LB_BASE_URL", "").strip()
    return (configured or DEFAULT_BASE_URL).rstrip("/")


def _request(method: str, path: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes, str]:
    request_headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
        "User-Agent": "ai-lb-image-mcp/1.0",
    }
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(_base_url() + path, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type", "")


def _multipart(fields: list[tuple[str, str]], files: list[tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----ai-lb-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )
    for filename, data, content_type in files:
        chunks.append(
            (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode()
            + data
            + b"\r\n"
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def list_image_models() -> str:
    status, body, _content_type = _request("GET", "/models")
    if status != 200:
        raise RuntimeError(body.decode("utf-8", errors="replace")[:800])
    payload = json.loads(body)
    lines = []
    for item in payload.get("data", []):
        model_id = str(item.get("id", ""))
        if not model_id.startswith("cloudflare/"):
            continue
        if model_id in REFERENCE_LIMITS:
            lines.append(f"{model_id}  reference images: up to {REFERENCE_LIMITS[model_id]}")
        elif model_id in _TEXT_ONLY or "flux" in model_id or "leonardo" in model_id or "diffusion" in model_id or "dreamshaper" in model_id:
            lines.append(f"{model_id}  text prompt only")
    if not lines:
        return "No Cloudflare image models are available."
    return "\n".join(lines)


def generate_image(arguments: dict[str, object]) -> tuple[str, bytes, str]:
    prompt = str(arguments.get("prompt") or "").strip()
    if not prompt:
        raise RuntimeError("prompt is required")
    model = str(arguments.get("model") or DEFAULT_MODEL).strip()
    fields = [("model", model), ("prompt", prompt), ("response_format", "b64_json")]
    for name in ("size", "steps", "strength", "seed"):
        value = arguments.get(name)
        if value is not None and value != "":
            fields.append((name, str(value)))

    image_paths = arguments.get("image_paths") or []
    if not isinstance(image_paths, list):
        raise RuntimeError("image_paths must be a list of local file paths")
    files: list[tuple[str, bytes, str]] = []
    for raw_path in image_paths:
        path = Path(str(raw_path))
        if not path.is_file():
            raise RuntimeError(f"reference image not found: {path}")
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        files.append((path.name, path.read_bytes(), content_type))

    body, content_type = _multipart(fields, files)
    status, response_body, _response_type = _request(
        "POST",
        "/images/generations",
        data=body,
        headers={"Content-Type": content_type},
    )
    if status != 200:
        raise RuntimeError(response_body.decode("utf-8", errors="replace")[:800])
    payload = json.loads(response_body)
    encoded = payload["data"][0]["b64_json"]
    import base64

    image_bytes = base64.b64decode(encoded)
    extension = "png" if image_bytes.startswith(b"\x89PNG") else "jpg"
    mime = "image/png" if extension == "png" else "image/jpeg"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    slug = model.rsplit("/", 1)[-1].replace("@", "")
    destination = _output_dir() / f"{stamp}-{slug}.{extension}"
    destination.write_bytes(image_bytes)
    return f"Saved {destination}", image_bytes, mime


def _tools() -> list[dict[str, object]]:
    return [
        {
            "name": "list_image_models",
            "description": "List Cloudflare image models available through AI LB, including which ones accept reference image uploads.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "generate_image",
            "description": (
                "Generate an image through AI LB. Flux 2 models accept up to 4 local reference images. "
                "Stable Diffusion models accept 1 reference image. flux-1-schnell and the Leonardo models are text-only. "
                "The image is saved locally and returned."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "model": {"type": "string", "description": f"Defaults to {DEFAULT_MODEL}"},
                    "size": {"type": "string", "description": "Width x height, for example 512x512"},
                    "steps": {"type": "integer"},
                    "strength": {"type": "number", "description": "Stable Diffusion reference strength from 0 to 1"},
                    "seed": {"type": "integer"},
                    "image_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Absolute local paths of reference images",
                    },
                },
                "required": ["prompt"],
            },
        },
    ]


def _call_tool(name: str, arguments: dict[str, object]) -> dict[str, object]:
    try:
        if name == "list_image_models":
            return {"content": [{"type": "text", "text": list_image_models()}]}
        if name == "generate_image":
            text, image_bytes, mime = generate_image(arguments)
            import base64

            content: list[dict[str, str]] = [{"type": "text", "text": text}]
            if len(image_bytes) <= 2_000_000:
                content.append(
                    {
                        "type": "image",
                        "data": base64.b64encode(image_bytes).decode("ascii"),
                        "mimeType": mime,
                    }
                )
            return {"content": content}
        raise RuntimeError(f"Unknown tool {name}")
    except Exception as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "isError": True}


def _handle(message: dict[str, object]) -> dict[str, object] | None:
    method = str(message.get("method") or "")
    message_id = message.get("id")
    params = message.get("params")
    if not isinstance(params, dict):
        params = {}
    if method == "notifications/initialized" or message_id is None and method.startswith("notifications/"):
        return None
    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "ai-lb-images", "version": "1.0.0"},
        }
    elif method == "tools/list":
        result = {"tools": _tools()}
    elif method == "tools/call":
        arguments = params.get("arguments")
        result = _call_tool(str(params.get("name") or ""), arguments if isinstance(arguments, dict) else {})
    elif method == "ping":
        result = {}
    else:
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _read_message() -> dict[str, object] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        decoded = line.decode("ascii", errors="replace")
        if ":" not in decoded:
            continue
        key, value = decoded.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    payload = json.loads(sys.stdin.buffer.read(length))
    if not isinstance(payload, dict):
        return None
    return payload


def _write_message(payload: dict[str, object]) -> None:
    raw = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def main() -> None:
    while True:
        message = _read_message()
        if message is None:
            return
        response = _handle(message)
        if response is not None:
            _write_message(response)


def cli(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate images through the Bonnate AI LB.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("models", help="List image models")
    generate = commands.add_parser("generate", help="Generate an image and save it locally")
    generate.add_argument("prompt")
    generate.add_argument("--model", default=DEFAULT_MODEL)
    generate.add_argument("--size", help="Width x height, for example 512x512")
    generate.add_argument("--steps", type=int)
    generate.add_argument("--strength", type=float)
    generate.add_argument("--seed", type=int)
    generate.add_argument("--image", action="append", default=[], help="Reference image path, repeatable")
    generate.add_argument("--out-dir", help="Directory to save into")
    args = parser.parse_args(argv)

    try:
        if args.command == "models":
            print(list_image_models())
            return 0
        if args.out_dir:
            os.environ["AI_LB_IMAGE_DIR"] = args.out_dir
        text, _image_bytes, _mime = generate_image(
            {
                "prompt": args.prompt,
                "model": args.model,
                "size": args.size,
                "steps": args.steps,
                "strength": args.strength,
                "seed": args.seed,
                "image_paths": args.image,
            }
        )
        print(text)
        return 0
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv[1:]))
    try:
        main()
    except BrokenPipeError:
        pass

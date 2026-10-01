# AI LB image MCP

Bonnate 공개 서버 `https://lb.bonnate.com/v1`의 이미지 생성만 쓰는 MCP입니다. SSH가 필요 없습니다.

키는 이미지 전용 키를 씁니다. 이 키로는 아래 9개 이미지 모델만 보이고, 채팅 모델은 403입니다.

## 이 저장소에 없는 파일

- `api-key`: 이미지 생성 전용 키. 이 폴더에 두면 스크립트가 읽습니다. 다른 위치면 `AI_LB_API_KEY_FILE`로 지정합니다.

생성된 이미지는 이 저장소의 `images/`에 저장됩니다. `AI_LB_IMAGE_DIR`로 바꿀 수 있습니다.

## 모델

| 모델 | 참고 이미지 |
|---|---|
| `cloudflare/@cf/black-forest-labs/flux-2-klein-4b` (기본) | 최대 4장 |
| `cloudflare/@cf/black-forest-labs/flux-2-klein-9b` | 최대 4장 |
| `cloudflare/@cf/black-forest-labs/flux-2-dev` | 최대 4장 |
| `cloudflare/@cf/bytedance/stable-diffusion-xl-lightning` | 1장, `strength` |
| `cloudflare/@cf/stabilityai/stable-diffusion-xl-base-1.0` | 1장, `strength` |
| `cloudflare/@cf/lykon/dreamshaper-8-lcm` | 1장, `strength` |
| `cloudflare/@cf/black-forest-labs/flux-1-schnell` | 없음 |
| `cloudflare/@cf/leonardo/lucid-origin` | 없음 |
| `cloudflare/@cf/leonardo/phoenix-1.0` | 없음 |

## 실행

stdio MCP입니다. 포트를 열지 않고, 클라이언트가 Python으로 이 파일을 실행합니다. 표준 라이브러리만 씁니다.

## OpenCode

이 저장소의 `opencode.jsonc`가 설정입니다. 클론한 폴더에서 OpenCode를 켜면 프로바이더 `ai-lb-bonnate-images`와 MCP `ai-lb-images`가 잡힙니다. 키는 같은 폴더의 `api-key`를 읽습니다.

채팅에서 이미지 모델을 고르면 서버가 400을 돌려줍니다. 이미지는 MCP의 `generate_image` 도구로 만듭니다.

## Codex

`~/.codex/config.toml`

```toml
[mcp_servers.ai-lb-images]
command = "python"
args = ["C:\\path\\to\\ai-lb-image-mcp\\image_generation_mcp.py"]
tool_timeout_sec = 180.0

[mcp_servers.ai-lb-images.env]
AI_LB_BASE_URL = "https://lb.bonnate.com/v1"
AI_LB_API_KEY_FILE = "C:\\path\\to\\ai-lb-image-mcp\\api-key"
```

## Claude Code

`~/.claude.json`의 최상위 `mcpServers`입니다.

```json
"ai-lb-images": {
  "type": "stdio",
  "command": "python",
  "args": ["C:\\path\\to\\ai-lb-image-mcp\\image_generation_mcp.py"],
  "timeout": 180000,
  "env": {
    "AI_LB_BASE_URL": "https://lb.bonnate.com/v1",
    "AI_LB_API_KEY_FILE": "C:\\path\\to\\ai-lb-image-mcp\\api-key"
  }
}
```

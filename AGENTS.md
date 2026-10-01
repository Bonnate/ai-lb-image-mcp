# AGENTS

이 저장소는 Bonnate 공개 서버 `https://lb.bonnate.com/v1`의 이미지 생성만 다룬다. 채팅 모델 설정은 여기에 넣지 않는다.

## 동기화

모델, 도구 인자, 기본 주소, 키 파일 위치, 저장 폴더, 명령줄 사용법 중 하나를 바꾸면 같은 변경에서 아래를 모두 맞춘다. 하나만 고치고 끝내면 안 된다.

| 대상 | 파일 |
|---|---|
| 동작 | `image_generation_mcp.py` |
| OpenCode | `opencode.jsonc` |
| Claude Code | `.mcp.json`, `.claude/skills/ai-lb-images/SKILL.md` |
| Codex | `.codex/config.toml`, `.agents/skills/ai-lb-images/SKILL.md` |
| Cursor | `.cursor/mcp.json`, `.cursor/skills/ai-lb-images/SKILL.md` |
| 사람용 설명 | `README.md` |

스킬 세 파일은 내용이 같아야 한다. 원본은 `.agents/skills/ai-lb-images/SKILL.md`이고, 바꾼 뒤 그 내용을 `.claude/skills/ai-lb-images/SKILL.md`와 `.cursor/skills/ai-lb-images/SKILL.md`에 그대로 복사한다.

이 PC에서 저장소 밖 설정도 쓰면 같은 내용으로 맞춘다.

- `C:\Users\SUPERCENT\.codex\config.toml`의 `[mcp_servers.ai-lb-images]`
- `C:\Users\SUPERCENT\.claude.json`의 `mcpServers.ai-lb-images`
- `C:\Users\SUPERCENT\.cursor\mcp.json`의 `mcpServers.ai-lb-images`
- `C:\Users\SUPERCENT\.agents\skills\ai-lb-images`
- `C:\Users\SUPERCENT\.claude\skills\ai-lb-images`
- `C:\Users\SUPERCENT\.cursor\skills\ai-lb-images`

`api-key`와 `images/`는 커밋하지 않는다.

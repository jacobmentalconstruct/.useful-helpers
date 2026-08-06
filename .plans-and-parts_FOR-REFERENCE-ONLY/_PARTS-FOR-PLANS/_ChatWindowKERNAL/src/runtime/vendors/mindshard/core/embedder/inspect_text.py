from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def _bundle_root() -> Path:
    return Path(__file__).resolve().parent


def _find_bdvec_root() -> Path:
    bundle_root = _bundle_root()
    candidates = [
        bundle_root / "bdvec",
        bundle_root / "_Parts_Within_Can_Be_Used_WHOLE_" / "_BDVecEmbed",
    ]
    for candidate in candidates:
        if (candidate / "artifacts" / "tokenizer.json").is_file():
            return candidate
    raise FileNotFoundError("Could not locate BDVec artifacts in this bundle.")


def _find_src_root(bdvec_root: Path) -> Path:
    candidates = [
        bdvec_root,
        bdvec_root / "src",
        bdvec_root / "bpe_svd" / "src",
    ]
    for candidate in candidates:
        if (candidate / "bpe_svd" / "__init__.py").is_file():
            return candidate
    raise FileNotFoundError("Could not locate the BDVec Python source in this bundle.")


def _load_provider():
    bdvec_root = _find_bdvec_root()
    src_root = _find_src_root(bdvec_root)
    tokenizer_path = bdvec_root / "artifacts" / "tokenizer.json"
    embeddings_path = bdvec_root / "artifacts" / "embeddings.npy"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from bpe_svd import DeterministicEmbedProvider

    return (
        DeterministicEmbedProvider(tokenizer_path, embeddings_path),
        tokenizer_path,
        embeddings_path,
    )


def _load_text(args_map: dict[str, str]) -> tuple[str, str]:
    text = str(args_map.get("text", "")).strip()
    path = str(args_map.get("path", "")).strip()
    max_chars = int(str(args_map.get("max_chars", "4000")).strip() or "4000")
    if path:
        payload = Path(path).read_text(encoding="utf-8", errors="replace")
        return payload[:max_chars], path
    return text, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--args-json", required=True)
    parsed = parser.parse_args()
    args_map = json.loads(parsed.args_json)
    if not isinstance(args_map, dict):
        print(json.dumps({"ok": False, "error": "Invalid args payload."}, indent=2))
        return 2

    text, source_path = _load_text({str(key): str(value) for key, value in args_map.items()})
    if not text.strip():
        print(json.dumps({"ok": False, "error": "Provide text or path."}, indent=2))
        return 2

    provider, tokenizer_path, embeddings_path = _load_provider()
    result = provider.embed_texts([text])
    token_ids = result.token_ids[0] if result.token_ids else []
    tokens = provider.decode_token_ids(token_ids)
    vector = result.vectors[0] if result.vectors else []
    nearest_k = max(1, min(int(str(args_map.get("nearest_k", "8")).strip() or "8"), 20))
    nearest = [
        {"token": token, "score": round(score, 6)}
        for token, score, _vector in provider.nearest_tokens(vector, k=nearest_k)
    ]
    payload = {
        "ok": True,
        "source_path": source_path,
        "summary": f"BDVec tokenized {len(token_ids)} tokens across {len(text)} chars.",
        "trust_level": "normal",
        "tokenizer_path": str(tokenizer_path),
        "embeddings_path": str(embeddings_path),
        "dimensions": result.dimensions,
        "token_count": result.token_counts[0] if result.token_counts else 0,
        "token_ids": token_ids,
        "tokens": tokens,
        "vector_preview": [round(float(value), 6) for value in vector[:12]],
        "nearest_tokens": nearest,
        "text_preview": text[:500],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

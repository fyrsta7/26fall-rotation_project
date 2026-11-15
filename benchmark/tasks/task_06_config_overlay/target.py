"""多层配置覆盖与占位符展开引擎（包含状态更新失效语义）。"""

from __future__ import annotations
import re


VAR_PATTERN = re.compile(r"\$\{([a-zA-Z0-9_.-]+)\}")


class LayeredConfig:
    """按 defaults -> env -> runtime_overrides 优先级解析配置，并支持占位符递归展开。"""

    def __init__(
        self,
        defaults: dict[str, str] | None = None,
        env_layer: dict[str, str] | None = None,
    ) -> None:
        self._defaults: dict[str, str] = dict(defaults or {})
        self._env: dict[str, str] = dict(env_layer or {})
        self._overrides: dict[str, str] = {}

    def set_override(self, key: str, value: str) -> None:
        self._overrides[key] = value

    def clear_override(self, key: str) -> None:
        self._overrides.pop(key, None)

    def update_env(self, updates: dict[str, str]) -> None:
        self._env.update(updates)

    def _merged_raw_map(self) -> dict[str, str]:
        merged: dict[str, str] = {}
        merged.update(self._defaults)
        merged.update(self._env)
        merged.update(self._overrides)
        return merged

    def get_resolved(self, key: str, default: str = "") -> str:
        raw_map = self._merged_raw_map()
        if key not in raw_map:
            return default
        return self._expand_value(key, raw_map, visiting=set())

    def _expand_value(self, key: str, raw_map: dict[str, str], visiting: set[str]) -> str:
        if key in visiting:
            raise ValueError(f"Circular config reference detected at '{key}'")
        if key not in raw_map:
            return ""
        visiting.add(key)
        template = raw_map[key]

        def _replace(match: re.Match[str]) -> str:
            ref_key = match.group(1)
            if ref_key not in raw_map:
                return ""
            return self._expand_value(ref_key, raw_map, visiting)

        resolved = VAR_PATTERN.sub(_replace, template)
        visiting.remove(key)
        return resolved


def evaluate_request_configs(
    cfg: LayeredConfig,
    request_keys: list[str],
) -> list[str]:
    return [cfg.get_resolved(k, default="MISSING") for k in request_keys]

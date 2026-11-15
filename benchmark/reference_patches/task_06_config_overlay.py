"""task_06_config_overlay 参考优化实现：维护合并映射与已展开值缓存，修改操作自动使缓存失效。"""

from __future__ import annotations
import re


VAR_PATTERN = re.compile(r"\$\{([a-zA-Z0-9_.-]+)\}")
PLACEHOLDER_PREFIX = "$" + "{"


class LayeredConfig:
    def __init__(
        self,
        defaults: dict[str, str] | None = None,
        env_layer: dict[str, str] | None = None,
    ) -> None:
        self._defaults: dict[str, str] = dict(defaults or {})
        self._env: dict[str, str] = dict(env_layer or {})
        self._overrides: dict[str, str] = {}
        self._merged_cache: dict[str, str] | None = None
        self._resolved_cache: dict[str, str] = {}

    def _invalidate(self) -> None:
        self._merged_cache = None
        self._resolved_cache.clear()

    def set_override(self, key: str, value: str) -> None:
        if self._overrides.get(key) != value or key not in self._overrides:
            self._overrides[key] = value
            self._invalidate()

    def clear_override(self, key: str) -> None:
        if key in self._overrides:
            self._overrides.pop(key, None)
            self._invalidate()

    def update_env(self, updates: dict[str, str]) -> None:
        if updates:
            self._env.update(updates)
            self._invalidate()

    def _merged_raw_map(self) -> dict[str, str]:
        if self._merged_cache is None:
            merged: dict[str, str] = {}
            merged.update(self._defaults)
            merged.update(self._env)
            merged.update(self._overrides)
            self._merged_cache = merged
        return self._merged_cache

    def get_resolved(self, key: str, default: str = "") -> str:
        cached = self._resolved_cache.get(key)
        if cached is not None:
            return cached
        raw_map = self._merged_raw_map()
        if key not in raw_map:
            return default
        resolved = self._expand_value(key, raw_map, visiting=set())
        self._resolved_cache[key] = resolved
        return resolved

    def _expand_value(self, key: str, raw_map: dict[str, str], visiting: set[str]) -> str:
        cached = self._resolved_cache.get(key)
        if cached is not None:
            return cached
        if key in visiting:
            raise ValueError(f"Circular config reference detected at '{key}'")
        if key not in raw_map:
            return ""
        visiting.add(key)
        template = raw_map[key]
        if PLACEHOLDER_PREFIX not in template:
            visiting.remove(key)
            self._resolved_cache[key] = template
            return template

        def _replace(match: re.Match[str]) -> str:
            ref_key = match.group(1)
            if ref_key not in raw_map:
                return ""
            return self._expand_value(ref_key, raw_map, visiting)

        resolved = VAR_PATTERN.sub(_replace, template)
        visiting.remove(key)
        self._resolved_cache[key] = resolved
        return resolved


def evaluate_request_configs(
    cfg: LayeredConfig,
    request_keys: list[str],
) -> list[str]:
    get_fn = cfg.get_resolved
    return [get_fn(k, default="MISSING") for k in request_keys]

#!/usr/bin/env python3
"""BunnyScholar × GPTZero 拟人化降 AI 闭环工作流 CLI（100% Python 3 标准库，零第三方依赖）。"""

from __future__ import annotations

import argparse
import copy
import getpass
import hashlib
import io
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import warnings
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from xml.sax.saxutils import escape as xml_escape

if os.name == "nt":
    import msvcrt
else:
    import fcntl


# ==============================================================================
# 全局常量与自定义异常
# ==============================================================================

DEFAULT_API_URL = "https://bunnyscholar.cn/api/open/humanizer"
LOGIN_URL = "https://bunnyscholar.cn/"
CONSOLE_URL = "https://bunnyscholar.cn/developer"
BUNNYSCHOLAR_SKILL_URL = "https://bunnyscholar.cn/skills/bunnyscholar-api.md"
SKILL_VERSION = "1.2.3"
SUPPORTED_HUMANIZER_LANGUAGES: Tuple[str, ...] = ("en", "zh_CN")
SUPPORTED_PLATFORMS_BY_LANGUAGE: Dict[str, Tuple[str, ...]] = {
    "zh_CN": ("cnki", "wanfang", "weipu", "gezida", "daya", "turnitin"),
    "en": ("turnitin", "gptzero", "quillbot", "zerogpt", "cnki", "wanfang", "gezida", "weipu"),
}
HUMANIZER_REF_UNIT_PRICE_CNY = 1.0
SKILL_REPO_URL = "https://github.com/Whitopus/bunnyscholar-gptzero-loop"
SKILL_REMOTE_RAW_BASE = "https://raw.githubusercontent.com/Whitopus/bunnyscholar-gptzero-loop/main"
SKILL_REMOTE_SKILL_MD_URL = f"{SKILL_REMOTE_RAW_BASE}/SKILL.md"
SKILL_REMOTE_ARCHIVE = "https://codeload.github.com/Whitopus/bunnyscholar-gptzero-loop/zip/refs/heads/main"
SKILL_UPDATE_FILES: Tuple[str, ...] = (
    "SKILL.md",
    "README.md",
    "LICENSE",
    ".gitignore",
    ".env.example",
    "scripts/humanizer_loop.py",
    "references/onboarding_guide.md",
    "references/gptzero_browser_sop.md",
    "references/anti_ai_playbook.md",
)
UPDATE_CACHE_TTL_SECONDS = 86400
KEYS_URL = "https://bunnyscholar.cn/developer/keys"
RECHARGE_URL = "https://bunnyscholar.cn/developer/recharge"
DEFAULT_RATE_LIMIT = 20.0
DEFAULT_MAX_RETRIES = 0
DEFAULT_HTTP_RETRIES = 3
DEFAULT_TIMEOUT = 30.0

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# 常见 OOXML 命名空间静态映射表，避免序列化时被自动改写为 ns0/ns1 导致 Word 兼容性异常
STANDARD_OOXML_NAMESPACES: Dict[str, str] = {
    "w": W_NS,
    "r": R_NS,
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "m": MATH_NS,
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
}

# 匹配文内方括号引文组，支持 [1], [1, 2], [1-3], [1–3], [1—3], [1, 3-5, 8] 等形式
CITATION_GROUP_RE = re.compile(
    r"\[(\d+(?:\s*[-–—]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–—]\s*\d+)?)*)\]"
)

# 匹配学术文本第一人称代词（严格排除全大写缩写 "US"，且 "I" 仅匹配大写形式）
FIRST_PERSON_RE = re.compile(
    r"\b(?:I|[Mm]y|[Mm]e|[Mm]ine|[Ww]e|[Oo]ur|[Oo]urs|[Mm]yself|[Oo]urselves|us|Us)\b"
)

# 常见在独立大写 "I" 之前出现的罗马数字前导词（含单复数），用于降低误判率
ROMAN_PRECEDING_WORDS_RE = re.compile(
    r"\b(?:Types?|Phases?|Stages?|Class(?:es)?|Grades?|Parts?|Sections?|Tables?|Figures?|Appendix|Appendices|Factors?|Vitamins?|Chapters?|Volumes?|Wars?)\s+$",
    re.IGNORECASE,
)

# 超长连续纯字母词检查（>16 字母通常为接口偶发的粘连乱码词）
LONG_GARBLED_WORD_RE = re.compile(r"\b[A-Za-z]{17,}\b")

# URL 过滤正则（质量门禁校验超长词前先剔除合法网址）
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

# 参考文献标题行匹配（支持中英文常见标题文本及数字/罗马数字/字母/中文顿号章节编号前缀）
REFERENCES_HEADING_RE = re.compile(
    r"^(?:(?:\d+(?:\.\d+)*\.?|(?-i:[IVXLCDM]+)\.?|(?-i:[A-Z])\.)\s+|(?:\d+|[一二三四五六七八九十]+)、\s*)?"
    r"(?:references|bibliography|works\s+cited|literature\s+cited|参考文献)\s*:?\s*$",
    re.IGNORECASE,
)

API_KEY_NAME = "BUNNYSCHOLAR_API_KEY"
EXAMPLE_API_KEY = "sk-replace-with-your-bunnyscholar-api-key"


class CliError(RuntimeError):
    """CLI 业务逻辑、参数校验或文件格式异常。"""


class RateLimitError(RuntimeError):
    """HTTP 429 限流重试耗尽异常。"""


class ApiHttpError(RuntimeError):
    """不可重试的 HTTP 客户端错误（400/401/402/403 等）。"""

    def __init__(self, status_code: int, url: str, body_preview: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body_preview = body_preview


class QualityGateError(RuntimeError):
    """质量门禁重刷次数耗尽仍未通过的异常。"""


# ==============================================================================
# 通用工具函数
# ==============================================================================

def log_stderr(message: str) -> None:
    """将进度、限流或重试日志输出到 sys.stderr，不污染 stdout 结构化输出。"""
    print(message, file=sys.stderr)


def emit_result(data: Dict[str, Any], output_path: Optional[str]) -> None:
    """统一输出结果：指定 --output 时写 UTF-8 JSON 文件并在 stdout 打印简要提示，否则直接打印 JSON。"""
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Success! Result written to: {out}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def atomic_write_bytes(target_path: Path, payload: bytes) -> None:
    """在目标文件同目录创建临时文件并原子替换，避免写入中断损坏原文件。"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp_", suffix=target_path.suffix, dir=str(target_path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def atomic_write_json(target_path: Path, data: Any) -> None:
    """将对象序列化为 UTF-8 JSON 后原子写入目标路径。"""
    payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    atomic_write_bytes(target_path, payload)


def atomic_copy_file(src_path: Path, dst_path: Path) -> None:
    """先复制到目标同目录临时文件再原子替换，兼容跨分区复制。"""
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp_copy_", suffix=dst_path.suffix, dir=str(dst_path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        shutil.copy2(src_path, tmp_path)
        os.replace(tmp_path, dst_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def compute_sha256(file_path: Path) -> str:
    """流式计算文件的 SHA-256 十六进制摘要。"""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def is_cjk_char(ch: str) -> bool:
    """判断单个字符是否属于 BunnyScholar 按 1 计费单位处理的中日韩及全角字符范围。"""
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF      # CJK 统一汉字
        or 0x3400 <= code <= 0x4DBF   # CJK 扩展 A
        or 0xF900 <= code <= 0xFAFF   # CJK 兼容汉字
        or 0x3000 <= code <= 0x303F   # CJK 标点符号
        or 0x3040 <= code <= 0x30FF   # 日文平假名与片假名
        or 0xAC00 <= code <= 0xD7AF   # 韩文音节
        or 0xFF00 <= code <= 0xFFEF   # 全角 ASCII 与全角标点
    )


def compute_billable_chars(text: str) -> Dict[str, int]:
    """计算 BunnyScholar 计费字符数：CJK 1 字 = 1 单位，其余每 3 字符向上取整 = 1 单位。"""
    cjk_count = sum(1 for ch in text if is_cjk_char(ch))
    non_cjk_count = len(text) - cjk_count
    billable = cjk_count + math.ceil(non_cjk_count / 3)
    return {
        "raw_chars": len(text),
        "cjk_chars": cjk_count,
        "non_cjk_chars": non_cjk_count,
        "billable_chars": billable,
    }


def w_tag(local_name: str) -> str:
    """构造 WordprocessingML 主命名空间完整标签名。"""
    return f"{{{W_NS}}}{local_name}"


def r_tag(local_name: str) -> str:
    """构造 OfficeDocument Relationships 命名空间完整标签名。"""
    return f"{{{R_NS}}}{local_name}"


def xml_tag(local_name: str) -> str:
    """构造 XML 标准命名空间完整属性名。"""
    return f"{{{XML_NS}}}{local_name}"


def register_ooxml_namespaces(xml_bytes: bytes) -> List[Tuple[str, str]]:
    """注册标准 OOXML 前缀与源文档声明的全部命名空间，并返回根元素命名空间列表供序列化补全。"""
    for prefix, uri in STANDARD_OOXML_NAMESPACES.items():
        ET.register_namespace(prefix, uri)
    root_namespaces: List[Tuple[str, str]] = []
    seen_root = False
    for event, data in ET.iterparse(io.BytesIO(xml_bytes), events=("start-ns", "start")):
        if event == "start-ns":
            prefix, uri = data
            if not seen_root:
                root_namespaces.append((prefix, uri))
            if prefix:
                ET.register_namespace(prefix, uri)
        elif event == "start" and not seen_root:
            seen_root = True
    return root_namespaces


def serialize_document_xml(root: ET.Element, root_namespaces: Sequence[Tuple[str, str]]) -> bytes:
    """序列化 ElementTree 并补回被 ElementTree 裁剪的根级 xmlns 声明，确保 mc:Ignorable 完整有效。"""
    serialized = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
    match = re.search(r"<([A-Za-z0-9_:-]+)(\s[^>]*)?>", serialized)
    if match and root_namespaces:
        open_tag = match.group(0)
        missing_decls: List[str] = []
        seen_prefixes: Set[str] = set()
        for prefix, uri in root_namespaces:
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            attr_name = f"xmlns:{prefix}" if prefix else "xmlns"
            if f"{attr_name}=" not in open_tag:
                missing_decls.append(f'{attr_name}="{xml_escape(uri)}"')
        if missing_decls:
            patched_open_tag = open_tag[:-1] + " " + " ".join(missing_decls) + ">"
            serialized = serialized[:match.start()] + patched_open_tag + serialized[match.end():]
    return serialized.encode("utf-8")


# ==============================================================================
# 模块 1：check-env 无泄露环境探测
# ==============================================================================

def _parse_dotenv_key_from_line(line: str, key_name: str) -> Optional[str]:
    """解析单行 .env 定义中的指定变量值（自动剥离 UTF-8 BOM）；未匹配返回 None。"""
    s = line.lstrip("\ufeff").strip()
    if not s or s.startswith("#"):
        return None
    if s.startswith("export ") or s.startswith("export\t"):
        s = s[6:].lstrip()
    name, separator, value = s.partition("=")
    if not separator or name.strip() != key_name:
        return None
    val = value.strip()
    if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
        val = val[1:-1].strip()
    return val


def _usable_key(value: str) -> Optional[str]:
    value = value.strip()
    return value if value and value != EXAMPLE_API_KEY else None


def _read_dotenv_key(env_path: Path) -> Optional[str]:
    value = ""
    with env_path.open("r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            parsed = _parse_dotenv_key_from_line(line, API_KEY_NAME)
            if parsed is not None:
                value = parsed
    return _usable_key(value)


def _read_key_for_runtime_call(
    env_paths: Optional[Sequence[str]] = None,
    ignore_process_env: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """仅供 humanize 发送 HTTP 鉴权头时在内存临时读取 Key；严禁将返回值写入日志或输出 JSON。"""
    if not ignore_process_env:
        env_val = _usable_key(os.environ.get(API_KEY_NAME, ""))
        if env_val:
            return env_val, f"env:{API_KEY_NAME}"

    candidate_files = _resolve_default_env_paths(env_paths)
    for env_file in candidate_files:
        if not env_file.is_file():
            continue
        matched_val = _read_dotenv_key(env_file)
        if matched_val:
            return matched_val, str(env_file)
    return None, None


def _resolve_default_env_paths(env_paths: Optional[Sequence[str]] = None) -> List[Path]:
    """解析待检查的 .env 文件路径列表。"""
    if env_paths is not None:
        return [Path(p).expanduser() for p in env_paths]
    home = Path.home()
    return [
        home / ".env",
        home / ".gemini" / "config" / "plugins" / "bunnyscholar-api" / ".env",
    ]


def setup_api_key(env_file: Path) -> Dict[str, Any]:
    """交互式录入密钥，在 .env 中替换同名条目并保留其他设置。"""
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise CliError("Open a local terminal and run setup-key there for hidden input.")

    log_stderr(f"Need a key? Sign in at {LOGIN_URL}, then open {KEYS_URL}")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass(f"Paste {API_KEY_NAME} (input hidden), then press Enter: ").strip()
    except getpass.GetPassWarning as exc:
        raise CliError("This terminal cannot hide input. Run setup-key in a local terminal.") from exc
    except (EOFError, KeyboardInterrupt) as exc:
        raise CliError("Key setup cancelled.") from exc
    if not _usable_key(key) or re.search(r"""[\s'"]""", key):
        raise CliError("Paste the API key from your BunnyScholar console, without quotes or spaces.")

    env_file = env_file.expanduser().resolve()
    existing = env_file.read_bytes() if env_file.exists() else b""
    has_bom = existing.startswith(b"\xef\xbb\xbf")
    content = existing.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in content else "\n"
    lines = [
        line for line in content.splitlines(keepends=True)
        if _parse_dotenv_key_from_line(line, API_KEY_NAME) is None
    ]
    retained = "".join(lines)
    if retained and not retained.endswith(("\n", "\r")):
        retained += newline
    updated = f"{retained}{API_KEY_NAME}={key}{newline}"
    atomic_write_bytes(env_file, updated.encode("utf-8-sig" if has_bom else "utf-8"))
    if _read_dotenv_key(env_file) != key:
        raise CliError(f"Could not verify the saved key in {env_file}.")
    return {
        "saved_to": str(env_file),
        "process_env_takes_precedence": bool(_usable_key(os.environ.get(API_KEY_NAME, ""))),
    }


def detect_word_com() -> Dict[str, Any]:
    """探测 Windows 下 Microsoft Word COM 自动化是否可用。"""
    if os.name != "nt":
        return {"available": False, "version": None, "error": "Word COM is only supported on Windows."}
    try:
        reg_res = subprocess.run(
            ["reg", "query", r"HKEY_CLASSES_ROOT\Word.Application"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if reg_res.returncode != 0:
            return {"available": False, "version": None, "error": "Word.Application COM class not registered."}
    except Exception as exc:
        return {"available": False, "version": None, "error": f"Registry check failed: {exc}"}

    ps_probe = (
        "$ErrorActionPreference = 'Stop'; "
        "$w = $null; "
        "try { "
        "$w = New-Object -ComObject Word.Application; "
        "$w.Visible = $false; "
        "$w.DisplayAlerts = 0; "
        "Write-Output $w.Version "
        "} finally { "
        "if ($w -ne $null) { "
        "try { $w.Quit() } catch {}; "
        "[System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null "
        "} }"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_probe],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            ver = proc.stdout.strip().splitlines()[-1].strip() if proc.stdout.strip() else None
            return {"available": True, "version": ver, "error": None}
        err_msg = (proc.stderr or proc.stdout or "Unknown Word COM error").strip()
        return {"available": False, "version": None, "error": err_msg[:300]}
    except Exception as exc:
        return {"available": False, "version": None, "error": str(exc)}


def detect_libreoffice() -> Dict[str, Any]:
    """探测系统中可用的 LibreOffice `soffice` 可执行文件及版本。"""
    candidates: List[str] = []
    for name in ("soffice", "soffice.exe", "soffice.com"):
        resolved = shutil.which(name)
        if resolved and resolved not in candidates:
            candidates.append(resolved)

    fallback_paths: List[Path] = []
    if os.name == "nt":
        fallback_paths = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.com"),
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.com"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
            Path(r"C:\ProgramData\LibreOfficeExtract\program\soffice.com"),
            Path(r"C:\ProgramData\LibreOfficeExtract\program\soffice.exe"),
        ]
    elif sys.platform == "darwin":
        fallback_paths = [Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")]
    else:
        fallback_paths = [Path("/usr/bin/soffice"), Path("/usr/local/bin/soffice")]

    for p in fallback_paths:
        if p.is_file() and str(p) not in candidates:
            candidates.append(str(p))

    last_err: Optional[str] = None
    for exe_path in candidates:
        try:
            proc = subprocess.run([exe_path, "--version"], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                version_line = (proc.stdout or proc.stderr or "").strip().splitlines()
                return {
                    "available": True,
                    "path": exe_path,
                    "version": version_line[0] if version_line else None,
                    "error": None,
                }
            last_err = (proc.stderr or proc.stdout or f"Exit code {proc.returncode}").strip()
        except Exception as exc:
            last_err = str(exc)

    return {
        "available": False,
        "path": None,
        "version": None,
        "error": last_err or "soffice executable not found in PATH or standard directories.",
    }


def detect_bunnyscholar_skill() -> Dict[str, Any]:
    """探测全局安装、插件内置及主流客户端（Antigravity/Claude Code/Codex/Gemini CLI/OpenCode）的 bunnyscholar-api 技能。"""
    home = Path.home()
    cwd = Path.cwd()
    candidates = [
        home / ".gemini" / "config" / "skills" / "bunnyscholar-api" / "SKILL.md",
        home / ".gemini" / "config" / "plugins" / "bunnyscholar-api" / "skills" / "bunnyscholar-api" / "SKILL.md",
        home / ".gemini" / "config" / "plugins" / "bunnyscholar-api" / "SKILL.md",
        home / ".claude" / "skills" / "bunnyscholar-api" / "SKILL.md",
        home / ".agents" / "skills" / "bunnyscholar-api" / "SKILL.md",
        home / ".gemini" / "skills" / "bunnyscholar-api" / "SKILL.md",
        home / ".config" / "opencode" / "skills" / "bunnyscholar-api" / "SKILL.md",
        Path(__file__).resolve().parents[2] / "bunnyscholar-api" / "SKILL.md",
    ]
    candidates.extend(
        root / relative / "bunnyscholar-api" / "SKILL.md"
        for root in (cwd, *cwd.parents)
        for relative in (".agents/skills", ".claude/skills", ".gemini/skills", ".agent/skills")
    )
    candidates = list(dict.fromkeys(candidates))
    checked = [str(p) for p in candidates]
    for p in candidates:
        if p.is_file():
            return {"found": True, "path": str(p), "checked_paths": checked}
    return {"found": False, "path": None, "checked_paths": checked}


def _parse_semver(ver: str) -> Tuple[int, ...]:
    """解析语义化版本号为整数元组，便于安全比较。"""
    nums = [int(x) for x in re.findall(r"\d+", ver)]
    return tuple((nums + [0, 0, 0])[:3])


def _extract_frontmatter_version(text: str) -> Optional[str]:
    """从 SKILL.md YAML frontmatter 提取 version 字段。"""
    m = re.match(r"^\s*---\s*\r?\n(.*?)\r?\n---", text.lstrip("\ufeff"), re.DOTALL)
    if not m:
        return None
    vm = re.search(r"^\s*version:\s*['\"]?([0-9]+\.[0-9]+(?:\.[0-9]+)?)['\"]?\s*$", m.group(1), re.MULTILINE)
    return vm.group(1) if vm else None


def _read_skill_version(skill_dir: Path) -> Optional[str]:
    manifest = skill_dir / "SKILL.md"
    if not manifest.is_file():
        return None
    return _extract_frontmatter_version(manifest.read_text(encoding="utf-8"))


def _update_version_status(current: Optional[str], latest: str) -> str:
    if current is None or _parse_semver(latest) > _parse_semver(current):
        return "update_available"
    if _parse_semver(latest) < _parse_semver(current):
        return "local_newer"
    return "up_to_date"


def check_skill_update(
    skip: bool = False,
    force: bool = False,
    source_url: str = SKILL_REMOTE_SKILL_MD_URL,
    timeout: float = 2.0,
    current_version: Optional[str] = SKILL_VERSION,
) -> Dict[str, Any]:
    """短超时且可跳过的版本探针，默认使用 24 小时缓存。"""
    skill_dir = Path(__file__).resolve().parent.parent
    is_git = (skill_dir / ".git").exists()
    update_cmd = (
        f'git -C "{skill_dir}" pull --ff-only'
        if is_git
        else f'python "{Path(__file__).resolve()}" self-update --apply'
    )
    base: Dict[str, Any] = {
        "current_version": current_version,
        "latest_version": None,
        "update_available": False,
        "status": "skipped" if skip else "unknown",
        "cached": False,
        "install_mode": "git" if is_git else "copy",
        "repo_url": SKILL_REPO_URL,
        "update_command": update_cmd,
    }
    if skip:
        return base

    cache_path = Path(tempfile.gettempdir()) / "bunnyscholar_gptzero_loop_update_cache.json"
    official_source = source_url == SKILL_REMOTE_SKILL_MD_URL
    if official_source and not force and cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8-sig"))
            ts = float(cached.get("checked_at", 0.0))
            if (time.time() - ts) < UPDATE_CACHE_TTL_SECONDS and cached.get("latest_version"):
                latest = str(cached["latest_version"])
                status = _update_version_status(current_version, latest)
                base.update({
                    "latest_version": latest,
                    "update_available": status == "update_available",
                    "status": status,
                    "cached": True,
                })
                return base
        except Exception:
            pass

    try:
        req = urllib.request.Request(source_url, headers={"User-Agent": f"bunnyscholar-gptzero-loop/{SKILL_VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read(8192).decode("utf-8", errors="replace")
        latest = _extract_frontmatter_version(content)
        if not latest:
            base["status"] = "unreachable"
            return base
        status = _update_version_status(current_version, latest)
        base.update({
            "latest_version": latest,
            "update_available": status == "update_available",
            "status": status,
            "cached": False,
        })
        if official_source:
            try:
                cache_path.write_text(
                    json.dumps({"checked_at": time.time(), "latest_version": latest}),
                    encoding="utf-8",
                )
            except OSError:
                pass
        return base
    except Exception:
        base["status"] = "unreachable"
        return base


def _download_skill_files(raw_base: str, timeout: float) -> Dict[str, bytes]:
    headers = {"User-Agent": f"bunnyscholar-gptzero-loop/{SKILL_VERSION}"}
    if raw_base == SKILL_REMOTE_RAW_BASE:
        with urllib.request.urlopen(urllib.request.Request(SKILL_REMOTE_ARCHIVE, headers=headers), timeout=timeout) as resp:
            archive_bytes = resp.read()
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            manifests = [name for name in archive.namelist() if name.count("/") == 1 and name.endswith("/SKILL.md")]
            if len(manifests) != 1:
                raise CliError("The update archive must contain one top-level skill folder.")
            root = manifests[0].split("/")[0]
            try:
                return {rel: archive.read(f"{root}/{rel}") for rel in SKILL_UPDATE_FILES}
            except KeyError as exc:
                raise CliError(f"The update archive is incomplete: {exc}") from exc

    downloaded: Dict[str, bytes] = {}
    for rel in SKILL_UPDATE_FILES:
        request = urllib.request.Request(f"{raw_base}/{rel}", headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            downloaded[rel] = resp.read()
    return downloaded


def self_update_skill(
    apply_changes: bool = False,
    skill_dir: Optional[Path] = None,
    raw_base: str = SKILL_REMOTE_RAW_BASE,
    timeout: float = 15.0,
    repair: bool = False,
) -> Dict[str, Any]:
    """从 Git 或同一次发布的仓库归档更新 Skill。"""
    target_dir = (skill_dir if skill_dir else Path(__file__).resolve().parent.parent).resolve()
    is_git = (target_dir / ".git").exists()
    raw_base = raw_base.rstrip("/")
    mode = "git_pull" if is_git else ("http_archive" if raw_base == SKILL_REMOTE_RAW_BASE else "http_raw_whitelist")
    local_version = _read_skill_version(target_dir)
    common = {"dry_run": not apply_changes, "skill_dir": str(target_dir), "mode": mode}

    if not apply_changes:
        probe = check_skill_update(
            force=True, source_url=f"{raw_base}/SKILL.md", timeout=timeout, current_version=local_version,
        )
        return {
            **common,
            "current_version": local_version,
            "latest_version": probe.get("latest_version"),
            "update_available": probe.get("update_available", False),
            "status": probe.get("status"),
            "note": "Re-run with --apply to perform the update.",
        }

    if is_git:
        def git_output(*args: str) -> str:
            proc = subprocess.run(
                ["git", "-C", str(target_dir), *args],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
            if proc.returncode != 0:
                raise CliError(f"git {' '.join(args)} failed: {(proc.stderr or proc.stdout).strip()}")
            return proc.stdout.strip()

        old_head = git_output("rev-parse", "HEAD")
        pull_output = git_output("pull", "--ff-only")
        updated = git_output("rev-parse", "HEAD") != old_head
        return {
            **common,
            "updated": updated,
            "status": "updated" if updated else "up_to_date",
            "previous_version": local_version,
            "latest_version": _read_skill_version(target_dir),
            "git_output": pull_output,
        }

    downloaded = _download_skill_files(raw_base, timeout)
    empty_files = [rel for rel, payload in downloaded.items() if not payload]
    if empty_files:
        raise CliError(f"The update contains empty files: {', '.join(empty_files)}.")
    new_ver = _extract_frontmatter_version(downloaded["SKILL.md"].decode("utf-8", errors="replace"))
    if not new_ver:
        raise CliError("The downloaded SKILL.md has no valid version.")

    status = _update_version_status(local_version, new_ver)
    result = {**common, "previous_version": local_version, "latest_version": new_ver}
    if status == "local_newer" or (status == "up_to_date" and not repair):
        return {**result, "updated": False, "status": status, "updated_files": []}

    # Write the version marker last, so an interrupted upgrade can be rerun.
    updated_files = [rel for rel in SKILL_UPDATE_FILES if rel != "SKILL.md"] + ["SKILL.md"]
    for rel in updated_files:
        atomic_write_bytes(target_dir / rel, downloaded[rel])
    return {**result, "updated": True, "status": "updated", "updated_files": updated_files}


def check_environment(
    env_paths: Optional[Sequence[str]] = None,
    ignore_process_env: bool = False,
    skip_update_check: bool = False,
    force_update_check: bool = False,
    update_source_url: str = SKILL_REMOTE_SKILL_MD_URL,
    skip_pdf_check: bool = False,
) -> Dict[str, Any]:
    """执行完整环境探测，返回绝对不含任何敏感 Key 明文的结构化报告。"""
    sources_checked: List[Dict[str, Any]] = []
    matched_source: Optional[str] = None
    api_found = False

    if not ignore_process_env:
        has_proc_key = bool(_usable_key(os.environ.get(API_KEY_NAME, "")))
        sources_checked.append({
            "source": "env:BUNNYSCHOLAR_API_KEY",
            "type": "process_env",
            "exists": "BUNNYSCHOLAR_API_KEY" in os.environ,
            "found": has_proc_key,
        })
        if has_proc_key:
            api_found = True
            matched_source = "env:BUNNYSCHOLAR_API_KEY"

    for env_file in _resolve_default_env_paths(env_paths):
        file_exists = env_file.is_file()
        file_has_key = bool(_read_dotenv_key(env_file)) if file_exists else False
        sources_checked.append({
            "source": str(env_file),
            "type": "dotenv_file",
            "exists": file_exists,
            "found": file_has_key,
        })
        if file_has_key and not api_found:
            api_found = True
            matched_source = str(env_file)

    if skip_pdf_check:
        word_com = {"available": False, "version": None, "error": None}
        libreoffice = {"available": False, "path": None, "version": None, "error": None}
    else:
        word_com = detect_word_com()
        libreoffice = detect_libreoffice()
    preferred_pdf_backend: Optional[str] = None
    if word_com["available"]:
        preferred_pdf_backend = "word_com"
    elif libreoffice["available"]:
        preferred_pdf_backend = "libreoffice"

    skill_info = detect_bunnyscholar_skill()
    update_info = check_skill_update(
        skip=skip_update_check,
        force=force_update_check,
        source_url=update_source_url,
    )

    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python_version": platform.python_version(),
        },
        "api_key": {
            "found": api_found,
            "matched_source": matched_source,
            "sources_checked": sources_checked,
        },
        "setup_instructions": {
            "required": not api_found,
            "bunnyscholar_api_prerequisite": {
                "installed": bool(skill_info.get("found")),
                "skill_url": BUNNYSCHOLAR_SKILL_URL,
                "prerequisite_prompt": f"参考官方接口说明 {BUNNYSCHOLAR_SKILL_URL}。如需离线复用，可安装 bunnyscholar-api。",
            },
            "console_url": CONSOLE_URL,
            "login_url": LOGIN_URL,
            "keys_url": KEYS_URL,
            "recharge_url": RECHARGE_URL,
            "setup_command": f'python "{Path(__file__).resolve()}" setup-key',
            "note": (
                "Run setup-key in a local terminal. A detected key is a local presence check, "
                "and has not been authenticated."
            ),
        },
        "pdf_backends": {
            "checked": not skip_pdf_check,
            "word_com": word_com,
            "libreoffice": libreoffice,
            "preferred": preferred_pdf_backend,
        },
        "skills": {
            "bunnyscholar_api": skill_info,
        },
        "update": update_info,
    }


def print_environment_summary(result: Dict[str, Any]) -> None:
    print(f"Python {result['platform']['python_version']} | Skill {SKILL_VERSION}")
    key_info = result["api_key"]
    setup = result["setup_instructions"]
    if key_info["found"]:
        print(f"BunnyScholar key: found in {key_info['matched_source']} (local check only)")
    else:
        print(f"BunnyScholar key: missing. If new or signed out, log in first at {setup['login_url']}")
        print(f"Open API Keys: {setup['keys_url']}")
        print(f"Then run in your own terminal: {setup['setup_command']}")

    if result["skills"]["bunnyscholar_api"]["found"]:
        print("BunnyScholar API reference: local skill found")
    else:
        print(f"BunnyScholar API reference: {BUNNYSCHOLAR_SKILL_URL}")

    pdf = result["pdf_backends"]
    if pdf["checked"]:
        print(f"PDF export: {pdf['preferred'] or 'unavailable (text and DOCX editing still work)'}")
    if result["update"]["update_available"]:
        print(f"Available skill update: {result['update']['latest_version']}")


# ==============================================================================
# 模块 2：OpenXML 原生解析、inspect 与 apply
# ==============================================================================

def read_docx_document_xml(docx_path: Path) -> Tuple[bytes, ET.Element]:
    """读取 .docx 压缩包内的 word/document.xml 并按源文档命名空间解析为 ElementTree。"""
    if not docx_path.is_file():
        raise CliError(f"DOCX file not found: {docx_path}")
    with zipfile.ZipFile(docx_path, "r") as zf:
        if "word/document.xml" not in zf.namelist():
            raise CliError(f"Invalid DOCX archive (missing word/document.xml): {docx_path}")
        raw_xml = zf.read("word/document.xml")
    register_ooxml_namespaces(raw_xml)
    root = ET.fromstring(raw_xml)
    return raw_xml, root


def write_docx_with_document_xml(src_docx: Path, dst_docx: Path, new_xml_bytes: bytes) -> None:
    """无损拷贝除 word/document.xml 外的所有 zip 条目并原子写回新 .docx。"""
    dst_docx.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp_docx_", suffix=".docx", dir=str(dst_docx.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with zipfile.ZipFile(src_docx, "r") as src_zip:
            with zipfile.ZipFile(tmp_path, "w") as dst_zip:
                for info in src_zip.infolist():
                    if info.filename == "word/document.xml":
                        # 必须显式按文件名写入，不可复用旧 ZipInfo，否则旧 CRC/长度会导致文件损坏
                        dst_zip.writestr("word/document.xml", new_xml_bytes, compress_type=zipfile.ZIP_DEFLATED)
                    else:
                        dst_zip.writestr(info, src_zip.read(info.filename))
        os.replace(tmp_path, dst_docx)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def iter_body_paragraphs(root: ET.Element) -> List[ET.Element]:
    """返回 <w:body> 直接子级的所有 <w:p> 元素，确保表格与页眉页脚不干扰段落索引。"""
    body = root.find(w_tag("body"))
    if body is None:
        raise CliError("Invalid word/document.xml: missing <w:body> element.")
    return body.findall(w_tag("p"))


def _iter_effective_runs_in_container(container: ET.Element) -> Iterable[ET.Element]:
    """递归遍历段落及透明包裹节点内的有效正文 <w:r>，跳过属性、删除修订、公式及域指令。"""
    skip_tags = {
        w_tag("pPr"),
        w_tag("rPr"),
        w_tag("del"),
        w_tag("moveFrom"),
        w_tag("pict"),
        w_tag("drawing"),
        f"{{{MATH_NS}}}oMath",
        f"{{{MATH_NS}}}oMathPara",
    }
    for child in list(container):
        if child.tag in skip_tags:
            continue
        if child.tag == w_tag("r"):
            # 跳过纯修订删除或域代码指令 run
            if child.find(w_tag("instrText")) is not None or child.find(w_tag("delText")) is not None:
                continue
            yield child
        else:
            yield from _iter_effective_runs_in_container(child)


def _extract_run_text_and_highlight(r_elem: ET.Element) -> Tuple[str, Optional[str]]:
    """提取单个有效 <w:r> 的可见纯文本及其 <w:highlight w:val='...'> 颜色。"""
    parts: List[str] = []
    for child in list(r_elem):
        if child.tag == w_tag("t"):
            parts.append(child.text or "")
        elif child.tag == w_tag("tab"):
            parts.append("\t")
        elif child.tag in (w_tag("br"), w_tag("cr")):
            parts.append("\n")
    highlight_val: Optional[str] = None
    rpr = r_elem.find(w_tag("rPr"))
    if rpr is not None:
        hl = rpr.find(w_tag("highlight"))
        if hl is not None:
            highlight_val = hl.get(w_tag("val")) or hl.get("val")
    return "".join(parts), highlight_val


def expand_citation_group(inner: str) -> Optional[List[int]]:
    """展开方括号引文内容（如 '1, 3-5' -> [1, 3, 4, 5]），自动跳过年份等非引文数值。"""
    expanded: List[int] = []
    for raw_token in inner.split(","):
        token = raw_token.strip()
        if not token:
            continue
        range_match = re.fullmatch(r"(\d+)\s*[-–—]\s*(\d+)", token)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if 1 <= start <= end <= 500 and (end - start) <= 50:
                expanded.extend(range(start, end + 1))
        else:
            num = int(token)
            if 1 <= num <= 500:
                expanded.append(num)
    return expanded if expanded else None


def extract_citations_from_text(text: str) -> Tuple[List[str], List[int]]:
    """从纯文本中提取所有方括号引文原始片段及展开后的整数序号序列。"""
    tokens: List[str] = []
    numbers: List[int] = []
    for match in CITATION_GROUP_RE.finditer(text):
        nums = expand_citation_group(match.group(1))
        if nums:
            tokens.append(match.group(0))
            numbers.extend(nums)
    return tokens, numbers


def detect_first_person_pronouns(text: str, ignore_quotes: bool = True) -> List[str]:
    """检测学术文本中的第一人称代词，自动过滤 URL、直接引语及 'Type I'/'I.' 等误判。"""
    cleaned = URL_RE.sub(" ", text)
    if ignore_quotes:
        cleaned = re.sub(r'"[^"\n]{1,400}"', " ", cleaned)
        cleaned = re.sub(r"\u201c[^\u201d\n]{1,400}\u201d", " ", cleaned)

    hits: List[str] = []
    for match in FIRST_PERSON_RE.finditer(cleaned):
        token = match.group(0)
        if token == "I":
            start, end = match.start(), match.end()
            before = cleaned[:start]
            after = cleaned[end:]
            if ROMAN_PRECEDING_WORDS_RE.search(before):
                continue
            if after.startswith(".") or after.startswith(")"):
                continue
        hits.append(token)
    return hits


def extract_paragraph_info(p_elem: ET.Element, para_index: int) -> Dict[str, Any]:
    """提取单个 <w:p> 的文本、样式标记、高亮分布、引文与第一人称信息。"""
    ppr = p_elem.find(w_tag("pPr"))
    style_id: Optional[str] = None
    if ppr is not None:
        pstyle = ppr.find(w_tag("pStyle"))
        if pstyle is not None:
            style_id = pstyle.get(w_tag("val")) or pstyle.get("val")

    is_heading = bool(style_id and re.match(r"^(heading|title|subtitle|toc|标题)", style_id, re.IGNORECASE))
    has_hyperlink = p_elem.find(f".//{w_tag('hyperlink')}") is not None
    has_field_codes = (
        p_elem.find(f".//{w_tag('fldChar')}") is not None
        or p_elem.find(f".//{w_tag('fldSimple')}") is not None
    )
    has_math = any(el.tag.endswith("}oMath") or el.tag.endswith("}oMathPara") for el in p_elem.iter())
    has_page_break_before = False
    if ppr is not None:
        pbb = ppr.find(w_tag("pageBreakBefore"))
        if pbb is not None:
            pbb_val = (pbb.get(w_tag("val")) or pbb.get("val") or "1").lower()
            if pbb_val not in ("0", "false", "off"):
                has_page_break_before = True
    if not has_page_break_before:
        for br in p_elem.findall(f".//{w_tag('br')}"):
            if (br.get(w_tag("type")) or br.get("type") or "").lower() == "page":
                has_page_break_before = True
                break

    run_records: List[Tuple[str, Optional[str]]] = []
    text_parts: List[str] = []
    for r_elem in _iter_effective_runs_in_container(p_elem):
        r_text, r_hl = _extract_run_text_and_highlight(r_elem)
        text_parts.append(r_text)
        run_records.append((r_text, r_hl))

    text = "".join(text_parts)
    non_ws_runs = [(t, hl) for t, hl in run_records if t.strip() != ""]
    eval_runs = non_ws_runs if non_ws_runs else run_records

    highlight_colors: List[str] = []
    for _, hl in eval_runs:
        if hl and hl not in highlight_colors:
            highlight_colors.append(hl)

    has_yellow_highlight = any(hl == "yellow" for _, hl in eval_runs)
    all_runs_yellow = bool(eval_runs) and all(hl == "yellow" for _, hl in eval_runs)
    if all_runs_yellow:
        highlight_coverage = "full"
    elif has_yellow_highlight:
        highlight_coverage = "partial"
    else:
        highlight_coverage = "none"

    citation_tokens, citations = extract_citations_from_text(text)
    first_person = detect_first_person_pronouns(text)
    billing = compute_billable_chars(text)

    return {
        "para_index": para_index,
        "text": text,
        "word_count": len(re.findall(r"\S+", text)),
        "char_count": len(text),
        "billable_chars": billing["billable_chars"],
        "style_id": style_id,
        "is_heading": is_heading,
        "is_empty": text.strip() == "",
        "has_hyperlink": has_hyperlink,
        "has_field_codes": has_field_codes,
        "has_math": has_math,
        "has_page_break_before": has_page_break_before,
        "highlight_colors": highlight_colors,
        "has_yellow_highlight": has_yellow_highlight,
        "all_runs_yellow": all_runs_yellow,
        "highlight_coverage": highlight_coverage,
        "citation_tokens": citation_tokens,
        "citations": citations,
        "first_person_pronouns": first_person,
    }


def inspect_docx(docx_path: Path) -> Dict[str, Any]:
    """解析 .docx 全文段落并返回统计摘要、高亮状态、引文单调性检查及第一人称命中情况。"""
    _, root = read_docx_document_xml(docx_path)
    body = root.find(w_tag("body"))
    body_paras = iter_body_paragraphs(root)
    table_count = len(body.findall(w_tag("tbl"))) if body is not None else 0

    paragraphs: List[Dict[str, Any]] = []
    references_start_para: Optional[int] = None

    for idx, p_elem in enumerate(body_paras, start=1):
        info = extract_paragraph_info(p_elem, idx)
        paragraphs.append(info)
        if references_start_para is None and REFERENCES_HEADING_RE.match(info["text"].strip()):
            references_start_para = idx

    # 启发式标注各段落结构角色（front_matter / body / references_heading / reference_entry / heading / empty）
    seen_body_long = False
    for info in paragraphs:
        p_idx = info["para_index"]
        if info["is_empty"]:
            info["section_role"] = "empty"
        elif references_start_para is not None and p_idx == references_start_para:
            info["section_role"] = "references_heading"
        elif references_start_para is not None and p_idx > references_start_para:
            info["section_role"] = "reference_entry"
        elif info["is_heading"]:
            info["section_role"] = "heading"
        elif not seen_body_long and info["word_count"] < 35:
            info["section_role"] = "front_matter"
        else:
            seen_body_long = True
            info["section_role"] = "body"

    # 在参考文献章节之前校验正文中各引文编号首次出现的单调递增性
    scan_limit = (references_start_para - 1) if references_start_para is not None else len(paragraphs)
    seen: Set[int] = set()
    max_seen = 0
    first_appearance_order: List[int] = []
    anomalies: List[Dict[str, Any]] = []

    for info in paragraphs[:scan_limit]:
        p_idx = info["para_index"]
        for num in info["citations"]:
            if num not in seen:
                seen.add(num)
                first_appearance_order.append(num)
                if num < max_seen:
                    anomalies.append({
                        "type": "out_of_order",
                        "citation": num,
                        "para_index": p_idx,
                        "max_seen_before": max_seen,
                    })
                elif num > max_seen + 1:
                    anomalies.append({
                        "type": "skipped_number",
                        "citation": num,
                        "para_index": p_idx,
                        "expected_next": max_seen + 1,
                    })
                max_seen = max(max_seen, num)

    citations_non_decreasing = not any(a["type"] == "out_of_order" for a in anomalies)
    citations_monotonic = len(anomalies) == 0

    return {
        "docx": str(docx_path),
        "summary": {
            "total_paragraphs": len(paragraphs),
            "non_empty_paragraphs": sum(1 for p in paragraphs if not p["is_empty"]),
            "total_words": sum(p["word_count"] for p in paragraphs),
            "table_count": table_count,
            "yellow_highlighted_paras": [p["para_index"] for p in paragraphs if p["has_yellow_highlight"]],
            "body_para_indices": [p["para_index"] for p in paragraphs if p.get("section_role") == "body"],
            "page_break_paras": [p["para_index"] for p in paragraphs if p.get("has_page_break_before")],
            "references_start_para": references_start_para,
            "citations_monotonic": citations_monotonic,
            "citations_non_decreasing": citations_non_decreasing,
            "citation_sequence": first_appearance_order,
            "all_citations_seen": sorted(seen),
            "citation_anomalies": anomalies,
            "first_person_paras": [p["para_index"] for p in paragraphs if p["first_person_pronouns"]],
        },
        "paragraphs": paragraphs,
    }


def _strip_highlight_from_rpr(rpr: Optional[ET.Element]) -> Optional[ET.Element]:
    """深拷贝 <w:rPr> 并移除旧的 <w:highlight> 子节点。"""
    if rpr is None:
        return None
    cloned = copy.deepcopy(rpr)
    for old_hl in list(cloned.findall(w_tag("highlight"))):
        cloned.remove(old_hl)
    return cloned


def _strip_hyperlink_style_from_rpr(rpr: Optional[ET.Element]) -> Optional[ET.Element]:
    """从超链接 run 的样式副本中剥离超链接专属蓝字/下划线样式，仅保留字体字号等基础格式。"""
    cleaned = _strip_highlight_from_rpr(rpr)
    if cleaned is None:
        return None
    for child in list(cleaned):
        if child.tag == w_tag("rStyle"):
            val = child.get(w_tag("val")) or child.get("val") or ""
            if val.lower() == "hyperlink":
                cleaned.remove(child)
        elif child.tag in (w_tag("color"), w_tag("u")):
            cleaned.remove(child)
    return cleaned if len(cleaned) > 0 else None


def set_run_highlight(r_elem: ET.Element, color: Optional[str]) -> None:
    """设置或清除 <w:r> 的荧光笔高亮，并确保 <w:rPr> 始终处于 <w:r> 的第 0 个子节点位置。"""
    rpr = r_elem.find(w_tag("rPr"))
    if rpr is None:
        if not color:
            return
        rpr = ET.Element(w_tag("rPr"))
        # OOXML Schema 强制要求 <w:rPr> 位于 <w:t> 之前
        r_elem.insert(0, rpr)
    else:
        for old_hl in list(rpr.findall(w_tag("highlight"))):
            rpr.remove(old_hl)
        # 若原本位置不在首位则纠正
        if list(r_elem).index(rpr) != 0:
            r_elem.remove(rpr)
            r_elem.insert(0, rpr)

    if color:
        hl = ET.Element(w_tag("highlight"))
        hl.set(w_tag("val"), color)
        rpr.append(hl)
    elif len(rpr) == 0:
        r_elem.remove(rpr)


def _build_run_element(
    text: str,
    rpr_template: Optional[ET.Element],
    highlight_color: Optional[str],
) -> ET.Element:
    """构建标准 <w:r> 节点，自动处理换行、制表符、xml:space='preserve' 与高亮属性。"""
    r_elem = ET.Element(w_tag("r"))
    if rpr_template is not None:
        r_elem.append(_strip_highlight_from_rpr(rpr_template))

    # 统一将 \r\n、\r、\n 映射为单个 <w:br/>、\t 映射为 <w:tab/>，避免裸 \r 触发 XML 1.0 规范化导致双换行
    parts = re.split(r"(\r\n|\r|\n|\t)", text)
    if not parts or parts == [""]:
        t_elem = ET.SubElement(r_elem, w_tag("t"))
        t_elem.set(xml_tag("space"), "preserve")
        t_elem.text = ""
    else:
        for part in parts:
            if part in ("\r\n", "\r", "\n"):
                ET.SubElement(r_elem, w_tag("br"))
            elif part == "\t":
                ET.SubElement(r_elem, w_tag("tab"))
            elif part != "":
                t_elem = ET.SubElement(r_elem, w_tag("t"))
                t_elem.set(xml_tag("space"), "preserve")
                t_elem.text = part

    if highlight_color:
        set_run_highlight(r_elem, highlight_color)
    return r_elem


def _extract_base_rpr(p_elem: ET.Element) -> Optional[ET.Element]:
    """提取段落的首选正文样式模板 <w:rPr>：优先普通 <w:r>，否则从 <w:hyperlink> 中回退提取。"""
    for child in list(p_elem):
        if child.tag == w_tag("r") and (
            child.find(w_tag("t")) is not None
            or child.find(w_tag("tab")) is not None
            or child.find(w_tag("br")) is not None
        ):
            rpr = child.find(w_tag("rPr"))
            if rpr is not None:
                return _strip_highlight_from_rpr(rpr)
            return None

    for hl in p_elem.findall(f".//{w_tag('hyperlink')}"):
        for r_elem in hl.findall(w_tag("r")):
            rpr = r_elem.find(w_tag("rPr"))
            if rpr is not None:
                return _strip_hyperlink_style_from_rpr(rpr)
    return None


def _compute_highlight_ranges(text: str, substrings: Sequence[str]) -> List[Tuple[int, int]]:
    """计算目标子串在 text 中的非重叠高亮区间（按出现位置合并）。"""
    intervals: List[Tuple[int, int]] = []
    for sub in substrings:
        if not sub:
            continue
        start = 0
        while True:
            idx = text.find(sub, start)
            if idx == -1:
                break
            intervals.append((idx, idx + len(sub)))
            start = idx + len(sub)
    if not intervals:
        return []
    intervals.sort()
    merged: List[Tuple[int, int]] = [intervals[0]]
    for s, e in intervals[1:]:
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _append_runs_for_slice(
    container: ET.Element,
    slice_text: str,
    slice_offset: int,
    rpr_template: Optional[ET.Element],
    default_highlight: Optional[str],
    hl_ranges: Sequence[Tuple[int, int]],
) -> None:
    """将文本切片按局部高亮区间拆分为 <w:r> 节点追加到 container。"""
    if not hl_ranges or default_highlight == "yellow":
        container.append(_build_run_element(slice_text, rpr_template, default_highlight))
        return
    slice_end = slice_offset + len(slice_text)
    pos = slice_offset
    for rs, re_pos in hl_ranges:
        if re_pos <= pos or rs >= slice_end:
            continue
        if rs > pos:
            container.append(_build_run_element(slice_text[pos - slice_offset:rs - slice_offset], rpr_template, None))
        hl_s = max(pos, rs)
        hl_e = min(slice_end, re_pos)
        container.append(_build_run_element(slice_text[hl_s - slice_offset:hl_e - slice_offset], rpr_template, "yellow"))
        pos = hl_e
    if pos < slice_end:
        container.append(_build_run_element(slice_text[pos - slice_offset:], rpr_template, None))


def _replace_paragraph_preserving_structure(
    p_elem: ET.Element,
    para_index: int,
    new_text: str,
    highlight_yellow: bool,
    warnings: List[str],
    highlight_substrings: Optional[Sequence[str]] = None,
) -> None:
    """无损替换单段正文，完整保留 <w:pPr>、书签/批注锚点与 <w:hyperlink r:id='...'> 关系节点。"""
    if (
        p_elem.find(f".//{w_tag('fldChar')}") is not None
        or p_elem.find(f".//{w_tag('fldSimple')}") is not None
        or any(el.tag.endswith("}oMath") or el.tag.endswith("}oMathPara") for el in p_elem.iter())
    ):
        raise CliError(
            f"Paragraph {para_index} contains Word field codes or math equations (<w:fldChar>/<m:oMath>); "
            "refusing to overwrite to prevent structure corruption."
        )

    ppr = p_elem.find(w_tag("pPr"))
    ppr_copy = copy.deepcopy(ppr) if ppr is not None else None

    start_anchors: List[ET.Element] = []
    end_anchors: List[ET.Element] = []
    hyperlink_records: List[Dict[str, Any]] = []

    for child in list(p_elem):
        if child.tag in (w_tag("bookmarkStart"), w_tag("commentRangeStart")):
            start_anchors.append(copy.deepcopy(child))
        elif child.tag in (w_tag("bookmarkEnd"), w_tag("commentRangeEnd")):
            end_anchors.append(copy.deepcopy(child))
        elif child.tag == w_tag("hyperlink"):
            hl_text_parts: List[str] = []
            hl_rpr: Optional[ET.Element] = None
            for hr in _iter_effective_runs_in_container(child):
                rt, _ = _extract_run_text_and_highlight(hr)
                hl_text_parts.append(rt)
                if hl_rpr is None:
                    hrpr = hr.find(w_tag("rPr"))
                    if hrpr is not None:
                        hl_rpr = _strip_highlight_from_rpr(hrpr)
            hyperlink_records.append({
                "attrib": dict(child.attrib),
                "old_text": "".join(hl_text_parts),
                "rpr": hl_rpr,
                "rid": child.get(r_tag("id")) or child.get("id") or child.get(w_tag("anchor")) or "unknown",
            })

    base_rpr = _extract_base_rpr(p_elem)
    hl_color = "yellow" if highlight_yellow else None
    hl_ranges: List[Tuple[int, int]] = []
    if not highlight_yellow and highlight_substrings:
        hl_ranges = _compute_highlight_ranges(new_text, highlight_substrings)
        if not hl_ranges:
            warn_msg = f"Paragraph {para_index}: none of highlight_substrings matched in target text."
            warnings.append(warn_msg)
            log_stderr(f"Warning: {warn_msg}")

    # 清空原段落子节点并按 OOXML 标准顺序重建
    for child in list(p_elem):
        p_elem.remove(child)
    if ppr_copy is not None:
        p_elem.append(ppr_copy)
    for anc in start_anchors:
        p_elem.append(anc)

    if not hyperlink_records:
        _append_runs_for_slice(p_elem, new_text, 0, base_rpr, hl_color, hl_ranges)
    else:
        cursor = 0
        unmatched_links: List[Dict[str, Any]] = []
        lower_new = new_text.lower()

        for rec in hyperlink_records:
            anchor_text = rec["old_text"]
            found_idx = -1
            if anchor_text.strip():
                found_idx = new_text.find(anchor_text, cursor)
                if found_idx == -1:
                    found_idx = lower_new.find(anchor_text.lower(), cursor)

            if found_idx != -1:
                if found_idx > cursor:
                    _append_runs_for_slice(p_elem, new_text[cursor:found_idx], cursor, base_rpr, hl_color, hl_ranges)
                matched_slice = new_text[found_idx:found_idx + len(anchor_text)]
                hl_elem = ET.Element(w_tag("hyperlink"), rec["attrib"])
                link_rpr = rec["rpr"] if rec["rpr"] is not None else base_rpr
                _append_runs_for_slice(hl_elem, matched_slice, found_idx, link_rpr, hl_color, hl_ranges)
                p_elem.append(hl_elem)
                cursor = found_idx + len(anchor_text)
            else:
                unmatched_links.append(rec)

        if cursor < len(new_text):
            _append_runs_for_slice(p_elem, new_text[cursor:], cursor, base_rpr, hl_color, hl_ranges)

        # 兜底策略：若新文本未命中原超链接锚文本，保留零文本超链接节点以防 rId 变成孤儿关系，并显式告警
        for rec in unmatched_links:
            hl_elem = ET.Element(w_tag("hyperlink"), rec["attrib"])
            link_rpr = rec["rpr"] if rec["rpr"] is not None else base_rpr
            hl_elem.append(_build_run_element("", link_rpr, None))
            p_elem.append(hl_elem)
            warn_msg = (
                f"Paragraph {para_index}: hyperlink ({rec['rid']}) anchor text '{rec['old_text']}' "
                "was not matched in humanized text; preserved empty hyperlink node at paragraph end to keep .rels integrity."
            )
            warnings.append(warn_msg)
            log_stderr(f"Warning: {warn_msg}")

    for anc in end_anchors:
        p_elem.append(anc)


def apply_humanized_to_docx(
    docx_path: Path,
    humanized_items: List[Dict[str, Any]],
    output_docx: Path,
    highlight_paras: Set[int],
    clear_other_highlights: bool = False,
) -> Dict[str, Any]:
    """将 humanized JSON 中的文本一字不改写入指定段落，同时执行高亮涂黄与结构保护。"""
    raw_xml, root = read_docx_document_xml(docx_path)
    root_namespaces = register_ooxml_namespaces(raw_xml)
    body_paras = iter_body_paragraphs(root)
    total_paras = len(body_paras)

    humanized_map: Dict[int, str] = {}
    highlight_override_map: Dict[int, bool] = {}
    highlight_substrings_map: Dict[int, List[str]] = {}
    for item in humanized_items:
        if not isinstance(item, dict):
            raise CliError("Each humanized entry must be a JSON object.")
        para_idx = item.get("para_index")
        if not isinstance(para_idx, int) or isinstance(para_idx, bool) or not (1 <= para_idx <= total_paras):
            raise CliError(f"Invalid para_index {para_idx!r}; valid range is 1..{total_paras}.")
        if "humanized_text" in item and item["humanized_text"] is not None:
            new_text = item["humanized_text"]
        elif "text" in item and item["text"] is not None:
            new_text = item["text"]
        else:
            raise CliError(f"Missing 'humanized_text' or 'text' for para_index={para_idx}.")
        if not isinstance(new_text, str):
            raise CliError(f"Text for para_index={para_idx} must be a string.")
        humanized_map[para_idx] = new_text
        if isinstance(item.get("highlight"), bool):
            highlight_override_map[para_idx] = item["highlight"]
        if isinstance(item.get("highlight_substrings"), list):
            subs = [str(s) for s in item["highlight_substrings"] if isinstance(s, str) and s]
            if subs:
                highlight_substrings_map[para_idx] = subs

    for h_idx in sorted(highlight_paras):
        if not (1 <= h_idx <= total_paras):
            raise CliError(f"Invalid --highlight-paras index {h_idx}; valid range is 1..{total_paras}.")

    warnings: List[str] = []
    replaced_paras: List[int] = []
    highlighted_applied: List[int] = []
    cleared_paras: List[int] = []

    for idx, p_elem in enumerate(body_paras, start=1):
        want_yellow = highlight_override_map.get(idx, idx in highlight_paras)
        sub_list = highlight_substrings_map.get(idx)
        if idx in humanized_map:
            _replace_paragraph_preserving_structure(
                p_elem=p_elem,
                para_index=idx,
                new_text=humanized_map[idx],
                highlight_yellow=want_yellow,
                warnings=warnings,
                highlight_substrings=sub_list,
            )
            replaced_paras.append(idx)
            if want_yellow or sub_list:
                highlighted_applied.append(idx)
        elif want_yellow:
            for r_elem in _iter_effective_runs_in_container(p_elem):
                set_run_highlight(r_elem, "yellow")
            highlighted_applied.append(idx)
        elif clear_other_highlights:
            changed = False
            for r_elem in _iter_effective_runs_in_container(p_elem):
                rpr = r_elem.find(w_tag("rPr"))
                if rpr is not None and rpr.find(w_tag("highlight")) is not None:
                    set_run_highlight(r_elem, None)
                    changed = True
            if changed:
                cleared_paras.append(idx)

    new_xml_bytes = serialize_document_xml(root, root_namespaces)
    write_docx_with_document_xml(docx_path, output_docx, new_xml_bytes)

    return {
        "source_docx": str(docx_path),
        "output_docx": str(output_docx),
        "replaced_paras": replaced_paras,
        "highlighted_paras": sorted(highlighted_applied),
        "cleared_highlight_paras": cleared_paras,
        "warnings": warnings,
    }


def _load_humanized_items(json_path: Path) -> List[Dict[str, Any]]:
    """读取并兼容解析 humanize 输出或待应用段落 JSON（支持 UTF-8 BOM）。"""
    if not json_path.is_file():
        raise CliError(f"JSON input file not found: {json_path}")
    with json_path.open("r", encoding="utf-8-sig") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("paragraphs"), list):
            return payload["paragraphs"]
        if isinstance(payload.get("results"), list):
            return payload["results"]
    raise CliError("JSON must be a list of paragraph objects or contain 'paragraphs'/'results' list.")


def _parse_int_csv(raw: Optional[str]) -> Set[int]:
    """解析逗号分隔的正整数列表（如 '1,2,3'）。"""
    if not raw:
        return set()
    result: Set[int] = set()
    for part in raw.split(","):
        s = part.strip()
        if not s:
            continue
        if not s.isdigit() or int(s) <= 0:
            raise CliError(f"Invalid positive paragraph index: '{s}'")
        result.add(int(s))
    return result


# ==============================================================================
# 模块 3：snapshot 与 rollback 版本保护
# ==============================================================================

def _parse_pages_arg(raw: Optional[str]) -> Optional[Any]:
    """解析 --pages 参数，兼容 JSON 字符串或 '1=98,2=87' / '1:98,2:87' 键值对。"""
    if raw is None or not raw.strip():
        return None
    s = raw.strip()
    if s.startswith("{") or s.startswith("["):
        return json.loads(s)
    parsed: Dict[str, float] = {}
    for item in s.split(","):
        token = item.strip()
        if not token:
            continue
        if "=" in token:
            k, v = token.split("=", 1)
        elif ":" in token:
            k, v = token.split(":", 1)
        else:
            raise CliError(f"Invalid --pages token '{token}'; expected JSON or key=value pairs.")
        parsed[k.strip()] = float(v.strip())
    return parsed


def _load_snapshot_history(snap_dir: Path, docx_name: str) -> Dict[str, Any]:
    """读取快照目录的 history.json；若不存在则初始化空历史结构（支持 UTF-8 BOM）。"""
    history_path = snap_dir / "history.json"
    if not history_path.is_file():
        return {"docx_name": docx_name, "next_version": 1, "snapshots": []}
    with history_path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("snapshots"), list):
        raise CliError(f"Corrupted snapshot history file: {history_path}")
    return data


def _resolve_snapshot_dir(docx_path: Path, snapshot_dir: Optional[Path]) -> Path:
    if snapshot_dir is not None:
        return snapshot_dir

    root = docx_path.parent / ".snapshots"
    per_document = root / docx_path.name
    if per_document.is_dir() or not (root / "history.json").is_file():
        return per_document

    # Keep reading an existing default history for the document that owns it.
    history = _load_snapshot_history(root, docx_path.name)
    owner = history.get("docx_name")
    if isinstance(owner, str) and os.path.normcase(owner) == os.path.normcase(docx_path.name):
        return root
    return per_document


def create_snapshot(
    docx_path: Path,
    snapshot_dir: Optional[Path] = None,
    overall_human: Optional[float] = None,
    mixed: Optional[float] = None,
    ai: Optional[float] = None,
    pages: Optional[Any] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """备份当前 .docx 并原子更新该文档的 history.json。"""
    if not docx_path.is_file():
        raise CliError(f"DOCX file not found: {docx_path}")
    snap_dir = _resolve_snapshot_dir(docx_path, snapshot_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)

    history = _load_snapshot_history(snap_dir, docx_path.name)
    existing_max = max((int(s.get("version", 0)) for s in history["snapshots"]), default=0)
    version = max(int(history.get("next_version", 1)), existing_max + 1)

    now_utc = datetime.now(timezone.utc)
    iso_ts = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    file_ts = now_utc.strftime("%Y%m%d_%H%M%S")
    snap_filename = f"v{version}_{file_ts}.docx"
    snap_file = snap_dir / snap_filename

    sha256_val = compute_sha256(docx_path)
    atomic_copy_file(docx_path, snap_file)

    entry: Dict[str, Any] = {
        "version": version,
        "timestamp": iso_ts,
        "file": snap_filename,
        "sha256": sha256_val,
        "overall_human": overall_human,
        "mixed": mixed,
        "ai": ai,
        "pages": pages,
        "note": note or "",
    }
    history["docx_name"] = docx_path.name
    history["next_version"] = version + 1
    history["snapshots"].append(entry)
    atomic_write_json(snap_dir / "history.json", history)

    return {
        "action": "snapshot_created",
        "docx": str(docx_path),
        "snapshot_dir": str(snap_dir),
        "snapshot_path": str(snap_file),
        "entry": entry,
    }


def _select_best_snapshot(snapshots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """按 (overall_human, version) 降序选择历史得分最高的快照。"""
    scored = [s for s in snapshots if s.get("overall_human") is not None]
    if not scored:
        return None
    return max(scored, key=lambda s: (float(s["overall_human"]), int(s["version"])))


def rollback_snapshot(
    docx_path: Path,
    snapshot_dir: Optional[Path] = None,
    list_only: bool = False,
    version: Optional[int] = None,
    best: bool = False,
) -> Dict[str, Any]:
    """查看快照对比列表或将指定/最高分快照安全原子回滚至目标 .docx。"""
    snap_dir = _resolve_snapshot_dir(docx_path, snapshot_dir)
    history = _load_snapshot_history(snap_dir, docx_path.name)
    snapshots = history["snapshots"]
    best_entry = _select_best_snapshot(snapshots)

    if list_only:
        return {
            "action": "list",
            "docx": str(docx_path),
            "snapshot_dir": str(snap_dir),
            "total_snapshots": len(snapshots),
            "best_version": best_entry["version"] if best_entry else None,
            "snapshots": snapshots,
        }

    if not snapshots:
        raise CliError(f"No snapshots found in {snap_dir}")

    target_entry: Optional[Dict[str, Any]] = None
    if version is not None:
        for item in snapshots:
            if int(item.get("version", -1)) == version:
                target_entry = item
                break
        if target_entry is None:
            raise CliError(f"Snapshot version v{version} not found in {snap_dir / 'history.json'}.")
    else:
        # 未指定 --version 且非 --list 时默认启用 --best
        if best_entry is None:
            raise CliError(
                "No snapshot has an 'overall_human' score for --best selection; "
                "please specify --version <N> explicitly."
            )
        target_entry = best_entry

    snap_file = snap_dir / str(target_entry["file"])
    if not snap_file.is_file():
        raise CliError(f"Snapshot binary file missing: {snap_file}")

    actual_sha = compute_sha256(snap_file)
    expected_sha = target_entry.get("sha256")
    if expected_sha and actual_sha != expected_sha:
        raise CliError(
            f"Snapshot integrity check failed for {snap_file}: "
            f"expected sha256 {expected_sha}, got {actual_sha}."
        )

    pre_rollback_backup: Optional[str] = None
    if docx_path.is_file():
        backup_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_path = snap_dir / f"pre_rollback_{backup_ts}.docx"
        suffix_idx = 1
        while backup_path.exists():
            backup_path = snap_dir / f"pre_rollback_{backup_ts}_{suffix_idx}.docx"
            suffix_idx += 1
        atomic_copy_file(docx_path, backup_path)
        pre_rollback_backup = str(backup_path)

    atomic_copy_file(snap_file, docx_path)

    return {
        "action": "rolled_back",
        "mode": "version" if version is not None else "best",
        "docx": str(docx_path),
        "restored_version": target_entry["version"],
        "restored_from": str(snap_file),
        "sha256": actual_sha,
        "overall_human": target_entry.get("overall_human"),
        "pre_rollback_backup": pre_rollback_backup,
    }


# ==============================================================================
# 模块 4：humanize 跨进程限流 + 重试 + 质量门禁
# ==============================================================================

class CrossProcessFileLock:
    """跨平台（Windows msvcrt / POSIX fcntl）排他文件锁上下文管理器。"""

    def __init__(self, lock_path: Path, timeout: float = 60.0) -> None:
        self.lock_path = lock_path
        self.timeout = timeout
        self._fp: Optional[Any] = None

    def __enter__(self) -> "CrossProcessFileLock":
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = self.lock_path.open("a+b")
        if os.name == "nt":
            # Windows msvcrt.locking 需要锁定范围内至少存在 1 字节
            if os.fstat(self._fp.fileno()).st_size == 0:
                self._fp.write(b"\x00")
                self._fp.flush()
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    self._fp.seek(0)
                    msvcrt.locking(self._fp.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        self._fp.close()
                        self._fp = None
                        raise TimeoutError(f"Timed out acquiring Windows file lock: {self.lock_path}")
                    time.sleep(0.005)
        else:
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    fcntl.flock(self._fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        self._fp.close()
                        self._fp = None
                        raise TimeoutError(f"Timed out acquiring POSIX file lock: {self.lock_path}")
                    time.sleep(0.005)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._fp is None:
            return
        try:
            if os.name == "nt":
                self._fp.seek(0)
                msvcrt.locking(self._fp.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._fp.fileno(), fcntl.LOCK_UN)
        finally:
            self._fp.close()
            self._fp = None


def _default_lock_file_path() -> Path:
    """获取默认限流锁路径，~/.cache 不可写时自动回退至系统临时目录。"""
    candidate = Path.home() / ".cache" / "bunnyscholar-gptzero-loop" / "rate_limit.lock"
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        return candidate
    except OSError:
        return Path(tempfile.gettempdir()) / "bunnyscholar_rate_limit.lock"


def acquire_rate_limit_slot(lock_path: Path, rate_limit: float) -> float:
    """在跨进程文件锁保护下使用 time.monotonic() 强制控制全局发包频率 <= rate_limit。"""
    if rate_limit <= 0:
        raise CliError(f"--rate-limit must be > 0, got {rate_limit}")
    interval = 1.0 / rate_limit
    state_path = Path(f"{lock_path}.state")

    with CrossProcessFileLock(lock_path):
        last_mono: Optional[float] = None
        last_wall: Optional[float] = None
        if state_path.is_file():
            try:
                with state_path.open("r", encoding="utf-8") as sf:
                    st = json.load(sf)
                    if isinstance(st, dict):
                        lm = st.get("last_monotonic")
                        lw = st.get("last_wall")
                        last_mono = float(lm) if lm is not None else None
                        last_wall = float(lw) if lw is not None else None
            except Exception:
                last_mono = None
                last_wall = None

        now_mono = time.monotonic()
        now_wall = time.time()
        elapsed = interval

        if last_mono is not None:
            mono_elapsed = now_mono - last_mono
            wall_elapsed = (now_wall - last_wall) if last_wall is not None else None
            # 若 wall clock 与 monotonic 漂移小于 60s 且非负，判定为同一系统运行周期内
            if mono_elapsed >= 0 and (wall_elapsed is None or abs(wall_elapsed - mono_elapsed) < 60.0):
                elapsed = mono_elapsed
            elif wall_elapsed is not None and 0.0 <= wall_elapsed < interval:
                # 跨系统重启后 monotonic 会归零，此时仅对刚发生过的短间隔做保守回退等待
                elapsed = wall_elapsed

        sleep_sec = 0.0
        if elapsed < interval:
            sleep_sec = interval - elapsed
            # 持锁睡眠可彻底防止多个并发进程同时穿透同一时间窗
            time.sleep(sleep_sec)

        fire_mono = time.monotonic()
        fire_wall = time.time()
        state_payload = {
            "last_monotonic": fire_mono,
            "last_wall": fire_wall,
            "pid": os.getpid(),
        }
        with state_path.open("w", encoding="utf-8") as sf:
            json.dump(state_payload, sf)
            sf.flush()
            os.fsync(sf.fileno())
        return sleep_sec


def check_quality_gate(
    source_text: str,
    returned_text: str,
    personal_terms: Optional[Sequence[str]] = None,
    allow_first_person: bool = False,
    max_word_len: int = 16,
) -> List[str]:
    """执行 3 项质量门禁校验：第一人称代词、超长乱码拼接词、丢失文内引文 [n]。"""
    issues: List[str] = []

    # 1. 第一人称代词检查（可通过 --allow-first-person 关闭）
    if not allow_first_person:
        fp_hits = detect_first_person_pronouns(returned_text)
        if fp_hits:
            unique_fp = list(dict.fromkeys(fp_hits))
            issues.append(f"first_person_pronoun:{','.join(unique_fp)}")

    # 2. 检查 >max_word_len 字母纯英文连续拼接乱码词（剔除 URL 与用户白名单术语）
    cleaned = URL_RE.sub(" ", returned_text)
    if personal_terms:
        for term in personal_terms:
            t = term.strip()
            if len(t) > max_word_len:
                prefix = r"\b" if (t[0].isalnum() or t[0] == "_") else r"(?<!\w)"
                suffix = r"\b" if (t[-1].isalnum() or t[-1] == "_") else r"(?!\w)"
                cleaned = re.sub(f"{prefix}{re.escape(t)}{suffix}", " ", cleaned, flags=re.IGNORECASE)
    long_word_re = re.compile(rf"\b[A-Za-z]{{{max(1, max_word_len) + 1},}}\b")
    long_words = long_word_re.findall(cleaned)
    if long_words:
        unique_long = list(dict.fromkeys(long_words))
        issues.append(f"garbled_long_word:{','.join(unique_long)}")

    # 3. 校验原段落中所有 [n] 引文序号在返回文本中完整保留
    _, src_nums = extract_citations_from_text(source_text)
    _, ret_nums = extract_citations_from_text(returned_text)
    missing_nums = sorted(set(src_nums) - set(ret_nums))
    if missing_nums:
        issues.append(f"missing_citations:{missing_nums}")

    return issues


def call_humanizer_api(
    text: str,
    api_key: str,
    api_url: str,
    dual_stage: bool,
    rate_limit: float,
    lock_path: Path,
    timeout: float,
    http_retries: int,
    personal_terms: Optional[List[str]] = None,
    language: str = "en",
    platform_name: str = "gptzero",
) -> Dict[str, Any]:
    """带跨进程限流与 429/5xx 指数退避重试的 BunnyScholar 拟人改写 API 调用函数。"""
    payload_obj: Dict[str, Any] = {
        "text": text,
        "language": language,
        "platform": platform_name,
        "needPlagiarismReduction": bool(dual_stage),
    }
    if personal_terms:
        payload_obj["personalTerms"] = personal_terms

    body_bytes = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    attempts = max(1, http_retries)
    for attempt in range(attempts):
        waited = acquire_rate_limit_slot(lock_path, rate_limit)
        if waited > 0.001:
            log_stderr(f"Rate limiter throttled request for {waited:.3f}s (limit={rate_limit} req/s).")

        req = urllib.request.Request(api_url, data=body_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_resp = resp.read().decode("utf-8", errors="replace")
                parsed = json.loads(raw_resp)
                data_obj = parsed.get("data") if isinstance(parsed, dict) else None
                ret_text = data_obj.get("text") if isinstance(data_obj, dict) else None
                if not isinstance(ret_text, str) or ret_text == "":
                    raise CliError(f"Unexpected API response from {api_url}: missing non-empty data.text.")
                return parsed
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")[:1000]
            if exc.code == 429:
                if attempt + 1 >= attempts:
                    raise RateLimitError(
                        f"HTTP 429 Too Many Requests from {api_url} (rate_limit={rate_limit} req/s) "
                        f"after {attempts} attempts. Response: {err_body}"
                    ) from exc
                retry_after_raw = exc.headers.get("Retry-After") if exc.headers else None
                backoff = float(2 ** attempt)
                if retry_after_raw:
                    try:
                        backoff = min(60.0, max(backoff, float(retry_after_raw)))
                    except ValueError:
                        pass
                log_stderr(f"HTTP 429 from {api_url}; backing off {backoff:.1f}s (attempt {attempt + 1}/{attempts})...")
                time.sleep(backoff)
                continue

            if exc.code >= 500:
                if attempt + 1 >= attempts:
                    raise RuntimeError(
                        f"Server HTTP {exc.code} from {api_url} after {attempts} attempts. Response: {err_body}"
                    ) from exc
                backoff = float(2 ** attempt)
                log_stderr(f"HTTP {exc.code} from {api_url}; retrying in {backoff:.1f}s (attempt {attempt + 1}/{attempts})...")
                time.sleep(backoff)
                continue

            hint = ""
            if exc.code == 402:
                hint = f" Insufficient balance — please recharge at {RECHARGE_URL}."
            elif exc.code in (401, 403):
                hint = f" Check your BUNNYSCHOLAR_API_KEY at {KEYS_URL}."
            raise ApiHttpError(
                status_code=exc.code,
                url=api_url,
                body_preview=err_body,
                message=f"HTTP {exc.code} from {api_url} (rate_limit={rate_limit} req/s).{hint} Body: {err_body}",
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt + 1 >= attempts:
                raise RuntimeError(f"Network error calling {api_url} after {attempts} attempts: {exc}") from exc
            backoff = float(2 ** attempt)
            log_stderr(f"Network/timeout error calling {api_url}: {exc}; retrying in {backoff:.1f}s...")
            time.sleep(backoff)

    raise RuntimeError(f"Failed calling {api_url} after {attempts} attempts.")


def _parse_personal_terms(raw: Optional[str]) -> Optional[List[str]]:
    """解析 --personal-terms（支持逗号分隔字符串或 JSON 字符串数组）。"""
    if not raw or not raw.strip():
        return None
    s = raw.strip()
    if s.startswith("["):
        parsed = json.loads(s)
        if not isinstance(parsed, list):
            raise CliError("--personal-terms JSON must be an array of strings.")
        terms = [str(x).strip() for x in parsed if str(x).strip()]
        return terms or None
    terms = [part.strip() for part in s.split(",") if part.strip()]
    return terms or None


def _matching_personal_terms(text: str, terms: Sequence[str]) -> List[str]:
    """查找原样出现的术语，忽略大小写及空白差异。"""
    normalized_text = " ".join(text.split())
    matched = []
    # ASCII 术语按词边界比较，允许它紧邻中文文字。
    word_chars = r"[A-Za-z0-9_]"
    for term in dict.fromkeys(terms):
        phrase = " ".join(term.split())
        if not phrase:
            continue
        prefix = rf"(?<!{word_chars})" if re.fullmatch(word_chars, phrase[0]) else ""
        suffix = rf"(?!{word_chars})" if re.fullmatch(word_chars, phrase[-1]) else ""
        if re.search(f"{prefix}{re.escape(phrase)}{suffix}", normalized_text, re.IGNORECASE):
            matched.append(term)
    return matched


def run_humanize_batch(
    input_path: Optional[Path],
    output_path: Optional[Path],
    dual_stage: bool = False,
    rate_limit: float = DEFAULT_RATE_LIMIT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    http_retries: int = DEFAULT_HTTP_RETRIES,
    api_url: str = DEFAULT_API_URL,
    lock_file: Optional[Path] = None,
    timeout: float = DEFAULT_TIMEOUT,
    personal_terms: Optional[List[str]] = None,
    env_paths: Optional[Sequence[str]] = None,
    ignore_process_env: bool = False,
    allow_quality_warnings: bool = False,
    language: str = "en",
    platform_name: Optional[str] = None,
    allow_first_person: bool = False,
    max_word_len: int = 16,
    disable_quality_gate: bool = False,
    text_file: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """预检段落长度与语言/平台参数，并按需调用 API 与检查改写结果。"""
    if language not in SUPPORTED_HUMANIZER_LANGUAGES:
        raise CliError(
            f"Unsupported --language '{language}' for BunnyScholar humanizer; "
            f"supported values: {', '.join(SUPPORTED_HUMANIZER_LANGUAGES)}."
        )
    resolved_platform = platform_name if platform_name else ("cnki" if language == "zh_CN" else "gptzero")
    allowed_platforms = SUPPORTED_PLATFORMS_BY_LANGUAGE[language]
    dry_warnings: List[str] = []
    if resolved_platform not in allowed_platforms:
        warn_msg = (
            f"Platform '{resolved_platform}' is not in documented {language} list "
            f"({', '.join(allowed_platforms)}); BunnyScholar server may fall back to default."
        )
        dry_warnings.append(warn_msg)
        log_stderr(f"Warning: {warn_msg}")

    if not dry_run and output_path is None:
        raise CliError("Provide --output for live requests, or use --dry-run to check the input first.")

    if text_file is not None:
        label = "standard input" if text_file == "-" else text_file
        if text_file == "-":
            text = sys.stdin.buffer.read().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        else:
            text = Path(text_file).read_text(encoding="utf-8-sig")
        items = [{"para_index": 1, "text": text.strip()}]
    elif input_path is not None:
        label = str(input_path)
        items = _load_humanized_items(input_path)
    else:
        raise CliError("Provide --input or --text-file.")
    if not items:
        raise CliError(f"No paragraph items found in {label}.")

    # 预检全部段落文本结构与计费长度（20–500 计费字符）
    validated_items: List[Tuple[int, str, int]] = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise CliError(f"Item #{idx} in {label} must be an object.")
        para_index = item.get("para_index", idx)
        if not isinstance(para_index, int) or isinstance(para_index, bool) or para_index <= 0:
            raise CliError(f"Invalid para_index in item #{idx}: {para_index!r}")
        src_text = item.get("text")
        if not isinstance(src_text, str) or not src_text.strip():
            raise CliError(f"Missing non-empty 'text' for para_index={para_index}.")
        billable = compute_billable_chars(src_text)["billable_chars"]
        if billable < 20 or billable > 500:
            advice = (
                "Skip short text or merge before calling."
                if billable < 20
                else "Split paragraph at sentence boundaries (.) before calling."
            )
            raise CliError(
                f"Paragraph {para_index} billable length is {billable} units, outside API required range [20, 500]. {advice}"
            )
        validated_items.append((para_index, src_text, billable))

    if dry_run:
        total_billable = sum(item[2] for item in validated_items)
        est_cost = round((total_billable / 1000.0) * HUMANIZER_REF_UNIT_PRICE_CNY, 4)
        paragraphs: List[Dict[str, Any]] = []
        for para_index, src_text, billable in validated_items:
            paragraph: Dict[str, Any] = {"para_index": para_index, "billable_chars_estimated": billable}
            if personal_terms:
                paragraph["matched_personal_terms"] = _matching_personal_terms(src_text, personal_terms)
            paragraphs.append(paragraph)
        preview: Dict[str, Any] = {
            "dry_run": True,
            "language": language,
            "platform": resolved_platform,
            "dual_stage": dual_stage,
            "total_billable_chars_estimated": total_billable,
            "estimated_cost_cny": est_cost,
            "pricing_note": (
                f"Reference unit price: {HUMANIZER_REF_UNIT_PRICE_CNY} CNY / 1000 billable chars "
                "(credits used before cash balance; live pricing: https://bunnyscholar.cn/developer/pricing)."
            ),
            "paragraphs": paragraphs,
        }
        if dry_warnings:
            preview["warnings"] = dry_warnings
        emit_result(preview, str(output_path) if output_path else None)
        return preview

    api_key, key_source = _read_key_for_runtime_call(env_paths=env_paths, ignore_process_env=ignore_process_env)
    if not api_key:
        raise CliError(
            f"{API_KEY_NAME} not found. Log in if needed at {LOGIN_URL}, open {KEYS_URL}, then run "
            "'setup-key' in your local terminal, or set the environment variable for this process."
        )

    resolved_lock = lock_file if lock_file else _default_lock_file_path()
    total_gate_rounds = 1 + max(0, max_retries)
    results: List[Dict[str, Any]] = []
    failed_paras: List[int] = []
    total_cost = 0.0

    for para_index, src_text, billable in validated_items:
        log_stderr(f"Humanizing paragraph {para_index} (billable={billable}, dual_stage={dual_stage})...")
        last_text = ""
        last_issues: List[str] = []
        last_usage: Dict[str, Any] = {}
        attempts_used = 0
        passed = False

        for round_idx in range(1, total_gate_rounds + 1):
            attempts_used = round_idx
            resp = call_humanizer_api(
                text=src_text,
                api_key=api_key,
                api_url=api_url,
                dual_stage=dual_stage,
                rate_limit=rate_limit,
                lock_path=resolved_lock,
                timeout=timeout,
                http_retries=http_retries,
                personal_terms=personal_terms,
                language=language,
                platform_name=resolved_platform,
            )
            # 保留服务的原始候选文本，便于比较与复测。
            api_text = resp["data"]["text"]
            last_text = api_text
            last_usage = resp.get("usage") if isinstance(resp.get("usage"), dict) else {}
            if isinstance(last_usage.get("amount"), (int, float)):
                total_cost += float(last_usage["amount"])

            if disable_quality_gate:
                issues = []
                passed = True
                break

            issues = check_quality_gate(
                src_text,
                api_text,
                personal_terms=personal_terms,
                allow_first_person=allow_first_person,
                max_word_len=max_word_len,
            )
            last_issues = issues
            if not issues:
                passed = True
                break
            log_stderr(
                f"Quality gate failed for para {para_index} on attempt {round_idx}/{total_gate_rounds}: "
                f"{'; '.join(issues)}"
            )

        if not passed:
            failed_paras.append(para_index)

        result: Dict[str, Any] = {
            "para_index": para_index,
            "source_text": src_text,
            "text": last_text,
            "humanized_text": last_text,
            "billable_chars_estimated": billable,
            "quality_passed": passed,
            "quality_issues": last_issues,
            "attempts_used": attempts_used,
            "usage": last_usage,
        }
        if personal_terms:
            matched_terms = _matching_personal_terms(src_text, personal_terms)
            kept_terms = set(_matching_personal_terms(last_text, matched_terms))
            missing_terms = [term for term in matched_terms if term not in kept_terms]
            result["matched_personal_terms"] = matched_terms
            result["missing_personal_terms"] = missing_terms
            if missing_terms:
                log_stderr(
                    f"Warning: paragraph {para_index} is missing {len(missing_terms)} requested term(s); "
                    "see missing_personal_terms in the result."
                )
        results.append(result)

    output_payload = {
        "api_url": api_url,
        "key_source": key_source,
        "language": language,
        "platform": resolved_platform,
        "dual_stage": bool(dual_stage),
        "allow_first_person": bool(allow_first_person),
        "max_word_len": int(max_word_len),
        "quality_gate_enabled": not bool(disable_quality_gate),
        "rate_limit": rate_limit,
        "total_paragraphs": len(results),
        "passed_count": sum(1 for r in results if r["quality_passed"]),
        "failed_count": len(failed_paras),
        "failed_paras": failed_paras,
        "total_usage_amount": round(total_cost, 6),
        "paragraphs": results,
    }
    emit_result(output_payload, str(output_path))

    if failed_paras and not allow_quality_warnings:
        raise QualityGateError(
            f"Quality gate did not pass after {max_retries} retries for paragraph(s): {failed_paras}. "
            "Unmodified final API text has been saved to the output JSON for inspection."
        )
    return output_payload


# ==============================================================================
# 模块 5：export-pdf 双后端导出与 --stage-to
# ==============================================================================

def _ps_single_quote_escape(value: str) -> str:
    """转义 PowerShell 单引号字符串中的单引号。"""
    return value.replace("'", "''")


def _export_pdf_via_word_com(docx_abs: Path, pdf_abs: Path) -> None:
    """在 Windows 下通过无窗口 PowerShell 调用 Microsoft Word COM 导出 PDF。"""
    in_escaped = _ps_single_quote_escape(str(docx_abs))
    out_escaped = _ps_single_quote_escape(str(pdf_abs))
    ps_script = (
        "$ErrorActionPreference = 'Stop'\n"
        f"$inPath = '{in_escaped}'\n"
        f"$outPath = '{out_escaped}'\n"
        "$word = $null\n"
        "$doc = $null\n"
        "try {\n"
        "  $word = New-Object -ComObject Word.Application\n"
        "  $word.Visible = $false\n"
        "  $word.DisplayAlerts = 0\n"
        "  $doc = $word.Documents.Open($inPath, $false, $true)\n"
        "  $doc.ExportAsFixedFormat($outPath, 17)\n"
        "} finally {\n"
        "  if ($doc -ne $null) {\n"
        "    try { $doc.Close(0) } catch {}\n"
        "    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null\n"
        "  }\n"
        "  if ($word -ne $null) {\n"
        "    try { $word.Quit() } catch {}\n"
        "    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null\n"
        "  }\n"
        "  [GC]::Collect()\n"
        "  [GC]::WaitForPendingFinalizers()\n"
        "}\n"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        err_detail = (proc.stderr or proc.stdout or f"Exit code {proc.returncode}").strip()
        raise CliError(f"Word COM PDF export failed: {err_detail}")


def _export_pdf_via_soffice(docx_abs: Path, pdf_abs: Path) -> None:
    """通过 LibreOffice soffice --headless 导出 PDF，并使用独立临时 UserInstallation 隔离互锁。"""
    lo_info = detect_libreoffice()
    if not lo_info["available"] or not lo_info["path"]:
        raise CliError(f"LibreOffice soffice backend unavailable: {lo_info.get('error')}")
    soffice_path = str(lo_info["path"])

    tmp_root = Path(tempfile.mkdtemp(prefix="lo_export_"))
    profile_dir = tmp_root / "profile"
    out_dir = tmp_root / "out"
    profile_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        profile_uri = profile_dir.resolve().as_uri()
        cmd = [
            soffice_path,
            "--headless",
            "--norestore",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(docx_abs),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            err_detail = (proc.stderr or proc.stdout or f"Exit code {proc.returncode}").strip()
            raise CliError(f"LibreOffice soffice export failed: {err_detail}")
        generated_pdf = out_dir / f"{docx_abs.stem}.pdf"
        if not generated_pdf.is_file() or generated_pdf.stat().st_size == 0:
            raise CliError("LibreOffice soffice finished but no non-empty PDF was generated.")
        atomic_copy_file(generated_pdf, pdf_abs)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def export_pdf(
    docx_path: Path,
    pdf_path: Optional[Path] = None,
    backend: str = "auto",
    stage_to: Optional[Path] = None,
) -> Dict[str, Any]:
    """将 .docx 导出为 PDF（Windows 优先 Word COM 并自动降级 soffice），可选复制到 --stage-to 目录。"""
    if not docx_path.is_file():
        raise CliError(f"DOCX file not found: {docx_path}")
    docx_abs = docx_path.resolve()
    pdf_abs = (pdf_path if pdf_path else docx_abs.with_suffix(".pdf")).resolve()
    pdf_abs.parent.mkdir(parents=True, exist_ok=True)

    backend_used: Optional[str] = None
    fallback_reason: Optional[str] = None

    if backend == "word":
        if os.name != "nt":
            raise CliError("Backend 'word' is only supported on Windows.")
        _export_pdf_via_word_com(docx_abs, pdf_abs)
        backend_used = "word_com"
    elif backend == "soffice":
        _export_pdf_via_soffice(docx_abs, pdf_abs)
        backend_used = "libreoffice"
    elif backend == "auto":
        if os.name == "nt":
            try:
                _export_pdf_via_word_com(docx_abs, pdf_abs)
                backend_used = "word_com"
            except Exception as exc:
                fallback_reason = str(exc)
                log_stderr(f"Warning: Word COM export failed ({exc}); falling back to LibreOffice soffice...")
                _export_pdf_via_soffice(docx_abs, pdf_abs)
                backend_used = "libreoffice"
        else:
            _export_pdf_via_soffice(docx_abs, pdf_abs)
            backend_used = "libreoffice"
    else:
        raise CliError(f"Unsupported --backend value: {backend}")

    if not pdf_abs.is_file() or pdf_abs.stat().st_size == 0:
        raise CliError(f"PDF export completed without valid output file: {pdf_abs}")

    staged_path: Optional[str] = None
    if stage_to is not None:
        stage_dir = stage_to.resolve()
        stage_dir.mkdir(parents=True, exist_ok=True)
        dst_staged = stage_dir / pdf_abs.name
        atomic_copy_file(pdf_abs, dst_staged)
        staged_path = str(dst_staged)

    return {
        "docx_path": str(docx_abs),
        "pdf_path": str(pdf_abs),
        "pdf_size_bytes": pdf_abs.stat().st_size,
        "backend_requested": backend,
        "backend_used": backend_used,
        "fallback_reason": fallback_reason,
        "staged_path": staged_path,
    }


# ==============================================================================
# CLI 参数解析与入口路由
# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 入口与子命令。"""
    parser = argparse.ArgumentParser(
        prog="humanizer_loop.py",
        description="BunnyScholar x GPTZero Humanizer Loop CLI (zero third-party dependencies).",
    )
    parser.add_argument("--version", action="version", version=SKILL_VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<subcommand>")

    # 1. check-env
    p_check = subparsers.add_parser(
        "check-env",
        help="Silently probe BUNNYSCHOLAR_API_KEY, PDF export backends, and bunnyscholar-api skill.",
    )
    p_check.add_argument(
        "--env-paths",
        nargs="+",
        default=None,
        help="Override .env file paths to probe instead of default ~/.env and plugin .env.",
    )
    p_check.add_argument(
        "--ignore-process-env",
        action="store_true",
        help="Ignore BUNNYSCHOLAR_API_KEY from current process environment (useful for isolated testing).",
    )
    p_check.add_argument("--skip-update-check", action="store_true", help="Skip remote version check.")
    p_check.add_argument("--force-update-check", action="store_true", help="Bypass 24h cache for remote version check.")
    p_check.add_argument("--update-source-url", default=SKILL_REMOTE_SKILL_MD_URL, help="Override remote SKILL.md URL for version check.")
    p_check.add_argument("--quick", action="store_true", help="Check credentials and local skill only; skip PDF and remote version checks.")
    p_check.add_argument("--summary", action="store_true", help="Print a short human-readable setup summary (JSON is the default).")
    p_check.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    p_setup = subparsers.add_parser("setup-key", help="Reuse an existing BunnyScholar key or save a new one with hidden input.")
    p_setup.add_argument("--env-file", type=Path, help="Check and save to this file (default save location: ~/.env).")
    p_setup.add_argument("--replace", action="store_true", help="Enter a new key even if one is already available.")

    # 2. inspect
    p_inspect = subparsers.add_parser(
        "inspect",
        help="Inspect a .docx file for paragraph stats, highlights, citations [1]..[N], and first-person pronouns.",
    )
    p_inspect.add_argument("--docx", required=True, help="Path to target .docx file.")
    p_inspect.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    # 3. snapshot
    p_snap = subparsers.add_parser(
        "snapshot",
        help="Save a timestamped backup snapshot of .docx and record GPTZero metrics in history.json.",
    )
    p_snap.add_argument("--docx", required=True, help="Path to target .docx file.")
    p_snap.add_argument("--snapshot-dir", default=None, help="Snapshot directory (default: a per-document directory under .snapshots).")
    p_snap.add_argument("--overall-human", type=float, default=None, help="Overall Human percentage (0-100).")
    p_snap.add_argument("--mixed", type=float, default=None, help="Mixed percentage (0-100).")
    p_snap.add_argument("--ai", type=float, default=None, help="AI percentage (0-100).")
    p_snap.add_argument("--pages", default=None, help="Page-by-page scores as JSON or '1=98,2=87'.")
    p_snap.add_argument("--note", default="", help="Version note describing changes.")
    p_snap.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    # 4. rollback
    p_roll = subparsers.add_parser(
        "rollback",
        help="List snapshots or roll back .docx to a specific version or highest overall_human score.",
    )
    p_roll.add_argument("--docx", required=True, help="Path to target .docx file.")
    p_roll.add_argument("--snapshot-dir", default=None, help="Snapshot directory (default: <docx_dir>/.snapshots).")
    roll_group = p_roll.add_mutually_exclusive_group()
    roll_group.add_argument("--list", action="store_true", help="List snapshot versions and scores without modifying .docx.")
    roll_group.add_argument("--version", type=int, default=None, help="Restore a specific snapshot version number.")
    roll_group.add_argument("--best", action="store_true", help="Restore the highest overall_human snapshot (default).")
    p_roll.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    # 5. humanize
    p_hum = subparsers.add_parser(
        "humanize",
        help="Call BunnyScholar humanizer API with cross-process rate limiting, retries, and quality gate.",
    )
    hum_input = p_hum.add_mutually_exclusive_group(required=True)
    hum_input.add_argument("--input", type=Path, help="Input JSON containing a list of paragraphs.")
    hum_input.add_argument("--text-file", help="UTF-8 text file or '-' for stdin; sends the full text as a single request.")
    p_hum.add_argument("--output", type=Path, help="Output JSON path (required for live requests).")
    p_hum.add_argument("--dry-run", action="store_true", help="Validate input and estimate billable characters without a key or network request.")
    p_hum.add_argument("--dual-stage", action="store_true", help="Enable needPlagiarismReduction=True.")
    p_hum.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT, help="Max requests/sec across processes (default: 20.0).")
    p_hum.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Extra potentially billable quality retries per paragraph (default: 0).")
    p_hum.add_argument("--http-retries", type=int, default=DEFAULT_HTTP_RETRIES, help="Max HTTP 429/5xx attempts per call (default: 3).")
    p_hum.add_argument("--api-url", default=DEFAULT_API_URL, help=f"API endpoint URL (default: {DEFAULT_API_URL}).")
    p_hum.add_argument("--lock-file", default=None, help="Cross-process rate-limit lock file path.")
    p_hum.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP request timeout in seconds (default: 30.0).")
    p_hum.add_argument(
        "--personal-terms", default=None,
        help="Comma-separated terms or a JSON array; sent to BunnyScholar and checked in the final candidate.",
    )
    p_hum.add_argument("--env-paths", nargs="+", default=None, help="Override .env file paths for API key lookup.")
    p_hum.add_argument("--ignore-process-env", action="store_true", help="Ignore BUNNYSCHOLAR_API_KEY in process env.")
    p_hum.add_argument(
        "--allow-quality-warnings",
        action="store_true",
        help="Exit 0 even if some paragraphs fail quality gate after max retries (results remain unmodified).",
    )
    p_hum.add_argument("--language", default="en", help="Target language for BunnyScholar humanizer (en or zh_CN; default: en).")
    p_hum.add_argument("--platform", default=None, help="Target AI detector platform (default: gptzero for en, cnki for zh_CN).")
    p_hum.add_argument("--allow-first-person", action="store_true", help="Disable first-person pronoun check in quality gate.")
    p_hum.add_argument("--max-word-len", type=int, default=16, help="Max allowed alphabetical word length before garbled-word trigger (default: 16).")
    p_hum.add_argument("--disable-quality-gate", action="store_true", help="Skip quality-gate checks and retries.")

    # 6. apply
    p_apply = subparsers.add_parser(
        "apply",
        help="Write unmodified humanized text back into .docx while preserving styles and <w:hyperlink> nodes.",
    )
    p_apply.add_argument("--docx", required=True, help="Source .docx file path.")
    p_apply.add_argument("--humanized", required=True, help="JSON file from humanize command.")
    p_apply.add_argument("--output-docx", default=None, help="Target .docx path (default: overwrite --docx atomically).")
    p_apply.add_argument("--highlight-paras", default=None, help="Comma-separated 1-based paragraph indices to highlight yellow.")
    p_apply.add_argument("--clear-other-highlights", action="store_true", help="Clear highlights on paragraphs not in --highlight-paras.")
    p_apply.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    # 7. export-pdf
    p_pdf = subparsers.add_parser(
        "export-pdf",
        help="Export .docx to PDF via Word COM (Windows preferred) or LibreOffice soffice, optionally staging to a folder.",
    )
    p_pdf.add_argument("--docx", required=True, help="Source .docx file path.")
    p_pdf.add_argument("--pdf", default=None, help="Target PDF output path (default: same name with .pdf).")
    p_pdf.add_argument("--stage-to", default=None, help="Optional directory to copy the exported PDF into.")
    p_pdf.add_argument(
        "--backend",
        choices=("auto", "word", "soffice"),
        default="auto",
        help="PDF export backend (default: auto).",
    )
    p_pdf.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    # 8. self-update
    p_upd = subparsers.add_parser(
        "self-update",
        help="Check or apply a safe update for this skill (git pull --ff-only or static whitelist download).",
    )
    p_upd.add_argument("--apply", action="store_true", help="Apply update (default is dry-run version check).")
    p_upd.add_argument("--repair", action="store_true", help="With --apply, reinstall the same version on a copied installation.")
    p_upd.add_argument("--skill-dir", default=None, help="Override target skill directory.")
    p_upd.add_argument("--raw-base", default=SKILL_REMOTE_RAW_BASE, help="Override remote raw base URL.")
    p_upd.add_argument("--timeout", type=float, default=15.0, help="Download/git timeout in seconds (default: 15.0).")
    p_upd.add_argument("--output", default=None, help="Optional path to write UTF-8 JSON report.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI 主入口，解析参数并分发到对应子命令处理函数。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "check-env":
            result = check_environment(
                env_paths=args.env_paths,
                ignore_process_env=bool(args.ignore_process_env),
                skip_update_check=args.skip_update_check or (args.quick and not args.force_update_check),
                force_update_check=bool(args.force_update_check),
                update_source_url=args.update_source_url,
                skip_pdf_check=args.quick,
            )
            if args.summary:
                print_environment_summary(result)
            if args.output or not args.summary:
                emit_result(result, args.output)
            return 0

        if args.command == "setup-key":
            if not args.replace:
                explicit_paths = [str(args.env_file)] if args.env_file is not None else None
                _, existing_source = _read_key_for_runtime_call(
                    env_paths=explicit_paths,
                    ignore_process_env=explicit_paths is not None,
                )
                if existing_source:
                    print(f"Using the existing BunnyScholar key from {existing_source} (local check only).")
                    return 0
            result = setup_api_key(args.env_file or Path.home() / ".env")
            print(f"Saved and verified the local key in {result['saved_to']}.")
            if result["process_env_takes_precedence"]:
                print(f"{API_KEY_NAME} in the process environment takes precedence over the saved file.")
            print(f"Before your first paid rewrite, check your balance at {CONSOLE_URL}")
            print(f"If needed, top up at {RECHARGE_URL}")
            return 0

        if args.command == "inspect":
            result = inspect_docx(Path(args.docx))
            emit_result(result, args.output)
            return 0

        if args.command == "snapshot":
            pages_val = _parse_pages_arg(args.pages)
            result = create_snapshot(
                docx_path=Path(args.docx),
                snapshot_dir=Path(args.snapshot_dir) if args.snapshot_dir else None,
                overall_human=args.overall_human,
                mixed=args.mixed,
                ai=args.ai,
                pages=pages_val,
                note=args.note,
            )
            emit_result(result, args.output)
            return 0

        if args.command == "rollback":
            result = rollback_snapshot(
                docx_path=Path(args.docx),
                snapshot_dir=Path(args.snapshot_dir) if args.snapshot_dir else None,
                list_only=bool(args.list),
                version=args.version,
                best=bool(args.best),
            )
            emit_result(result, args.output)
            return 0

        if args.command == "humanize":
            terms = _parse_personal_terms(args.personal_terms)
            run_humanize_batch(
                input_path=args.input,
                output_path=args.output,
                dual_stage=bool(args.dual_stage),
                rate_limit=args.rate_limit,
                max_retries=args.max_retries,
                http_retries=args.http_retries,
                api_url=args.api_url,
                lock_file=Path(args.lock_file) if args.lock_file else None,
                timeout=args.timeout,
                personal_terms=terms,
                env_paths=args.env_paths,
                ignore_process_env=bool(args.ignore_process_env),
                allow_quality_warnings=bool(args.allow_quality_warnings),
                language=args.language,
                platform_name=args.platform,
                allow_first_person=bool(args.allow_first_person),
                max_word_len=args.max_word_len,
                disable_quality_gate=bool(args.disable_quality_gate),
                text_file=args.text_file,
                dry_run=args.dry_run,
            )
            return 0

        if args.command == "apply":
            docx_src = Path(args.docx)
            docx_dst = Path(args.output_docx) if args.output_docx else docx_src
            items = _load_humanized_items(Path(args.humanized))
            hl_paras = _parse_int_csv(args.highlight_paras)
            result = apply_humanized_to_docx(
                docx_path=docx_src,
                humanized_items=items,
                output_docx=docx_dst,
                highlight_paras=hl_paras,
                clear_other_highlights=bool(args.clear_other_highlights),
            )
            emit_result(result, args.output)
            return 0

        if args.command == "export-pdf":
            result = export_pdf(
                docx_path=Path(args.docx),
                pdf_path=Path(args.pdf) if args.pdf else None,
                backend=args.backend,
                stage_to=Path(args.stage_to) if args.stage_to else None,
            )
            emit_result(result, args.output)
            return 0

        if args.command == "self-update":
            result = self_update_skill(
                apply_changes=bool(args.apply),
                skill_dir=Path(args.skill_dir) if args.skill_dir else None,
                raw_base=args.raw_base,
                timeout=args.timeout,
                repair=bool(args.repair),
            )
            emit_result(result, args.output)
            return 0

        parser.error(f"Unknown command: {args.command}")
        return 2
    except (
        CliError,
        RateLimitError,
        ApiHttpError,
        QualityGateError,
        OSError,
        json.JSONDecodeError,
        ET.ParseError,
        zipfile.BadZipFile,
        TimeoutError,
        ValueError,
        RuntimeError,
    ) as exc:
        log_stderr(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

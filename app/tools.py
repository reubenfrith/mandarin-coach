"""The five agent tools.

Built via make_tools(user_id) so the personal-error tools are bound to the right
user namespace without the LLM having to supply a user id. The agent selects
among these based on intent — that selection is what makes this an agent rather
than a chatbot.

  1. grammar_rule_fetcher   — hybrid BM25+dense RAG over grammar_rules (internal)
  2. error_pattern_analyser — personal error history + deterministic stats (internal)
  3. drill_generator        — LLM-generated targeted exercises (internal LLM call)
  4. dictionary_lookup      — grounded pinyin/definition/HSK (external CC-CEDICT + pypinyin)
  5. web_search             — Tavily live search (external)
"""
import json
import os
import re
import zipfile
from io import BytesIO
from pathlib import Path

import requests
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from pypinyin import Style, pinyin as _pinyin

import memory
from config import get_llm
from prompts import DRILL_SYSTEM_PROMPT

_ROOT = Path(__file__).resolve().parent.parent
_DATA = _ROOT / "data"


# --------------------------------------------------------------------------- #
# CC-CEDICT: lazy download + cache, for grounded definitions
# --------------------------------------------------------------------------- #
_CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
_CEDICT_CACHE = _DATA / "cedict.txt"
_CEDICT_LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.+)/$")
_cedict = None
_hsk_map = None


def _load_cedict() -> dict:
    """simplified -> {'pinyin': ..., 'defs': [...]}. Empty dict if unavailable."""
    global _cedict
    if _cedict is not None:
        return _cedict
    _cedict = {}
    try:
        if not _CEDICT_CACHE.exists():
            resp = requests.get(_CEDICT_URL, timeout=30)
            resp.raise_for_status()
            with zipfile.ZipFile(BytesIO(resp.content)) as z:
                name = next(n for n in z.namelist() if n.endswith(".u8"))
                _CEDICT_CACHE.write_bytes(z.read(name))
        for line in _CEDICT_CACHE.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                continue
            m = _CEDICT_LINE.match(line)
            if m:
                _, simp, py, defs = m.groups()
                if simp not in _cedict:
                    _cedict[simp] = {"pinyin": py, "defs": defs.split("/")}
    except Exception:
        pass  # offline / download failed — dictionary degrades to pinyin only
    return _cedict


def _load_hsk_map() -> dict:
    global _hsk_map
    if _hsk_map is None:
        records = json.loads((_DATA / "hsk_vocab.json").read_text(encoding="utf-8"))
        _hsk_map = {r["word"]: r["hsk_level"] for r in records}
    return _hsk_map


def _tone_pinyin(text: str) -> str:
    return " ".join(s[0] for s in _pinyin(text, style=Style.TONE))


def pinyin_segments(text: str) -> list[dict]:
    """Per-character segmentation for ruby display (汉字 with pīnyīn underneath).

    Returns an ordered list where each Han character is one `{"hanzi", "pinyin"}` entry
    and each run of non-Han characters (punctuation, spaces, latin) is one `{"text"}`
    entry — so the UI can render `<ruby>` per character while keeping punctuation inline.

    pīnyīn is looked up per maximal Han run (not per isolated character) so pypinyin's
    word context still applies — e.g. 银行→yín háng, 不行→bù xíng — which per-character
    lookup would get wrong for polyphones."""
    is_han = lambda c: "一" <= c <= "鿿"
    segs: list[dict] = []
    i, n = 0, len(text)
    while i < n:
        if is_han(text[i]):
            j = i
            while j < n and is_han(text[j]):
                j += 1
            run = text[i:j]
            marks = _pinyin(run, style=Style.TONE)  # one entry per char, with word context
            for k, ch in enumerate(run):
                segs.append({"hanzi": ch, "pinyin": marks[k][0] if k < len(marks) else ""})
            i = j
        else:
            j = i
            while j < n and not is_han(text[j]):
                j += 1
            segs.append({"text": text[i:j]})
            i = j
    return segs


def annotate_tones(text: str) -> list[dict]:
    """Per-Han-character pinyin + numeric tone, for the pronunciation coach's target.

    Returns e.g. [{"hanzi": "你", "pinyin": "nǐ", "tone": 3}, ...], one entry per Chinese
    character (non-Han characters are skipped). Tone 5 = neutral. Per-character lookup keeps
    hanzi↔pinyin alignment exact; tone sandhi is not applied here (a Phase-2 refinement)."""
    out = []
    for ch in text:
        if "一" <= ch <= "鿿":
            mark = _pinyin(ch, style=Style.TONE)[0][0]
            num = _pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True)[0][0]
            m = re.search(r"([1-5])$", num)
            out.append({"hanzi": ch, "pinyin": mark, "tone": int(m.group(1)) if m else 5})
    return out


# --------------------------------------------------------------------------- #
# Tool factory
# --------------------------------------------------------------------------- #
def make_tools(user_id: str) -> list:
    @tool
    def grammar_rule_fetcher(query: str) -> str:
        """Fetch Mandarin grammar rules relevant to a sentence or grammar question.
        Use this to explain WHY something is wrong or to answer a grammar question,
        e.g. the 把 construction, 了 vs 过, measure words."""
        # Hybrid BM25+dense (RRF) — the Task 6 advanced retriever; degrades to
        # dense automatically if the optional BM25 deps are unavailable.
        hits = memory.query_grammar_rules_hybrid(query, n=3)
        if not hits:
            return "No matching grammar rule found."
        out = []
        for h in hits:
            m = h["metadata"]
            # hsk_level 0 = unknown (Chinese Grammar Wiki patterns carry no level) —
            # omit rather than print a fabricated "HSK 0".
            lvl = m.get("hsk_level") or 0
            tag = f" (HSK {lvl})" if lvl else ""
            out.append(f"- {m['name']}{tag}: {h['document']}")
        return "\n".join(out)

    @tool
    def error_pattern_analyser(query: str) -> str:
        """Analyse the user's personal error history. Use this to (a) find the user's
        past mistakes similar to the current one, and (b) report their overall error
        statistics — counts and trends by category. Use for 'what am I getting wrong?',
        'show my progress', 'drill me on my weak points', or when correcting a sentence
        to check whether it is a recurring pattern."""
        stats = memory.error_stats(user_id)
        if stats["total"] == 0:
            return "No personal error history yet — this is a fresh corpus."
        lines = [f"Total errors logged: {stats['total']}."]
        lines.append("By category (most frequent first):")
        for cat, n in stats["by_category"].items():
            lines.append(f"  - {cat}: {n} ({stats['trend'].get(cat, 'steady')})")
        similar = memory.query_personal_errors(user_id, query, n=3)
        if similar:
            lines.append("Similar past mistakes by this user:")
            for s in similar:
                md = s["metadata"]
                lines.append(f"  - {md['original']} -> {md['correction']} [{md['category']}]")
        return "\n".join(lines)

    @tool
    def drill_generator(topic: str) -> str:
        """Generate 3-5 targeted practice exercises on a specific error category or
        grammar topic (e.g. '把 sentences', 'measure words', 'tones'). Use when the
        user asks to practise or drill, or to offer practice after a correction."""
        rules = memory.query_grammar_rules(topic, n=2)
        rule_context = "\n".join(h["document"] for h in rules) if rules else ""
        llm = get_llm(streaming=False)
        msg = [
            SystemMessage(content=DRILL_SYSTEM_PROMPT),
            HumanMessage(content=f"Topic: {topic}\n\nReference rule:\n{rule_context}"),
        ]
        resp = llm.invoke(msg)
        content = resp.content
        if isinstance(content, list):  # reasoning-model block list
            content = "".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        return content or "Could not generate a drill."

    @tool
    def dictionary_lookup(word: str) -> str:
        """Look up a Chinese word: pinyin, English definition, and HSK level.
        Use for an unfamiliar word in the user's input. Pinyin and HSK are grounded
        (not guessed) — always prefer this over recalling a word's pinyin from memory."""
        py = _tone_pinyin(word)
        entry = _load_cedict().get(word)
        hsk = _load_hsk_map().get(word)
        parts = [f"{word}  pinyin: {py}"]
        if entry:
            parts.append("definition: " + "; ".join(d for d in entry["defs"] if d)[:300])
        else:
            parts.append("definition: (not in dictionary cache)")
        if hsk:
            parts.append(f"HSK level: {hsk}")
        return "\n".join(parts)

    @tool
    def web_search(query: str) -> str:
        """Search the live web for real-world Chinese usage examples, cultural context,
        or current usage when the built-in corpus is insufficient. Use sparingly."""
        key = os.environ.get("TAVILY_API_KEY", "").strip()
        if not key or key.startswith("#"):
            return "Web search unavailable (no TAVILY_API_KEY configured)."
        try:
            from tavily import TavilyClient

            res = TavilyClient(api_key=key).search(query, max_results=3)
            out = []
            for r in res.get("results", []):
                out.append(f"- {r.get('title', '')}: {r.get('content', '')[:200]}")
            return "\n".join(out) or "No results."
        except Exception as e:
            return f"Web search failed: {type(e).__name__}."

    return [
        grammar_rule_fetcher,
        error_pattern_analyser,
        drill_generator,
        dictionary_lookup,
        web_search,
    ]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特语料全集快速检索与原典溯源工具 v2.0
新增：--strict 精确匹配模式（减少误召回）；改进去重逻辑（同段落只保留一次）
"""

import os
import sys
import re
import argparse

CORPUS_DEFAULT_DIR = "/Users/spad0611/Downloads/巴菲特资料全集"
CORPUS_EXTRA_DIR = "/Users/spad0611/.gemini/config/skills/buffett-stock-analysis/resources/master_corpus"


def search_corpus(keywords, corpus_dir=CORPUS_DEFAULT_DIR, category=None,
                  max_results=10, context_chars=200, strict=False):
    """
    strict=False（默认）：字符间允许少量空白（max 2个字符），兼容跨行排版
    strict=True：精确子串匹配，提高精准度，减少因排版换行导致的误召回
    """
    dirs_to_search = []
    if os.path.exists(corpus_dir):
        dirs_to_search.append(corpus_dir)
    if os.path.exists(CORPUS_EXTRA_DIR) and CORPUS_EXTRA_DIR not in dirs_to_search:
        dirs_to_search.append(CORPUS_EXTRA_DIR)

    if not dirs_to_search:
        print(f"错误: 语料库目录不存在: {corpus_dir}", file=sys.stderr)
        return

    if not keywords or not any(k.strip() for k in keywords):
        print("未指定有效关键词", file=sys.stderr)
        return

    results = []

    for c_dir in dirs_to_search:
        for root, _, files in os.walk(c_dir):
            rel_dir = os.path.relpath(root, c_dir)
            if category and category not in rel_dir and category not in root:
                continue

            for file in sorted(files):
                if not file.endswith(".md") and not file.endswith(".txt"):
                    continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                match_positions = []
                all_matched = True

                for k in keywords:
                    k_clean = k.strip()
                    if not k_clean:
                        continue

                    if strict:
                        # 精确匹配：直接搜索子串
                        p = re.compile(re.escape(k_clean), re.IGNORECASE)
                    else:
                        # 宽松匹配：字符间允许最多2个空白字符（比原来的\s*更严格）
                        pattern_str = r"\s{0,2}".join([re.escape(ch) for ch in k_clean])
                        p = re.compile(pattern_str, re.IGNORECASE)

                    matches = list(p.finditer(content))
                    if not matches:
                        all_matched = False
                        break
                    match_positions.extend([m.start() for m in matches])

                if all_matched and match_positions:
                    # 去重相近位置（同一段落内的多次匹配只保留第一个）
                    deduped_positions = []
                    last_pos = -context_chars * 2
                    for pos in sorted(match_positions):
                        if pos - last_pos > context_chars:
                            deduped_positions.append(pos)
                            last_pos = pos

                    for pos in deduped_positions[:3]:
                        start = max(0, pos - context_chars)
                        end = min(len(content), pos + context_chars + len(keywords[0]))
                        snippet = re.sub(r"\s+", " ", content[start:end]).strip()
                        results.append({
                            "file": file,
                            "category": rel_dir if rel_dir != "." else "大师原典库",
                            "path": filepath,
                            "pos": pos,
                            "snippet": f"...{snippet}...",
                        })

    mode_label = "【精确匹配】" if strict else "【宽松匹配】"
    kw_str = " & ".join(f"'{k}'" for k in keywords if k.strip())
    print(f"=== {mode_label} 检索关键词: {kw_str} | 找到 {len(results)} 条相关出处 ===")
    if len(results) == 0:
        if strict:
            print("  提示：精确模式未找到结果，可去掉 --strict 尝试宽松匹配")
        else:
            print("  提示：未找到匹配结果，可尝试拆分关键词或更换同义词")
    for idx, r in enumerate(results[:max_results], 1):
        print(f"\n[{idx}] 【{r['category']}】《{r['file']}》")
        print(f"    摘要: {r['snippet']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="巴菲特语料库原典快速检索工具 v2.0")
    parser.add_argument("keywords", nargs="+", help="检索关键词（多个关键词需同时包含）")
    parser.add_argument("--dir", default=CORPUS_DEFAULT_DIR, help="语料库路径")
    parser.add_argument("--category",
                        choices=["伯克希尔股东信", "致合伙人信", "特别信件", "采访与演讲"],
                        help="指定子分类")
    parser.add_argument("--max", type=int, default=8, help="最大返回结果数")
    parser.add_argument("--context", type=int, default=200, help="上下文前后字符数")
    parser.add_argument("--strict", action="store_true",
                        help="精确匹配模式：禁止字符间空白，提高精准度，减少误召回")

    args = parser.parse_args()
    search_corpus(
        args.keywords,
        corpus_dir=args.dir,
        category=args.category,
        max_results=args.max,
        context_chars=args.context,
        strict=args.strict,
    )

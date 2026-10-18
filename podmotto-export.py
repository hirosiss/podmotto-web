#!/usr/bin/env python3
"""
podmotto-export.py
------------------
Apple Podcasts (Mac) の購読番組リストを OPML 形式で書き出す。
出力先: ~/Desktop/podmotto-podcasts.opml

使い方:
  python3 podmotto-export.py

次のステップ:
  出力ファイルを iPhone に AirDrop または iCloud Drive で転送し、
  PodMotto アプリの「OPML ファイルを選択」でインポートしてください。
"""

import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Apple Podcasts のデータベースパス（macOS 固定）
DB_PATH = os.path.expanduser(
    "~/Library/Group Containers/243LU875E5.groups.com.apple.podcasts"
    "/Documents/MTLibrary.sqlite"
)

OUTPUT_PATH = os.path.expanduser("~/Desktop/podmotto-podcasts.opml")


def fetch_podcasts(db_path: str) -> list[tuple[str, str]]:
    """ZMTPODCAST テーブルから (rss_url, title) を取得する。"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT ZFEEDURL, ZTITLE FROM ZMTPODCAST WHERE ZFEEDURL IS NOT NULL ORDER BY ZTITLE"
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        print(f"データベースの読み取りに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()
    return [(rss, title or "") for rss, title in rows if rss]


def build_opml(podcasts: list[tuple[str, str]]) -> str:
    """podcast リストから OPML XML 文字列を生成する。"""
    opml_el = ET.Element("opml", version="2.0")

    head = ET.SubElement(opml_el, "head")
    ET.SubElement(head, "title").text = "Apple Podcasts Subscriptions"
    ET.SubElement(head, "dateCreated").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    body = ET.SubElement(opml_el, "body")
    for rss_url, title in podcasts:
        ET.SubElement(
            body,
            "outline",
            type="rss",
            text=title,
            title=title,
            xmlUrl=rss_url,
        )

    ET.indent(opml_el, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        opml_el, encoding="unicode"
    )


def main() -> None:
    if not os.path.exists(DB_PATH):
        print(
            "エラー: Apple Podcasts のデータベースが見つかりません。\n"
            f"  パス: {DB_PATH}\n"
            "Mac で Apple Podcasts を一度起動してから再試行してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Apple Podcasts データベースを読み取り中...")
    podcasts = fetch_podcasts(DB_PATH)

    if not podcasts:
        print("購読中の番組が見つかりませんでした。", file=sys.stderr)
        sys.exit(1)

    print(f"  {len(podcasts)} 番組を検出")

    opml = build_opml(podcasts)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(opml)

    print(f"\n✅ エクスポート完了: {OUTPUT_PATH}")
    print("\n次のステップ:")
    print("  1. このファイルを iPhone に AirDrop または iCloud Drive で転送")
    print("  2. PodMotto を開き「Apple Podcasts からインポート」→「OPML ファイルを選択」")


if __name__ == "__main__":
    main()

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parser(desc: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--gif", metavar="PATH", help="matplotlib で GIF に保存する")
    p.add_argument("--mpl", action="store_true", help="matplotlib のウィンドウで表示する")
    p.add_argument("--delay", type=float, default=0.15, help="ターミナル表示の1コマの秒数")
    p.add_argument("--no-color", action="store_true")
    return p

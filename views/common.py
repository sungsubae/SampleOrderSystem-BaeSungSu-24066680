import unicodedata
from colorama import init, Fore, Style

init(autoreset=True)

WIDTH = 62


def _display_len(s: str) -> int:
    """한글 등 전각 문자를 2칸으로 계산한 실제 터미널 표시 폭."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def _center_display(s: str, width: int) -> str:
    """전각 문자를 고려해 실제 표시 폭 기준으로 가운데 정렬."""
    pad = max(0, width - _display_len(s))
    return " " * (pad // 2) + s + " " * (pad - pad // 2)


def header(title: str):
    print()
    print(Fore.CYAN + "╔" + "═" * WIDTH + "╗")
    print(Fore.CYAN + "║" + _center_display(title, WIDTH) + "║")
    print(Fore.CYAN + "╚" + "═" * WIDTH + "╝")


def section(title: str):
    dashes = max(0, WIDTH - _display_len(title) - 3)
    print()
    print(Fore.YELLOW + f"┌─ {title} " + "─" * dashes + "┐")


def success(msg: str):
    print(Fore.GREEN + f"  ✔ {msg}")


def error(msg: str):
    print(Fore.RED + f"  ✖ {msg}")


def divider():
    print(Fore.WHITE + Style.DIM + "  " + "─" * (WIDTH - 2))


def ask(prompt: str) -> str:
    return input(Fore.WHITE + f"  {prompt} ").strip()


def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(ask(prompt))
        except ValueError:
            error("숫자를 입력해주세요.")


def ask_float(prompt: str) -> float:
    while True:
        try:
            return float(ask(prompt))
        except ValueError:
            error("숫자를 입력해주세요.")


def menu_item(num: int | str, label: str):
    print(f"  {Fore.CYAN}[{num}]{Style.RESET_ALL} {label}")

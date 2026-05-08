from colorama import init, Fore, Style

init(autoreset=True)

WIDTH = 62


def header(title: str):
    print()
    print(Fore.CYAN + "╔" + "═" * WIDTH + "╗")
    print(Fore.CYAN + "║" + title.center(WIDTH) + "║")
    print(Fore.CYAN + "╚" + "═" * WIDTH + "╝")


def section(title: str):
    print()
    print(Fore.YELLOW + f"┌─ {title} " + "─" * max(0, WIDTH - len(title) - 3) + "┐")


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

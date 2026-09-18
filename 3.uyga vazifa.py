import argparse

def main():
    parser = argparse.ArgumentParser(description="CLI Servis va Tizim Boshqaruvi")
    subparsers = parser.add_subparsers(dest="command", help="Mavjud buyruqlar")

    # 'start' buyrug'i
    start_parser = subparsers.add_parser("start", help="Servisni ishga tushirish")
    start_parser.add_argument("--port", type=int, default=8000, help="Port raqami (standart 8000)")

    # 'stop' buyrug'i
    stop_parser = subparsers.add_parser("stop", help="Servisni to'xtatish")
    stop_parser.add_argument("--force", action="store_true", help="Majburiy to'xtatish")

    args = parser.parse_args()

    if args.command == "start":
        print(f"Servis {args.port}-portda ishga tushirildi...")
    elif args.command == "stop":
        if args.force:
            print("Servis majburiy ravishda (FORCE) to'xtatildi!")
        else:
            print("Servis tinch yo'l bilan to'xtatildi.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
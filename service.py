import argparse

def main():
    parser = argparse.ArgumentParser(description="Xizmatni boshqarish skripti")
    subparsers = parser.add_subparsers(dest="command", help="Buyruqlar")

    # 'start' buyrug'i
    start_parser = subparsers.add_parser("start", help="Xizmatni ishga tushirish")
    
    # 'stop' buyrug'i
    stop_parser = subparsers.add_parser("stop", help="Xizmatni to'xtatish")

    args = parser.parse_args()

    if args.command == "start":
        print("Xizmat muvaffaqiyatli ishga tushirildi.")
    elif args.command == "stop":
        print("Xizmat to'xtatildi.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
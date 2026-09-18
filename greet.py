import argparse

parser = argparse.ArgumentParser(description="Salomlashuv skripti")
parser.add_argument("--name", type=str, required=True, help="Ismingizni kiriting")

args = parser.parse_args()
print(f"Salom, {args.name}!")
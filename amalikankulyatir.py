def calculator():
    try:
        num1 = float(input("Birinchi sonni kiriting: "))
        operator = input("Amalni kiriting (+, -, *, /): ").strip()
        num2 = float(input("Ikkinchi sonni kiriting: "))

        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            if num2 == 0:
                raise ZeroDivisionError("Nolga bo'lish mumkin emas!")
            result = num1 / num2
        else:
            print("Noto'g'ri amal kiritildi.")
            return

        print(f"Natija: {result}")

    except ValueError:
        print("Xatolik: Iltimos, faqat son kiriting!")
    except ZeroDivisionError as e:
        print(f"Xatolik: {e}")

# Funksiyani chaqirish
calculator()
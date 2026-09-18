# 1. To'g'ri login va parol (dastur ichida saqlanadi)
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "secret123"


max_attempts = 3
attempts = 0
is_logged_in = False


while attempts < max_attempts and not is_logged_in:
    print(f"\n--- Tizimga kirish ({max_attempts - attempts} ta urinish qoldi) ---")
    username = input("Loginni kiriting: ")
    password = input("Parolni kiriting: ")
    if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:
        is_logged_in = True
        print("\n Muvaffaqiyatli kirdingiz! Xush kelibsiz.")
    else:
        attempts += 1
        if attempts < max_attempts:
            print(" Noto'g'ri login yoki parol. Qayta urinib ko'ring.")


if not is_logged_in:
    print("\n Urinishlar soni tugadi. Tizimga kirish bloklandi!")
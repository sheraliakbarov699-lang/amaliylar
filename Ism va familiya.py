def split_full_name():
    try:
        full_name = input("To'liq ism familyangizni kiriting: ").strip()
        parts = full_name.split()

        if len(parts) < 2:
            print("Xatolik: Kamida ism va familiyani kiriting (bo'shliq bilan ajratib).")
            return

        first_name = parts[0]
        last_name = parts[1]

        print(f"Ism: {first_name}")
        print(f"Familiya: {last_name}")

    except Exception as e:
        print(f"Kutilmagan xatolik yuz berdi: {e}")

# Funksiyani chaqirish
split_full_name()
# 'x' (Create) - Yangi fayl yaratadi. Fayl allaqachon mavjud bo'lsa, FileExistsError beradi.
try:
    with open("malumot.txt", "x") as file:
        file.write("Yangi fayl yaratildi.\n")
except FileExistsError:
    print("Fayl allaqachon mavjud!")

# 'w' (Write) - Faylga yozish. Fayl bo'lsa, uning ichidagi eski ma'lumotlarni o'chirib yuborib yangisini yozadi.
with open("malumot.txt", "w") as file:
    file.write("Fayldagi ma'lumot yangilandi (eskilari o'chirildi).\n")

# 'a' (Append) - Fayl oxiriga ma'lumot qo'shish. Eski ma'lumotlar saqlanib qoladi.
with open("malumot.txt", "a") as file:
    file.write("Ushbu matn fayl oxiriga qo'shildi.\n")

# 'r' (Read) - Fayl ichidagi ma'lumotni o'qish uchun ochadi (standart rejim).
try:
    with open("malumot.txt", "r") as file:
        content = file.read()
        print("\nFayl tarkibi:\n" + content)
except FileNotFoundError:
    print("O'qish uchun fayl topilmadi!")
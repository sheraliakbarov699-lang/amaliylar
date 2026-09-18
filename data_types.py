# str
name = "Sherali"

# int
age = 15

# float
height = 158.5

# bool
student = True

# list
fruits = ["olma", "banan", "uzum"]

# tuple
colors = ("qizil", "yashil", "ko'k")

# set
numbers = {1, 2, 3, 4, 5}

# dict
person = {
    "name": "Sherali",
    "age": 15,
    "city": "Olmaliq"
}


# Qiymatlar va type()
print("name:", name)
print("type:", type(name))

print("age:", age)
print("type:", type(age))

print("height:", height)
print("type:", type(height))

print("student:", student)
print("type:", type(student))

print("fruits:", fruits)
print("type:", type(fruits))

print("colors:", colors)
print("type:", type(colors))

print("numbers:", numbers)
print("type:", type(numbers))

print("person:", person)
print("type:", type(person))


# list bilan for
print("\nList:")
for fruit in fruits:
    print(fruit)


# tuple bilan for
print("\nTuple:")
for color in colors:
    print(color)


# set bilan for
print("\nSet:")
for number in numbers:
    print(number)


# dict bilan for
print("\nDict:")
for key, value in person.items():
    print(key, ":", value)
    
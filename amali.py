# 1. Virtual muhit yaratish
python3 -m venv myenv

# Virtual muhitni faollashtirish
source myenv/bin/activate

# 2. requests kutubxonasini o'rnatish va requirements.txt faylini yaratish
pip install requests
pip freeze > requirements.txt
# Code Quality Analyzer
Flask asosidagi Python kod sifatini tahlil qiluvchi o‘quv loyihasi.

## Windows PowerShell
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python app.py
```
Brauzerda http://127.0.0.1:5000 manzilini oching.

Tahlillar: sintaksis xatosi, uzun funksiya, katta sinf, taxminiy murakkablik, Magic Number, takrorlangan qator va ishlatilmagan import.

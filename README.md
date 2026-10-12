# Telegram bot — zdjęcie i wybór płci

## Uruchomienie

1. Zainstaluj Python 3.10 lub nowszy.
2. Otwórz https://api.imgbb.com/ i wygeneruj klucz API ImgBB.
3. Skopiuj `.env.example` do `.env` i uzupełnij `BOT_TOKEN` oraz `IMGBB_API_KEY`.
4. Zainstaluj zależności:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. Uruchom:

   ```powershell
   python bot.py
   ```

Przepływ: `/start` → zdjęcie → przycisk „Mężczyzna” lub „Kobieta” → link do `huj-xi.vercel.app/id.html` z parametrami `name`, `surname`, `sex`, `birthday` i `image`.

Zdjęcia są przesyłane do ImgBB i stają się dostępne pod publicznym linkiem. ImgBB pozwala opcjonalnie ustawić czas wygaśnięcia uploadu; ten bot obecnie nie ustawia automatycznego usuwania.

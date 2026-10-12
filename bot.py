import calendar
import logging
import os
import random
from datetime import date, datetime, timedelta
from io import BytesIO
from urllib.parse import quote, quote_plus
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

MALE_NAMES = [
    "Marcin", "Piotr", "Michał", "Kacper", "Jakub", "Mateusz", "Szymon",
    "Bartosz", "Dawid", "Tomasz", "Marek", "Patryk", "Adam", "Paweł", "Jan",
]
FEMALE_NAMES = [
    "Anna", "Katarzyna", "Natalia", "Julia", "Zuzanna", "Maja", "Oliwia",
    "Wiktoria", "Alicja", "Weronika", "Martyna", "Karolina", "Maria", "Amelia", "Lena",
]
MALE_SURNAMES = [
    "Tomaszewski", "Kowalski", "Nowak", "Wiśniewski", "Wójcik", "Kamiński",
    "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski",
]
FEMALE_SURNAMES = [
    "Tomaszewska", "Kowalska", "Nowak", "Wiśniewska", "Wójcik", "Kamińska",
    "Lewandowska", "Zielińska", "Szymańska", "Woźniak", "Dąbrowska", "Kozłowska",
]
WARSAW_STREETS = [
    "Marszałkowska", "Nowy Świat", "Chmielna", "Długa", "Puławska",
    "Mokotowska", "Targowa", "Jerozolimskie", "Grójecka", "Żelazna",
    "Złota", "Krucza", "Wspólna", "Hoża", "Wilcza", "Koszykowa",
    "Świętokrzyska", "Tamka", "Solec", "Ostrobramska", "Grochowska",
    "Raszyńska", "Królewska", "Aleja Jana Pawła II", "Wejherowska",
]


def generate_identity(gender_code: str) -> tuple[str, str]:
    """Choose a random Polish first name and surname for the selected gender."""
    if gender_code == "m":
        return random.choice(MALE_NAMES), random.choice(MALE_SURNAMES)
    return random.choice(FEMALE_NAMES), random.choice(FEMALE_SURNAMES)


def generate_father_name(exclude: str) -> str:
    """Choose a male father name different from the profile name."""
    available_names = [name for name in MALE_NAMES if name != exclude]
    return random.choice(available_names)


def generate_mother_name(exclude: str) -> str:
    """Choose a female mother name different from the profile name."""
    available_names = [name for name in FEMALE_NAMES if name != exclude]
    return random.choice(available_names)


def generate_mother_surname() -> str:
    """Choose a random feminine surname."""
    return random.choice(FEMALE_SURNAMES)


def generate_warsaw_address() -> str:
    """Choose a Warsaw street and a random house number."""
    street = random.choice(WARSAW_STREETS)
    house_number = random.randint(1, 200)
    return quote_plus(f"{street} {house_number}")


def get_birthday() -> str:
    """Return the date that is exactly 18 years and 2 months before today."""
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    target_month = today.month - 2
    target_year = today.year
    if target_month <= 0:
        target_month += 12
        target_year -= 1

    target_year -= 18
    target_day = min(today.day, calendar.monthrange(target_year, target_month)[1])
    birthday = date(target_year, target_month, target_day)
    birthday += timedelta(days=random.randint(-20, 20))
    return birthday.strftime("%d.%m.%Y")


def get_issue_date() -> str:
    """Return today's date minus one year with a random +/-90-day offset."""
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    try:
        issue_date = today.replace(year=today.year - 1)
    except ValueError:
        # Handle February 29 when the previous year is not a leap year.
        issue_date = today.replace(year=today.year - 1, day=28)
    issue_date += timedelta(days=random.randint(-90, 90))
    return issue_date.strftime("%d.%m.%Y")


def get_issue_expiry_date(issue_date: str) -> str:
    """Return the issue date plus exactly ten years, without an offset."""
    issue = datetime.strptime(issue_date, "%d.%m.%Y").date()
    try:
        expiry = issue.replace(year=issue.year + 10)
    except ValueError:
        # Handle February 29 when the target year is not a leap year.
        expiry = issue.replace(year=issue.year + 10, day=28)
    return expiry.strftime("%d.%m.%Y")


def get_home_date(birthday: str) -> str:
    """Return birthday plus one year with a random +/- six-month offset."""
    birth = datetime.strptime(birthday, "%d.%m.%Y").date()
    try:
        home_date = birth.replace(year=birth.year + 1)
    except ValueError:
        # Handle February 29 when the following year is not a leap year.
        home_date = birth.replace(year=birth.year + 1, day=28)
    home_date += timedelta(days=random.randint(-183, 183))
    return home_date.strftime("%d.%m.%Y")


def generate_haczyk(birthday: str) -> str:
    """Build haczyk from birthday: YY + 2 + DD + five random digits."""
    birthday_date = datetime.strptime(birthday, "%d.%m.%Y")
    random_digits = "".join(str(random.randint(0, 9)) for _ in range(5))
    return f"{birthday_date.strftime('%y')}2{birthday_date.strftime('%d')}{random_digits}"


def generate_mdow_series() -> str:
    """Return the document series prefix followed by five random digits."""
    random_digits = "".join(str(random.randint(0, 9)) for _ in range(5))
    return f"MWYC+{random_digits}"


def generate_id_series() -> str:
    """Return the ID series prefix followed by six random digits."""
    random_digits = "".join(str(random.randint(0, 9)) for _ in range(6))
    return f"VBA+{random_digits}"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new photo flow."""
    context.user_data.clear()
    await update.message.reply_text("📸 Proszę wysłać zdjęcie.")


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the Telegram photo and ask for a gender choice."""
    if not IMGBB_API_KEY:
        await update.message.reply_text(
            "Brak konfiguracji IMGBB_API_KEY. Uzupełnij plik .env."
        )
        return

    photo = update.message.photo[-1]
    telegram_file = await context.bot.get_file(photo.file_id)
    image_bytes = await telegram_file.download_as_bytearray()

    try:
        image_url = await upload_to_imgbb(bytes(image_bytes))
    except Exception:
        logger.exception("Image upload failed")
        await update.message.reply_text(
            "Nie udało się wysłać zdjęcia na hosting. Spróbuj ponownie."
        )
        return

    context.user_data["image_url"] = image_url
    keyboard = [
        [
            InlineKeyboardButton("👨 Mężczyzna", callback_data="gender:male"),
            InlineKeyboardButton("👩 Kobieta", callback_data="gender:female"),
        ]
    ]
    await update.message.reply_text(
        "⚧️ PŁEĆ:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def upload_to_imgbb(image_bytes: bytes) -> str:
    """Upload an image through ImgBB's API."""
    files = {"image": ("photo.jpg", BytesIO(image_bytes), "image/jpeg")}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files=files,
        )
        response.raise_for_status()
        payload = response.json()

    if not payload.get("success") or not payload.get("data", {}).get("url"):
        raise RuntimeError("ImgBB returned an invalid response")
    return payload["data"]["url"]


async def choose_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    gender = {
        "gender:male": ("Mężczyzna", "m"),
        "gender:female": ("Kobieta", "k"),
    }.get(query.data)
    image_url = context.user_data.get("image_url")

    if not gender or not image_url:
        await query.edit_message_text("Sesja wygasła. Wyślij /start i spróbuj ponownie.")
        return

    gender_label, gender_code = gender
    name, surname = generate_identity(gender_code)
    father_name = generate_father_name(name)
    mother_name = generate_mother_name(name)
    mothers_family_name = generate_mother_surname()
    adress1 = generate_warsaw_address()
    birthday = get_birthday()
    home_date = get_home_date(birthday)
    haczyk = generate_haczyk(birthday)
    mdow_series = generate_mdow_series()
    id_series = generate_id_series()
    id_issue_date = get_issue_date()
    id_expiry_date = get_issue_expiry_date(id_issue_date)
    profile_link = f"https://huj-xi.vercel.app/id.html?name={quote(name, safe='')}&surname={quote(surname, safe='')}&sex={gender_code}&birthday={birthday}&pesel={haczyk}&mdow_series={mdow_series}&id_series={id_series}&id_issue_date={id_issue_date}&id_expiry_date={id_expiry_date}&issue_date=27.01.2026&expiry_date=27.01.2031&father_name={quote(father_name, safe='')}&mother_name={quote(mother_name, safe='')}&nationality=POLSKIE&birthPlace=Warszawa&countryOfBirth=Polska&adress1={adress1}&adress2=03-585&city=Warszawa&home_date={home_date}&familyName={quote(surname, safe='')}&fathersFamilyName={quote(surname, safe='')}&mothersFamilyName={quote(mothers_family_name, safe='')}&image={quote(image_url, safe='')}"

    guide = (
        "Poradnik:\n\n"
        "System iOS (iPhone): 📱\n"
        "Upewnij się, że używasz przeglądarki Safari.\n"
        "Uzupełnij dane i kliknij GENERUJ.\n"
        "Na nowej stronie naciśnij ikonę Udostępnij.\n"
        "Wybierz opcję Do Ekranu głównego.\n\n"
        "System Android: 🤖\n"
        "Upewnij się, że używasz przeglądarki Chrome lub Google.\n"
        "Uzupełnij dane i kliknij GENERUJ.\n"
        "Na nowej stronie naciśnij ikonę Menu (3 kropki) w prawym górnym rogu.\n"
        "Wybierz opcję Dodaj do ekranu głównego."
    )
    keyboard = [
        [InlineKeyboardButton("🔗 LINK", url=profile_link)],
        [InlineKeyboardButton("🔄 Wygeneruj nowego kota", callback_data="new_generation")],
    ]
    await query.edit_message_text(
        guide,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data.clear()


async def new_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the flow from the inline button."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("📸 Proszę wysłać zdjęcie.")


async def unexpected_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📸 Najpierw wyślij zdjęcie. Możesz też użyć /start.")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Brak BOT_TOKEN w zmiennych środowiskowych lub pliku .env")
    if not IMGBB_API_KEY:
        raise RuntimeError("Brak IMGBB_API_KEY w zmiennych środowiskowych lub pliku .env")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, receive_photo))
    application.add_handler(CallbackQueryHandler(choose_gender, pattern=r"^gender:"))
    application.add_handler(CallbackQueryHandler(new_generation, pattern=r"^new_generation$"))
    application.add_handler(MessageHandler(~filters.COMMAND, unexpected_message))

    logger.info("Bot is running")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

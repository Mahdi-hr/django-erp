# ERP تولید — کارخانه تجهیزات فلزی

سیستم ERP حرفه‌ای برای مدیریت کارخانه تولید تجهیزات فلزی و گازی.

## ویژگی‌ها

- **مواد اولیه** — مدیریت مواد، دسته‌بندی، قیمت‌ها، تاریخچه تغییرات
- **محصولات** — BOM (لیست مواد مصرفی)، محاسبه خودکار قیمت تمام‌شده
- **تولید** — سفارشات تولید، تولید روزانه، گزارش عملکرد کارگران
- **انبار** — مدیریت موجودی، خرید، ضایعات، برگشت، آستانه کمبود
- **مشتریان** — مدیریت اطلاعات مشتریان
- **فاکتورها** — صدور فاکتور، پرداخت، مالیات، پیش‌فاکتور
- **پیامک** — ارسال پیامک (Kavenegar + SMS.ir)
- **گزارشات** — داشبورد، نمودارها، خروجی Excel/PDF
- **بکاپ** — بکاپ کامل/جزئی، بازیابی (بروزرسانی/جایگزینی)
- **آپدیت** — آپدیت خودکار از GitHub
- **تنظیمات** — تم تاریک، تاریخ شمسی، ضرایب قیمت

## نصب

```bash
# ایجاد محیط مجازی
python -m venv venv
venv\Scripts\activate  # ویندوز

# نصب وابستگی‌ها
pip install -r requirements.txt

# مایگریشن
python manage.py migrate

# کاربر ادمین
python manage.py createsuperuser

# اجرا
python manage.py runserver
```

یا فایل `run.bat` را اجرا کنید.

## ساختار پروژه

```
erp_project/          # تنظیمات Django
apps/
  common/             # ابزارها، Setting model
  users/              # کاربران و نقش‌ها
  materials/          # مواد اولیه و دسته‌بندی
  products/           # محصولات و BOM
  production/         # سفارشات و تولید روزانه
  inventory/          # انبار، خرید، ضایعات
  workers/            # کارگران
  customers/          # مشتریان
  invoices/           # فاکتورها و پرداخت
  sms/                # پیامک (Kavenegar + SMS.ir)
  reports/            # گزارشات و خروجی‌ها
  dashboard/          # داشبورد اصلی
  backup/             # بکاپ و بازیابی
  settings_app/       # تنظیمات سیستم
  updater/            # آپدیت خودکار
templates/            # تمپلیت‌ها
static/               # CSS, JS, تصاویر
```

## نقش‌ها

| نقش | دسترسی |
|-----|--------|
| admin | مدیریت کامل |
| accountant | فاکتورها و گزارشات |
| warehouse | مدیریت انبار |
| operator | ثبت تولید روزانه |
| viewer | فقط مشاهده |

## متغیرهای محیطی

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
GITHUB_REPO_URL=https://github.com/user/repo.git
KAVENEGAR_API_KEY=your-key
SMSIR_API_KEY=your-key
```

## لایسنس

MIT

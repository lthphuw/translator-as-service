# 🧠 Translator as Service

A lightweight API for translating between English and Vietnamese using pretrained models. Supports auto language detection.

![Translator as Service](images/translator-as-service.jpg)

---

## 🖼️ Demo

### 🇻🇳 Vietnamese → English
![Translate vietnamese texts to english texts](images/vi2en.png)

---

### 🇺🇸 English → Vietnamese
![Translate english texts to vietnamese](images/en2vi.png)

---

### 🌐 Auto Detect Language
You can omit the `src_lang` field — the system will detect the language automatically:

![Omit the src_lang](images/detect_lang.png)

---

## 🚀 Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python manage.py

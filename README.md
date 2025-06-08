# 🧠 Translator as Service

A lightweight API for translating between English, Vietnamese, and French using pretrained models.  
Supports auto language detection and can be easily extended to other language pairs.

![Translator as Service](images/translator-as-service_v2.png)

---

## 🌍 Supported Language Pairs

| Source | Target       |
| ------ | ------------ |
| 🇺🇸 EN  | 🇻🇳 VI, 🇫🇷 FR |
| 🇻🇳 VI  | 🇺🇸 EN, 🇫🇷 FR |
| 🇫🇷 FR  | 🇺🇸 EN, 🇻🇳 VI |

> ✅ Built-in language detection allows you to omit the `src_lang` field for most use cases.

---

## 🖼️ Demo

### 🇻🇳 Vietnamese → English

![Translate vietnamese texts to english texts](images/vi2en.png)

---

### 🇺🇸 English → Vietnamese

![Translate english texts to vietnamese](images/en2vi.png)

---

### 🇫🇷 French → Vietnamese

![Translate french texts to vietnamese](images/fr2vi.png)

---

### 🌐 Auto Detect Language

You can omit the `src_lang` field — the system will detect the language automatically:

![Omit the src_lang](images/detect_lang.png)

---

## 🔧 Easily Extensible

To add a new language pair, simply implement a new `BaseTranslator` subclass and register it in `UniversalTranslator.TRANSLATOR_FACTORIES`.

---

## 🚀 Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python manage.py
```

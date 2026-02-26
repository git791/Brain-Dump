# 📚 Study Companion — Beginner's Guide

A smart study chatbot that helps you learn topics, tracks what you know, and gives you a step-by-step plan when you're stuck.

---

## 🧠 What Does This App Do?

You type questions or topics you're studying. The app:
- Answers your questions like a tutor
- Automatically saves concepts and definitions you've learned
- Gives you a 10-minute action plan when you say "I'm stuck"
- Lets you export your notes to Markdown, Anki flashcards, or Notion

---

## 📁 What Each File Does

| File | What it is |
|------|-----------|
| `app.py` | The entire app — all the code lives here |
| `.env` | Your secret API key — never share this |
| `.gitignore` | Tells git which files to NOT upload to GitHub |
| `requirements.txt` | List of libraries the app needs to run |
| `knowledge_notes.json` | Auto-created when you run the app — stores your saved notes |

---

## ⚙️ How to Set It Up (First Time)

### Step 1 — Install Python
Download Python from https://python.org if you don't have it.

### Step 2 — Install the required libraries
Open your terminal/command prompt in the project folder and run:
```
pip install -r requirements.txt
```
This reads `requirements.txt` and installs everything the app needs.

### Step 3 — Get a Gemini API Key
1. Go to https://aistudio.google.com
2. Click "Get API Key"
3. Copy the key

### Step 4 — Add your API key
Open the `.env` file and paste your key like this:
```
GEMINI_API_KEY=paste_your_key_here
```
No quotes, no spaces around the `=`.

### Step 5 — Run the app
```
streamlit run app.py
```
A browser window will open automatically.

---

## 🧩 Code Walkthrough — Line by Line

Don't worry if you've never coded before. Think of the code as a recipe — each section does one job.

---

### 📦 Part 1 — Imports (Lines 1–9)
```python
import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
```
**What this does:** Loads all the tools the app needs.
- `streamlit` → builds the website/UI (buttons, chat boxes, sidebar)
- `google.generativeai` → connects to Google's Gemini AI
- `json` → reads and writes `.json` files (like saving your notes)
- `os` → reads your `.env` file so the API key stays secret
- `datetime` → gets today's date (used when exporting notes)
- `load_dotenv()` → loads your `.env` file so the app can see your API key

---

### ⚙️ Part 2 — Configuration (Lines 12–16)
```python
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
KNOWLEDGE_FILE = "knowledge_notes.json"
model = genai.GenerativeModel('gemini-2.5-flash-lite')
```
**What this does:**
- `os.getenv("GEMINI_API_KEY")` → reads your secret key from `.env`
- `KNOWLEDGE_FILE` → sets the filename where your notes get saved
- `model` → prepares the Gemini AI model, ready to answer questions

---

### 💾 Part 3 — Saving & Loading Notes (Lines 19–30)
```python
def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r") as f:
            return json.load(f)
    return {"chapters": {}, "concepts": [], ...}

def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump(knowledge, f, indent=2)
```
**What this does:**
- `load_knowledge()` → opens `knowledge_notes.json` and reads your saved notes. If the file doesn't exist yet, it creates an empty structure.
- `save_knowledge()` → writes your notes back to the file so they persist even after you close the app.
- Think of it like opening and saving a Word document.

---

### 🤖 Part 4 — Extracting Knowledge from Chat (Lines 32–56)
```python
def extract_takeaways(messages, chapter):
```
**What this does:** Every 3 messages, this function sends your recent conversation to Gemini and asks it: *"What concepts, definitions, and confusions appeared in this chat?"* Gemini returns the answer as JSON (structured data), which gets saved to your notes file.

- `messages[-12:]` → only looks at the last 12 messages (to stay focused)
- The `if "```json"` lines → Gemini sometimes wraps its answer in code blocks, so this strips that out before reading the data

---

### 🛤️ Part 5 — The 10-Minute Pathway (Lines 58–72)
```python
def generate_10min_pathway(confusion_points, chapter):
```
**What this does:** When you say "I'm stuck", this sends your confusion points to Gemini and asks for a specific step-by-step action plan. It returns steps like "2 min: read this", "3 min: try this example", etc.

---

### 📤 Part 6 — Export Functions (Lines 75–130)
Three functions that format your saved notes differently:
- `export_to_markdown()` → formats notes as a `.md` file
- `export_to_anki()` → formats as a `.csv` file Anki can import as flashcards
- `export_to_notion()` → formats with bullet points ready to paste into Notion

---

### 🖥️ Part 7 — The UI (Lines 133 onward)
```python
def main():
    st.set_page_config(...)
```
This is where the entire visual app is built using Streamlit.

**Sidebar:**
- Shows how many concepts and definitions you've saved
- Has buttons for New Chapter, Exam Review, and Export
- Shows your last 8 concepts and 5 definitions live

**Main chat area:**
- Displays all previous messages
- Takes your new message as input
- Decides: are you confused (→ pathway) or asking a question (→ Gemini answer)?
- Every 3 messages, quietly extracts and saves knowledge in the background

---

### 🔀 Part 8 — The Decision Logic (The Heart of the App)
```python
confused_keywords = ["stuck", "confused", "don't understand", "help", "what is", "explain"]
is_confused = any(kw in prompt.lower() for kw in confused_keywords)

if is_confused:
    # Generate 10-minute pathway
else:
    # Answer the question normally via Gemini
```
**What this does:** Checks if your message contains any "I need help" words. If yes → pathway. If no → normal tutoring answer. Simple as that.

---

## 🚀 How to Use It

1. Type the topic you're studying in the chapter title box
2. Ask questions naturally: *"What is photosynthesis?"*
3. If you're lost, type: *"I'm stuck"* or *"I don't understand"*
4. Check the sidebar to see your notes build up automatically
5. Click **📖 Review** to see everything you've learned in exam mode
6. Export when you're done studying

---

## ❓ Common Issues

| Problem | Fix |
|---------|-----|
| App won't start | Run `pip install -r requirements.txt` again |
| API key error | Check your `.env` file has no extra spaces or quotes |
| Empty responses | Make sure your Gemini API key is valid and has quota |
| Notes not saving | Make sure the app has permission to write files in the folder |

---

## 🔒 Security Note

Never share your `.env` file or upload it to GitHub. Your API key is like a password — if someone else gets it, they can use your Gemini quota. The `.gitignore` file makes sure git ignores it automatically.

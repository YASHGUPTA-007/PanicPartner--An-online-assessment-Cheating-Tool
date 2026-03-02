import pytesseract
from PIL import ImageGrab, ImageStat
import tkinter as tk
import requests
import threading
import keyboard
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Set your Tesseract path
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# API Key - loaded from .env file
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Utility Functions

def get_average_color_from_center(w=200, h=60):
    """Get average color from center of screen for popup background"""
    try:
        screen = ImageGrab.grab()
        screen_width, screen_height = screen.size
        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        cropped = screen.crop((x, y, x + w, y + h))
        stat = ImageStat.Stat(cropped)
        r, g, b = stat.mean[:3]
        return f'#{int(r):02x}{int(g):02x}{int(b):02x}'
    except Exception as e:
        print(f"⚠️ Error getting background color: {e}")
        return "#f0f0f0"

def capture_fullscreen_text():
    """Capture screen excluding bottom 30% where terminal usually sits"""
    try:
        print("📸 Capturing screen...")
        image = ImageGrab.grab()
        screen_w, screen_h = image.size
        cropped = image.crop((0, 0, screen_w, int(screen_h * 0.70)))
        print("🧠 Running OCR...")
        text = pytesseract.image_to_string(cropped, config='--psm 6 --oem 3')
        print("📄 Extracted Text:\n", text)
        return text.strip()
    except Exception as e:
        print(f"❌ Error capturing screen: {e}")
        return ""

def ask_groq(prompt, max_tokens=100):
    """Send a prompt to Groq API and return the response"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.1
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None
    return response.json()['choices'][0]['message']['content'].strip()

# Short Answer (MCQ)
def ask_short(text):
    """Get short answer from Groq for MCQ questions"""
    if not GROQ_API_KEY:
        return "❌ API key not set"

    prompt = f"""You are solving a multiple-choice question. The question text may contain OCR errors (misread characters like 'Q' instead of '9', '0' instead of 'O', etc).

Question and Options:
{text}

Rules:
- Fix any obvious OCR errors before solving (e.g. 'Q' may mean '9', 'l' may mean '1')
- Solve the question mathematically/logically yourself
- Then match your answer to the closest option
- Respond with ONLY the exact corrected option text (e.g. "9 times" or "None of the above")
- Zero explanation, zero extra words

Your answer:"""

    try:
        print("📨 Asking Groq (Short)...")
        answer = ask_groq(prompt, max_tokens=50)
        return answer if answer else "❌ No response from Groq."
    except Exception as e:
        return f"❌ Error: {e}"

# Detailed Answer
def ask_detailed(text):
    """Get detailed answer from Groq for complex questions"""
    if not GROQ_API_KEY:
        return "❌ API key not set"

    prompt = f"""You are helping with a programming or theory question.

Question:
{text}

Respond with a clear, complete answer. Include pseudocode or steps if needed.
Avoid unnecessary verbosity. Make it useful and readable."""

    try:
        print("📨 Asking Groq (Detailed)...")
        answer = ask_groq(prompt, max_tokens=500)
        return answer if answer else "❌ No response from Groq."
    except Exception as e:
        return f"❌ Error: {e}"

# Popup Functions
def show_popup(answer):
    """Show small popup for MCQ answers"""
    def display():
        try:
            x, y, w, h = 100, 170, 200, 60
            bg_color = get_average_color_from_center(w, h)

            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-alpha", 0.85)
            root.configure(background=bg_color)
            root.geometry(f"{w}x{h}+{x}+{y}")

            label = tk.Label(
                root,
                text=answer,
                font=("Segoe UI", 11),
                bg=bg_color,
                fg="black",
                wraplength=w - 20,
                justify="center"
            )
            label.pack(fill="both", expand=True)
            root.after(2500, root.destroy)
            root.mainloop()
        except Exception as e:
            print(f"❌ Error showing popup: {e}")

    threading.Thread(target=display, daemon=True).start()

def show_large_popup(answer):
    """Show large popup for detailed answers"""
    def display():
        try:
            w, h = 380, 180
            screen = ImageGrab.grab()
            cropped = screen.crop((40, 80, 40 + w, 80 + h))
            stat = ImageStat.Stat(cropped)
            r, g, b = stat.mean[:3]
            bg_color = f'#{int(r):02x}{int(g):02x}{int(b):02x}'

            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-alpha", 0.83)
            root.configure(bg=bg_color)

            screen_height = root.winfo_screenheight()
            x = 40
            y = screen_height // 4
            root.geometry(f"{w}x{h}+{x}+{y}")

            text_widget = tk.Text(root, wrap="word", bg=bg_color, fg="black", font=("Segoe UI", 9))
            text_widget.insert("1.0", answer)
            text_widget.configure(state="disabled", relief="flat")
            text_widget.pack(expand=True, fill="both", padx=8, pady=8)

            root.after(6500, root.destroy)
            root.mainloop()
        except Exception as e:
            print(f"❌ Error showing large popup: {e}")

    threading.Thread(target=display, daemon=True).start()

# Main Runner
def run_ocr_assistant():
    """Main function to run the OCR assistant"""
    print("🎧 Panic Partner Starting...")
    print("=" * 40)

    if not os.path.exists(tesseract_path):
        print("❌ CRITICAL ERROR: Tesseract OCR not found!")
        print("📥 Please install from: https://github.com/UB-Mannheim/tesseract/wiki")
        input("Press Enter to exit...")
        return

    if not GROQ_API_KEY:
        print("⚠️ WARNING: No GROQ_API_KEY set in .env file!")
        return

    print("✅ Panic Partner Ready! (Powered by Groq)")
    print("CONTROLS:")
    print("• Press Ctrl + Alt   → MCQ Answer Mode")
    print("• Press Ctrl + Shift → Detailed Answer Mode")
    print("• Press Ctrl + C     → Exit")
    print("=" * 40)

    try:
        while True:
            if keyboard.is_pressed("ctrl+alt"):
                print("\n🔍 MCQ Hotkey detected.")
                time.sleep(0.5)
                question = capture_fullscreen_text()
                if question:
                    answer = ask_short(question)
                    print("🎯 Answer:", answer)
                    show_popup(answer)
                else:
                    print("⚠️ No text found on screen.")
                time.sleep(2)

            elif keyboard.is_pressed("ctrl+shift"):
                print("\n🧠 Detailed Hotkey detected.")
                time.sleep(0.5)
                question = capture_fullscreen_text()
                if question:
                    answer = ask_detailed(question)
                    print("📝 Detailed Answer:", answer)
                    show_large_popup(answer)
                else:
                    print("⚠️ No text found on screen.")
                time.sleep(2)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n👋 OCR Assistant stopped.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

# Start the application
if __name__ == "__main__":
    run_ocr_assistant()
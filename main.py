import csv
import os
import random
import re
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


DEFAULT_KNOWLEDGE = [
    ("name", "Nova"),
    ("creator", "Your Name"),
    ("description", "A local AI assistant created for offline chat and personal automation."),
    ("skill", "chat"),
    ("skill", "memory"),
    ("skill", "simple planning"),
    ("skill", "local knowledge"),
    ("fact", "This assistant runs completely offline."),
    ("fact", "It works without internet access."),
    ("fact", "It can be extended with custom rules and logic."),
]

MEMORY_FIELDS = ["timestamp", "user", "assistant"]
MAX_HISTORY = 100


class OfflineAI:
    def __init__(self, memory_file=None, knowledge_file=None):
        self.memory_file = memory_file or os.path.join(BASE_DIR, "memory.csv")
        self.knowledge_file = knowledge_file or os.path.join(BASE_DIR, "knowledge.csv")

        rows = self.load_knowledge()
        self.name = next((v for k, v in rows if k == "name"), "Nova")
        self.skills = [v for k, v in rows if k == "skill"] or ["chat"]
        self.facts = [v for k, v in rows if k == "fact"]
        self.chat_history = self.load_memory()

    # ---------- CSV storage ----------
    def load_knowledge(self):
        if not os.path.exists(self.knowledge_file):
            with open(self.knowledge_file, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["type", "value"])
                w.writerows(DEFAULT_KNOWLEDGE)
            return list(DEFAULT_KNOWLEDGE)
        with open(self.knowledge_file, "r", newline="", encoding="utf-8") as f:
            return [(r["type"].strip().lower(), r["value"]) for r in csv.DictReader(f)
                    if r.get("type") and r.get("value")]

    def load_memory(self):
        if not os.path.exists(self.memory_file):
            self.save_memory([])
            return []
        with open(self.memory_file, "r", newline="", encoding="utf-8") as f:
            return [dict(r) for r in csv.DictReader(f)][-MAX_HISTORY:]

    def save_memory(self, history=None):
        if history is None:
            history = self.chat_history
        with open(self.memory_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=MEMORY_FIELDS)
            w.writeheader()
            w.writerows(history)

    def add_memory(self, user_input, reply):
        self.chat_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "assistant": reply,
        })
        self.chat_history = self.chat_history[-MAX_HISTORY:]
        self.save_memory()

    def clear_memory(self):
        self.chat_history = []
        self.save_memory()

    # ---------- Logic ----------
    @staticmethod
    def normalize(text):
        return re.sub(r"\s+", " ", text.strip().lower())

    def intro(self):
        return (
            f"Hello! I am {self.name}, your offline AI assistant. "
            "I work without internet, API keys, or cloud services. "
            "Type /help to see commands."
        )

    def help_text(self):
        return (
            "Commands:\n"
            "- /help: show this help\n"
            "- /memory: show recent conversation memory\n"
            "- /clear: clear memory\n"
            "- /save: save current chat memory\n"
            "- /exit: quit the app\n"
            "\nYou can also just chat naturally."
        )

    def is_exit(self, text):
        return self.normalize(text) in ["/exit", "exit", "quit", "bye", "goodbye"]

    def respond(self, user_input):
        text = user_input.strip()
        if not text:
            return "Please say something."
        n = self.normalize(text)

        if self.is_exit(text):
            return "Goodbye! See you later."
        if n in ["/help", "help", "what can you do"]:
            return self.help_text()
        if n in ["/memory", "memory"]:
            if not self.chat_history:
                return "I do not have any saved memory yet."
            return "\n\n".join(f"You: {e['user']}\nAI: {e['assistant']}"
                               for e in self.chat_history[-5:])
        if n in ["/clear", "clear memory"]:
            self.clear_memory()
            return "Conversation memory has been cleared."
        if n in ["/save", "save"]:
            self.save_memory()
            return "Memory saved."
        if n in ["hello", "hi", "hey"]:
            return "Hello! How can I help you today?"
        if "your name" in n or "who are you" in n:
            return f"I am {self.name}, your offline AI assistant."
        if "time" in n:
            return f"The current time is {datetime.now().strftime('%H:%M:%S')}."
        if "date" in n:
            return f"Today is {datetime.now().strftime('%Y-%m-%d')}."
        if "joke" in n:
            return random.choice([
                "Why did the computer go to therapy? It had too many bytes of emotional baggage.",
                "I used to be a programmer, but now I just code at night.",
                "Why do programmers prefer dark mode? Because light attracts bugs.",
            ])
        if "offline" in n or "local" in n:
            return "Yes — I run entirely on your computer without internet, APIs, or cloud services."
        if "remember" in n:
            return "I can remember recent conversation history in my local memory file."
        for fact in self.facts:
            if fact.lower() in n or n in fact.lower():
                return fact
        if "thank" in n:
            return "You’re welcome. I’m here to help."
        if "how are you" in n:
            return "I’m doing well. Running locally and ready to help."
        return (
            f"I’m {self.name}, and I’m designed to help you locally. "
            "I can answer simple questions, remember chat, and be extended with your own rules."
        )


class ChatApp:
    def __init__(self, root):
        self.ai = OfflineAI()
        self.root = root
        root.title(f"{self.ai.name} - Offline AI Assistant")
        root.geometry("640x520")

        self.chat = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled",
                                              font=("Segoe UI", 10))
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))
        self.chat.tag_config("user", foreground="#1a5fb4")
        self.chat.tag_config("ai", foreground="#26a269")

        bar = tk.Frame(root)
        bar.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.entry = tk.Entry(bar, font=("Segoe UI", 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind("<Return>", lambda e: self.send())
        tk.Button(bar, text="Send", command=self.send, width=8).pack(side=tk.LEFT, padx=(6, 0))
        tk.Button(bar, text="Clear", command=self.clear, width=8).pack(side=tk.LEFT, padx=(6, 0))

        self.append("AI", self.ai.intro(), "ai")
        self.entry.focus_set()

    def append(self, who, text, tag):
        self.chat.config(state="normal")
        self.chat.insert(tk.END, f"{who}: ", tag)
        self.chat.insert(tk.END, text + "\n\n")
        self.chat.config(state="disabled")
        self.chat.see(tk.END)

    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.append("You", text, "user")
        reply = self.ai.respond(text)
        self.append("AI", reply, "ai")
        if self.ai.is_exit(text):
            self.root.after(600, self.root.destroy)
            return
        if self.ai.normalize(text) not in ["/clear", "clear memory"]:
            self.ai.add_memory(text, reply)

    def clear(self):
        self.ai.clear_memory()
        self.chat.config(state="normal")
        self.chat.delete("1.0", tk.END)
        self.chat.config(state="disabled")
        self.append("AI", "Conversation memory has been cleared.", "ai")


def main():
    root = tk.Tk()
    ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

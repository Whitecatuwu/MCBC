import tkinter as tk
import threading
import asyncio
import sys
import re
from func.init import init
from os import path as os_path
from time import time as current_time

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))

update_older: callable
update_newer: callable
update_older, update_newer = init(CURRENT_DIR)


class TextRedirector:
    ANSI_PATTERN = re.compile(r"\033\[(\d+)(;\d+)*m")
    ANSI_TAGS = {
        "0": "reset",
        "1": "bold",
        "90": "grey",
        "91": "red",
        "92": "green",
        "93": "yellow",
        "94": "blue",
        "95": "purple",
        "96": "cyan",
        "97": "white",
        "38;5;214": "orange",
    }

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self._setup_tags()

    def write(self, msg):
        self.text_widget.after(0, self._write_gui_safe, msg)

    def flush(self):
        pass

    def _setup_tags(self):
        self.text_widget.tag_config("bold", font=("Consolas", 12, "bold"))
        self.text_widget.tag_config("grey", foreground="#888888")
        self.text_widget.tag_config("red", foreground="red")
        self.text_widget.tag_config("green", foreground="green")
        self.text_widget.tag_config("yellow", foreground="yellow")
        self.text_widget.tag_config("blue", foreground="blue")
        self.text_widget.tag_config("purple", foreground="purple")
        self.text_widget.tag_config("cyan", foreground="cyan")
        self.text_widget.tag_config("white", foreground="#f0f0f0")
        self.text_widget.tag_config("orange", foreground="orange")
        self.text_widget.tag_config(
            "reset", foreground="white", font=("Consolas", 12, "normal")
        )

    def _write_gui_safe(self, msg):
        self.text_widget.config(state="normal")
        for text, tags in self._parse_ansi(msg):
            self.text_widget.insert(tk.END, text, tags)

        self.text_widget.see(tk.END)
        self.text_widget.config(state="disabled")

    def _parse_ansi(self, msg):
        parts = []
        last_end = 0
        active_tags = []

        for match in self.ANSI_PATTERN.finditer(msg):
            start, end = match.span()
            if start > last_end:
                parts.append((msg[last_end:start], active_tags.copy()))

            codes = match.group(0)[2:-1].split(";")
            for code in codes:
                if code == "0":
                    active_tags.clear()
                elif code in self.ANSI_TAGS:
                    tag = self.ANSI_TAGS[code]
                    if tag not in active_tags:
                        active_tags.append(tag)
            last_end = end

        if last_end < len(msg):
            parts.append((msg[last_end:], active_tags.copy()))
        return parts


async def async_task():
    update_older()
    update_newer()


def run_task():
    button.config(state="disabled")

    def worker():
        start_time = current_time()
        asyncio.run(async_task())
        print("\nFinish.")
        print("runtime: %s seconds" % (current_time() - start_time))
        window.after(0, lambda: button.config(state="normal"))

    threading.Thread(target=worker).start()


window = tk.Tk()
window.title("GUI")
window.geometry("640x640")
window.configure(bg="#2f2f2f")

button = tk.Button(window, width=40, text="Run", command=run_task)
button.pack(pady=5)

output_text = tk.Text(
    window,
    height=30,
    width=80,
    state="disabled",
    bg="#171717",
    fg="#e0e0e0",
    font=("Consolas", 12),
)
output_text.pack(padx=10, pady=10)

sys.stdout = TextRedirector(output_text)

window.mainloop()

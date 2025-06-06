import tkinter as tk
import threading
import asyncio
import sys

from func.init import init
from func.gui.TextRedirector import TextRedirector
from os import path as os_path
from time import time as current_time

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))

update_older: callable
update_newer: callable
update_older, update_newer = init(CURRENT_DIR)


async def async_task():
    update_older()
    update_newer()


def run_task():
    run_button.config(state="disabled")

    def worker():
        start_time = current_time()
        asyncio.run(async_task())
        print("\nFinish.")
        print("runtime: %s seconds" % (current_time() - start_time))
        window.after(0, lambda: run_button.config(state="normal"))

    threading.Thread(target=worker).start()


window = tk.Tk()
window.title("GUI")
window.geometry("1280x640")
window.configure(bg="#2f2f2f")

frame = tk.Frame(window)
frame.configure(bg="#2f2f2f")
frame.pack(pady=10)

label = tk.Label(frame, text="Filter", font=("Consolas", 14, "bold"), fg="#e0e0e0")
label.configure(bg="#2f2f2f")
label.pack(side="left")

search_entry = tk.Entry(frame)
search_entry.bind("<KeyRelease>", lambda _: redirector.filter(search_entry.get()))
search_entry.pack(side="left", padx=20, ipady=5)

run_button = tk.Button(frame, width=40, text="Run", command=run_task)
run_button.pack(side="left", padx=20)

output_text = tk.Text(
    window,
    height=50,
    width=200,
    state="disabled",
    bg="#171717",
    fg="#e0e0e0",
    font=("Consolas", 12),
)
output_text.pack(padx=10, pady=10)
redirector = TextRedirector(output_text)

sys.stdout = redirector
window.mainloop()

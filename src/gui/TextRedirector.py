import re


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
        self.log_buffer: list[str] = []

    def write(self, msg: str):
        if msg == "\n":
            return
        msgs: list = msg.split("\n")
        self.log_buffer.extend(msgs)
        for msg in msgs:
            self.text_widget.after(0, self._write_gui_safe, msg + "\n")

    def filter(self, keyword):
        self.text_widget.after(0, self._filter, keyword)

    def flush(self):
        pass

    def _filter(self, keyword):
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        generator = (
            (text, tags)
            for msg in self.log_buffer
            for text, tags in self._parse_ansi(msg)
        )

        for text, tags in generator:
            if keyword.lower() not in text.lower():
                continue
            self.text_widget.insert("end", text + "\n", tags)

        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def _setup_tags(self):
        self.text_widget.tag_config("bold", font=("Consolas", 12, "bold"))
        self.text_widget.tag_config("grey", foreground="#888888")
        self.text_widget.tag_config("red", foreground="red")
        self.text_widget.tag_config("green", foreground="green")
        self.text_widget.tag_config("yellow", foreground="yellow")
        self.text_widget.tag_config("blue", foreground="blue")
        self.text_widget.tag_config("purple", foreground="#c155c1")
        self.text_widget.tag_config("cyan", foreground="cyan")
        self.text_widget.tag_config("white", foreground="#f0f0f0")
        self.text_widget.tag_config("orange", foreground="orange")
        self.text_widget.tag_config(
            "reset", foreground="white", font=("Consolas", 12, "normal")
        )

    def _write_gui_safe(self, msg):
        self.text_widget.config(state="normal")
        for text, tags in self._parse_ansi(msg):
            self.text_widget.insert("end", text, tags)

        self.text_widget.see("end")
        self.text_widget.config(state="disabled")

    def _parse_ansi(self, msg):
        if msg == "":
            return [["", []]]

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

import tkinter as tk
import logging

class TextHandler(logging.Handler):
    """自定义日志处理器，将日志消息重定向到Tkinter Text控件。"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.configure(state='disabled')

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

import tkinter as tk
from InsightLabelmeMain import YoloAnnotator

if __name__ == '__main__':
    root = tk.Tk()
    app = YoloAnnotator(root)
    root.mainloop()

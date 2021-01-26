from tkinter import Tk
import os


def main():
    root = Tk()
    root.wm_title("Test Program")
    root.mainloop()

    print(os.getcwd())

import tkinter as tk
from tkinter import ttk
import threading
from utils import *


class Monitor(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.geometry("300x300")
        self.root.title("Status window")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.resizable(0, 0)

        # configure the grid
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)

        self.label_0 = tk.StringVar()
        self.label_0.set('Mode')
        self.l_0 = ttk.Label(self.root, textvariable=self.label_0)
        self.l_0.grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)

        self.info_0 = tk.StringVar()
        self.info_0.set('---')
        self.i_0 = ttk.Label(self.root, textvariable=self.info_0)
        self.i_0.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)

        self.label_1 = tk.StringVar()
        self.label_1.set('Current Row')
        self.l_l = ttk.Label(self.root, textvariable=self.label_1)
        self.l_l.grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)

        self.info_1 = tk.StringVar()
        self.info_1.set('---')
        self.i_1 = ttk.Label(self.root, textvariable=self.info_1)
        self.i_1.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)

        self.label_2 = tk.StringVar()
        self.label_2.set('Current Column')
        self.l_2 = ttk.Label(self.root, textvariable=self.label_2)
        self.l_2.grid(column=0, row=2, sticky=tk.W, padx=5, pady=5)

        self.info_2 = tk.StringVar()
        self.info_2.set('---')
        self.i_2 = ttk.Label(self.root, textvariable=self.info_2)
        self.i_2.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)

        self.label_3 = tk.StringVar()
        self.label_3.set('Current keyboard function')
        self.l_3 = ttk.Label(self.root, textvariable=self.label_3)
        self.l_3.grid(column=0, row=3, sticky=tk.W, padx=5, pady=5)

        self.info_3 = tk.StringVar()
        self.info_3.set('---')
        self.i_3 = ttk.Label(self.root, textvariable=self.info_3)
        self.i_3.grid(column=1, row=3, sticky=tk.W, padx=5, pady=5)

        self.label_4 = tk.StringVar()
        self.label_4.set('Current Level')
        self.l_4 = ttk.Label(self.root, textvariable=self.label_4)
        self.l_4.grid(column=0, row=4, sticky=tk.W, padx=5, pady=5)

        self.info_4 = tk.StringVar()
        self.info_4.set('---')
        self.i_4 = ttk.Label(self.root, textvariable=self.info_4)
        self.i_4.grid(column=1, row=4, sticky=tk.W, padx=5, pady=5)

        self.label_5 = tk.StringVar()
        self.label_5.set('Current Mass')
        self.l_5 = ttk.Label(self.root, textvariable=self.label_5)
        self.l_5.grid(column=0, row=5, sticky=tk.W, padx=5, pady=5)

        self.info_5 = tk.StringVar()
        self.info_5.set('---')
        self.i_5 = ttk.Label(self.root, textvariable=self.info_5)
        self.i_5.grid(column=1, row=5, sticky=tk.W, padx=5, pady=5)


        self.root.mainloop()


    def end_monitor(self):
        print('Close the monitor...')
        self.root.quit()

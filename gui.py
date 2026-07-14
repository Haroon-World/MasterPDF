from constant import *
from pdf_operations import *
import tkinter as tk
from tkinter import filedialog


class PDFMasterGUI:

    def __init__(self):
        self.window = None
        self.selected_files = []

        self.create_window()
        self.create_header()
        self.create_buttons()
        self.create_statusbar()

    # ==========================
    # Window
    # ==========================
    def create_window(self):
        self.window = tk.Tk()
        self.window.title(f"{APPNAME} v{VERSION}")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.resizable(False, False)

    # ==========================
    # Header
    # ==========================
    def create_header(self):

        header_frame = tk.Frame(self.window, bg="#d32f2f")
        header_frame.pack(fill="x")

        title = tk.Label(
            header_frame,
            text=APPNAME,
            bg="#d32f2f",
            fg="white",
            font=("Arial", 28, "bold")
        )
        title.pack(pady=(15, 5))

        subtitle = tk.Label(
            header_frame,
            text="All-in-One PDF Utility Suite",
            bg="#d32f2f",
            fg="white",
            font=("Arial", 12)
        )
        subtitle.pack(pady=(0, 15))

    # ==========================
    # Buttons
    # ==========================
    def create_buttons(self):

        content_frame = tk.Frame(self.window, bg="white")
        content_frame.pack(fill="both", expand=True)

        # Select PDF Button
        select_btn = tk.Button(
            content_frame,
            text="📄 Select PDF Files",
            bg="#e53935",
            fg="white",
            font=("Arial", 14, "bold"),
            width=25,
            height=2,
            command=self.select_pdf
        )
        select_btn.pack(pady=20)

        # Selected Files List
        self.file_list = tk.Listbox(
            content_frame,
            width=90,
            height=6
        )
        self.file_list.pack(pady=10)

        # Tool Buttons Frame
        tools_frame = tk.Frame(content_frame, bg="white")
        tools_frame.pack(pady=20)

        merge_btn = tk.Button(
            tools_frame,
            text="Merge PDF",
            width=18,
            bg="blue",
            command=self.merge_pdf
        )

        split_btn = tk.Button(
            tools_frame,
            text="Split PDF",
            width=18,
            command=self.split_pdf
        )

        protect_btn = tk.Button(
            tools_frame,
            text="Protect PDF",
            width=18,
            command=self.protect_pdf
        )

        extract_btn = tk.Button(
            tools_frame,
            text="Extract Pages",
            width=18,
            command=self.extract_pages
        )

        info_btn = tk.Button(
            tools_frame,
            text="PDF Info",
            width=18,
            command=self.pdf_info
        )

        history_btn = tk.Button(
            tools_frame,
            text="History",
            width=18,
            command=self.history
        )

        # First Row
        merge_btn.grid(row=0, column=0, padx=10, pady=10)
        split_btn.grid(row=0, column=1, padx=10, pady=10)
        protect_btn.grid(row=0, column=2, padx=10, pady=10)

        # Second Row
        extract_btn.grid(row=1, column=0, padx=10, pady=10)
        info_btn.grid(row=1, column=1, padx=10, pady=10)
        history_btn.grid(row=1, column=2, padx=10, pady=10)

    # ==========================
    # Select PDF
    # ==========================
    def select_pdf(self):

        self.selected_files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf")]
        )

        self.file_list.delete(0, tk.END)

        for file in self.selected_files:
            self.file_list.insert(tk.END, file)

        count = len(self.selected_files)

        self.status.config(
            text=f"Status : {count} PDF(s) Selected"
        )

    # ==========================
    # Tool Functions
    # ==========================
    def merge_pdf(self):
        MergePDF(self.selected_files)

    def split_pdf(self):
        SplitPDF(self.selected_files)

    def protect_pdf(self):
        ProtectPDF(self.selected_files)

    def extract_pages(self):
        ExtractPages(self.selected_files)

    def pdf_info(self):
        InfoPDF(self.selected_files)

    def history(self):
        ShowHistory()

    # ==========================
    # Status Bar
    # ==========================
    def create_statusbar(self):

        self.status = tk.Label(
            self.window,
            text="Status : Ready",
            anchor="w",
            bg="lightgray"
        )

        self.status.pack(
            side="bottom",
            fill="x"
        )

    # ==========================
    # Run Application
    # ==========================
    def run(self):
        self.window.mainloop()
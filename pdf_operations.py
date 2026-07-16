from pypdf import PdfReader, PdfWriter
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime


# ==========================================
# Merge PDF
# ==========================================
def MergePDF(files):

    if not files:
        messagebox.showwarning(
            "PDFMaster",
            "Please select PDF files first."
        )
        return

    writer = PdfWriter()

    try:
        for file in files:
            reader = PdfReader(file)

            # Add every page to the new PDF
            for page in reader.pages:
                writer.add_page(page)

        save_path = filedialog.asksaveasfilename(
            title="Save Merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not save_path:
            return

        # Save merged PDF
        with open(save_path, "wb") as output_file:
            writer.write(output_file)

        writer.close()

        # Save operation history
        SaveHistory("Merge PDF", files)

        messagebox.showinfo(
            "Success",
            "PDFs merged successfully!"
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            str(e)
        )


# ==========================================
# Split PDF
# ==========================================
import tkinter as tk

def SplitPDF(files):

    if not files:
        messagebox.showwarning(
            "PDFMaster",
            "Please select one PDF first."
        )
        return

    pdf_file = files[0]

    try:
        reader = PdfReader(pdf_file)
        total_pages = len(reader.pages)

        root_win = tk._default_root

        start_page = simpledialog.askinteger(
            "Split PDF",
            f"Enter Start Page (1-{total_pages})",
            parent=root_win
        )

        if start_page is None:
            return

        end_page = simpledialog.askinteger(
            "Split PDF",
            f"Enter End Page ({start_page}-{total_pages})",
            parent=root_win
        )

        if end_page is None:
            return

        if (
            start_page < 1 or
            end_page > total_pages or
            start_page > end_page
        ):
            messagebox.showwarning(
                "PDFMaster",
                "Invalid page range.",
                parent=root_win
            )
            return

        writer = PdfWriter()

        for page in range(start_page - 1, end_page):
            writer.add_page(reader.pages[page])

        save_path = filedialog.asksaveasfilename(
            title="Save Split PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            parent=root_win
        )

        if not save_path:
            return

        with open(save_path, "wb") as output_file:
            writer.write(output_file)

        writer.close()

        SaveHistory(
            f"Split PDF ({start_page}-{end_page})",
            [pdf_file]
        )

        messagebox.showinfo(
            "Success",
            "PDF split successfully!",
            parent=root_win
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            str(e),
            parent=tk._default_root
        )

# ==========================================
# Protect PDF
# ==========================================
def ProtectPDF(files):

    if not files:
        messagebox.showwarning(
            "PDFMaster",
            "Please select a PDF first."
        )
        return

    pdf_file = files[0]

    try:

        password = simpledialog.askstring(
            "Protect PDF",
            "Enter password:",
            show="*"
        )

        if not password:
            return

        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)

        # Encrypt PDF
        writer.encrypt(password)

        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            title="Save Protected PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not save_path:
            return

        # Save protected PDF
        with open(save_path, "wb") as output_file:
            writer.write(output_file)

        writer.close()

        SaveHistory("Protect PDF", [pdf_file])

        messagebox.showinfo(
            "Success",
            "PDF protected successfully!"
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            str(e)
        )
def ExtractPages(files):

    if not files:
        messagebox.showwarning(
            "PDFMaster",
            "Please select a PDF first."
        )
        return

    pdf_file = files[0]

    try:

        reader = PdfReader(pdf_file)

        total_pages = len(reader.pages)

        page_numbers = simpledialog.askstring(
            "Extract Pages",
            f"Enter page numbers (1-{total_pages})\nExample: 1,3,5"
        )

        if not page_numbers:
            return

        writer = PdfWriter()
        
        # Parse both commas and hyphens safely
        for part in page_numbers.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                pages = range(int(start), int(end) + 1)
            else:
                pages = [int(part)]
                
            for page in pages:
                if 1 <= page <= total_pages:
                    writer.add_page(reader.pages[page - 1])

            if len(writer.pages) == 0:
                messagebox.showwarning(
                    "PDFMaster",
                    "No valid pages selected."
                )
                return

        save_path = filedialog.asksaveasfilename(
            title="Save Extracted PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not save_path:
            return
        with open(save_path, "wb") as output_file:
            writer.write(output_file)

        writer.close()

        SaveHistory("Extract Pages", [pdf_file])

        messagebox.showinfo(
            "Success",
            "Pages extracted successfully!"
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            str(e)
        )

# ==========================================
# PDF Information
# ==========================================
def InfoPDF(files):

    if not files:
        messagebox.showwarning(
            "PDFMaster",
            "Please select a PDF first."
        )
        return

    try:
        reader = PdfReader(files[0])

        pages = len(reader.pages)

        messagebox.showinfo(
            "PDF Information",
            f"File: {basename(files[0])}\n\nTotal Pages: {pages}"
        )

    except Exception as e:
        messagebox.showerror(
            "Error",
            str(e)
        )

from os.path import basename

def SaveHistory(operation, files):
    try:
        with open("history.txt", "a", encoding="utf-8") as history:

            history.write("=" * 50 + "\n")
            history.write(f"Operation : {operation}\n")
            history.write(
                f"Date : {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n\n"
            )

            history.write("Files:\n")

            for file in files:
                history.write(f"{basename(file)}\n")

            history.write("\n")
    except Exception:
        pass
        
# History
def ShowHistory():
    try:
        with open("history.txt", "r", encoding="utf-8") as history:
            data = history.read()

        if not data.strip():
            data = "No history available."
            messagebox.showinfo("History", data, parent=tk._default_root)
            return

        # Pop-up 
        choice = messagebox.askyesno(
            "History Log",
            f"{data}\n\nDo you want to clear all history?",
            parent=tk._default_root
        )
#History Clearance
        if choice:
            with open("history.txt", "w", encoding="utf-8") as history:
                history.write("")
            messagebox.showinfo("Success", "History cleared!", parent=tk._default_root)

    except FileNotFoundError:
        messagebox.showinfo("History", "No history available.", parent=tk._default_root)

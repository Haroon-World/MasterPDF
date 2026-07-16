from constant import *
from pdf_operations import *
import tkinter as tk
from tkinter import filedialog
import fitz
import os
from PIL import Image, ImageTk


class PDFMasterGUI:

    def __init__(self):
        self.window = None
        self.selected_files = []
        self.selected_file_set = set()


        self.pdf_document = None
        self.current_page = 0
        self.preview_image = None

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
        self.window.resizable(True, True)

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

    def create_preview(self):

        preview_frame = tk.Frame(
            self.preview_parent,
            width=220,
            height=300,
            bg="white",
            relief="solid",
            bd=1
        )
        preview_frame.pack()
        preview_frame.pack_propagate(False)

        self.preview_label = tk.Label(
            preview_frame,
            bg="#dfd9d9",
            text="No PDF Selected"
        )
        self.preview_label.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        nav = tk.Frame(
            self.preview_parent, 
            bg="white"
        )
        nav.pack(pady=10)

        self.prev_btn = tk.Button(
            nav,
            text="◀ Previous",
            width=12,
            command=self.previous_page
        )

        self.prev_btn.grid(row=0,column=0,padx=10)

        self.page_label = tk.Label(
            nav,
            text="Page 0 / 0",
            bg="white",
            font=("Arial",10,"bold")
        )

        self.page_label.grid(row=0,column=1,padx=10)

        self.next_btn = tk.Button(
            nav,
            text="Next ▶",
            width=12,
            command=self.next_page
        )

        self.next_btn.grid(row=0,column=2,padx=10)

        self.prev_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)

    # ==========================
    # Buttons
    # ==========================

    def create_buttons(self):

        self.content_frame = tk.Frame(self.window, bg="white")
        self.content_frame.pack(fill="both", expand=True)

        # =========================
        # Select Button
        # =========================
        select_btn = tk.Button(
            self.content_frame,
            text="📄 Select PDF Files",
            bg="#e53935",
            fg="white",
            font=("Arial",14,"bold"),
            width=25,
            height=2,
            cursor="hand2",
            command=self.select_pdf
        )

        select_btn.pack(pady=(15,5))

        # =========================
        # Main Area
        # =========================
        main_frame = tk.Frame(self.content_frame,bg="white")
        main_frame.pack(expand=True,fill="both", pady=(5, 10)) 
        main_frame.grid_columnconfigure(0, weight=1) # Left Preview Column
        main_frame.grid_columnconfigure(1, weight=1) # Right Tools Column


        # LEFT COLUMN
        left_frame = tk.Frame(main_frame,bg="white")
        left_frame.grid(row=0,column=0,padx=20,sticky="e")

        self.preview_parent = left_frame
        self.create_preview()

        # RIGHT COLUMN
        right_frame = tk.Frame(main_frame,bg="white")
        right_frame.grid(row=0,column=1,padx=30,sticky="w")

        tk.Label(
            right_frame,
            text="Selected Files",
            bg="white",
            font=("Arial",12,"bold")
        ).pack(anchor="w")

        self.file_list = tk.Listbox(
            right_frame,
            width=52,
            height=5
        )

        self.file_list.pack(pady=(5,20), anchor="w")

        self.file_list.bind(
            "<<ListboxSelect>>",
            self.on_file_select
        )

       



        tools_frame = tk.Frame(right_frame,bg="white")
        tools_frame.pack()

        merge_btn = tk.Button(tools_frame,text="📑 Merge",width=16,height=2,bg="#ff0000",fg="black",cursor="hand2",command=self.merge_pdf)
        split_btn = tk.Button(tools_frame,text="✂ Split",width=16,height=2,bg="#f5f5f5",fg="black",cursor="hand2",command=self.split_pdf)
        protect_btn = tk.Button(tools_frame,text="🔒 Protect",width=16,height=2,bg="#f5f5f5",fg="black",cursor="hand2",command=self.protect_pdf)
        extract_btn = tk.Button(tools_frame,text="📄 Extract",width=16,height=2,bg="#f5f5f5",fg="black",cursor="hand2",command=self.extract_pages)
        info_btn = tk.Button(tools_frame,text="ℹ️ Info",width=16,height=2,bg="#f5f5f5",fg="black",cursor="hand2",command=self.pdf_info)
        history_btn = tk.Button(tools_frame,text="🕘 History",width=16,height=2,bg="#f5f5f5",fg="black",cursor="hand2",command=self.history)

        merge_btn.grid(row=0,column=0,padx=8,pady=8)
        split_btn.grid(row=0,column=1,padx=8,pady=8)
        protect_btn.grid(row=0,column=2,padx=8,pady=8)

        extract_btn.grid(row=1,column=0,padx=8,pady=8)
        info_btn.grid(row=1,column=1,padx=8,pady=8)
        history_btn.grid(row=1,column=2,padx=8,pady=8)

        remove_frame = tk.Frame(
        right_frame,
        bg="white"
        )
        remove_frame.pack(pady=(0,20))

        # 1. Variable 'remove_btn' 
        remove_btn = tk.Button(
            remove_frame,
            text="Remove Selected",
            width=16,
            bg="#f5f5f5",           
            fg="black",
            cursor="hand2",
            command=self.remove_selected
        )
        remove_btn.grid(row=0,column=0,padx=5)

        # 2. Variable 'clear_btn' 
        clear_btn = tk.Button(
            remove_frame,
            text="Clear All",
            width=16,
            bg="#f5f5f5",         
            fg="black",
            cursor="hand2",
            command=self.clear_all
        )
        clear_btn.grid(row=0,column=1,padx=5)
        

        # Hover effect
        def apply_hover_effect(button, normal_bg, hover_bg):
            button.bind("<Enter>", lambda e: button.config(bg=hover_bg))
            button.bind("<Leave>", lambda e: button.config(bg=normal_bg))

       
        apply_hover_effect(merge_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(split_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(protect_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(extract_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(info_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(history_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(remove_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(clear_btn, "#f5f5f5", "#00bce2")
        apply_hover_effect(select_btn, "#da3330", "#ce0505") # Main red button


# ==========================
# Select PDF
# ==========================
    def select_pdf(self):

        files = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not files:
            return

        # Add only new files
        for file in files:
            if file not in self.selected_file_set:
                self.selected_files.append(file)
                self.selected_file_set.add(file)

        # Refresh Listbox
        self.file_list.delete(0, tk.END)

        for file in self.selected_files:
            self.file_list.insert(tk.END, os.path.basename(file))

        self.status.config(
            text=f"Status : {len(self.selected_files)} PDF(s) Selected"
        )

    # Show preview of first PDF only
        if self.selected_files:

            if self.pdf_document is not None:
                self.pdf_document.close()

            self.file_list.selection_clear(0, tk.END)
            last_index = len(self.selected_files) - 1

            self.file_list.selection_set(last_index)
            self.file_list.activate(last_index)
            self.file_list.see(last_index)

            self.pdf_document = fitz.open(files[-1])
            self.current_page = 0
            self.show_page()


    def on_file_select(self, event):

        selection = self.file_list.curselection()

        if not selection:
            return

        index = selection[0]

        if self.pdf_document is not None:
            self.pdf_document.close()

        self.pdf_document = fitz.open(
            self.selected_files[index]
        )

        self.current_page = 0

        self.show_page()


    def remove_selected(self):

        selection = self.file_list.curselection()

        if not selection:
            return

        index = selection[0]

        removed = self.selected_files.pop(index)
        self.selected_file_set.remove(removed)

        self.file_list.delete(index)

        if not self.selected_files:

            if self.pdf_document:
                self.pdf_document.close()
                self.pdf_document = None

            self.preview_label.config(image="", text="No PDF Selected")
            self.page_label.config(text="Page 0 / 0")
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)

            self.status.config(text="Status : Ready")
            return

        # If removed selected file, show another file
        new_index = min(index, len(self.selected_files) - 1)

        self.file_list.selection_clear(0, tk.END)
        self.file_list.selection_set(new_index)
        self.file_list.activate(new_index)
        self.file_list.see(new_index)

        if self.pdf_document:
            self.pdf_document.close()

        self.pdf_document = fitz.open(self.selected_files[new_index])
        self.current_page = 0
        self.show_page()

        self.status.config(
            text=f"Status : {len(self.selected_files)} PDF(s) Selected"
        )

    def clear_all(self):

        self.selected_files.clear()
        self.selected_file_set.clear()

        self.file_list.delete(0, tk.END)

        if self.pdf_document:

            self.pdf_document.close()
            self.pdf_document = None

        self.preview_label.config(
            image="",
            text="No PDF Selected"
        )

        self.page_label.config(text="Page 0 / 0")

        self.prev_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)

        self.status.config(text="Status : Ready")



    
# ==========================
# Show Page
# ==========================
    def show_page(self):

        if self.pdf_document is None:
            return

        page = self.pdf_document.load_page(self.current_page)

        pix = page.get_pixmap(matrix=fitz.Matrix(.35,.35))

        mode = "RGBA" if pix.alpha else "RGB"

        image = Image.frombytes(
            mode,
            (pix.width, pix.height),
            pix.samples
        )

        frame_width = 400
        frame_height = 500

        image.thumbnail((frame_width, frame_height), Image.LANCZOS)

        self.preview_image = ImageTk.PhotoImage(image)

        self.preview_label.config(
            image=self.preview_image,
            text="",
            anchor="center"
        )

        self.page_label.config(
            text=f"Page {self.current_page + 1} / {len(self.pdf_document)}"
        )

        self.update_navigation_buttons()

# ==========================
# Previous Page
# ==========================
    def previous_page(self):

        if self.pdf_document is None:
            return

        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()

# ==========================
# Next Page
# ==========================
    def next_page(self):

        if self.pdf_document is None:
            return

        if self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.show_page()


# ==========================
# Update Navigation Buttons
# ==========================
    def update_navigation_buttons(self):

        if self.pdf_document is None:
            return

        if self.current_page == 0:
            self.prev_btn.config(state=tk.DISABLED)
        else:
            self.prev_btn.config(state=tk.NORMAL)

        if self.current_page == len(self.pdf_document) - 1:
            self.next_btn.config(state=tk.DISABLED)
        else:
            self.next_btn.config(state=tk.NORMAL)
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
            bg="#ececec",
            relief="sunken",
            bd=1
        )

        self.status.pack(
            side="bottom",
            fill="x",
            padx=10, pady=(0, 10)
        )
    # ==========================
    # Run Application
    # ==========================
    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.mainloop()

    def on_close(self):
        if self.pdf_document is not None:
            self.pdf_document.close()
            self.pdf_document = None

        self.preview_image = None
        self.window.destroy()
    # ==========================================
    # Backend Operations Connection
    # ==========================================
    def merge_pdf(self):
        
        if not self.selected_files:
            messagebox.showwarning("PDFMaster", "Please select PDF files first.")
            return
        MergePDF(self.selected_files)

    def split_pdf(self):
        
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showwarning("PDFMaster", "Please select a PDF from the list first.")
            return
        
        active_file = self.selected_files[selection[0]]
        SplitPDF([active_file])  

    def protect_pdf(self):
        
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showwarning("PDFMaster", "Please select a PDF from the list first.")
            return
        
        active_file = self.selected_files[selection[0]]
        ProtectPDF([active_file])

    def extract_pages(self):
        
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showwarning("PDFMaster", "Please select a PDF from the list first.")
            return
        
        active_file = self.selected_files[selection[0]]
        ExtractPages([active_file])

    def pdf_info(self):
    
        selection = self.file_list.curselection()
        if not selection:
            messagebox.showwarning("PDFMaster", "Please select a PDF from the list first.")
            return
        
        active_file = self.selected_files[selection[0]]
        InfoPDF([active_file])

    def history(self):
        ShowHistory()

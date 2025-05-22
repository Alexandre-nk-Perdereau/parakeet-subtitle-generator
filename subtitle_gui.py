import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinterdnd2 as tkdnd
import requests
import os
import threading
from pathlib import Path

class SubtitleApp:
    def __init__(self):
        self.root = tkdnd.Tk()
        self.root.title("Parakeet Subtitle Generator")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.api_url = "http://localhost:8000"
        
        self.setup_ui()
        self.check_api_status()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, text="Automatic Subtitle Generator", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        self.status_frame = ttk.LabelFrame(main_frame, text="API Status", padding="10")
        self.status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.status_label = ttk.Label(self.status_frame, text="Checking...", foreground="orange")
        self.status_label.grid(row=0, column=0)
        
        self.refresh_button = ttk.Button(self.status_frame, text="Refresh", 
                                        command=self.check_api_status)
        self.refresh_button.grid(row=0, column=1, padx=(10, 0))
        
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(config_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.api_url_entry = ttk.Entry(config_frame, width=40)
        self.api_url_entry.insert(0, self.api_url)
        self.api_url_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        config_frame.columnconfigure(1, weight=1)
        
        self.drop_frame = ttk.LabelFrame(main_frame, text="Drop files here", padding="20")
        self.drop_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        main_frame.rowconfigure(3, weight=1)
        
        self.drop_label = ttk.Label(self.drop_frame, 
                                   text="Drag and drop video/audio files here\nor click to browse",
                                   font=('Arial', 12), 
                                   anchor="center")
        self.drop_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.drop_frame.columnconfigure(0, weight=1)
        self.drop_frame.rowconfigure(0, weight=1)
        
        self.drop_frame.drop_target_register(tkdnd.DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_label.bind('<Button-1>', self.browse_files)
        
        self.files_frame = ttk.LabelFrame(main_frame, text="Files queue", padding="10")
        self.files_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.files_tree = ttk.Treeview(self.files_frame, columns=('status',), height=4)
        self.files_tree.heading('#0', text='File')
        self.files_tree.heading('status', text='Status')
        self.files_tree.column('status', width=150)
        self.files_tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        scrollbar = ttk.Scrollbar(self.files_frame, orient="vertical", command=self.files_tree.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        buttons_frame = ttk.Frame(self.files_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        self.clear_button = ttk.Button(buttons_frame, text="Clear list", command=self.clear_files)
        self.clear_button.grid(row=0, column=0, padx=(0, 10))
        
        self.auto_clear_var = tk.BooleanVar(value=True)
        self.auto_clear_check = ttk.Checkbutton(buttons_frame, text="Auto-clear after processing", 
                                               variable=self.auto_clear_var)
        self.auto_clear_check.grid(row=0, column=1, padx=(0, 10))
        
        self.process_button = ttk.Button(buttons_frame, text="Process files", 
                                        command=self.process_files, state=tk.DISABLED)
        self.process_button.grid(row=0, column=2)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_text = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_text)
        status_label.grid(row=6, column=0, columnspan=3)
        
        self.file_queue = []
        
    def check_api_status(self):
        def check():
            try:
                self.api_url = self.api_url_entry.get()
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("model_loaded", False):
                        self.status_label.config(text="✅ API ready", foreground="green")
                        self.process_button.config(state=tk.NORMAL)
                    else:
                        self.status_label.config(text="⏳ Model loading", foreground="orange")
                        self.process_button.config(state=tk.DISABLED)
                else:
                    self.status_label.config(text="❌ API unavailable", foreground="red")
                    self.process_button.config(state=tk.DISABLED)
            except requests.RequestException:
                self.status_label.config(text="❌ Cannot contact API", foreground="red")
                self.process_button.config(state=tk.DISABLED)
        
        threading.Thread(target=check, daemon=True).start()
    
    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)
    
    def browse_files(self, event=None):
        file_types = [
            ('All supported files', '*.mp4 *.avi *.mov *.mkv *.mp3 *.wav *.flac'),
            ('Video files', '*.mp4 *.avi *.mov *.mkv'),
            ('Audio files', '*.mp3 *.wav *.flac'),
            ('All files', '*.*')
        ]
        
        files = filedialog.askopenfilenames(
            title="Select files to subtitle",
            filetypes=file_types
        )
        
        if files:
            self.add_files(files)
    
    def add_files(self, files):
        for file_path in files:
            if os.path.isfile(file_path):
                ext = Path(file_path).suffix.lower()
                if ext in ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.flac']:
                    if file_path not in [f['path'] for f in self.file_queue]:
                        file_info = {
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'status': 'Waiting'
                        }
                        self.file_queue.append(file_info)
                        
                        self.files_tree.insert('', 'end', text=file_info['name'], 
                                             values=(file_info['status'],))
                else:
                    messagebox.showwarning("Unsupported format", 
                                         f"File {os.path.basename(file_path)} is not supported.")
    
    def clear_files(self):
        self.file_queue.clear()
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
    
    def process_files(self):
        if not self.file_queue:
            messagebox.showinfo("No files", "Please add files to process.")
            return
        
        self.process_button.config(state=tk.DISABLED)
        threading.Thread(target=self._process_files_thread, daemon=True).start()
    
    def _process_files_thread(self):
        total_files = len(self.file_queue)
        
        for i, file_info in enumerate(self.file_queue):
            try:
                self.root.after(0, lambda f=file_info: self.update_file_status(f, "Processing..."))
                self.root.after(0, lambda: self.status_text.set(f"Processing: {file_info['name']}"))
                
                progress = (i / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                
                with open(file_info['path'], 'rb') as f:
                    files = {'file': (file_info['name'], f, 'application/octet-stream')}
                    
                    response = requests.post(f"{self.api_url}/transcribe-file", 
                                           files=files, timeout=300)
                
                if response.status_code == 200:
                    srt_path = Path(file_info['path']).with_suffix('.srt')
                    with open(srt_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.root.after(0, lambda f=file_info: self.update_file_status(f, "✅ Done"))
                    self.root.after(0, lambda p=srt_path: messagebox.showinfo("Success", f"Subtitles saved: {p}"))
                else:
                    error_msg = f"Error {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', error_msg)
                    except:
                        pass
                    
                    self.root.after(0, lambda f=file_info, e=error_msg: self.update_file_status(f, f"❌ {e}"))
                
                if (i + 1) % 3 == 0:
                    try:
                        cleanup_response = requests.post(f"{self.api_url}/cleanup", timeout=10)
                        if cleanup_response.status_code == 200:
                            print(f"Memory cleaned after {i+1} files")
                    except:
                        pass
                    
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.root.after(0, lambda f=file_info, e=error_msg: self.update_file_status(f, e))
        
        try:
            requests.post(f"{self.api_url}/cleanup", timeout=10)
            print("Final memory cleanup completed")
        except:
            pass
        
        if self.auto_clear_var.get():
            self.root.after(0, self.clear_files)
        
        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.status_text.set("Processing complete"))
        self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
    
    def update_file_status(self, file_info, status):
        file_info['status'] = status
        
        for item in self.files_tree.get_children():
            if self.files_tree.item(item, 'text') == file_info['name']:
                self.files_tree.set(item, 'status', status)
                break
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SubtitleApp()
    app.run()
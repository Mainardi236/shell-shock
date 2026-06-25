import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class PowerShellEditorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PowerShell Script Editor")
        self.root.geometry("900x650")

        self.filename = None
        self.powershell_path = self.detect_powershell()

        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=4, pady=4)

        tk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Save As", command=self.save_file_as).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Run", command=self.run_script).pack(side=tk.LEFT, padx=2)

        self.editor = scrolledtext.ScrolledText(self.root, wrap=tk.NONE, undo=True, font=("Consolas", 11))
        self.editor.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        output_label = tk.Label(self.root, text="Output")
        output_label.pack(anchor=tk.W, padx=4)

        self.output = scrolledtext.ScrolledText(self.root, wrap=tk.NONE, height=12, state=tk.DISABLED, font=("Consolas", 10), bg="#1e1e1e", fg="#dcdcdc")
        self.output.pack(fill=tk.BOTH, expand=False, padx=4, pady=(0, 4))

        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.update_title()

    def detect_powershell(self):
        for program in ["pwsh", "powershell"]:
            path = shutil.which(program)
            if path:
                return path
        messagebox.showwarning("PowerShell not found", "PowerShell executable not found in PATH. Please install PowerShell or add it to your PATH.")
        return None

    def update_title(self):
        title = "PowerShell Script Editor"
        if self.filename:
            title = f"{os.path.basename(self.filename)} - {title}"
        self.root.title(title)

    def set_status(self, message):
        self.status_var.set(message)

    def new_file(self):
        if self.editor.edit_modified():
            if not messagebox.askyesno("Unsaved Changes", "Discard unsaved changes and create a new file?"):
                return
        self.filename = None
        self.editor.delete("1.0", tk.END)
        self.editor.edit_modified(False)
        self.update_title()
        self.set_status("New script")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("PowerShell Scripts", "*.ps1"), ("All Files", "*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.delete("1.0", tk.END)
                self.editor.insert(tk.END, f.read())
            self.filename = path
            self.editor.edit_modified(False)
            self.update_title()
            self.set_status(f"Opened {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Open Error", f"Could not open file:\n{exc}")

    def save_file(self):
        if not self.filename:
            return self.save_file_as()
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", tk.END))
            self.editor.edit_modified(False)
            self.set_status(f"Saved {os.path.basename(self.filename)}")
            return True
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save file:\n{exc}")
            return False

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".ps1", filetypes=[("PowerShell Scripts", "*.ps1"), ("All Files", "*")])
        if not path:
            return False
        self.filename = path
        self.update_title()
        return self.save_file()

    def run_script(self):
        if not self.powershell_path:
            self.set_status("PowerShell not available")
            return

        script_text = self.editor.get("1.0", tk.END)
        if not script_text.strip():
            self.set_status("No script to run")
            return

        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(script_text)
            temp_path = temp_file.name

        command = [self.powershell_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", temp_path]
        try:
            self.set_status("Running script...")
            result = subprocess.run(command, capture_output=True, text=True, shell=False)
            output_text = result.stdout
            error_text = result.stderr
            if result.returncode != 0:
                self.set_status(f"Script completed with errors (code {result.returncode})")
            else:
                self.set_status("Script completed successfully")
            self.output.configure(state=tk.NORMAL)
            if output_text:
                self.output.insert(tk.END, output_text)
            if error_text:
                self.output.insert(tk.END, error_text)
            self.output.configure(state=tk.DISABLED)
        except Exception as exc:
            self.output.configure(state=tk.NORMAL)
            self.output.insert(tk.END, f"Execution failed:\n{exc}\n")
            self.output.configure(state=tk.DISABLED)
            self.set_status("Execution failed")
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    def mainloop(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PowerShellEditorApp()
    app.mainloop()

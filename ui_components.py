import tkinter as tk
import os
from tkinter import ttk, messagebox, filedialog
import sqlite3
from typing import Callable, Optional, List, Dict
from database import DatabaseManager

# Add this at the top of the file, after imports:

def setup_ttk_styles(root):
    """Setup all TTK styles for the application (Mac-compatible)"""
    style = ttk.Style(root)
    
    # Green button for primary actions
    style.configure(
        "Green.TButton",
        font=("Arial", 11, "bold"),
        foreground="white",
        background="#28a745",
        borderwidth=2,
        focuscolor="none",
        padding=(10, 5)
    )
    style.map(
        "Green.TButton",
        background=[("active", "#218838"), ("pressed", "#1e7e34"), ("disabled", "#b1b1b1")],
        foreground=[("disabled", "#6c757d")]
    )
    
    # Red button for destructive actions
    style.configure(
        "Red.TButton",
        font=("Arial", 10, "bold"),
        foreground="white",
        background="#dc3545",
        borderwidth=2,
        focuscolor="none",
        padding=(8, 4)
    )
    style.map(
        "Red.TButton",
        background=[("active", "#c82333"), ("pressed", "#bd2130"), ("disabled", "#b1b1b1")],
        foreground=[("disabled", "#6c757d")]
    )
    
    # Blue button for info actions
    style.configure(
        "Blue.TButton",
        font=("Arial", 10, "bold"),
        foreground="white",
        background="#007bff",
        borderwidth=2,
        focuscolor="none",
        padding=(8, 4)
    )
    style.map(
        "Blue.TButton",
        background=[("active", "#0056b3"), ("pressed", "#004085"), ("disabled", "#b1b1b1")],
        foreground=[("disabled", "#6c757d")]
    )
    
    # Orange button for secondary actions
    style.configure(
        "Orange.TButton",
        font=("Arial", 10),
        foreground="white",
        background="#fd7e14",
        borderwidth=2,
        focuscolor="none",
        padding=(8, 4)
    )
    style.map(
        "Orange.TButton",
        background=[("active", "#e8650e"), ("pressed", "#dc5a00"), ("disabled", "#b1b1b1")],
        foreground=[("disabled", "#6c757d")]
    )
    
    # Gray button for neutral actions
    style.configure(
        "Gray.TButton",
        font=("Arial", 10),
        foreground="#495057",
        background="#f8f9fa",
        borderwidth=1,
        focuscolor="none",
        padding=(8, 4)
    )
    style.map(
        "Gray.TButton",
        background=[("active", "#e9ecef"), ("pressed", "#dee2e6"), ("disabled", "#f8f9fa")],
        foreground=[("disabled", "#adb5bd")]
    )
    
    # Teal button for export actions
    style.configure(
        "Teal.TButton",
        font=("Arial", 9, "bold"),
        foreground="white",
        background="#17a2b8",
        borderwidth=2,
        focuscolor="none",
        padding=(8, 4)
    )
    style.map(
        "Teal.TButton",
        background=[("active", "#138496"), ("pressed", "#0f6674"), ("disabled", "#b1b1b1")],
        foreground=[("disabled", "#6c757d")]
    )

    return style

class ColoredButton(tk.Button):
    """Custom button that maintains colors properly on Mac"""
    def __init__(self, parent, **kwargs):
        # Extract custom parameters before calling super().__init__
        self._enabled_bg = kwargs.pop('enabled_bg', '#dc3545')
        self._enabled_fg = kwargs.pop('enabled_fg', 'white')
        self._disabled_bg = kwargs.pop('disabled_bg', '#e9ecef')
        self._disabled_fg = kwargs.pop('disabled_fg', '#6c757d')
        
        # Now call super with only valid Button parameters
        super().__init__(parent, **kwargs)
    
    def enable_red(self):
        """Enable button with red styling"""
        self.config(
            state="normal",
            bg=self._enabled_bg,
            fg=self._enabled_fg,
            activebackground='#bb2d3b',
            activeforeground='white'
        )
        # Force the update
        self.update_idletasks()
    
    def disable_grey(self):
        """Disable button with grey styling"""
        self.config(
            state="disabled",
            bg=self._disabled_bg,
            fg=self._disabled_fg
        )
        # Force the update
        self.update_idletasks()
        
        
class DatabaseViewer:
    def __init__(self, parent, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.current_table = None
        self.current_page = 0
        self.page_size = 20
        self.total_records = 0
        self.total_pages = 0
        
        temp_window = tk.Toplevel(parent)
        self.style = setup_ttk_styles(temp_window)
        temp_window.destroy()
        
        self.setup_viewer()
    
    def setup_viewer(self):
        # Create viewer window
        self.viewer_window = tk.Toplevel(self.parent)
        self.viewer_window.title("Database Viewer")
        self.viewer_window.geometry("1000x700")
        
        # Table selection frame
        selection_frame = tk.Frame(self.viewer_window)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(selection_frame, text="Seleccionar Tabla:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(selection_frame, textvariable=self.table_var, 
                                       values=["Departamento", "Profesor", "ProfesorDepartamento", "Materia", "Seccion", "Sesion", "SeccionProfesor", "SesionProfesor"],
                                       state="readonly", width=15)
        self.table_combo.pack(side=tk.LEFT, padx=10)
        self.table_combo.bind('<<ComboboxSelected>>', self.on_table_selected)
        
        # Refresh button
        refresh_btn = ttk.Button(selection_frame, text="Actualizar", command=self.refresh_current_table, style = "Blue.TButton")
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Delete button (initially disabled)
            # FIXED: Delete button with proper configuration
        self.delete_btn = ttk.Button(
            selection_frame, 
            text="🗑️ Eliminar Seleccionado", 
            command=self.delete_selected, 
            state="disabled",
            style="Red.TButton",
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        # Initialize with disabled styling
        
        # Info frame
        self.info_frame = tk.Frame(self.viewer_window)
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_label = tk.Label(self.info_frame, text="Seleccione una tabla para ver los datos", 
                                  font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        # Search frame
        search_frame = tk.Frame(self.viewer_window)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        search_btn = ttk.Button(search_frame, text="Buscar", command=self.perform_search, style= "Blue.TButton")
        search_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(search_frame, text="Limpiar", command=self.clear_search, style="Gray.TButton")
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Table frame with scrollbars
        table_frame = tk.Frame(self.viewer_window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create Treeview with scrollbars
        self.tree = ttk.Treeview(table_frame)
        
        # Bind selection event to enable/disable delete button
        self.tree.bind('<<TreeviewSelect>>', self.on_item_selected)
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and tree
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Pagination frame
        pagination_frame = tk.Frame(self.viewer_window)
        pagination_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Page navigation
        self.first_btn = ttk.Button(pagination_frame, text="<<", command=self.first_page, state="disabled", style="Gray.TButton")
        self.first_btn.pack(side=tk.LEFT, padx=2)
        
        self.prev_btn = ttk.Button(pagination_frame, text="<", command=self.prev_page, state="disabled", style="Gray.TButton")
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.page_label = ttk.Label(pagination_frame, text="Página 0 de 0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = ttk.Button(pagination_frame, text=">", command=self.next_page, state="disabled", style="Gray.TButton")
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
        self.last_btn = ttk.Button(pagination_frame, text=">>", command=self.last_page, state="disabled", style="Gray.TButton")
        self.last_btn.pack(side=tk.LEFT, padx=2)
        
        # Page size selection
        tk.Label(pagination_frame, text="Registros por página:").pack(side=tk.LEFT, padx=(20, 5))
        self.page_size_var = tk.StringVar(value="20")
        page_size_combo = ttk.Combobox(pagination_frame, textvariable=self.page_size_var, 
                                      values=["10", "20", "50", "100"], width=5, state="readonly")
        page_size_combo.pack(side=tk.LEFT, padx=2)
        page_size_combo.bind('<<ComboboxSelected>>', self.on_page_size_changed)
        
        # Records info
        self.records_label = tk.Label(pagination_frame, text="")
        self.records_label.pack(side=tk.RIGHT, padx=10)
    
    def on_item_selected(self, event):
        """Handle item selection to enable/disable delete button with proper styling"""
        selection = self.tree.selection()
        if selection and self.current_table:
            # Enable delete button only for certain tables
            deletable_tables = ["Departamento", "Profesor", "Materia", "Seccion"]
            if self.current_table in deletable_tables:
                # Enable with red styling
                self.delete_btn.config(state="normal")
            else:
                # Disable for non-deletable tables
                self.delete_btn.config(state="disabled")
        else:
            # Disable when no selection
            self.delete_btn.config(state="disabled")
    
    def delete_selected(self):
        """Delete the selected item"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Por favor seleccione un elemento para eliminar.")
            return
        
        if not self.current_table:
            return
        
        # Get selected item data
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if not values:
            return
        
        # Get the primary key value based on table
        primary_key_value = None
        item_description = ""
        
        try:
            if self.current_table == "Departamento":
                primary_key_value = values[0]  # nombre
                item_description = f"departamento '{primary_key_value}'"
                
            elif self.current_table == "Profesor":
                primary_key_value = int(values[0])  # id
                nombres = values[1] if len(values) > 1 else ""
                apellidos = values[2] if len(values) > 2 else ""
                item_description = f"profesor '{nombres} {apellidos}' (ID: {primary_key_value})"
                
            elif self.current_table == "Materia":
                primary_key_value = values[0]  # codigo
                nombre = values[1] if len(values) > 1 else ""
                item_description = f"materia '{primary_key_value} - {nombre}'"
                
            elif self.current_table == "Seccion":
                primary_key_value = int(values[0])  # NRC
                indicador = values[1] if len(values) > 1 else ""
                item_description = f"sección NRC {primary_key_value} ({indicador})"
                
            else:
                messagebox.showwarning("Advertencia", f"Eliminación no soportada para la tabla {self.current_table}")
                return
        
        except (ValueError, IndexError) as e:
            messagebox.showerror("Error", f"Error al obtener datos del elemento: {e}")
            return
        
        # Confirmation dialog
        if not messagebox.askyesno(
            "Confirmar Eliminación", 
            f"¿Está seguro de que desea eliminar el {item_description}?\n\n"
            "Esta acción no se puede deshacer y eliminará todos los datos relacionados.",
            icon='warning'
        ):
            return
        
        # Perform deletion
        success = self.perform_deletion(primary_key_value)
        
        if success:
            messagebox.showinfo("Éxito", f"El {item_description} ha sido eliminado exitosamente.")
            self.refresh_current_table()  # Refresh the table
            # Reset delete button properly
            self._disable_delete_button()
        else:
            messagebox.showerror("Error", f"No se pudo eliminar el {item_description}.\n\n"
                            "Puede que tenga datos relacionados que impidan la eliminación.")
    
    def perform_deletion(self, primary_key_value) -> bool:
        """Perform the actual deletion based on table type"""
        try:
            if self.current_table == "Departamento":
                return self.db_manager.delete_departamento(primary_key_value)
                
            elif self.current_table == "Profesor":
                return self.db_manager.delete_profesor(primary_key_value)
                
            elif self.current_table == "Materia":
                return self.db_manager.delete_materia(primary_key_value)
                
            elif self.current_table == "Seccion":
                return self.db_manager.delete_seccion(primary_key_value)
                
            return False
            
        except Exception as e:
            print(f"Error during deletion: {e}")
            return False
        
    def _disable_delete_button(self):
        """Helper method to properly disable the delete button"""
        self.delete_btn.config(state="disabled")
    
    def load_table_data(self):
        """Load current table data with pagination"""
        if not self.current_table:
            return
        
        search_term = self.search_var.get().strip() if self.search_var.get().strip() else None
        offset = self.current_page * self.page_size
        
        # Get data for current page
        data = self.db_manager.get_table_data(
            self.current_table, search_term, self.page_size, offset
        )
        
        # Get total count separately
        total_count = self.get_total_record_count(search_term)
        self.total_records = total_count
        self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
        
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if data:
            try:
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({self.current_table})")
                columns = [column[1] for column in cursor.fetchall()]
                conn.close()
                
                # Configure columns
                self.tree["columns"] = columns
                self.tree["show"] = "headings"
                
                # Set column headings and widths
                for col in columns:
                    self.tree.heading(col, text=col)
                    self.tree.column(col, width=100, minwidth=50)
                
                # Insert data
                for row in data:
                    # Convert None values to empty strings for display
                    display_row = [str(item) if item is not None else "" for item in row]
                    self.tree.insert("", "end", values=display_row)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading table data: {str(e)}")
        
        # Update UI elements
        self.update_pagination_controls()
        self.update_info_labels()
        
        # Disable delete button when table refreshes
        self._disable_delete_button()

    def get_total_record_count(self, search_term: str = None) -> int:
        """Get total record count for current table with optional search"""
        try:
            query = f"SELECT COUNT(*) FROM {self.current_table}"
            params = []
            
            if search_term:
                if self.current_table == "Profesor":
                    query += " WHERE (nombres LIKE ? OR apellidos LIKE ?)"
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                elif self.current_table == "Materia":
                    query += " WHERE (codigo LIKE ? OR nombre LIKE ?)"
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                elif self.current_table == "Departamento":
                    query += " WHERE nombre LIKE ?"
                    params.append(f"%{search_term}%")
                elif self.current_table == "Seccion":
                    query += " WHERE CAST(NRC AS TEXT) LIKE ?"
                    params.append(f"%{search_term}%")
                elif self.current_table == "ProfesorDepartamento":
                    query += " WHERE (departamento_nombre LIKE ?)"
                    params.append(f"%{search_term}%")
                elif self.current_table == "SeccionProfesor":
                    query += " WHERE CAST(seccion_NRC AS TEXT) LIKE ?"
                    params.append(f"%{search_term}%")
                elif self.current_table == "SesionProfesor":
                    query += " WHERE CAST(sesion_id AS TEXT) LIKE ?"
                    params.append(f"%{search_term}%")
            
            result = self.db_manager.execute_query(query, tuple(params), fetch_one=True)
            return result[0] if result else 0
            
        except Exception as e:
            print(f"Error getting total count: {e}")
            return 0
    
    def update_pagination_controls(self):
        """Update pagination button states"""
        # Enable/disable navigation buttons
        self.first_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
        self.last_btn.config(state="normal" if self.current_page < self.total_pages - 1 else "disabled")
        
        # Update page label
        current_page_display = self.current_page + 1 if self.total_pages > 0 else 0
        self.page_label.config(text=f"Página {current_page_display} de {self.total_pages}")
    
    def update_info_labels(self):
        """Update information labels"""
        start_record = self.current_page * self.page_size + 1 if self.total_records > 0 else 0
        end_record = min((self.current_page + 1) * self.page_size, self.total_records)
        
        self.info_label.config(text=f"Tabla: {self.current_table} - Total: {self.total_records} registros")
        self.records_label.config(text=f"Mostrando {start_record}-{end_record} de {self.total_records}")
    
    def on_table_selected(self, event=None):
        """Handle table selection"""
        self.current_table = self.table_var.get()
        self.current_page = 0
        self.search_var.set("")
        self.load_table_data()
    
    def on_page_size_changed(self, event=None):
        """Handle page size change"""
        self.page_size = int(self.page_size_var.get())
        self.current_page = 0
        self.load_table_data()
    
    def on_search(self, event=None):
        """Handle search as user types (with delay)"""
        # Cancel previous search timer if exists
        if hasattr(self, 'search_timer'):
            self.viewer_window.after_cancel(self.search_timer)
        
        # Set new timer for search
        self.search_timer = self.viewer_window.after(500, self.perform_search)
    
    def perform_search(self):
        """Perform search and reset to first page"""
        self.current_page = 0
        self.load_table_data()
    
    def clear_search(self):
        """Clear search and reload data"""
        self.search_var.set("")
        self.current_page = 0
        self.load_table_data()
    
    def refresh_current_table(self):
        """Refresh current table data"""
        if self.current_table:
            self.load_table_data()
    
    def first_page(self):
        """Go to first page"""
        self.current_page = 0
        self.load_table_data()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_table_data()
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_table_data()
    
    def last_page(self):
        """Go to last page"""
        if self.total_pages > 0:
            self.current_page = self.total_pages - 1
            self.load_table_data()
            
class ProgressDialog:
    """Progress dialog for long-running operations"""
    def __init__(self, parent, title="Procesando...", message="Por favor espere..."):
        self.parent = parent
        self.cancelled = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self._center_dialog()
        
        # Prevent closing
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message label
        self.message_label = tk.Label(main_frame, text=message, font=("Arial", 10))
        self.message_label.pack(pady=(0, 15))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))
        self.progress.start()
        
        # Cancel button
        self.cancel_btn = tk.Button(main_frame, text="Cancelar", command=self._on_cancel)
        self.cancel_btn.pack()
        
    def _center_dialog(self):
        """Center dialog on parent"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _on_close(self):
        """Prevent closing with X button"""
        pass
    
    def _on_cancel(self):
        """Handle cancel button"""
        self.cancelled = True
        self.close()
    
    def update_message(self, message):
        """Update progress message"""
        self.message_label.config(text=message)
        self.dialog.update()
    
    def close(self):
        """Close the dialog"""
        self.progress.stop()
        self.dialog.destroy()
    
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled

class ConfirmDialog:
    """Simple confirmation dialog"""
    def __init__(self, parent, title, message, confirm_text="Sí", cancel_text="No"):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("350x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self._center_dialog()
        
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message
        message_label = tk.Label(main_frame, text=message, wraplength=300, justify=tk.CENTER)
        message_label.pack(pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack()
        
        confirm_btn = tk.Button(btn_frame, text=confirm_text, command=self._on_confirm)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text=cancel_text, command=self._on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Wait for user response
        self.dialog.wait_window()
    
    def _center_dialog(self):
        """Center dialog on parent"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _on_confirm(self):
        """Handle confirm"""
        self.result = True
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel"""
        self.result = False
        self.dialog.destroy()
    
    def get_result(self):
        """Get dialog result"""
        return self.result

class SearchProfessorDialog:
    """Dialog for searching professors"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Buscar Profesor")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Buscar Profesor", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Search fields
        tk.Label(main_frame, text="Nombre:").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(main_frame, textvariable=self.name_var, width=30, font=("Arial", 12))
        name_entry.pack(pady=(5, 10), fill=tk.X)
        name_entry.focus()
        
        tk.Label(main_frame, text="Apellido:").pack(anchor=tk.W)
        self.lastname_var = tk.StringVar()
        lastname_entry = tk.Entry(main_frame, textvariable=self.lastname_var, width=30, font=("Arial", 12))
        lastname_entry.pack(pady=(5, 20), fill=tk.X)
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        search_btn = ttk.Button(btn_frame, text="🔍 Buscar", command=self.perform_search,
                              style="Blue.TButton")
        search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(btn_frame, text="Cerrar", command=self.on_cancel,
                              style="Gray.TButton")
        cancel_btn.pack(side=tk.LEFT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.perform_search())
    
    def perform_search(self):
        """Perform the search"""
        nombres = self.name_var.get().strip()
        apellidos = self.lastname_var.get().strip()
        
        if not nombres and not apellidos:
            messagebox.showwarning("Advertencia", "Por favor ingrese al menos un nombre o apellido")
            return
        
        try:
            # Search for professors
            all_profs = self.db_manager.get_all_profesores()
            
            # Filter results
            results = []
            for prof in all_profs:
                name_match = not nombres or nombres.lower() in prof['nombres'].lower()
                lastname_match = not apellidos or apellidos.lower() in prof['apellidos'].lower()
                
                if name_match and lastname_match:
                    results.append(prof)
            
            if results:
                self.show_results(results)
            else:
                messagebox.showinfo("Sin resultados", "No se encontraron profesores que coincidan con la búsqueda")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en la búsqueda: {str(e)}")
    
    # Update SearchProfessorDialog to show multiple departments:
    
    def show_results(self, results):
        """Show search results with multiple departments"""
        # Create results window
        results_window = tk.Toplevel(self.dialog)
        results_window.title("Resultados de Búsqueda")
        results_window.geometry("800x400")  # Wider to accommodate departments
        
        # Results frame
        main_frame = tk.Frame(results_window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text=f"Se encontraron {len(results)} profesores:", 
                font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Results table
        columns = ('ID', 'Nombre', 'Departamentos', 'Sesiones', 'Secciones')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        # Define columns
        tree.heading('ID', text='ID')
        tree.heading('Nombre', text='Nombre')
        tree.heading('Departamentos', text='Departamentos')
        tree.heading('Sesiones', text='Sesiones')
        tree.heading('Secciones', text='Secciones')
        
        tree.column('ID', width=50)
        tree.column('Nombre', width=200)
        tree.column('Departamentos', width=300)  # Wider for multiple departments
        tree.column('Sesiones', width=80)
        tree.column('Secciones', width=80)
        
        # Add data
        for prof in results:
            tree.insert('', tk.END, values=(
                prof['id'],
                prof['full_name'],
                prof['departamentos'],  # Now shows multiple departments
                prof['num_sessions'],
                prof['num_sections']
            ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel"""
        self.dialog.destroy()
        
        
class ProfessorSessionsDialog:
    """Dialog for querying professor sessions"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.selected_professor = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Consultar Sesiones de Profesor")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        
        # Main container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Consultar Sesiones de Profesor", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                         style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Selection frame - UPDATED: Made more compact for two-column layout
        selection_frame = ttk.LabelFrame(main_frame, text="Selección de Profesor", padding="15")
        selection_frame.pack(fill=tk.X, pady=(0, 15))  # Reduced bottom padding
        
        # Search professor section - UPDATED: Horizontal layout to save space
        search_frame = tk.Frame(selection_frame)
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(search_frame, text="Buscar profesor:").pack(side=tk.LEFT)
        
        search_input_frame = tk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_input_frame, textvariable=self.search_var, width=40,
                                     font=("Arial", 11), relief="solid", bd=1)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        search_btn = ttk.Button(search_input_frame, text="🔍 Buscar", command=self.search_professors,
                               style = "Blue.TButton")
        search_btn.pack(side=tk.LEFT)
        
        # Clear search button
        clear_btn = ttk.Button(search_input_frame, text="✕", command=self.clear_search,
                            style="Gray.TButton", width=3)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
            # Professor selection table
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create Treeview for professor selection
        columns = ('Nombre', 'Departamentos', 'Sesiones', 'Secciones')
        self.professor_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        
        # Configure columns
        column_configs = {
            'Nombre': {'width': 250, 'text': 'Profesor'},
            'Departamentos': {'width': 300, 'text': 'Departamentos'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        for col, config in column_configs.items():
            self.professor_tree.heading(col, text=config['text'])
            self.professor_tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar for professor table
        prof_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.professor_tree.yview)
        self.professor_tree.configure(yscrollcommand=prof_scrollbar.set)
        
        self.professor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prof_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.professor_tree.bind('<<TreeviewSelect>>', self.on_professor_select)
        
        # Add alternating row colors for better readability
        self.professor_tree.tag_configure('oddrow', background='#f8f9fa')
        self.professor_tree.tag_configure('evenrow', background='white')
        
        # Action buttons container
        action_container = tk.Frame(selection_frame)
        action_container.pack(fill=tk.X)
        
        self.query_btn = ttk.Button(
            selection_frame, 
            text="📊 Consultar Sesiones", 
            command=self.query_sessions,
            state="disabled",
            style="Green.TButton"
            )
        self.query_btn.pack(pady=(5, 5))
        
        # Results frame (initially hidden)
        self.results_frame = tk.Frame(main_frame)
        
        
        
        # Load all professors initially
        self.load_professors()
    
    def load_professors(self, filter_text=""):
        """Load professors into listbox"""
        for item in self.professor_tree.get_children():
            self.professor_tree.delete(item)
        self.professors_data = []
        
        try:
            all_professors = self.db_manager.get_all_profesores()
            
            # Filter professors if search text provided
            if filter_text:
                filtered_professors = []
                filter_lower = filter_text.lower()
                for prof in all_professors:
                    if (filter_lower in prof['nombres'].lower() or 
                        filter_lower in prof['apellidos'].lower() or
                        filter_lower in prof['departamentos'].lower()):
                        filtered_professors.append(prof)
                professors = filtered_professors
            else:
                professors = all_professors
            
            # Sort by department then by name
            professors.sort(key=lambda x: (x['departamentos'], x['apellidos'], x['nombres']))
            
            # Add professors to table
            for i, prof in enumerate(professors):
                # Truncate department names if too long for better display
                dept_display = prof['departamentos']
                if len(dept_display) > 45:
                    dept_display = dept_display[:42] + "..."
                
                # Determine row tag for alternating colors
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                item = self.professor_tree.insert('', tk.END, values=(
                    prof['full_name'],
                    dept_display,
                    prof['num_sessions'],
                    prof['num_sections']
                ), tags=(tag,))
                
                self.professors_data.append(prof)
            
            # Update search placeholder if no results
            if not professors and filter_text:
                self.professor_tree.insert('', tk.END, values=(
                    "Sin resultados", "Intente con otros términos de búsqueda", "", ""
                ), tags=('no-results',))
                
                # Configure no-results tag
                self.professor_tree.tag_configure('no-results', background='#fff3cd', foreground='#856404')
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
            
            
    def clear_search(self):
        """Clear search field and reload all professors"""
        self.search_var.set("")
        self.load_professors()
        self.query_btn.config(state="disabled")
        self.selected_professor = None
        
    def on_search_change(self, event=None):
        """Handle search text change with delay"""
        if hasattr(self, 'search_timer'):
            self.dialog.after_cancel(self.search_timer)
        
        self.search_timer = self.dialog.after(300, self.search_professors)
    
    def search_professors(self):
        """Search professors based on input"""
        search_text = self.search_var.get().strip()
        self.load_professors(search_text)
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
    def on_professor_select(self, event=None):
        """Handle professor selection from table"""
        selection = self.professor_tree.selection()
        if selection:
            item = selection[0]
            values = self.professor_tree.item(item, 'values')
            
            # Check if it's a valid professor selection (not a "no results" item)
            if values and values[0] != "Sin resultados":
                # Find the professor in our data by matching the display name
                selected_name = values[0]
                
                for prof in self.professors_data:
                    if prof['full_name'] == selected_name:
                        self.selected_professor = prof
                        self.query_btn.config(state="normal")
                        return
            
            # If we get here, no valid professor was selected
            self.selected_professor = None
            self.query_btn.config(state="disabled")
        else:
            self.selected_professor = None
            self.query_btn.config(state="disabled")
    
    def query_sessions(self):
        """Query and display professor sessions"""
        if not self.selected_professor:
            messagebox.showwarning("Advertencia", "Por favor seleccione un profesor.")
            return
        
        try:
            professor_id = self.selected_professor['id']
            
            # Get sessions and summary
            sessions = self.db_manager.get_profesor_sessions(professor_id)
            summary = self.db_manager.get_profesor_sessions_summary(professor_id)
            
            if not sessions:
                messagebox.showinfo("Sin resultados", 
                                   f"El profesor {self.selected_professor['full_name']} "
                                   "no tiene sesiones asignadas.")
                return
            
            # Show results
            self.show_results(sessions, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar sesiones: {str(e)}")
    
        # Replace the show_results method in ProfessorSessionsDialog class:
    
    def show_results(self, sessions, summary):
        """Display query results with optimized vertical space usage"""
        # Show and configure results frame
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # COLUMN LAYOUT - Create two main columns
        columns_container = tk.Frame(self.results_frame)
        columns_container.pack(fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN - Professor info and summary with scrollbar
        left_column_container = tk.Frame(columns_container, width=400)
        left_column_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_column_container.pack_propagate(False)  # Maintain fixed width
        
        # Create canvas and scrollbar for left column
        canvas = tk.Canvas(left_column_container, width=380)
        left_scrollbar = ttk.Scrollbar(left_column_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # RIGHT COLUMN - Sessions table
        right_column = tk.Frame(columns_container)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === LEFT COLUMN CONTENT (now in scrollable frame) ===
        
        # Compact Professor info header
        prof_info_frame = ttk.LabelFrame(scrollable_frame, text="Profesor", padding="10")
        prof_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        prof_name = self.selected_professor['full_name']
        prof_depts = self.selected_professor['departamentos']
        
        # Professor name - more compact
        tk.Label(prof_info_frame, text=prof_name, 
                font=("Arial", 11, "bold"), fg="#2c3e50").pack(anchor=tk.W)
        
        # Department info - more compact
        dept_label = tk.Label(prof_info_frame, text=f"Deptartamentos: {prof_depts}", 
                font=("Arial", 10, "bold"), wraplength=350, justify=tk.LEFT, fg="#34495e")
        dept_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Summary statistics - NOW WITH MORE SPACE
        summary_frame = ttk.LabelFrame(scrollable_frame, text="Resumen Estadístico", padding="12")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create statistics container
        stats_container = tk.Frame(summary_frame)
        stats_container.pack(fill=tk.X)
        
        # Main statistics - each on its own row for better visibility
        main_stats = [
            ("Total de sesiones:", summary.get('total_sessions', 0), "#e74c3c"),
            ("Secciones diferentes:", summary.get('total_sections', 0), "#3498db"),
            ("Créditos totales:", summary.get('total_credits', 0), "#27ae60"),
            ("Estudiantes totales:", summary.get('total_students', 0), "#f39c12"),
            ("Departamentos:", len(summary.get('departments', [])), "#9b59b6"),
            ("Materias diferentes:", len(summary.get('materias', [])), "#e67e22")
        ]
        
        for label, value, color in main_stats:
            stat_frame = tk.Frame(stats_container, relief="solid", bd=1, bg="#f8f9fa")
            stat_frame.pack(fill=tk.X, pady=2, padx=1)
            
            # Create inner frame for padding
            inner_frame = tk.Frame(stat_frame, bg="#f8f9fa")
            inner_frame.pack(fill=tk.X, padx=8, pady=4)
            
            # Label
            label_widget = tk.Label(inner_frame, text=label, font=("Arial", 9, "bold"), 
                                   anchor="w", bg="#f8f9fa")
            label_widget.pack(side=tk.LEFT)
            
            # Value with prominent display
            value_widget = tk.Label(inner_frame, text=str(value), font=("Arial", 12, "bold"), 
                                   fg=color, anchor="e", bg="#f8f9fa")
            value_widget.pack(side=tk.RIGHT)
        
        secondary_frame = tk.Frame(stats_container)
        secondary_frame.pack(fill=tk.X, pady=(8, 0))
        
        # Schedule days info
        if summary.get('schedule_days'):
            days_frame = ttk.LabelFrame(scrollable_frame, text="Horario", padding="8")
            days_frame.pack(fill=tk.X, pady=(0, 10))
            
            days_text = ', '.join(summary['schedule_days'])
            tk.Label(days_frame, text=f"Días: {days_text}", font=("Arial", 9), 
                    fg="#3498db", wraplength=350).pack(anchor=tk.W)
        
        # Departments breakdown
        if len(summary.get('departments', [])) > 1:
            dept_frame = ttk.LabelFrame(scrollable_frame, text="Distribución por Departamento", padding="10")
            dept_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Calculate sessions per department
            dept_sessions = {}
            for session in sessions:
                dept = session['departamento']
                dept_sessions[dept] = dept_sessions.get(dept, 0) + 1
            
            for dept, count in sorted(dept_sessions.items()):
                dept_info_frame = tk.Frame(dept_frame, relief="solid", bd=1, bg="#ecf0f1")
                dept_info_frame.pack(fill=tk.X, pady=2, padx=1)
                
                # Create inner frame for padding
                inner_dept_frame = tk.Frame(dept_info_frame, bg="#ecf0f1")
                inner_dept_frame.pack(fill=tk.X, padx=8, pady=3)
                
                # Department name - truncate if too long but make it more readable
                dept_display = dept[:30] + "..." if len(dept) > 30 else dept
                tk.Label(inner_dept_frame, text=f"• {dept_display}", 
                        font=("Arial", 9), bg="#ecf0f1", anchor="w").pack(side=tk.LEFT)
                
                # Session count with percentage
                percentage = (count / len(sessions)) * 100
                count_text = f"{count} sesiones ({percentage:.1f}%)"
                tk.Label(inner_dept_frame, text=count_text, 
                        font=("Arial", 9, "bold"), fg="#7f8c8d", bg="#ecf0f1", anchor="e").pack(side=tk.RIGHT)
            
        # Export button
        export_btn = ttk.Button(scrollable_frame, text="📄 Exportar", 
                              command=lambda: self.export_results(sessions, summary),
                              style="Teal.TButton")
        export_btn.pack(fill=tk.X, pady=(10, 5))
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        # === RIGHT COLUMN CONTENT (unchanged) ===
        
        # Sessions table title
        table_title_frame = tk.Frame(right_column)
        table_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(table_title_frame, text="Detalle de Sesiones", 
                font=("Arial", 14, "bold"), fg="#2c3e50").pack(side=tk.LEFT)
        
        # Session count badge
        count_label = tk.Label(table_title_frame, text=f"{len(sessions)} sesiones", 
                              font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d", 
                              padx=8, pady=2, relief="solid", bd=1)
        count_label.pack(side=tk.RIGHT)
        
        # Sessions table frame
        table_frame = tk.Frame(right_column)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview for sessions
        columns = ('NRC', 'Materia', 'Departamento', 'Horario', 'Días', 'Lugar', 'Estudiantes')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_configs = {
            'NRC': {'width': 70, 'text': 'NRC'},
            'Materia': {'width': 180, 'text': 'Materia'},
            'Departamento': {'width': 120, 'text': 'Departamento'},
            'Horario': {'width': 100, 'text': 'Horario'},
            'Días': {'width': 60, 'text': 'Días'},
            'Lugar': {'width': 120, 'text': 'Lugar'},
            'Estudiantes': {'width': 80, 'text': 'Estudiantes'}
        }
        
        for col, config in column_configs.items():
            tree.heading(col, text=config['text'])
            tree.column(col, width=config['width'], minwidth=50)
        
        # Add sessions data
        for session in sessions:
            # Format time range
            if session['hora_inicio'] and session['hora_fin']:
                horario = f"{session['hora_inicio']}-{session['hora_fin']}"
            else:
                horario = "Sin definir"
            
            # Format location
            lugar = "Sin especificar"
            if session['edificio'] and session['edificio'] != 'No especificado':
                lugar = session['edificio']
                if session['salon'] and session['salon'] != 'No especificado':
                    lugar += f"-{session['salon']}"
            
            # Format days
            dias = session['dias'] if session['dias'] else ''
            
            # Format students
            estudiantes = f"{session['inscritos']}/{session['cupo']}"
            
            # Format materia (code only for space)
            materia = session['materia_codigo']
            
            # Truncate department name if too long
            departamento = session['departamento'][:15] + "..." if len(session['departamento']) > 15 else session['departamento']
            
            tree.insert('', tk.END, values=(
                session['nrc'],
                materia,
                departamento,
                horario,
                dias,
                lugar,
                estudiantes
            ))
        
        # Scrollbar for table
        tree_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add alternating row colors
        tree.tag_configure('oddrow', background='#f8f9fa')
        tree.tag_configure('evenrow', background='white')
        
        # Apply row colors
        for i, child in enumerate(tree.get_children()):
            if i % 2 == 0:
                tree.item(child, tags=('evenrow',))
            else:
                tree.item(child, tags=('oddrow',))
    '''
    def export_results(self, sessions, summary):
        """Export results to console"""
        try:
            prof_name = self.selected_professor['full_name']
            prof_depts = self.selected_professor['departamentos']
            
            print("\n" + "="*100)
            print(f"SESIONES DEL PROFESOR: {prof_name}")
            print(f"DEPARTAMENTOS: {prof_depts}")
            print("="*100)
            
            # Print summary
            print(f"\nRESUMEN:")
            print(f"• Total de sesiones: {summary['total_sessions']}")
            print(f"• Total de secciones: {summary['total_sections']}")
            print(f"• Créditos totales: {summary['total_credits']}")
            print(f"• Total de estudiantes: {summary['total_students']}")
            print(f"• Días de clase: {', '.join(summary['schedule_days']) if summary['schedule_days'] else 'Ninguno'}")
            print(f"• Departamentos: {', '.join(summary['departments'])}")
            
            # Print detailed sessions
            print(f"\nDETALLE DE SESIONES:")
            print("-" * 100)
            print(f"{'NRC':<8} {'Materia':<35} {'Horario':<18} {'Días':<8} {'Lugar':<25} {'Est.':<8}")
            print("-" * 100)
            
            for session in sessions:
                nrc = str(session['nrc'])
                materia = f"{session['materia_codigo']} - {session['materia_nombre']}"[:34]
                
                if session['hora_inicio'] and session['hora_fin']:
                    horario = f"{session['hora_inicio']}-{session['hora_fin']}"
                else:
                    horario = "No definido"
                
                dias = session['dias'] if session['dias'] else ''
                
                lugar = ""
                if session['edificio'] and session['edificio'] != 'No especificado':
                    lugar = session['edificio']
                    if session['salon'] and session['salon'] != 'No especificado':
                        lugar += f"-{session['salon']}"
                lugar = lugar[:24] if lugar else "No especificado"
                
                estudiantes = f"{session['inscritos']}/{session['cupo']}"
                
                print(f"{nrc:<8} {materia:<35} {horario:<18} {dias:<8} {lugar:<25} {estudiantes:<8}")
            
            print("="*100)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    '''
    def close_dialog(self):
        """Close the dialog"""
        if self.callback:
            self.callback()
        self.dialog.destroy()
        
# Add this new class to the ui_components.py file:

class ProfessorSectionsDialog:
    """Dialog for querying professor sections"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.selected_professor = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Consultar Secciones de Profesor")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Setup TTK styles for Mac compatibility
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI with TTK buttons"""
        # Main container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button on the same row
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Consultar Secciones de Profesor", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button - TTK
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Selección de Profesor", padding="15")
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Search section
        search_frame = tk.Frame(selection_frame)
        search_frame.pack(fill=tk.X)
        
        tk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Arial", 11), width = 40,
                                     relief="solid", bd=1)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Search button - TTK
        search_btn = ttk.Button(search_frame, text="🔍", command=self.search_professors,
                               style="Blue.TButton")
        search_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        clear_btn = ttk.Button(search_frame, text="✕", command=self.clear_search,
                          style="Gray.TButton", width=3)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Professor selection
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create Treeview for professor selection
        columns = ('Nombre', 'Departamentos', 'Sesiones', 'Secciones')
        self.professor_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        
        # Configure columns
        column_configs = {
            'Nombre': {'width': 250, 'text': 'Profesor'},
            'Departamentos': {'width': 300, 'text': 'Departamentos'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        for col, config in column_configs.items():
            self.professor_tree.heading(col, text=config['text'])
            self.professor_tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar for professor table
        prof_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.professor_tree.yview)
        self.professor_tree.configure(yscrollcommand=prof_scrollbar.set)
        
        self.professor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prof_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.professor_tree.bind('<<TreeviewSelect>>', self.on_professor_select)
        
        # Add alternating row colors for better readability
        self.professor_tree.tag_configure('oddrow', background='#f8f9fa')
        self.professor_tree.tag_configure('evenrow', background='white')
        
        # Action buttons container
        action_container = tk.Frame(selection_frame)
        action_container.pack(fill=tk.X)
        
        # Query button - TTK with prominent style
        self.query_btn = ttk.Button(
            selection_frame, 
            text="📚 CONSULTAR SECCIONES", 
            command=self.query_sections,
            state="disabled",
            style="Green.TButton"
        )
        self.query_btn.pack(pady=(5, 0))
        
        # Results frame
        self.results_frame = tk.Frame(main_frame)
        
        # Load professors
        self.load_professors()
    
    def load_professors(self, filter_text=""):
        """Load professors into listbox"""
        for item in self.professor_tree.get_children():
            self.professor_tree.delete(item)
            
        self.professors_data = []
        
        try:
            all_professors = self.db_manager.get_all_profesores()
            
            # Filter professors if search text provided
            if filter_text:
                filtered_professors = []
                filter_lower = filter_text.lower()
                for prof in all_professors:
                    if (filter_lower in prof['nombres'].lower() or 
                        filter_lower in prof['apellidos'].lower() or
                        filter_lower in prof['departamentos'].lower()):
                        filtered_professors.append(prof)
                professors = filtered_professors
            else:
                professors = all_professors
            
            # Sort by department then by name
            professors.sort(key=lambda x: (x['departamentos'], x['apellidos'], x['nombres']))
            
                    # Add professors to table
            for i, prof in enumerate(professors):
                # Truncate department names if too long for better display
                dept_display = prof['departamentos']
                if len(dept_display) > 45:
                    dept_display = dept_display[:42] + "..."
                
                # Determine row tag for alternating colors
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                item = self.professor_tree.insert('', tk.END, values=(
                    prof['full_name'],
                    dept_display,
                    prof['num_sessions'],
                    prof['num_sections']
                ), tags=(tag,))
                
                self.professors_data.append(prof)
            
            # Update search placeholder if no results
            if not professors and filter_text:
                self.professor_tree.insert('', tk.END, values=(
                    "Sin resultados", "Intente con otros términos de búsqueda", "", ""
                ), tags=('no-results',))
                
                # Configure no-results tag
                self.professor_tree.tag_configure('no-results', background='#fff3cd', foreground='#856404')
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
    
    def on_search_change(self, event=None):
        """Handle search text change with delay"""
        if hasattr(self, 'search_timer'):
            self.dialog.after_cancel(self.search_timer)
        
        self.search_timer = self.dialog.after(300, self.search_professors)
    
    def search_professors(self):
        """Search professors based on input"""
        search_text = self.search_var.get().strip()
        self.load_professors(search_text)
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
        # Replace the on_professor_select method in ProfessorSectionsDialog class:
    
    def on_professor_select(self, event=None):
        """Handle professor selection from table"""
        selection = self.professor_tree.selection()
        if selection:
            item = selection[0]
            values = self.professor_tree.item(item, 'values')
            
            # Check if it's a valid professor selection (not a "no results" item)
            if values and values[0] != "Sin resultados":
                # Find the professor in our data by matching the display name
                selected_name = values[0]
                
                for prof in self.professors_data:
                    if prof['full_name'] == selected_name:
                        self.selected_professor = prof
                        self.query_btn.config(state="normal")
                        return
            
            # If we get here, no valid professor was selected
            self.selected_professor = None
            self.query_btn.config(state="disabled")
        else:
            self.selected_professor = None
            self.query_btn.config(state="disabled")
    
    def query_sections(self):
        """Query and display professor sections"""
        if not self.selected_professor:
            messagebox.showwarning("Advertencia", "Por favor seleccione un profesor.")
            return
        
        try:
            professor_id = self.selected_professor['id']
            
            # Get sections and summary
            sections = self.db_manager.get_profesor_sections(professor_id)
            summary = self.db_manager.get_profesor_sections_summary(professor_id)
            
            if not sections:
                messagebox.showinfo("Sin resultados", 
                                   f"El profesor {self.selected_professor['full_name']} "
                                   "no tiene secciones asignadas.")
                return
            
            # Show results
            self.show_results(sections, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar secciones: {str(e)}")
    
    def show_results(self, sections, summary):
        """Display query results with optimized vertical space usage"""
        # Show and configure results frame
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # COLUMN LAYOUT - Create two main columns
        columns_container = tk.Frame(self.results_frame)
        columns_container.pack(fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN - Professor info and summary with scrollbar
        left_column_container = tk.Frame(columns_container, width=400)
        left_column_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_column_container.pack_propagate(False)  # Maintain fixed width
        
        # Create canvas and scrollbar for left column
        canvas = tk.Canvas(left_column_container, width=380)
        left_scrollbar = ttk.Scrollbar(left_column_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # RIGHT COLUMN - Sections table
        right_column = tk.Frame(columns_container)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === LEFT COLUMN CONTENT (now in scrollable frame) ===
        
        # Compact Professor info header
        prof_info_frame = ttk.LabelFrame(scrollable_frame, text="Profesor", padding="10")
        prof_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        prof_name = self.selected_professor['full_name']
        prof_depts = self.selected_professor['departamentos']
        
        # Professor name
        tk.Label(prof_info_frame, text=prof_name, 
                font=("Arial", 11, "bold"), fg="#2c3e50").pack(anchor=tk.W)
        
        # Department info - bigger and more prominent
        dept_label = tk.Label(prof_info_frame, text=f"Departamentos: {prof_depts}", 
                font=("Arial", 10, "bold"), wraplength=350, justify=tk.LEFT, fg="#34495e")
        dept_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Summary statistics
        summary_frame = ttk.LabelFrame(scrollable_frame, text="Resumen Estadístico", padding="12")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        
        # Create statistics container
        stats_container = tk.Frame(summary_frame)
        stats_container.pack(fill=tk.X)
        
        # ALL STATISTICS - Now with uniform formatting
        all_stats = [
            ("Total de secciones:", summary.get('total_sections', 0), "#e74c3c"),
            ("Créditos totales:", summary.get('total_credits', 0), "#27ae60"),
            ("Estudiantes totales:", summary.get('total_students', 0), "#f39c12"),
            ("Capacidad total:", summary.get('total_capacity', 0), "#3498db"),
            ("Departamentos:", len(summary.get('departments', [])), "#9b59b6"),
            ("Materias diferentes:", len(summary.get('materias', [])), "#e67e22")
        ]
        
        # Display all statistics with uniform formatting
        for label, value, color in all_stats:
            stat_frame = tk.Frame(stats_container, relief="solid", bd=1, bg="#f8f9fa")
            stat_frame.pack(fill=tk.X, pady=2, padx=1)
            
            # Create inner frame for padding
            inner_frame = tk.Frame(stat_frame, bg="#f8f9fa")
            inner_frame.pack(fill=tk.X, padx=8, pady=4)
            
            # Label
            label_widget = tk.Label(inner_frame, text=label, font=("Arial", 9, "bold"), 
                                   anchor="w", bg="#f8f9fa")
            label_widget.pack(side=tk.LEFT)
            
            # Value with prominent display
            value_widget = tk.Label(inner_frame, text=str(value), font=("Arial", 12, "bold"), 
                                   fg=color, anchor="e", bg="#f8f9fa")
            value_widget.pack(side=tk.RIGHT)
        
        # Academic levels info
        if summary.get('academic_levels'):
            levels_frame = ttk.LabelFrame(scrollable_frame, text="Niveles Académicos", padding="8")
            levels_frame.pack(fill=tk.X, pady=(0, 10))
            
            levels_text = ', '.join(summary['academic_levels'])
            tk.Label(levels_frame, text=f"Niveles: {levels_text}", font=("Arial", 9), 
                    fg="#3498db", wraplength=350).pack(anchor=tk.W)
        
        # Campus info
        if summary.get('campus_list'):
            campus_frame = ttk.LabelFrame(scrollable_frame, text="Campus", padding="8")
            campus_frame.pack(fill=tk.X, pady=(0, 10))
            
            campus_text = ', '.join(summary['campus_list'])
            tk.Label(campus_frame, text=f"Campus: {campus_text}", font=("Arial", 9), 
                    fg="#17a2b8", wraplength=350).pack(anchor=tk.W)
        
        # Departments breakdown - Only show if there are multiple departments
        if len(summary.get('departments', [])) > 1:
            dept_frame = ttk.LabelFrame(scrollable_frame, text="Distribución por Departamento", padding="10")
            dept_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Calculate sections per department
            dept_sections = {}
            for section in sections:
                dept = section['departamento']
                dept_sections[dept] = dept_sections.get(dept, 0) + 1
            
            for dept, count in sorted(dept_sections.items()):
                dept_info_frame = tk.Frame(dept_frame, relief="solid", bd=1, bg="#ecf0f1")
                dept_info_frame.pack(fill=tk.X, pady=2, padx=1)
                
                # Create inner frame for padding
                inner_dept_frame = tk.Frame(dept_info_frame, bg="#ecf0f1")
                inner_dept_frame.pack(fill=tk.X, padx=8, pady=3)
                
                # Department name
                dept_display = dept[:30] + "..." if len(dept) > 30 else dept
                tk.Label(inner_dept_frame, text=f"• {dept_display}", 
                        font=("Arial", 9), bg="#ecf0f1", anchor="w").pack(side=tk.LEFT)
                
                # Section count with percentage
                percentage = (count / len(sections)) * 100
                count_text = f"{count} secciones ({percentage:.1f}%)"
                tk.Label(inner_dept_frame, text=count_text, 
                        font=("Arial", 9, "bold"), fg="#7f8c8d", bg="#ecf0f1", anchor="e").pack(side=tk.RIGHT)
        
        # Export button
        export_btn = ttk.Button(scrollable_frame, text="📄 Exportar", 
                              command=lambda: self.export_results(sections, summary),
                              style="Teal.TButton")
        export_btn.pack(fill=tk.X, pady=(10, 5))
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        # === RIGHT COLUMN CONTENT ===
        
        # Sections table title
        table_title_frame = tk.Frame(right_column)
        table_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(table_title_frame, text="Detalle de Secciones", 
                font=("Arial", 14, "bold"), fg="#2c3e50").pack(side=tk.LEFT)
        
        # Section count badge
        count_label = tk.Label(table_title_frame, text=f"{len(sections)} secciones", 
                              font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d", 
                              padx=8, pady=2, relief="solid", bd=1)
        count_label.pack(side=tk.RIGHT)
        
        # Sections table frame
        table_frame = tk.Frame(right_column)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview for sections
        columns = ('NRC', 'Materia', 'Departamento', 'Créditos', 'Estudiantes', 'Campus', 'Sesiones')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_configs = {
            'NRC': {'width': 70, 'text': 'NRC'},
            'Materia': {'width': 150, 'text': 'Materia'},
            'Departamento': {'width': 150, 'text': 'Departamento'},
            'Créditos': {'width': 70, 'text': 'Créditos'},
            'Estudiantes': {'width': 90, 'text': 'Estudiantes'},
            'Campus': {'width': 80, 'text': 'Campus'},
            'Sesiones': {'width': 70, 'text': 'Sesiones'}
        }
        
        for col, config in column_configs.items():
            tree.heading(col, text=config['text'])
            tree.column(col, width=config['width'], minwidth=50)
        
        # Add sections data
        for section in sections:
            # Format students
            estudiantes = f"{section['inscritos']}/{section['cupo']}"
            
            # Format materia (code only for space)
            materia = section['materia_codigo']
            
            # Truncate department name if too long
            departamento = section['departamento'][:20] + "..." if len(section['departamento']) > 20 else section['departamento']
            
            tree.insert('', tk.END, values=(
                section['nrc'],
                materia,
                departamento,
                section['creditos'],
                estudiantes,
                section['campus'],
                section['num_sessions']
            ))
        
        # Scrollbar for table
        tree_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add alternating row colors
        tree.tag_configure('oddrow', background='#f8f9fa')
        tree.tag_configure('evenrow', background='white')
        
        # Apply row colors
        for i, child in enumerate(tree.get_children()):
            if i % 2 == 0:
                tree.item(child, tags=('evenrow',))
            else:
                tree.item(child, tags=('oddrow',))
                
    def clear_search(self):
        """Clear search field and reload all professors"""
        self.search_var.set("")
        self.load_professors()
        self.query_btn.config(state="disabled")
        self.selected_professor = None       
    '''
    
    def export_results(self, sections, summary):
        """Export results to console with improved formatting"""
        try:
            prof_name = self.selected_professor['full_name']
            prof_depts = self.selected_professor['departamentos']
            
            print("\n" + "="*120)
            print(f"SECCIONES DEL PROFESOR: {prof_name}")
            print(f"DEPARTAMENTOS: {prof_depts}")
            print("="*120)
            
            # Print summary
            print(f"\nRESUMEN ESTADÍSTICO:")
            print(f"• Total de secciones: {summary['total_sections']}")
            print(f"• Total de créditos: {summary['total_credits']}")
            print(f"• Total de estudiantes: {summary['total_students']}")
            print(f"• Capacidad total: {summary['total_capacity']}")
            print(f"• Departamentos: {len(summary['departments'])}")
            print(f"• Materias diferentes: {len(summary['materias'])}")
            print(f"• Total de sesiones: {summary['total_sessions']}")
            print(f"• Niveles académicos: {', '.join(summary['academic_levels']) if summary['academic_levels'] else 'Ninguno'}")
            print(f"• Campus: {', '.join(summary['campus_list']) if summary['campus_list'] else 'Ninguno'}")
            print(f"• Departamentos involucrados: {', '.join(summary['departments'])}")
            
            # Department breakdown
            if len(summary['departments']) > 1:
                print(f"\nDISTRIBUCIÓN POR DEPARTAMENTO:")
                dept_sections = {}
                for section in sections:
                    dept = section['departamento']
                    dept_sections[dept] = dept_sections.get(dept, 0) + 1
                
                for dept, count in sorted(dept_sections.items()):
                    percentage = (count / len(sections)) * 100
                    print(f"• {dept}: {count} secciones ({percentage:.1f}%)")
            
            # Print detailed sections
            print(f"\nDETALLE DE SECCIONES:")
            print("-" * 120)
            print(f"{'NRC':<8} {'Materia':<15} {'Departamento':<25} {'Créditos':<9} {'Estudiantes':<12} {'Campus':<10} {'Sesiones':<9} {'Nombre Materia':<25}")
            print("-" * 120)
            
            for section in sections:
                nrc = str(section['nrc'])
                materia_code = section['materia_codigo'][:14]  # Truncate for table
                departamento = section['departamento'][:24]  # Truncate for table
                creditos = str(section['creditos'])
                estudiantes = f"{section['inscritos']}/{section['cupo']}"
                campus = section['campus'][:9]  # Truncate for table
                sesiones = str(section['num_sessions'])
                nombre_materia = section['materia_nombre'][:24]  # Truncate for table
                
                print(f"{nrc:<8} {materia_code:<15} {departamento:<25} {creditos:<9} {estudiantes:<12} {campus:<10} {sesiones:<9} {nombre_materia:<25}")
            
            print("="*120)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola con formato mejorado.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    '''
    
    def close_dialog(self):
        """Close the dialog"""
        if self.callback:
            self.callback()
        self.dialog.destroy()

# Add this new class to the ui_components.py file:

class MateriaSectionsDialog:
    """Dialog for querying materia sections"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.selected_materia = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Consultar Secciones de Materia")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Setup TTK styles for Mac compatibility
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI with TTK buttons"""
        # Main container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button on the same row
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Consultar Secciones de Materia", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button - TTK
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Selection frame with better styling
        selection_frame = ttk.LabelFrame(main_frame, text="Selección de Materia", padding="15")
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # NEW: Department filter section
        filter_container = tk.Frame(selection_frame)
        filter_container.pack(fill=tk.X, pady=(0, 15))
        
        # Department filter row
        dept_filter_frame = tk.Frame(filter_container)
        dept_filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(dept_filter_frame, text="🏢 Filtrar por Departamento:", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.dept_filter_var = tk.StringVar()
        self.dept_filter_combo = ttk.Combobox(dept_filter_frame, textvariable=self.dept_filter_var,
                                            state="readonly", width=40)
        self.dept_filter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.dept_filter_combo.bind('<<ComboboxSelected>>', self.on_department_filter_change)
        
        # Clear department filter button
        clear_dept_btn = ttk.Button(dept_filter_frame, text="✕ Todos", command=self.clear_department_filter,
                                style="Gray.TButton", width=8)
        clear_dept_btn.pack(side=tk.LEFT)
        
        # Search section - more compact and elegant
        search_container = tk.Frame(selection_frame)
        search_container.pack(fill=tk.X, pady=(0, 15))
        
        # Search input with modern styling
        search_input_frame = tk.Frame(search_container)
        search_input_frame.pack(fill=tk.X)
        
        # Search icon and entry in same line
        tk.Label(search_input_frame, text="🔍", font=("Arial", 14)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_input_frame, textvariable=self.search_var, 
                                    font=("Arial", 11), width=40,
                                    relief="solid", bd=1)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Clear search button
        clear_btn = ttk.Button(search_input_frame, text="✕", command=self.clear_search,
                              style="Gray.TButton", width=3)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Materia selection table
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create Treeview for materia selection
        columns = ('Código', 'Nombre', 'Departamento', 'Créditos', 'Secciones', 'Sesiones', 'Estudiantes')
        self.materia_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        
        # Configure columns
        column_configs = {
            'Código': {'width': 100, 'text': 'Código'},
            'Nombre': {'width': 250, 'text': 'Nombre'},
            'Departamento': {'width': 200, 'text': 'Departamento'},
            'Créditos': {'width': 70, 'text': 'Créditos'},
            'Secciones': {'width': 80, 'text': 'Secciones'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Estudiantes': {'width': 90, 'text': 'Estudiantes'}
        }
        
        for col, config in column_configs.items():
            self.materia_tree.heading(col, text=config['text'])
            self.materia_tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar for materia table
        mat_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.materia_tree.yview)
        self.materia_tree.configure(yscrollcommand=mat_scrollbar.set)
        
        self.materia_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.materia_tree.bind('<<TreeviewSelect>>', self.on_materia_select)
        
        # Add alternating row colors for better readability
        self.materia_tree.tag_configure('oddrow', background='#f8f9fa')
        self.materia_tree.tag_configure('evenrow', background='white')
        
        # Action buttons container
        action_container = tk.Frame(selection_frame)
        action_container.pack(fill=tk.X)
        
        # Query button - centered and prominent
        self.query_btn = ttk.Button(
            action_container, 
            text="📖 CONSULTAR SECCIONES", 
            command=self.query_sections,
            state="disabled",
            style="Green.TButton"
        )
        self.query_btn.pack(expand=True)
        
        # Results frame
        self.results_frame = tk.Frame(main_frame)
        
        # Load materias
        self.load_departments()
        self.load_materias()
    
    
    def load_materias(self, filter_text=""):
        """Load materias into table with department and search filtering"""
        # Clear existing data
        for item in self.materia_tree.get_children():
            self.materia_tree.delete(item)
        
        self.materias_data = []
        
        try:
            all_materias = self.db_manager.get_all_materias_with_stats()
            
            # Apply department filter first
            department_filter = self.get_current_department_filter()
            if department_filter:
                all_materias = [m for m in all_materias if m['departamento'] == department_filter]
            
            # Apply search filter if provided
            if filter_text:
                filtered_materias = []
                filter_lower = filter_text.lower()
                for materia in all_materias:
                    if (filter_lower in materia['codigo'].lower() or 
                        filter_lower in materia['nombre'].lower() or
                        filter_lower in materia['departamento'].lower()):
                        filtered_materias.append(materia)
                materias = filtered_materias
            else:
                materias = all_materias
            
            # Sort by department then by code
            materias.sort(key=lambda x: (x['departamento'], x['codigo']))
            
            # Add materias to table
            for i, materia in enumerate(materias):
                # Truncate names if too long for better display
                nombre_display = materia['nombre']
                if len(nombre_display) > 35:
                    nombre_display = nombre_display[:32] + "..."
                
                dept_display = materia['departamento']
                if len(dept_display) > 25:
                    dept_display = dept_display[:22] + "..."
                
                # Determine row tag for alternating colors
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                item = self.materia_tree.insert('', tk.END, values=(
                    materia['codigo'],
                    nombre_display,
                    dept_display,
                    materia['creditos'],
                    materia['num_sections'],
                    materia['num_sessions'],
                    materia['total_students']
                ), tags=(tag,))
                
                self.materias_data.append(materia)
            
            # Update search placeholder if no results
            if not materias and (filter_text or department_filter):
                no_results_msg = "Sin resultados"
                if department_filter and filter_text:
                    detail_msg = f"No hay materias en '{department_filter}' que coincidan con '{filter_text}'"
                elif department_filter:
                    detail_msg = f"No hay materias en el departamento '{department_filter}'"
                elif filter_text:
                    detail_msg = f"No hay materias que coincidan con '{filter_text}'"
                else:
                    detail_msg = "Intente con otros criterios de búsqueda"
                
                self.materia_tree.insert('', tk.END, values=(
                    no_results_msg, detail_msg, "", "", "", "", ""
                ), tags=('no-results',))
                
                # Configure no-results tag
                self.materia_tree.tag_configure('no-results', background='#fff3cd', foreground='#856404')
            
            # Update count information
            self.update_results_count(len(materias), len(all_materias))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar materias: {str(e)}")
    
    def update_results_count(self, filtered_count, total_count):
        """Update the display to show filtering results count"""
        department_filter = self.get_current_department_filter()
        search_filter = self.search_var.get().strip()
        
        if department_filter or search_filter:
            # Show filter status
            status_parts = []
            if department_filter:
                status_parts.append(f"Dept: {department_filter}")
            if search_filter:
                status_parts.append(f"Búsqueda: '{search_filter}'")
            
            filter_status = " | ".join(status_parts)
            count_msg = f"Mostrando {filtered_count} de {total_count} materias ({filter_status})"
        else:
            count_msg = f"Mostrando {filtered_count} materias"
        
        # Update the dialog title with count info
        base_title = "Consultar Secciones de Materia"
        if filtered_count != total_count:
            self.dialog.title(f"{base_title} - {filtered_count}/{total_count}")
        else:
            self.dialog.title(base_title)
    
    def clear_search(self):
        """Clear search field and reload all materias"""
        self.search_var.set("")
        self.load_materias()
        self.query_btn.config(state="disabled")
        self.selected_materia = None
    
    def on_search_change(self, event=None):
        """Handle search text change with delay"""
        if hasattr(self, 'search_timer'):
            self.dialog.after_cancel(self.search_timer)
        
        self.search_timer = self.dialog.after(300, self.search_materias)
    
    def search_materias(self):
        """Search materias based on input"""
        search_text = self.search_var.get().strip()
        self.load_materias(search_text)
        self.query_btn.config(state="disabled")
        self.selected_materia = None
    
    def on_materia_select(self, event=None):
        """Handle materia selection from table"""
        selection = self.materia_tree.selection()
        if selection:
            item = selection[0]
            values = self.materia_tree.item(item, 'values')
            
            # Check if it's a valid materia selection (not a "no results" item)
            if values and values[0] != "Sin resultados":
                # Find the materia in our data by matching the codigo
                selected_codigo = values[0]
                
                for materia in self.materias_data:
                    if materia['codigo'] == selected_codigo:
                        self.selected_materia = materia
                        self.query_btn.config(state="normal")
                        return
            
            # If we get here, no valid materia was selected
            self.selected_materia = None
            self.query_btn.config(state="disabled")
        else:
            self.selected_materia = None
            self.query_btn.config(state="disabled")
    
    def query_sections(self):
        """Query and display materia sections"""
        if not self.selected_materia:
            messagebox.showwarning("Advertencia", "Por favor seleccione una materia.")
            return
        
        try:
            materia_codigo = self.selected_materia['codigo']
            
            # Get sections and summary
            sections = self.db_manager.get_materia_sections(materia_codigo)
            summary = self.db_manager.get_materia_sections_summary(materia_codigo)
            
            if not sections:
                messagebox.showinfo("Sin resultados", 
                                   f"La materia {self.selected_materia['display_name']} "
                                   "no tiene secciones asignadas.")
                return
            
            # Show results
            self.show_results(sections, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar secciones: {str(e)}")
    
    # Add these methods to the MateriaSectionsDialog class:
    
    def load_departments(self):
        """Load departments into filter combobox"""
        try:
            departments = self.db_manager.get_departamentos()
            
            # Add "Todos los departamentos" option at the beginning
            dept_options = ["-- Todos los departamentos --"] + sorted(departments)
            self.dept_filter_combo['values'] = dept_options
            
            # Set default selection
            self.dept_filter_var.set("-- Todos los departamentos --")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar departamentos: {str(e)}")
    
    def on_department_filter_change(self, event=None):
        """Handle department filter change"""
        # Clear current search to avoid conflicts
        self.search_var.set("")
        
        # Reload materias with department filter
        self.load_materias()
        
        # Clear selection
        self.query_btn.config(state="disabled")
        self.selected_materia = None
        
        # Update status
        selected_dept = self.dept_filter_var.get()
        if selected_dept == "-- Todos los departamentos --":
            self.update_filter_status("Mostrando todas las materias")
        else:
            self.update_filter_status(f"Filtrado por: {selected_dept}")
    
    def clear_department_filter(self):
        """Clear department filter and show all materias"""
        self.dept_filter_var.set("-- Todos los departamentos --")
        self.search_var.set("")
        self.load_materias()
        self.query_btn.config(state="disabled")
        self.selected_materia = None
        self.update_filter_status("Mostrando todas las materias")
    
    def get_current_department_filter(self):
        """Get current department filter value"""
        selected = self.dept_filter_var.get()
        return None if selected == "-- Todos los departamentos --" else selected
    
    def update_filter_status(self, message):
        """Update filter status (you can add a status label if needed)"""
        # For now, we'll just update the window title to show filter status
        current_title = "Consultar Secciones de Materia"
        if "Filtrado por:" in message:
            dept_name = message.split("Filtrado por: ")[1]
            self.dialog.title(f"{current_title} - {dept_name}")
        else:
            self.dialog.title(current_title)
    
    def show_results(self, sections, summary):
        """Display query results with optimized vertical space usage"""
        # Show and configure results frame
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # COLUMN LAYOUT - Create two main columns
        columns_container = tk.Frame(self.results_frame)
        columns_container.pack(fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN - Materia info and summary with scrollbar
        left_column_container = tk.Frame(columns_container, width=400)
        left_column_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_column_container.pack_propagate(False)  # Maintain fixed width
        
        # Create canvas and scrollbar for left column
        canvas = tk.Canvas(left_column_container, width=380)
        left_scrollbar = ttk.Scrollbar(left_column_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # RIGHT COLUMN - Sections table
        right_column = tk.Frame(columns_container)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === LEFT COLUMN CONTENT (now in scrollable frame) ===
        
        # Compact Materia info header
        mat_info_frame = ttk.LabelFrame(scrollable_frame, text="Materia", padding="10")
        mat_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Materia name and code
        materia_title = f"{self.selected_materia['codigo']} - {self.selected_materia['nombre']}"
        tk.Label(mat_info_frame, text=materia_title, 
                font=("Arial", 11, "bold"), fg="#2c3e50", wraplength=350).pack(anchor=tk.W)
        
        # Department info
        dept_label = tk.Label(mat_info_frame, text=f"Departamento: {summary['department']}", 
                font=("Arial", 10, "bold"), wraplength=350, justify=tk.LEFT, fg="#34495e")
        dept_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Summary statistics
        summary_frame = ttk.LabelFrame(scrollable_frame, text="Resumen Estadístico", padding="12")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create statistics container
        stats_container = tk.Frame(summary_frame)
        stats_container.pack(fill=tk.X)
        
        # ALL STATISTICS - Now with uniform formatting
        all_stats = [
            ("Total de secciones:", summary.get('total_sections', 0), "#e74c3c"),
            ("Estudiantes totales:", summary.get('total_students', 0), "#f39c12"),
            ("Capacidad total:", summary.get('total_capacity', 0), "#3498db"),
            ("Total de sesiones:", summary.get('total_sessions', 0), "#9b59b6"),
            ("Profesores asignados:", len(summary.get('professors', [])), "#e67e22"),
            ("Campus:", len(summary.get('campus_list', [])), "#17a2b8")
        ]
        
        # Display all statistics with uniform formatting
        for label, value, color in all_stats:
            stat_frame = tk.Frame(stats_container, relief="solid", bd=1, bg="#f8f9fa")
            stat_frame.pack(fill=tk.X, pady=2, padx=1)
            
            # Create inner frame for padding
            inner_frame = tk.Frame(stat_frame, bg="#f8f9fa")
            inner_frame.pack(fill=tk.X, padx=8, pady=4)
            
            # Label
            label_widget = tk.Label(inner_frame, text=label, font=("Arial", 9, "bold"), 
                                   anchor="w", bg="#f8f9fa")
            label_widget.pack(side=tk.LEFT)
            
            # Value with prominent display
            value_widget = tk.Label(inner_frame, text=str(value), font=("Arial", 12, "bold"), 
                                   fg=color, anchor="e", bg="#f8f9fa")
            value_widget.pack(side=tk.RIGHT)
        
        # Materia details info
        details_frame = ttk.LabelFrame(scrollable_frame, text="Detalles de la Materia", padding="8")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        details_info = [
            ("Créditos:", summary.get('credits', 0)),
            ("Nivel académico:", summary.get('academic_level', 'No especificado')),
            ("Modo de calificación:", summary.get('grading_mode', 'No especificado')),
            ("Período:", summary.get('period', 'No especificado'))
        ]
        
        for detail_label, detail_value in details_info:
            detail_row = tk.Frame(details_frame)
            detail_row.pack(fill=tk.X, pady=1)
            
            tk.Label(detail_row, text=detail_label, font=("Arial", 9), 
                    fg="#495057").pack(side=tk.LEFT)
            tk.Label(detail_row, text=str(detail_value), font=("Arial", 9, "bold"), 
                    fg="#212529").pack(side=tk.RIGHT)
        
        # Campus info (if multiple)
        if len(summary.get('campus_list', [])) > 1:
            campus_frame = ttk.LabelFrame(scrollable_frame, text="Campus", padding="8")
            campus_frame.pack(fill=tk.X, pady=(0, 10))
            
            campus_text = ', '.join(summary['campus_list'])
            tk.Label(campus_frame, text=f"Campus: {campus_text}", font=("Arial", 9), 
                    fg="#17a2b8", wraplength=350).pack(anchor=tk.W)
        
        # Professors info (if any)
        if summary.get('professors'):
            prof_frame = ttk.LabelFrame(scrollable_frame, text="Profesores Asignados", padding="8")
            prof_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Show first few professors, with "..." if there are more
            prof_list = summary['professors'][:5]  # Show only first 5
            if len(summary['professors']) > 5:
                prof_text = ', '.join(prof_list) + f" y {len(summary['professors']) - 5} más..."
            else:
                prof_text = ', '.join(prof_list)
            
            tk.Label(prof_frame, text=prof_text, font=("Arial", 9), 
                    fg="#6f42c1", wraplength=350, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Export button
        export_btn = ttk.Button(scrollable_frame, text="📄 Exportar", 
                              command=lambda: self.export_results(sections, summary),
                              style="Teal.TButton")
        export_btn.pack(fill=tk.X, pady=(10, 5))
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        # === RIGHT COLUMN CONTENT ===
        
        # Sections table title
        table_title_frame = tk.Frame(right_column)
        table_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(table_title_frame, text="Detalle de Secciones", 
                font=("Arial", 14, "bold"), fg="#2c3e50").pack(side=tk.LEFT)
        
        # Section count badge
        count_label = tk.Label(table_title_frame, text=f"{len(sections)} secciones", 
                              font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d", 
                              padx=8, pady=2, relief="solid", bd=1)
        count_label.pack(side=tk.RIGHT)
        
        # Sections table frame
        table_frame = tk.Frame(right_column)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview for sections
        columns = ('NRC', 'Indicador', 'Estudiantes', 'Profesores', 'Sesiones', 'Campus')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_configs = {
            'NRC': {'width': 80, 'text': 'NRC'},
            'Indicador': {'width': 80, 'text': 'Indicador'},
            'Estudiantes': {'width': 100, 'text': 'Estudiantes'},
            'Profesores': {'width': 200, 'text': 'Profesores'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Campus': {'width': 100, 'text': 'Campus'}
        }
        
        for col, config in column_configs.items():
            tree.heading(col, text=config['text'])
            tree.column(col, width=config['width'], minwidth=50)
        
        # Add sections data
        for section in sections:
            # Format students
            estudiantes = f"{section['inscritos']}/{section['cupo']}"
            
            # Format professors (truncate if too long)
            profesores = section['profesores']
            if len(profesores) > 30:
                profesores = profesores[:27] + "..."
            
            tree.insert('', tk.END, values=(
                section['nrc'],
                section['indicador'],
                estudiantes,
                profesores,
                section['num_sessions'],
                section['campus']
            ))
        
        # Scrollbar for table
        tree_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add alternating row colors
        tree.tag_configure('oddrow', background='#f8f9fa')
        tree.tag_configure('evenrow', background='white')
        
        # Apply row colors
        for i, child in enumerate(tree.get_children()):
            if i % 2 == 0:
                tree.item(child, tags=('evenrow',))
            else:
                tree.item(child, tags=('oddrow',))
    
    def export_results(self, sections, summary):
        """Export results to console with improved formatting"""
        try:
            materia_name = f"{self.selected_materia['codigo']} - {self.selected_materia['nombre']}"
            
            print("\n" + "="*120)
            print(f"SECCIONES DE LA MATERIA: {materia_name}")
            print(f"DEPARTAMENTO: {summary['department']}")
            print("="*120)
            
            # Print summary
            print(f"\nRESUMEN ESTADÍSTICO:")
            print(f"• Total de secciones: {summary['total_sections']}")
            print(f"• Estudiantes totales: {summary['total_students']}")
            print(f"• Capacidad total: {summary['total_capacity']}")
            print(f"• Total de sesiones: {summary['total_sessions']}")
            print(f"• Profesores asignados: {len(summary['professors'])}")
            print(f"• Créditos: {summary['credits']}")
            print(f"• Nivel académico: {summary['academic_level']}")
            print(f"• Modo de calificación: {summary['grading_mode']}")
            print(f"• Período: {summary['period']}")
            print(f"• Campus: {', '.join(summary['campus_list']) if summary['campus_list'] else 'No especificado'}")
            
            # Professors list
            if summary['professors']:
                print(f"\nPROFESORES ASIGNADOS:")
                for i, prof in enumerate(summary['professors'], 1):
                    print(f"{i}. {prof}")
            
            # Print detailed sections
            print(f"\nDETALLE DE SECCIONES:")
            print("-" * 120)
            print(f"{'NRC':<8} {'Indicador':<10} {'Estudiantes':<12} {'Sesiones':<9} {'Campus':<15} {'Profesores':<40}")
            print("-" * 120)
            
            for section in sections:
                nrc = str(section['nrc'])
                indicador = section['indicador'][:9]  # Truncate for table
                estudiantes = f"{section['inscritos']}/{section['cupo']}"
                sesiones = str(section['num_sessions'])
                campus = section['campus'][:14]  # Truncate for table
                profesores = section['profesores'][:39]  # Truncate for table
                
                print(f"{nrc:<8} {indicador:<10} {estudiantes:<12} {sesiones:<9} {campus:<15} {profesores:<40}")
            
            print("="*120)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola con formato mejorado.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def close_dialog(self):
        """Close the dialog"""
        if self.callback:
            self.callback()
        self.dialog.destroy()
    
    
        
class DepartmentProfessorsDialog:
    """Multi-step dialog for querying professors by department"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.selected_departamento = None
        self.selected_professor = None
        self.profesores_data = []
        self.current_step = 0  # 0: Select Department, 1: Select Professor, 2: Show Results
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Consultar Profesores por Departamento")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Setup TTK styles for Mac compatibility
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI with TTK buttons"""
        # Main container
        self.main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button on the same row
        title_frame = tk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Consultar Profesores por Departamento", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button - TTK
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Progress indicator
        self.progress_frame = tk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_label = tk.Label(self.progress_frame, text="Paso 1: Seleccionar Departamento",
                                     font=("Arial", 12, "bold"), fg="#2c3e50")
        self.progress_label.pack()
        
        # Content frame (will change based on step)
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Navigation button frame
        self.nav_frame = tk.Frame(self.main_frame)
        self.nav_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Start with step 1
        self.show_step_1()
    
    def show_step_1(self):
        """Step 1: Select department"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.progress_label.config(text="Paso 1: Seleccionar Departamento")
        
        # Instructions
        instructions = ttk.Label(self.content_frame, 
                                text="Seleccione un departamento para ver sus profesores y estadísticas:",
                                font=("Arial", 11))
        instructions.pack(pady=(0, 20))
        
        # Department selection table
        table_container = tk.Frame(self.content_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create Treeview for department selection
        columns = ('Departamento', 'Profesores', 'Secciones', 'Sesiones', 'Estudiantes')
        self.dept_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=12)
        
        # Configure columns
        column_configs = {
            'Departamento': {'width': 300, 'text': 'Departamento'},
            'Profesores': {'width': 100, 'text': 'Profesores'},
            'Secciones': {'width': 100, 'text': 'Secciones'},
            'Sesiones': {'width': 100, 'text': 'Sesiones'},
            'Estudiantes': {'width': 120, 'text': 'Estudiantes'}
        }
        
        for col, config in column_configs.items():
            self.dept_tree.heading(col, text=config['text'])
            self.dept_tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar for department table
        dept_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.dept_tree.yview)
        self.dept_tree.configure(yscrollcommand=dept_scrollbar.set)
        
        self.dept_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dept_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.dept_tree.bind('<<TreeviewSelect>>', self.on_department_select)
        
        # Add alternating row colors
        self.dept_tree.tag_configure('oddrow', background='#f8f9fa')
        self.dept_tree.tag_configure('evenrow', background='white')
        
        # Load departments
        self.load_departments()
        
        # Setup navigation buttons
        self.setup_step_1_navigation()
    
    def load_departments(self):
        """Load departments into table"""
        # Clear existing data
        for item in self.dept_tree.get_children():
            self.dept_tree.delete(item)
        
        try:
            departamentos = self.db_manager.get_departamentos_with_professor_stats()
            
            for i, dept in enumerate(departamentos):
                # Determine row tag for alternating colors
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                item = self.dept_tree.insert('', tk.END, values=(
                    dept['nombre'],
                    dept['num_professors'],
                    dept['num_sections'],
                    dept['num_sessions'],
                    dept['total_students']
                ), tags=(tag,))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar departamentos: {str(e)}")
    
    def on_department_select(self, event=None):
        """Handle department selection"""
        selection = self.dept_tree.selection()
        if selection:
            item = selection[0]
            values = self.dept_tree.item(item, 'values')
            if values:
                self.selected_departamento = {
                    'nombre': values[0],
                    'num_professors': int(values[1]),
                    'num_sections': int(values[2]),
                    'num_sessions': int(values[3]),
                    'total_students': int(values[4])
                }
                # Enable next button
                if hasattr(self, 'next_btn'):
                    self.next_btn.config(state="normal")
        else:
            self.selected_departamento = None
            if hasattr(self, 'next_btn'):
                self.next_btn.config(state="disabled")
    
    def setup_step_1_navigation(self):
        """Setup navigation buttons for step 1"""
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # Next button (initially disabled)
        self.next_btn = ttk.Button(self.nav_frame, text="Siguiente →", 
                                 command=self.go_to_step_2, state="disabled",
                                 style="Blue.TButton")
        self.next_btn.pack(side=tk.RIGHT)
    
    def go_to_step_2(self):
        """Go to step 2 - select professor"""
        if not self.selected_departamento:
            messagebox.showwarning("Advertencia", "Por favor seleccione un departamento.")
            return
        
        self.current_step = 1
        self.show_step_2()
    
    def show_step_2(self):
        """Step 2: Select professor from department"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.progress_label.config(text="Paso 2: Seleccionar Profesor")
        
        # Show selected department info
        dept_info_frame = ttk.LabelFrame(self.content_frame, text="Departamento Seleccionado", padding="10")
        dept_info_frame.pack(fill=tk.X, pady=(0, 15))
        
        dept_name = self.selected_departamento['nombre']
        dept_stats = (f"{self.selected_departamento['num_professors']} profesores, "
                     f"{self.selected_departamento['num_sections']} secciones, "
                     f"{self.selected_departamento['total_students']} estudiantes")
        
        tk.Label(dept_info_frame, text=dept_name, font=("Arial", 12, "bold"), fg="#2c3e50").pack(anchor=tk.W)
        tk.Label(dept_info_frame, text=dept_stats, font=("Arial", 10), fg="#7f8c8d").pack(anchor=tk.W)
        
        # NEW: Search section for professors
        search_container = tk.Frame(self.content_frame)
        search_container.pack(fill=tk.X, pady=(0, 15))
        
        # Search input with modern styling
        search_input_frame = tk.Frame(search_container)
        search_input_frame.pack(fill=tk.X)
        
        # Search icon and entry in same line
        tk.Label(search_input_frame, text="🔍", font=("Arial", 14)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.prof_search_var = tk.StringVar()
        self.prof_search_entry = tk.Entry(search_input_frame, textvariable=self.prof_search_var, 
                                        font=("Arial", 11), width=40,
                                        relief="solid", bd=1)
        self.prof_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.prof_search_entry.bind('<KeyRelease>', self.on_prof_search_change)
        
        # Clear search button
        clear_prof_btn = ttk.Button(search_input_frame, text="✕", command=self.clear_prof_search,
                                style="Gray.TButton", width=3)
        clear_prof_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Professor selection table
        table_container = tk.Frame(self.content_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create Treeview for professor selection
        columns = ('Profesor', 'Tipo', 'Secciones', 'Sesiones', 'Estudiantes')
        self.prof_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=10)
        
        # Configure columns
        column_configs = {
            'Profesor': {'width': 250, 'text': 'Profesor'},
            'Tipo': {'width': 100, 'text': 'Tipo'},
            'Secciones': {'width': 100, 'text': 'Secciones'},
            'Sesiones': {'width': 100, 'text': 'Sesiones'},
            'Estudiantes': {'width': 120, 'text': 'Estudiantes'}
        }
        
        for col, config in column_configs.items():
            self.prof_tree.heading(col, text=config['text'])
            self.prof_tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar for professor table
        prof_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.prof_tree.yview)
        self.prof_tree.configure(yscrollcommand=prof_scrollbar.set)
        
        self.prof_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prof_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        
        # Add alternating row colors
        self.prof_tree.tag_configure('oddrow', background='#f8f9fa')
        self.prof_tree.tag_configure('evenrow', background='white')
        
        # Load professors from selected department
        self.load_professors()
        
        # Setup navigation buttons
        self.setup_step_2_navigation()
    
    
    def load_professors(self, filter_text=""):
        """Load professors from selected department with optional filtering"""
        # Clear existing data
        for item in self.prof_tree.get_children():
            self.prof_tree.delete(item)
        
        try:
            # Get all professors from the department
            all_profesores = self.db_manager.get_profesores_by_departamento(self.selected_departamento['nombre'])
            
            # Filter professors if search text provided
            if filter_text:
                filtered_profesores = []
                filter_lower = filter_text.lower()
                for prof in all_profesores:
                    if (filter_lower in prof['nombres'].lower() or 
                        filter_lower in prof['apellidos'].lower() or
                        filter_lower in prof['full_name'].lower() or
                        filter_lower in prof['tipo'].lower()):
                        filtered_profesores.append(prof)
                profesores = filtered_profesores
            else:
                profesores = all_profesores
            
            # Store filtered professor data separately for later use
            self.profesores_data = []
            
            # Get additional stats for each professor and populate table
            for i, prof in enumerate(profesores):
                # Get sections and sessions count
                sections = self.db_manager.get_profesor_sections(prof['id'])
                sessions = self.db_manager.get_profesor_sessions(prof['id'])
                
                # Calculate total students
                total_students = sum(section['inscritos'] for section in sections)
                
                # Determine row tag for alternating colors
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                
                item = self.prof_tree.insert('', tk.END, values=(
                    prof['full_name'],
                    prof['tipo'],
                    len(sections),
                    len(sessions),
                    total_students
                ), tags=(tag,))
                
                # Store professor data for later reference using list index
                self.profesores_data.append(prof)
            
            # Show "no results" message if search yielded nothing
            if not profesores and filter_text:
                self.prof_tree.insert('', tk.END, values=(
                    "Sin resultados", f"No se encontraron profesores con '{filter_text}'", "", "", ""
                ), tags=('no-results',))
                
                # Configure no-results tag
                self.prof_tree.tag_configure('no-results', background='#fff3cd', foreground='#856404')
            
            # Update the count in instructions or status
            if hasattr(self, 'content_frame'):
                # Update instructions to show count
                for widget in self.content_frame.winfo_children():
                    if isinstance(widget, ttk.Label) and "seleccione un profesor" in widget.cget('text').lower():
                        if filter_text:
                            count_text = f"Se encontraron {len(profesores)} profesores que coinciden con '{filter_text}'. Seleccione uno:"
                        else:
                            count_text = f"Seleccione un profesor ({len(profesores)} disponibles):"
                        widget.config(text=count_text)
                        break
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
    
    def setup_step_2_navigation(self):
        """Setup navigation buttons for step 2"""
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # Back button
        back_btn = ttk.Button(self.nav_frame, text="← Atrás", 
                            command=self.go_back_to_step_1,
                            style="Gray.TButton")
        back_btn.pack(side=tk.LEFT)
        
    
    def go_back_to_step_1(self):
        """Go back to step 1"""
        self.current_step = 0
        self.selected_departamento = None
        self.selected_professor = None
        if hasattr(self, 'prof_search_var'):
            self.prof_search_var.set("")
        self.show_step_1()
    
    def show_professor_sections(self):
        """Show the selected professor's sections (reuse existing dialog)"""
        if not self.selected_professor:
            messagebox.showwarning("Advertencia", "Por favor seleccione un profesor.")
            return
        
        try:
            # Create a ProfessorSectionsDialog but pre-populate it with our selected professor
            sections_dialog = ProfessorSectionsDialog(self.dialog, self.db_manager)
            
            # Set the selected professor and directly query sections
            sections_dialog.selected_professor = self.selected_professor
            sections_dialog.query_sections()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar secciones: {str(e)}")
    
    
    # Add these methods to the DepartmentProfessorsDialog class:
    
    def on_prof_search_change(self, event=None):
        """Handle professor search text change with delay"""
        if hasattr(self, 'prof_search_timer'):
            self.dialog.after_cancel(self.prof_search_timer)
        
        self.prof_search_timer = self.dialog.after(300, self.search_professors_in_dept)
    
    def search_professors_in_dept(self):
        """Search professors within the department based on input"""
        search_text = self.prof_search_var.get().strip()
        self.load_professors(search_text)
        # Clear selection when searching
        self.selected_professor = None
        if hasattr(self, 'view_sections_btn'):
            self.view_sections_btn.config(state="disabled")
    
    def clear_prof_search(self):
        """Clear professor search field and reload all professors"""
        self.prof_search_var.set("")
        self.load_professors()
        self.selected_professor = None
        if hasattr(self, 'view_sections_btn'):
            self.view_sections_btn.config(state="disabled")
    
    def close_dialog(self):
        """Close the dialog"""
        if self.callback:
            self.callback()
        self.dialog.destroy()
        
# Add this new class to ui_components.py:

class PersonalDataLinkingDialog:
    """Dialog for personal data linking process"""
    
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.linking_engine = None
        self.current_step = 0  # 0: Load File, 1: Review Matches, 2: Apply Changes
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Vincular Datos Personales")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Setup TTK styles
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main container
        self.main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button
        title_frame = tk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Vincular Datos Personales", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Progress indicator
        self.progress_frame = tk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = tk.Label(self.progress_frame, text="Paso 1: Cargar Archivo de Datos Personales",
                                     font=("Arial", 12, "bold"), fg="#2c3e50")
        self.progress_label.pack()
        
        # Content frame (changes based on step)
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Navigation frame
        self.nav_frame = tk.Frame(self.main_frame)
        self.nav_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Start with step 1
        self.show_step_1()
    
    def show_step_1(self):
        """Step 1: Load personal data file"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.progress_label.config(text="Paso 1: Cargar Archivo de Datos Personales")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(self.content_frame, text="Instrucciones", padding="15")
        instructions_frame.pack(fill=tk.X, pady=(0, 20))
        
        instructions_text = (
            "1. Seleccione el archivo CSV con los datos personales de los profesores\n"
            "2. El archivo debe contener columnas: 'Apellido y Nombre', 'Cargo', 'Número de persona', etc.\n"
            "3. Solo se procesarán registros de 'FACULTAD DE INGENIERÍA'\n"
            "4. Se buscarán coincidencias con los profesores existentes en la base de datos"
        )
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text, 
                                    font=("Arial", 10), justify=tk.LEFT)
        instructions_label.pack(anchor=tk.W)
        
        # File selection section
        file_frame = ttk.LabelFrame(self.content_frame, text="Seleccionar Archivo", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        # File selection row
        select_row = tk.Frame(file_frame)
        select_row.pack(fill=tk.X, pady=(0, 10))
        
        self.select_file_btn = ttk.Button(select_row, text="📁 Seleccionar Archivo CSV",
                                         command=self.select_file, style="Blue.TButton")
        self.select_file_btn.pack(side=tk.LEFT)
        
        # File info display
        self.file_info_var = tk.StringVar(value="Ningún archivo seleccionado")
        self.file_info_label = tk.Label(file_frame, textvariable=self.file_info_var,
                                      font=("Arial", 9), fg="gray")
        self.file_info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Process button
        self.process_file_btn = ttk.Button(file_frame, text="⚙️ Procesar Archivo",
                                         command=self.process_file, state="disabled",
                                         style="Green.TButton")
        self.process_file_btn.pack(anchor=tk.W)
        
        # Current database status
        status_frame = ttk.LabelFrame(self.content_frame, text="Estado Actual de la Base de Datos", padding="15")
        status_frame.pack(fill=tk.X)
        
        try:
            total_profs = len(self.db_manager.get_all_profesores())
            without_personal = len(self.db_manager.get_professors_without_personal_data())
            with_personal = total_profs - without_personal
            
            status_text = (
                f"• Total de profesores: {total_profs}\n"
                f"• Con datos personales: {with_personal}\n"
                f"• Sin datos personales: {without_personal}"
            )
            
        except Exception as e:
            status_text = f"Error al obtener estadísticas: {str(e)}"
        
        status_label = tk.Label(status_frame, text=status_text, font=("Arial", 10), justify=tk.LEFT)
        status_label.pack(anchor=tk.W)
        
        # Setup navigation
        self.setup_step_1_navigation()
    
    def select_file(self):
        """Select personal data file"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de datos personales",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            # Validate file
            from personal_data_processor import validate_personal_data_file
            validation = validate_personal_data_file(file_path)
            
            if not validation['valid']:
                error_msg = "Errores en el archivo:\n" + "\n".join(validation['errors'])
                messagebox.showerror("Archivo inválido", error_msg)
                return
            
            # Show warnings if any
            if validation['warnings']:
                warning_msg = "Advertencias:\n" + "\n".join(validation['warnings'])
                if not messagebox.askyesno("Advertencias", f"{warning_msg}\n\n¿Continuar?"):
                    return
            
            self.selected_file = file_path
            file_info = validation['file_info']
            
            info_text = (
                f"📄 {os.path.basename(file_path)} ({file_info['file_size_mb']} MB)\n"
                f"Registros totales: {file_info['total_rows']}"
            )
            
            if 'engineering_records' in file_info:
                info_text += f", Ingeniería: {file_info['engineering_records']}"
            
            self.file_info_var.set(info_text)
            self.process_file_btn.config(state="normal")
    
    def process_file(self):
        """Process the selected file"""
        if not hasattr(self, 'selected_file'):
            messagebox.showerror("Error", "Por favor seleccione un archivo primero")
            return
        
        # Create progress dialog
        progress = ProgressDialog(self.dialog, "Procesando datos personales", 
                                "Cargando archivo y buscando coincidencias...")
        
        try:
            # Create linking engine and process file
            from personal_data_processor import PersonalDataLinkingEngine
            self.linking_engine = PersonalDataLinkingEngine(self.db_manager)
            
            result = self.linking_engine.load_and_process_personal_data(self.selected_file)
            
            progress.close()
            
            if result['success']:
                self.process_result = result
                self.show_step_2()
            else:
                error_msg = "Errores al procesar:\n" + "\n".join(result['errors'])
                messagebox.showerror("Error de procesamiento", error_msg)
                
        except Exception as e:
            progress.close()
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")
    
    def show_step_2(self):
        """Step 2: Review matches"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.progress_label.config(text="Paso 2: Revisar Coincidencias")
        
        # Statistics summary
        stats = self.process_result['statistics']
        summary_frame = ttk.LabelFrame(self.content_frame, text="Resumen de Coincidencias", padding="15")
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create two columns for statistics
        stats_container = tk.Frame(summary_frame)
        stats_container.pack(fill=tk.X)
        
        left_stats = tk.Frame(stats_container)
        left_stats.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        right_stats = tk.Frame(stats_container)
        right_stats.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Left column stats
        left_text = (
            f"📄 Archivo procesado: {stats['file_info']['file_name']}\n"
            f"📊 Registros de ingeniería: {stats['file_info']['engineering_faculty_rows']}\n"
            f"🎯 Coincidencias encontradas: {stats['total_matches']}\n"
            f"⚡ Automáticas (≥95%): {stats['automatic_matches']}"
        )
        
        tk.Label(left_stats, text=left_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Right column stats
        right_text = (
            f"👥 Profesores existentes: {stats['existing_professors_count']}\n"
            f"📋 Sin datos personales: {stats['professors_without_personal_data']}\n"
            f"🔍 Requieren revisión: {stats['review_needed']}\n"
            f"📈 Confianza promedio: {stats['avg_confidence']:.1%}"
        )
        
        tk.Label(right_stats, text=right_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Quick actions row
        actions_row = tk.Frame(summary_frame)
        actions_row.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(actions_row, text="✓ Aprobar Automáticas", 
                  command=self.approve_automatic_matches, style="Green.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(actions_row, text="📋 Exportar Reporte", 
                  command=self.export_report, style="Teal.TButton").pack(side=tk.LEFT)
        
        # Approval status
        self.approval_status_var = tk.StringVar()
        self.approval_status_label = tk.Label(actions_row, textvariable=self.approval_status_var,
                                            font=("Arial", 9), fg="blue")
        self.approval_status_label.pack(side=tk.RIGHT)
        
        self.update_approval_status()
        
        # Matches review table
        table_frame = ttk.LabelFrame(self.content_frame, text="Revisar Coincidencias", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matches table
        self.create_matches_table(table_frame)
        
        # Setup navigation
        self.setup_step_2_navigation()
    
    # Replace the create_matches_table method in ui_components.py:
    
    def create_matches_table(self, parent):
        """Create the matches review table"""
        # Table container
        table_container = tk.Frame(parent)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for matches
        columns = ('Estado', 'Confianza', 'Profesor Existente', 'Datos Personales', 'Nuevo Tipo', 'Subcategoría')
        self.matches_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_configs = {
            'Estado': {'width': 80, 'text': 'Estado'},
            'Confianza': {'width': 80, 'text': 'Confianza'},
            'Profesor Existente': {'width': 200, 'text': 'Profesor Existente'},
            'Datos Personales': {'width': 200, 'text': 'Datos Personales'},
            'Nuevo Tipo': {'width': 150, 'text': 'Nuevo Tipo'},
            'Subcategoría': {'width': 80, 'text': 'Subcat.'}
        }
        
        for col, config in column_configs.items():
            self.matches_tree.heading(col, text=config['text'])
            self.matches_tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar
        matches_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.matches_tree.yview)
        self.matches_tree.configure(yscrollcommand=matches_scrollbar.set)
        
        self.matches_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        matches_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.matches_tree.bind('<Double-1>', self.toggle_match_approval)
        self.matches_tree.bind('<<TreeviewSelect>>', self.on_match_select)
        
        # Configure tags for different states
        self.matches_tree.tag_configure('approved', background='#d4edda', foreground='#155724')
        self.matches_tree.tag_configure('rejected', background='#f8d7da', foreground='#721c24')
        self.matches_tree.tag_configure('pending', background='#fff3cd', foreground='#856404')
        self.matches_tree.tag_configure('high_confidence', background='#e7f5e7')
        
        # ADD THIS: Dictionary to map tree items to match IDs
        self.item_to_match_id = {}
        
        # Load matches data
        self.load_matches_data()
        
        # Action buttons below table
        button_row = tk.Frame(parent)
        button_row.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_row, text="✓ Aprobar", command=self.approve_selected,
                  style="Green.TButton").pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_row, text="✗ Rechazar", command=self.reject_selected,
                  style="Red.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_row, text="📋 Detalles", command=self.show_match_details,
                  style="Blue.TButton").pack(side=tk.LEFT)
    
    def load_matches_data(self):
        """Load matches into the table"""
        # Clear existing data
        for item in self.matches_tree.get_children():
            self.matches_tree.delete(item)
        
        # Clear the mapping dictionary
        self.item_to_match_id.clear()
        
        if not self.linking_engine or not self.linking_engine.current_matches:
            return
        
        for match in self.linking_engine.current_matches:
            preview = self.linking_engine.get_match_preview(match)
            match_id = preview['match_id']
            
            # Determine status
            if match in self.linking_engine.approved_matches:
                status = "✓ APROBADO"
                tag = 'approved'
            elif match in self.linking_engine.rejected_matches:
                status = "✗ RECHAZADO"
                tag = 'rejected'
            else:
                status = "⏳ PENDIENTE"
                tag = 'pending'
                if preview['confidence'] >= 0.95:
                    tag = 'high_confidence'
            
            # Format confidence as percentage
            confidence = f"{preview['confidence']:.1%}"
            
            # Truncate long names for display
            existing_name = preview['existing']['full_name']
            if len(existing_name) > 25:
                existing_name = existing_name[:22] + "..."
            
            personal_name = preview['personal']['full_name_standardized']
            if len(personal_name) > 25:
                personal_name = personal_name[:22] + "..."
            
            new_tipo = preview['changes']['new_tipo']
            if len(new_tipo) > 20:
                new_tipo = new_tipo[:17] + "..."
            
            subcategoria = str(preview['changes']['subcategoria']) if preview['changes']['subcategoria'] else "-"
            
            item = self.matches_tree.insert('', tk.END, values=(
                status,
                confidence,
                existing_name,
                personal_name,
                new_tipo,
                subcategoria
            ), tags=(tag,))
            
            # FIXED: Store match_id in the mapping dictionary
            self.item_to_match_id[item] = match_id
    
    def approve_automatic_matches(self):
        """Approve all high confidence matches"""
        count = self.linking_engine.approve_all_high_confidence()
        self.load_matches_data()
        self.update_approval_status()
        messagebox.showinfo("Aprobación automática", f"Se aprobaron {count} coincidencias automáticas.")
    
    def toggle_match_approval(self, event=None):
        """Toggle approval status of selected match"""
        selection = self.matches_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        # FIXED: Get match_id from mapping dictionary
        match_id = self.item_to_match_id.get(item)
        if not match_id:
            return
        
        # Find the match
        match = self.linking_engine._find_match_by_id(match_id)
        if not match:
            return
        
        # Toggle status
        if match in self.linking_engine.approved_matches:
            self.linking_engine.reject_match(match_id)
        elif match in self.linking_engine.rejected_matches:
            self.linking_engine.approve_match(match_id)
        else:
            self.linking_engine.approve_match(match_id)
        
        self.load_matches_data()
        self.update_approval_status()
    
    def approve_selected(self):
        """Approve selected match"""
        selection = self.matches_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Por favor seleccione una coincidencia.")
            return
        
        item = selection[0]
        # FIXED: Get match_id from mapping dictionary
        match_id = self.item_to_match_id.get(item)
        if not match_id:
            return
        
        if self.linking_engine.approve_match(match_id):
            self.load_matches_data()
            self.update_approval_status()
    
    def reject_selected(self):
        """Reject selected match"""
        selection = self.matches_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Por favor seleccione una coincidencia.")
            return
        
        item = selection[0]
        # FIXED: Get match_id from mapping dictionary
        match_id = self.item_to_match_id.get(item)
        if not match_id:
            return
        
        if self.linking_engine.reject_match(match_id):
            self.load_matches_data()
            self.update_approval_status()
    
    def show_match_details(self):
        """Show detailed information for selected match"""
        selection = self.matches_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Por favor seleccione una coincidencia.")
            return
        
        item = selection[0]
        # FIXED: Get match_id from mapping dictionary
        match_id = self.item_to_match_id.get(item)
        if not match_id:
            return
            
        match = self.linking_engine._find_match_by_id(match_id)
        
        if match:
            self.show_match_detail_dialog(match)
    
    def show_match_detail_dialog(self, match):
        """Show detailed match information in a dialog"""
        detail_dialog = tk.Toplevel(self.dialog)
        detail_dialog.title("Detalles de Coincidencia")
        detail_dialog.geometry("600x500")
        detail_dialog.transient(self.dialog)
        
        # Create scrollable frame
        main_frame = tk.Frame(detail_dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        preview = self.linking_engine.get_match_preview(match)
        
        # Title
        title_label = tk.Label(main_frame, text="Detalles de Coincidencia", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Confidence
        conf_label = tk.Label(main_frame, text=f"Confianza: {preview['confidence']:.1%}", 
                             font=("Arial", 12, "bold"), 
                             fg="green" if preview['confidence'] >= 0.95 else "orange")
        conf_label.pack(pady=(0, 15))
        
        # Existing professor info
        existing_frame = ttk.LabelFrame(main_frame, text="Profesor Existente", padding="10")
        existing_frame.pack(fill=tk.X, pady=(0, 10))
        
        existing_text = (
            f"ID: {preview['existing']['id']}\n"
            f"Nombre: {preview['existing']['full_name']}\n"
            f"Tipo actual: {preview['existing']['tipo_actual']}\n"
            f"Departamentos: {preview['existing']['departamentos']}"
        )
        
        tk.Label(existing_frame, text=existing_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Personal data info
        personal_frame = ttk.LabelFrame(main_frame, text="Datos Personales", padding="10")
        personal_frame.pack(fill=tk.X, pady=(0, 10))
        
        personal_text = (
            f"Número de persona: {preview['personal']['person_id']}\n"
            f"Nombre estandarizado: {preview['personal']['full_name_standardized']}\n"
            f"Cargo original: {preview['personal']['cargo_original']}\n"
            f"Departamento oficial: {preview['personal']['departamento_oficial']}"
        )
        
        tk.Label(personal_frame, text=personal_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Proposed changes
        changes_frame = ttk.LabelFrame(main_frame, text="Cambios Propuestos", padding="10")
        changes_frame.pack(fill=tk.X, pady=(0, 15))
        
        changes_text = (
            f"Nuevo tipo: {preview['changes']['new_tipo']}\n"
            f"Subcategoría: {preview['changes']['subcategoria'] or 'Sin subcategoría'}\n"
            f"Número de persona: {preview['changes']['person_id']}"
        )
        
        tk.Label(changes_frame, text=changes_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Flags
        flags_frame = ttk.LabelFrame(main_frame, text="Indicadores", padding="10")
        flags_frame.pack(fill=tk.X, pady=(0, 15))
        
        flags_text = (
            f"{'✓' if preview['flags']['name_exact_match'] else '✗'} Coincidencia exacta de nombres\n"
            f"{'⚠' if preview['flags']['tipo_will_change'] else '✓'} El tipo cambiará\n"
            f"{'✓' if preview['flags']['has_person_id'] else '✗'} Tiene número de persona\n"
            f"{'✓' if preview['flags']['has_subcategoria'] else '✗'} Tiene subcategoría"
        )
        
        tk.Label(flags_frame, text=flags_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Close button
        ttk.Button(main_frame, text="Cerrar", command=detail_dialog.destroy,
                  style="Gray.TButton").pack(pady=10)
    
    def update_approval_status(self):
        """Update the approval status display"""
        if not self.linking_engine:
            return
        
        summary = self.linking_engine.get_approval_summary()
        status_text = (
            f"Aprobadas: {summary['approved']} | "
            f"Rechazadas: {summary['rejected']} | "
            f"Pendientes: {summary['pending']}"
        )
        self.approval_status_var.set(status_text)
    
    def export_report(self):
        """Export matching report"""
        try:
            file_path = self.linking_engine.export_match_report()
            messagebox.showinfo("Reporte exportado", f"Reporte guardado en:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar reporte: {str(e)}")
    
    def proceed_to_apply(self):
        """Proceed to apply approved matches"""
        summary = self.linking_engine.get_approval_summary()
        
        if summary['approved'] == 0:
            messagebox.showwarning("Sin aprobaciones", "No hay coincidencias aprobadas para aplicar.")
            return
        
        if not messagebox.askyesno("Confirmar aplicación", 
                                  f"¿Aplicar {summary['approved']} coincidencias aprobadas?\n\n"
                                  "Esta acción actualizará los registros de profesores."):
            return
        
        self.show_step_3()
    
    def show_step_3(self):
        """Step 3: Apply changes"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.progress_label.config(text="Paso 3: Aplicar Cambios")
        
        # Summary before applying
        summary = self.linking_engine.get_approval_summary()
        summary_frame = ttk.LabelFrame(self.content_frame, text="Resumen de Aplicación", padding="15")
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        summary_text = (
            f"Se aplicarán {summary['approved']} coincidencias aprobadas.\n"
            f"Los profesores serán actualizados con sus datos personales.\n\n"
            f"Cambios que se aplicarán:\n"
            f"• Número de persona\n"
            f"• Tipo de profesor actualizado\n"
            f"• Subcategoría académica\n"
            f"• Cargo original registrado"
        )
        
        tk.Label(summary_frame, text=summary_text, font=("Arial", 11), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Apply button
        apply_frame = tk.Frame(self.content_frame)
        apply_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.apply_btn = ttk.Button(apply_frame, text="🔄 APLICAR CAMBIOS",
                                   command=self.apply_changes, style="Green.TButton")
        self.apply_btn.pack()
        
        # Results area (initially empty)
        self.results_frame = ttk.LabelFrame(self.content_frame, text="Resultados", padding="15")
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Setup navigation
        self.setup_step_3_navigation()
    
    def apply_changes(self):
        """Apply the approved changes"""
        progress = ProgressDialog(self.dialog, "Aplicando cambios", "Actualizando registros de profesores...")
        
        try:
            result = self.linking_engine.apply_approved_matches()
            progress.close()
            
            # Clear results frame
            for widget in self.results_frame.winfo_children():
                widget.destroy()
            
            if result['success']:
                results_data = result['results']
                
                # Success message
                success_text = (
                    f"✅ Cambios aplicados exitosamente!\n\n"
                    f"Profesores actualizados: {results_data['updated']}\n"
                    f"Errores: {len(results_data['errors'])}"
                )
                
                success_label = tk.Label(self.results_frame, text=success_text, 
                                       font=("Arial", 12, "bold"), fg="green", justify=tk.LEFT)
                success_label.pack(anchor=tk.W, pady=(0, 15))
                
                # Show updated professors
                if results_data['updated_professors']:
                    updated_frame = ttk.LabelFrame(self.results_frame, text="Profesores Actualizados", padding="10")
                    updated_frame.pack(fill=tk.X, pady=(0, 10))
                    
                    # Create a simple list
                    for prof in results_data['updated_professors'][:10]:  # Show first 10
                        prof_text = f"• {prof['name']} → {prof['new_tipo']}"
                        if prof['subcategoria']:
                            prof_text += f" (Subcat: {prof['subcategoria']})"
                        
                        tk.Label(updated_frame, text=prof_text, font=("Arial", 9)).pack(anchor=tk.W)
                    
                    if len(results_data['updated_professors']) > 10:
                        more_label = tk.Label(updated_frame, text=f"... y {len(results_data['updated_professors']) - 10} más",
                                            font=("Arial", 9), fg="gray")
                        more_label.pack(anchor=tk.W)
                
                # Show errors if any
                if results_data['errors']:
                    error_frame = ttk.LabelFrame(self.results_frame, text="Errores", padding="10")
                    error_frame.pack(fill=tk.X)
                    
                    error_text = "\n".join(results_data['errors'][:5])  # Show first 5 errors
                    tk.Label(error_frame, text=error_text, font=("Arial", 9), fg="red").pack(anchor=tk.W)
                
                # Disable apply button
                self.apply_btn.config(state="disabled", text="✅ Cambios Aplicados")
                
            else:
                error_label = tk.Label(self.results_frame, text=f"❌ Error: {result['error']}", 
                                     font=("Arial", 12), fg="red")
                error_label.pack(anchor=tk.W)
                
        except Exception as e:
            progress.close()
            messagebox.showerror("Error", f"Error al aplicar cambios: {str(e)}")
    
    def setup_step_1_navigation(self):
        """Setup navigation for step 1"""
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # Only close button
        ttk.Button(self.nav_frame, text="Cerrar", command=self.close_dialog,
                  style="Gray.TButton").pack(side=tk.RIGHT)
    
    def setup_step_2_navigation(self):
        """Setup navigation for step 2"""
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # Back button
        ttk.Button(self.nav_frame, text="← Atrás", command=self.show_step_1,
                  style="Gray.TButton").pack(side=tk.LEFT)
        
        # Apply button
        ttk.Button(self.nav_frame, text="Aplicar Cambios →", command=self.proceed_to_apply,
                  style="Blue.TButton").pack(side=tk.RIGHT)
    
    def setup_step_3_navigation(self):
        """Setup navigation for step 3"""
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # Back to step 2
        ttk.Button(self.nav_frame, text="← Revisar", command=self.show_step_2,
                  style="Gray.TButton").pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(self.nav_frame, text="Finalizar", command=self.close_dialog,
                  style="Green.TButton").pack(side=tk.RIGHT)
    
    def on_match_select(self, event=None):
        """Handle match selection (for future use)"""
        pass
    
    def close_dialog(self):
        """Close the dialog"""
        if self.callback:
            self.callback()
        self.dialog.destroy()
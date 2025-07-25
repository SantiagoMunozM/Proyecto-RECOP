import tkinter as tk
import os
from tkinter import ttk, messagebox, filedialog
import sqlite3
from typing import Callable, Optional, List, Dict
from database import DatabaseManager
import sys
import subprocess
import json

def detect_dark_mode():
    """Detect if system is in dark mode"""
    try:
        if sys.platform == "darwin":  # macOS
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True, text=True
            )
            return result.stdout.strip() == 'Dark'
        elif sys.platform == "win32":  # Windows
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            except:
                pass
        # Linux/others - default to light mode
        return False
    except:
        return False

def get_theme_colors():
    """Get colors based on system theme"""
    is_dark = detect_dark_mode()
    
    if is_dark:
        return {
            'bg': '#2d2d2d',           # Dark background
            'fg': '#ffffff',           # White text
            'select_bg': '#404040',    # Selection background
            'select_fg': '#ffffff',    # Selection text
            'entry_bg': '#404040',     # Entry background
            'entry_fg': '#ffffff',     # Entry text
            'button_bg': '#404040',    # Button background
            'frame_bg': '#333333',     # Frame background
            'tree_bg': '#2d2d2d',      # Tree background
            'tree_fg': '#ffffff',      # Tree text
            'tree_select': '#0066cc',  # Tree selection
            'border': '#555555' ,       # Border color
            'comment': '#B0BEC5',
            'card_bg': '#353535',
            'title_bg': '#1e1e1e',
            'accent': '#64B5F6'
        }
    else:
        return {
            'bg': '#ffffff',           # Light background
            'fg': '#000000',           # Black text
            'select_bg': '#0078d4',    # Selection background
            'select_fg': '#ffffff',    # Selection text
            'entry_bg': '#ffffff',     # Entry background
            'entry_fg': '#000000',     # Entry text
            'button_bg': '#f0f0f0',    # Button background
            'frame_bg': '#f8f9fa',     # Frame background
            'tree_bg': '#ffffff',      # Tree background
            'tree_fg': '#000000',      # Tree text
            'tree_select': '#0078d4',  # Tree selection
            'border': '#cccccc',        # Border color
            'comment': '#666666',
            'card_bg': '#f8f9fa',        # Light gray for cards
            'title_bg': '#e9ecef',       # Slightly darker for titles
            'accent': '#0078d4'   
        }

def setup_ttk_styles(root):
    """Setup all TTK styles for the application (Dark mode compatible)"""
    style = ttk.Style(root)
    colors = get_theme_colors()
    
    # Configure the base theme
    style.theme_use('clam')  # Use clam as base theme
    
    # Configure basic widget styles
    style.configure('.',
                   background=colors['bg'],
                   foreground=colors['fg'],
                   bordercolor=colors['border'],
                   lightcolor=colors['bg'],
                   darkcolor=colors['bg'])
    
    # Frame styles
    style.configure('TFrame', background=colors['bg'])
    style.configure('TLabelFrame', background=colors['bg'], foreground=colors['fg'])
    style.configure('TLabelFrame.Label', background=colors['bg'], foreground=colors['fg'])
    
    style.configure('Dark.TFrame', 
               background=colors['bg'],
               relief='flat')

    style.configure('Dark.TLabelFrame',
               background=colors['bg'],
               foreground=colors['fg'],
               relief='solid',
               borderwidth=1,
               bordercolor=colors['border'])

    style.configure('Dark.TLabelFrame.Label',
               background=colors['bg'],
               foreground=colors['fg'])
    
    # Label styles
    style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
    
    # Entry styles
    style.configure('TEntry',
                   background=colors['entry_bg'],
                   foreground=colors['entry_fg'],
                   bordercolor=colors['border'],
                   insertcolor=colors['fg'])
    
    # Combobox styles
    style.configure('TCombobox',
                   background=colors['entry_bg'],
                   foreground=colors['entry_fg'],
                   bordercolor=colors['border'])
    
    # Treeview styles
    style.configure('Treeview',
                   background=colors['tree_bg'],
                   foreground=colors['tree_fg'],
                   bordercolor=colors['border'],
                   lightcolor=colors['tree_bg'],  # Add this
                   darkcolor=colors['tree_bg'],   # Add this
                   focuscolor='none')             # Add this
    
    style.configure('Treeview.Heading',
                   background=colors['button_bg'],
                   foreground=colors['fg'],
                   bordercolor=colors['border'],
                   lightcolor=colors['button_bg'],  # Add this
                   darkcolor=colors['button_bg'])   # Add this
    
    style.map('Treeview',
             background=[('selected', colors['tree_select']),
                        ('!selected', colors['tree_bg'])],  # Add this line
             foreground=[('selected', colors['select_fg']),
                        ('!selected', colors['tree_fg'])])  # Add this line
    
    style.map('Treeview.Heading',
             background=[('active', colors['select_bg'])])
    
    # Progressbar styles
    style.configure('TProgressbar',
                   background=colors['tree_select'],
                   bordercolor=colors['border'])
    
    # Button styles - Updated with better contrast
    button_styles = {
        'Blue.TButton': {'bg': '#0066cc', 'hover': '#0052a3'},
        'Green.TButton': {'bg': '#28a745', 'hover': '#1e7e34'},
        'Red.TButton': {'bg': '#dc3545', 'hover': '#bd2130'},
        'Orange.TButton': {'bg': '#fd7e14', 'hover': '#dc5a00'},
        'Teal.TButton': {'bg': '#17a2b8', 'hover': '#0f6674'},
        'Gray.TButton': {'bg': colors['button_bg'], 'hover': colors['select_bg'], 'fg': colors['fg']}
    }
    
    for style_name, style_colors in button_styles.items():
        fg_color = style_colors.get('fg', '#ffffff')
        
        style.configure(style_name,
                       font=("Arial", 10, "bold"),
                       foreground=fg_color,
                       background=style_colors['bg'],
                       bordercolor=colors['border'],
                       focuscolor='none',
                       padding=(8, 4))
        
        style.map(style_name,
                 background=[('active', style_colors['hover']),
                           ('pressed', style_colors['hover']),
                           ('disabled', colors['button_bg'])],
                 foreground=[('disabled', '#888888')])
    
    # Scrollbar styles
    style.configure('Vertical.TScrollbar',
                   background=colors['button_bg'],
                   bordercolor=colors['border'],
                   arrowcolor=colors['fg'])
    
    style.configure('Horizontal.TScrollbar',
                   background=colors['button_bg'],
                   bordercolor=colors['border'],
                   arrowcolor=colors['fg'])
    
    style.configure('TCombobox',
                   fieldbackground=colors['entry_bg'],  # This is the key property
                   background=colors['entry_bg'],
                   foreground=colors['entry_fg'],
                   bordercolor=colors['border'],
                   lightcolor=colors['entry_bg'],
                   darkcolor=colors['entry_bg'],
                   insertcolor=colors['fg'])
    
    # Configure the dropdown arrow button
    style.configure('TCombobox.downarrow',
                   background=colors['button_bg'],
                   foreground=colors['fg'])
    
    # Map states for interactive behavior
    style.map('TCombobox',
             fieldbackground=[('readonly', colors['entry_bg']),
                            ('!readonly', colors['entry_bg']),
                            ('focus', colors['entry_bg'])],
             background=[('readonly', colors['entry_bg']),
                        ('active', colors['select_bg'])],
             foreground=[('readonly', colors['entry_fg']),
                        ('!readonly', colors['entry_fg'])],
             bordercolor=[('focus', colors['tree_select'])])
    
    # Configure the dropdown listbox
    style.configure('TCombobox.Listbox',
                   background=colors['tree_bg'],
                   foreground=colors['tree_fg'],
                   selectbackground=colors['tree_select'],
                   selectforeground=colors['select_fg'])
    
    return style

def apply_dark_mode_to_dialog(dialog_window, theme_colors):
    """Universal dark mode application for any dialog window"""
    if not dialog_window or not theme_colors:
        return
    
    # Configure the main window
    dialog_window.configure(bg=theme_colors['bg'])
    
    # Apply to all child widgets recursively
    def apply_to_children(parent):
        for child in parent.winfo_children():
            widget_class = child.winfo_class()
            
            try:
                if widget_class == 'Frame':
                    child.configure(bg=theme_colors['bg'])
                    
                    # Special handling for frames that contain Treeview
                    for grandchild in child.winfo_children():
                        if grandchild.winfo_class() == 'Treeview':
                            child.configure(bg=theme_colors['tree_bg'])
                            break
                            
                elif widget_class == 'Label':
                    child.configure(bg=theme_colors['bg'], fg=theme_colors['fg'])
                elif widget_class == 'Entry':
                    child.configure(bg=theme_colors['entry_bg'], fg=theme_colors['entry_fg'],
                                  insertbackground=theme_colors['fg'],
                                  selectbackground=theme_colors['tree_select'],
                                  selectforeground=theme_colors['select_fg'])
                elif widget_class == 'Text':
                    child.configure(bg=theme_colors['entry_bg'], fg=theme_colors['entry_fg'],
                                  insertbackground=theme_colors['fg'],
                                  selectbackground=theme_colors['tree_select'],
                                  selectforeground=theme_colors['select_fg'])
                elif widget_class == 'Canvas':
                    child.configure(bg=theme_colors['bg'],
                                  highlightbackground=theme_colors['bg'])
                elif widget_class == 'Toplevel':
                    child.configure(bg=theme_colors['bg'])
                elif widget_class == 'Listbox':
                    child.configure(bg=theme_colors['tree_bg'], fg=theme_colors['tree_fg'],
                                  selectbackground=theme_colors['tree_select'],
                                  selectforeground=theme_colors['select_fg'])
                elif widget_class == 'Button':
                    # Only update regular buttons, not TTK buttons
                    child.configure(bg=theme_colors['button_bg'], fg=theme_colors['fg'],
                                  activebackground=theme_colors['select_bg'],
                                  activeforeground=theme_colors['select_fg'])
            except tk.TclError:
                # Skip widgets that can't be configured
                pass
            
            # Recursively apply to children
            apply_to_children(child)
    
    apply_to_children(dialog_window)

# Add this method after the apply_dark_mode_to_dialog function:

def configure_canvas_dark_mode(canvas, scrollable_frame, theme_colors):
    """Configure canvas and scrollable frame for dark mode"""
    canvas.configure(
        bg=theme_colors['bg'],
        highlightbackground=theme_colors['bg'],
        highlightcolor=theme_colors['bg']
    )
    
    # Configure the scrollable frame
    scrollable_frame.configure(style='Dark.TFrame')
    
    # Update all children of the scrollable frame
    def update_frame_children(frame):
        for child in frame.winfo_children():
            widget_class = child.winfo_class()
            try:
                if widget_class == 'Frame':
                    child.configure(bg=theme_colors['bg'])
                elif widget_class == 'Label':
                    child.configure(bg=theme_colors['bg'], fg=theme_colors['fg'])
                elif widget_class == 'LabelFrame':
                    child.configure(bg=theme_colors['bg'], fg=theme_colors['fg'])
                
                # Recursively update children
                update_frame_children(child)
            except tk.TclError:
                pass
    
    update_frame_children(scrollable_frame)
    
def configure_treeview_dark_mode(tree, theme_colors):
    """Configure treeview for dark mode with proper colors"""
    # Configure alternating row colors for dark mode
    tree.tag_configure('oddrow', 
                      background=theme_colors['tree_bg'], 
                      foreground=theme_colors['tree_fg'])
    tree.tag_configure('evenrow', 
                      background=theme_colors['select_bg'], 
                      foreground=theme_colors['select_fg'])
    
    # Apply to existing items
    for i, child in enumerate(tree.get_children()):
        if i % 2 == 0:
            tree.item(child, tags=('evenrow',))
        else:
            tree.item(child, tags=('oddrow',))
        
class DatabaseViewer:
    def __init__(self, parent, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.current_table = None
        self.current_page = 0
        self.page_size = 20
        self.total_records = 0
        self.total_pages = 0
        
        self.theme_colors = get_theme_colors()  
        
        temp_window = tk.Toplevel(parent)
        self.style = setup_ttk_styles(temp_window)
        temp_window.destroy()
        
        self.setup_viewer()
        apply_dark_mode_to_dialog(self.viewer_window, self.theme_colors)
    
    
    def setup_viewer(self):
        # Create viewer window
        self.viewer_window = tk.Toplevel(self.parent)
        self.viewer_window.title("Database Viewer")
        self.viewer_window.geometry("1000x700")
        self.viewer_window.configure(bg=self.theme_colors['bg'])
        
        title_frame = tk.Frame(self.viewer_window)
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        # Title label
        title_label = tk.Label(title_frame, text="Visor de Base de Datos", 
                            font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_viewer,
                            style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
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
        
        search_row1 = tk.Frame(search_frame)
        search_row1.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(search_row1, text="Buscar:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_row1, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        search_btn = ttk.Button(search_row1, text="Buscar", command=self.perform_search, style= "Blue.TButton")
        search_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(search_row1, text="Limpiar", command=self.clear_search, style="Gray.TButton")
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_frame = tk.Frame(search_frame)
        
        tk.Label(self.filter_frame, text="Filtrar por tipo:").pack(side=tk.LEFT)
    
        self.tipo_filter_var = tk.StringVar(value="Todos los tipos")
        self.tipo_filter_combo = ttk.Combobox(self.filter_frame, textvariable=self.tipo_filter_var,
                                            state="readonly", width=20)
        self.tipo_filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.tipo_filter_combo.bind('<<ComboboxSelected>>', self.on_tipo_filter_change)
        
        clear_filter_btn = ttk.Button(self.filter_frame, text="Limpiar Filtros", 
                                    command=self.clear_filters, style="Gray.TButton")
        clear_filter_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Table frame with scrollbars
        table_frame = tk.Frame(self.viewer_window, bg=self.theme_colors['tree_bg'])
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
        
        # Apply filters for professor table
        if self.current_table == "Profesor":
            data = self.get_filtered_profesor_data(search_term, offset)
            total_count = self.get_filtered_profesor_count(search_term)
        else:
            # Regular table data for other tables
            data = self.db_manager.get_table_data(
                self.current_table, search_term, self.page_size, offset
            )
            # FIXED: Pass table_name as first parameter, search_term as second
            total_count = self.get_total_record_count(self.current_table, search_term)
            
        self.total_records = total_count
        self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
        
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if data:
            # Get column names for the table
            columns = self.get_table_columns(self.current_table)
            
            # Configure tree columns
            self.tree['columns'] = columns
            self.tree['show'] = 'headings'
            
            # Configure column headings and widths
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=150)
            
            # Insert data
            for i, row in enumerate(data):
                # UPDATED: Format dedication data for display
                if self.current_table == "Seccion" and len(row) >= 8:
                    formatted_row = list(row)
                    # Format profesor_dedicaciones (last column) for better readability
                    if formatted_row[7]:  # profesor_dedicaciones column
                        try:
                            if isinstance(formatted_row[7], str):
                                dedicaciones = json.loads(formatted_row[7])
                            elif isinstance(formatted_row[7], dict):
                                dedicaciones = formatted_row[7]
                            else:
                                dedicaciones = {}
                            
                            if dedicaciones:
                                # Format as "ID1:ded1%, ID2:ded2%"
                                formatted_ded = ", ".join([f"{pid}:{ded}%" for pid, ded in dedicaciones.items()])
                                formatted_row[7] = formatted_ded
                            else:
                                formatted_row[7] = "Sin dedicaciones"
                        except Exception as e:
                            formatted_row[7] = "Error en formato"
                    
                    self.tree.insert('', tk.END, values=formatted_row, tags=('evenrow' if i % 2 == 0 else 'oddrow',))
                else:
                    self.tree.insert('', tk.END, values=row, tags=('evenrow' if i % 2 == 0 else 'oddrow',))
            
            # Apply dark mode colors to treeview
            configure_treeview_dark_mode(self.tree, self.theme_colors)
        
        # Update UI elements
        self.update_pagination_controls()
        self.update_info_labels()
        
        # Disable delete button when table refreshes
        self._disable_delete_button()
        
    
    def get_filtered_profesor_data(self, search_term=None, offset=0):
        """Get filtered professor data with tipo filter"""
        try:
            query = "SELECT * FROM Profesor"
            params = []
            conditions = []
            
            # Apply search filter
            if search_term:
                conditions.append("(nombres LIKE ? OR apellidos LIKE ?)")
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            # Apply tipo filter
            tipo_filter = self.get_current_tipo_filter()
            if tipo_filter:
                conditions.append("tipo = ?")
                params.append(tipo_filter)
            
            # Add WHERE clause if conditions exist
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Add ordering and pagination
            query += " ORDER BY apellidos, nombres"
            query += f" LIMIT {self.page_size} OFFSET {offset}"
            
            return self.db_manager.execute_query(query, tuple(params))
            
        except Exception as e:
            print(f"Error getting filtered professor data: {e}")
            return []

    def get_filtered_profesor_count(self, search_term=None):
        """Get total count of filtered professors"""
        try:
            query = "SELECT COUNT(*) FROM Profesor"
            params = []
            conditions = []
            
            # Apply search filter
            if search_term:
                conditions.append("(nombres LIKE ? OR apellidos LIKE ?)")
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            # Apply tipo filter
            tipo_filter = self.get_current_tipo_filter()
            if tipo_filter:
                conditions.append("tipo = ?")
                params.append(tipo_filter)
            
            # Add WHERE clause if conditions exist
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            result = self.db_manager.execute_query(query, tuple(params), fetch_one=True)
            return result[0] if result else 0
            
        except Exception as e:
            print(f"Error getting filtered professor count: {e}")
            return 0


    def get_total_record_count(self, table_name: str, search_term: str = None) -> int:
        """Get total record count for current table with optional search"""
        try:
            # Special handling for Sesion table
            if table_name == "Sesion":
                query = """
                    SELECT COUNT(*) 
                    FROM Sesion ses
                    JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
                    JOIN Materia m ON sec.materia_codigo = m.codigo
                """
                params = []
                
                if search_term:
                    query += """ WHERE (
                        ses.tipoHorario LIKE ? OR
                        ses.edificio LIKE ? OR
                        ses.salon LIKE ? OR
                        m.codigo LIKE ? OR
                        m.nombre LIKE ? OR
                        m.departamento_nombre LIKE ? OR
                        CAST(ses.seccion_NRC AS TEXT) LIKE ?
                    )"""
                    search_param = f"%{search_term}%"
                    params.extend([search_param] * 7)
                
                result = self.db_manager.execute_query(query, tuple(params), fetch_one=True)
                return result[0] if result else 0
            
            # Original logic for other tables
            if search_term:
                columns = self.get_table_columns(table_name)
                if columns:
                    search_conditions = []
                    for col in columns:
                        search_conditions.append(f"CAST({col} AS TEXT) LIKE ?")
                    query = f"SELECT COUNT(*) FROM {table_name} WHERE ({' OR '.join(search_conditions)})"
                    params = [f"%{search_term}%"] * len(columns)
                    result = self.db_manager.execute_query(query, tuple(params), fetch_one=True)
                    return result[0] if result else 0
            
            result = self.db_manager.execute_query(f"SELECT COUNT(*) FROM {table_name}", fetch_one=True)
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting record count for {table_name}: {e}")
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
        """Update information labels with filter status"""
        start_record = self.current_page * self.page_size + 1 if self.total_records > 0 else 0
        end_record = min((self.current_page + 1) * self.page_size, self.total_records)
        
        # Build info message
        info_text = f"Tabla: {self.current_table} - Total: {self.total_records} registros"
        
        # Add filter status for professor table
        if self.current_table == "Profesor":
            tipo_filter = self.get_current_tipo_filter()
            if tipo_filter:
                info_text += f" (Filtrado por tipo: {tipo_filter})"
        
        self.info_label.config(text=info_text)
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
        self.clear_filters()
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
            

    def close_viewer(self):
        """Close the database viewer window"""
        try:
            # Cancel any pending search timers
            if hasattr(self, 'search_timer'):
                self.viewer_window.after_cancel(self.search_timer)
            
            # Destroy the window
            self.viewer_window.destroy()
            
        except Exception as e:
            print(f"Error closing viewer: {e}")
            # Force destroy if there's an error
            try:
                self.viewer_window.destroy()
            except:
                pass
    
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        try:
            # Special handling for Sesion table with materia information
            if table_name == "Sesion":
                return [
                    'id', 'tipoHorario', 'horaInicio', 'horaFin', 'duracion', 
                    'edificio', 'salon', 'atributoSalon', 'dias', 'PER', 
                    'seccion_NRC', 'materia_codigo', 'materia_nombre', 
                    'departamento_nombre', 'profesor_ids'
                ]
                
            if table_name == "Seccion":
                return [
                    'NRC', 'indicador', 'cupo', 'inscritos', 'cupoDisponible',
                    'lista_cruzada', 'materia_codigo', 'profesor_dedicaciones'
                ]
            
            # Original logic for other tables
            result = self.db_manager.execute_query(f"PRAGMA table_info({table_name})")
            return [row[1] for row in result]  # Column name is at index 1
        except Exception as e:
            print(f"Error getting columns for table {table_name}: {e}")
            return []
        
        
    def on_table_selected(self, event=None):
        """Handle table selection with filter support"""
        self.current_table = self.table_var.get()
        self.current_page = 0
        self.search_var.set("")
        self.clear_filters()  # Clear any existing filters
        
        # Show/hide filter frame based on table
        if self.current_table == "Profesor":
            self.load_profesor_tipos()  # Load available tipos
            self.filter_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.filter_frame.pack_forget()
        
        self.load_table_data()
    
    def load_profesor_tipos(self):
        """Load available professor types for filter"""
        try:
            # Get unique tipos from database
            tipos_result = self.db_manager.execute_query(
                "SELECT DISTINCT tipo FROM Profesor WHERE tipo IS NOT NULL ORDER BY tipo"
            )
            
            tipos = [row[0] for row in tipos_result if row[0]]
            tipos.insert(0, "Todos los tipos")  # Add default option
            
            self.tipo_filter_combo['values'] = tipos
            
        except Exception as e:
            print(f"Error loading professor tipos: {e}")
            self.tipo_filter_combo['values'] = ["Todos los tipos"]
    
    def on_tipo_filter_change(self, event=None):
        """Handle tipo filter change"""
        self.current_page = 0  # Reset to first page
        self.load_table_data()
    
    def clear_filters(self):
        """Clear all filters"""
        self.tipo_filter_var.set("Todos los tipos")
        if self.current_table == "Profesor":
            self.current_page = 0
            self.load_table_data()
    
    def get_current_tipo_filter(self):
        """Get current tipo filter value"""
        filter_value = self.tipo_filter_var.get()
        return None if filter_value == "Todos los tipos" else filter_value
            
class ProgressDialog:
    """Progress dialog for long-running operations"""
    def __init__(self, parent, title="Procesando...", message="Por favor espere..."):
        self.parent = parent
        self.cancelled = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x180")
        self.dialog.transient(parent)
        
        # Center dialog
        self._center_dialog()
        
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        
        # Prevent closing
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message label
        self.message_label = tk.Label(main_frame, text=message, font=("Arial", 10),
                                      wraplength=400, justify=tk.CENTER)
        self.message_label.pack(pady=(0, 15))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))
        self.progress.start()
        
        # Cancel button
        self.cancel_btn = tk.Button(main_frame, text="Cancelar", command=self._on_cancel)
        self.cancel_btn.pack()
        
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
        
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
        self.dialog.lift()
    
    def close(self):
        """Close the dialog with error handling"""
        try:
            if hasattr(self, 'progress') and self.progress:
                self.progress.stop()
        except tk.TclError:
            # Progress bar may already be destroyed
            pass
        
        try:
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.destroy()
        except tk.TclError:
            # Dialog may already be destroyed
            pass
    
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled
    
        # Add these methods to the DatabaseViewer class:
    
    def on_table_selected(self, event=None):
        """Handle table selection with filter support"""
        self.current_table = self.table_var.get()
        self.current_page = 0
        self.search_var.set("")
        self.clear_filters()  # Clear any existing filters
        
        # Show/hide filter frame based on table
        if self.current_table == "Profesor":
            self.load_profesor_tipos()  # Load available tipos
            self.filter_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.filter_frame.pack_forget()
        
        self.load_table_data()
    
    def load_profesor_tipos(self):
        """Load available professor types for filter"""
        try:
            # Get unique tipos from database
            tipos_result = self.db_manager.execute_query(
                "SELECT DISTINCT tipo FROM Profesor WHERE tipo IS NOT NULL ORDER BY tipo"
            )
            
            tipos = [row[0] for row in tipos_result if row[0]]
            tipos.insert(0, "Todos los tipos")  # Add default option
            
            self.tipo_filter_combo['values'] = tipos
            
        except Exception as e:
            print(f"Error loading professor tipos: {e}")
            self.tipo_filter_combo['values'] = ["Todos los tipos"]
    
    def on_tipo_filter_change(self, event=None):
        """Handle tipo filter change"""
        self.current_page = 0  # Reset to first page
        self.load_table_data()
    
    def clear_filters(self):
        """Clear all filters"""
        self.tipo_filter_var.set("Todos los tipos")
        if self.current_table == "Profesor":
            self.current_page = 0
            self.load_table_data()
    
    def get_current_tipo_filter(self):
        """Get current tipo filter value"""
        filter_value = self.tipo_filter_var.get()
        return None if filter_value == "Todos los tipos" else filter_value

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
        
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
        
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
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
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
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
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
        
        # Filters row
        filters_frame = tk.Frame(selection_frame)
        filters_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Department filter
        tk.Label(filters_frame, text="Departamento:").pack(side=tk.LEFT)
        
        self.department_var = tk.StringVar(value="Todos los departamentos")
        self.department_combo = ttk.Combobox(filters_frame, textvariable=self.department_var,
                                            state="readonly", width=25)
        self.department_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.department_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Tipo filter
        tk.Label(filters_frame, text="Tipo:").pack(side=tk.LEFT)
        
        self.tipo_var = tk.StringVar(value="Todos los tipos")
        self.tipo_combo = ttk.Combobox(filters_frame, textvariable=self.tipo_var,
                                    state="readonly", width=15)
        self.tipo_combo.pack(side=tk.LEFT, padx=(5, 15))
        self.tipo_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Clear filters button
        clear_filters_btn = ttk.Button(filters_frame, text="🔄 Limpiar Filtros",
                                    command=self.clear_filters, style="Gray.TButton")
        clear_filters_btn.pack(side=tk.LEFT, padx=(5, 0))
        
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
        
        self.results_info_frame = tk.Frame(selection_frame)
        self.results_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.results_label = tk.Label(self.results_info_frame, text="", 
                                    font=("Arial", 9), fg="gray")
        self.results_label.pack(side=tk.LEFT)
        
        # Professor selection table - UPDATED WITH PAGINATION
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create paginated professor selection table
        columns = ('Nombre', 'Departamentos', 'Sesiones', 'Secciones')
        column_configs = {
            'Nombre': {'width': 250, 'text': 'Profesor'},
            'Departamentos': {'width': 300, 'text': 'Departamentos'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        # Create paginated table for professor selection
        self.professor_table = PaginatedTreeview(table_container, columns, column_configs, page_size=15)
        self.professor_table.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event to the paginated table
        self.professor_table.bind_selection(self.on_professor_select)
        
        # Query button
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
        self.load_filters()
        self.load_professors()

    
    # In the ProfessorSessionsDialog class, update the load_professors method:
    
    # In the ProfessorSessionsDialog class, update the load_professors method:
    
    def load_professors(self, filter_text="", tipo_filter=None, department_filter=None):
        """Load professors into paginated table with filters"""
        try:
            # Get all professors with filtering
            if tipo_filter or department_filter:
                professors = self.get_filtered_professors(filter_text, tipo_filter, department_filter)
            else:
                # Use existing method for name filtering only
                if filter_text:
                    professors = self.db_manager.execute_query(
                        """SELECT DISTINCT p.id, p.nombres, p.apellidos, p.tipo,
                                  COUNT(DISTINCT sp.sesion_id) as num_sessions,
                                  COUNT(DISTINCT scp.seccion_NRC) as num_sections
                           FROM Profesor p
                           LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
                           LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
                           WHERE LOWER(p.nombres) LIKE ? OR LOWER(p.apellidos) LIKE ?
                           GROUP BY p.id, p.nombres, p.apellidos, p.tipo
                           ORDER BY p.apellidos, p.nombres""",
                        (f"%{filter_text.lower()}%", f"%{filter_text.lower()}%")
                    )
                else:
                    professors = self.db_manager.execute_query(
                        """SELECT DISTINCT p.id, p.nombres, p.apellidos, p.tipo,
                                  COUNT(DISTINCT sp.sesion_id) as num_sessions,
                                  COUNT(DISTINCT scp.seccion_NRC) as num_sections
                           FROM Profesor p
                           LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
                           LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
                           GROUP BY p.id, p.nombres, p.apellidos, p.tipo
                           ORDER BY p.apellidos, p.nombres"""
                    )
            
            # Process results and prepare both table data and professor objects
            table_data = []
            professor_objects = []  # Keep the original objects separate
            
            for row in professors:
                profesor_id = row[0]
                
                # Get departments for this professor
                dept_results = self.db_manager.execute_query(
                    """SELECT DISTINCT departamento_nombre 
                       FROM ProfesorDepartamento 
                       WHERE profesor_id = ? 
                       ORDER BY departamento_nombre""",
                    (profesor_id,)
                )
                
                departamentos = [dept[0] for dept in dept_results]
                departamentos_str = ', '.join(departamentos) if departamentos else 'Sin departamento'
                
                # Create professor object
                professor_obj = {
                    'id': row[0],
                    'nombres': row[1],
                    'apellidos': row[2],
                    'tipo': row[3],
                    'full_name': f"{row[1]} {row[2]}",
                    'departamentos': departamentos_str,
                    'num_sessions': row[4] if row[4] else 0,
                    'num_sections': row[5] if row[5] else 0
                }
                
                # Create table row data
                table_row = [
                    professor_obj['full_name'],
                    departamentos_str,
                    professor_obj['num_sessions'],
                    professor_obj['num_sections']
                ]
                
                table_data.append(table_row)
                professor_objects.append(professor_obj)
            
            # Store the professor objects, NOT the table data
            self.professors_data = professor_objects
            
            # Update paginated table with table data
            self.professor_table.set_data(table_data)
            
            # Update results count
            total_professors = len(self.db_manager.get_all_profesores())
            self.update_results_count(len(professor_objects), total_professors)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
    
    # Also update the on_professor_select method to handle the paginated table properly:
    
    def on_professor_select(self, event=None):
        """Handle professor selection from paginated table"""
        selected_data = self.professor_table.get_selected_item()
        if selected_data and len(selected_data) >= 1:
            # The selected_data is a tuple from the table
            prof_name = selected_data[0]  # First column is the name
            
            # Find the corresponding professor object
            for prof in self.professors_data:
                if prof['full_name'] == prof_name:
                    self.selected_professor = prof
                    self.query_btn.config(state="normal")
                    return
        
        # If we get here, no professor was found
        self.selected_professor = None
        self.query_btn.config(state="disabled")
    
    def get_filtered_professors(self, name_filter="", tipo_filter=None, department_filter=None):
        """Get professors with tipo and department filters"""
        
        # Base query
        base_query = """
            SELECT DISTINCT p.id, p.nombres, p.apellidos, p.tipo,
                   COUNT(DISTINCT sp.sesion_id) as num_sessions,
                   COUNT(DISTINCT scp.seccion_NRC) as num_sections
            FROM Profesor p
            LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
            LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
        """
        
        # Add department join if filtering by department
        if department_filter and department_filter != "Todos los departamentos":
            base_query += """
                JOIN ProfesorDepartamento pd ON p.id = pd.profesor_id
            """
        
        # WHERE conditions
        conditions = []
        params = []
        
        # Name filter
        if name_filter:
            conditions.append("(LOWER(p.nombres) LIKE ? OR LOWER(p.apellidos) LIKE ?)")
            params.extend([f"%{name_filter.lower()}%", f"%{name_filter.lower()}%"])
        
        # Tipo filter (Planta/Cátedra classification)
        if tipo_filter and tipo_filter != "Todos los tipos":
            if tipo_filter == "Planta":
                conditions.append("(p.tipo != 'CÁTEDRA' OR p.tipo IS NULL)")
            elif tipo_filter == "Cátedra":
                conditions.append("p.tipo = 'CÁTEDRA'")
            else:
                # Specific tipo selected
                conditions.append("p.tipo = ?")
                params.append(tipo_filter)
        
        # Department filter
        if department_filter and department_filter != "Todos los departamentos":
            conditions.append("pd.departamento_nombre = ?")
            params.append(department_filter)
        
        # Combine query
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " GROUP BY p.id, p.nombres, p.apellidos, p.tipo ORDER BY p.apellidos, p.nombres"
        
        return self.db_manager.execute_query(base_query, tuple(params))
    
    # Update the on_professor_select method:
    
    
    # Update search-related methods:
    
    def search_professors(self):
        """Search professors based on input"""
        search_text = self.search_var.get().strip()
        self.load_professors(search_text)
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
    def clear_search(self):
        """Clear search field and reload all professors"""
        self.search_var.set("")
        self.load_professors()
        self.query_btn.config(state="disabled")
        self.selected_professor = None

    
        # Add these methods to the ProfessorSessionsDialog class:
    
    def load_filters(self):
        """Load filter options"""
        try:
            # Load departments
            departments = self.db_manager.get_departamentos()
            department_options = ["Todos los departamentos"] + departments
            self.department_combo['values'] = department_options
            
            # Load professor tipos with Planta/Cátedra classification
            tipos_results = self.db_manager.execute_query(
                "SELECT DISTINCT tipo FROM Profesor WHERE tipo IS NOT NULL ORDER BY tipo"
            )
            tipos = [row[0] for row in tipos_results if row[0]]
            
            self.tipo_combo['values'] = tipos
            
        except Exception as e:
            print(f"Error loading filters: {e}")
    
    def on_filter_change(self, event=None):
        """Handle filter change"""
        self.search_professors()
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
    def clear_filters(self):
        """Clear all filters"""
        self.department_var.set("Todos los departamentos")
        self.tipo_var.set("Todos los tipos")
        self.search_var.set("")
        self.load_professors()
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
    def search_professors(self):
        """Search professors with filters"""
        search_text = self.search_var.get().strip()
        tipo_filter = self.get_current_tipo_filter()
        department_filter = self.get_current_department_filter()
        
        self.load_professors(search_text, tipo_filter, department_filter)
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
    def get_current_tipo_filter(self):
        """Get current tipo filter value"""
        filter_value = self.tipo_var.get()
        return None if filter_value == "Todos los tipos" else filter_value
    
    def get_current_department_filter(self):
        """Get current department filter value"""
        filter_value = self.department_var.get()
        return None if filter_value == "Todos los departamentos" else filter_value
    
    def update_results_count(self, filtered_count, total_count):
        """Update results count display"""
        if filtered_count == total_count:
            self.results_label.config(text=f"Mostrando {total_count} profesores")
        else:
            self.results_label.config(text=f"Mostrando {filtered_count} de {total_count} profesores")
    
    def on_search_change(self, event=None):
        """Handle search text change with delay"""
        if hasattr(self, 'search_timer'):
            self.dialog.after_cancel(self.search_timer)
        
        self.search_timer = self.dialog.after(300, self.search_professors)
    
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
            stat_frame = tk.Frame(stats_container, relief="solid", bd=1, bg= self.theme_colors['bg'])
            stat_frame.pack(fill=tk.X, pady=2, padx=1)
            
            # Create inner frame for padding
            value_color = self.theme_colors['tree_select']  # Use accent color consistently
        
            tk.Label(stat_frame, text=label, font=("Arial", 9), 
                bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(side=tk.LEFT)
            tk.Label(stat_frame, text=str(value), font=("Arial", 9, "bold"),
                bg=self.theme_colors['bg'], fg=value_color).pack(side=tk.RIGHT)
        
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
        
        configure_canvas_dark_mode(canvas, scrollable_frame, self.theme_colors)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        # === RIGHT COLUMN CONTENT - UPDATED WITH PAGINATION ===
    
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
        
        # UPDATED: Use paginated treeview instead of regular treeview
        columns = ('NRC', 'Materia', 'Departamento', 'Horario', 'Días', 'Lugar', 'PER' ,'Estudiantes')
        column_configs = {
            'NRC': {'width': 70, 'text': 'NRC'},
            'Materia': {'width': 180, 'text': 'Materia'},
            'Departamento': {'width': 120, 'text': 'Departamento'},
            'Horario': {'width': 100, 'text': 'Horario'},
            'Días': {'width': 60, 'text': 'Días'},
            'Lugar': {'width': 120, 'text': 'Lugar'},
            'PER': {'width': 50, 'text': 'PER'},
            'Estudiantes': {'width': 80, 'text': 'Estudiantes'}
        }
        
        # Create paginated table
        self.sessions_table = PaginatedTreeview(right_column, columns, column_configs, page_size=20)
        self.sessions_table.pack(fill=tk.BOTH, expand=True)
        
        # Prepare data for pagination
        table_data = []
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
            
            table_data.append((
                session['nrc'],
                materia,
                departamento,
                horario,
                dias,
                lugar,
                session['per'],
                estudiantes
            ))
        
        # Set data in paginated table
        self.sessions_table.set_data(table_data)

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
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
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
        
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create paginated professor selection table
        columns = ('Nombre', 'Departamentos', 'Sesiones', 'Secciones')
        column_configs = {
            'Nombre': {'width': 250, 'text': 'Profesor'},
            'Departamentos': {'width': 300, 'text': 'Departamentos'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        # Create paginated table for professor selection
        self.professor_table = PaginatedTreeview(table_container, columns, column_configs, page_size=15)
        self.professor_table.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.professor_table.bind_selection(self.on_professor_select)
        
        # Query button
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
    
        # Update the load_professors method in ProfessorSessionsDialog:
    
    def load_professors(self, filter_text=""):
        """Load professors into paginated table"""
        self.professors_data = []
        
        try:
            all_professors = self.db_manager.get_all_profesores()
            
            # Apply search filter if provided
            if filter_text:
                filter_text = filter_text.lower()
                filtered_professors = []
                for prof in all_professors:
                    if (filter_text in prof['full_name'].lower() or 
                        filter_text in prof['departamentos'].lower()):
                        filtered_professors.append(prof)
                all_professors = filtered_professors
            
            # Prepare data for paginated table
            table_data = []
            for prof in all_professors:
                table_data.append((
                    prof['full_name'],
                    prof['departamentos'],
                    prof['num_sessions'],
                    prof['num_sections']
                ))
            
            # Store data and update paginated table
            self.professors_data = all_professors
            self.professor_table.set_data(table_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
    
    # Update the on_professor_select method:
    
    def on_professor_select(self, event=None):
        """Handle professor selection from paginated table"""
        selected_data = self.professor_table.get_selected_item()
        if selected_data:
            # Find the professor by name
            prof_name = selected_data[0]  # First column is the name
            for prof in self.professors_data:
                if prof['full_name'] == prof_name:
                    self.selected_professor = prof
                    break
            
            self.query_btn.config(state="normal")
        else:
            self.selected_professor = None
            self.query_btn.config(state="disabled")
    
    # Update search-related methods:
    
    def search_professors(self):
        """Search professors based on input"""
        search_text = self.search_var.get().strip()
        self.load_professors(search_text)
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
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
        
        configure_canvas_dark_mode(canvas, scrollable_frame, self.theme_colors)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows/Mac
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
        
        # === RIGHT COLUMN CONTENT ===
        
        # === RIGHT COLUMN CONTENT - UPDATED WITH PAGINATION ===
    
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
        
        # UPDATED: Use paginated treeview
        columns = ('NRC', 'Materia', 'Departamento', 'Créditos', 'Estudiantes', 'Campus', 'Sesiones')
        column_configs = {
            'NRC': {'width': 70, 'text': 'NRC'},
            'Materia': {'width': 150, 'text': 'Materia'},
            'Departamento': {'width': 150, 'text': 'Departamento'},
            'Créditos': {'width': 70, 'text': 'Créditos'},
            'Estudiantes': {'width': 90, 'text': 'Estudiantes'},
            'Campus': {'width': 80, 'text': 'Campus'},
            'Sesiones': {'width': 70, 'text': 'Sesiones'}
        }
        
        # Create paginated table
        self.sections_table = PaginatedTreeview(right_column, columns, column_configs, page_size=15)
        self.sections_table.pack(fill=tk.BOTH, expand=True)
        
        # Prepare data for pagination
        table_data = []
        for section in sections:
            estudiantes = f"{section['inscritos']}/{section['cupo']}"
            
            table_data.append((
                section['nrc'],
                section['materia_codigo'],
                section['departamento'][:20] + "..." if len(section['departamento']) > 20 else section['departamento'],
                section['creditos'],
                estudiantes,
                section['campus'],
                section['num_sessions']
            ))
        
        # Set data in paginated table
        self.sections_table.set_data(table_data)
                
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
        
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
    def setup_ui(self):
        """Setup the UI"""
        # Main container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Consultar Secciones de Materia", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Selección de Materia", padding="15")
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Department filter
        filter_frame = tk.Frame(selection_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(filter_frame, text="Filtrar por departamento:").pack(side=tk.LEFT)
        
        self.department_var = tk.StringVar(value="Todos los departamentos")
        self.department_combo = ttk.Combobox(filter_frame, textvariable=self.department_var,
                                           state="readonly", width=30)
        self.department_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.department_combo.bind('<<ComboboxSelected>>', self.on_department_filter_change)
        
        clear_filter_btn = ttk.Button(filter_frame, text="Limpiar", command=self.clear_department_filter,
                                     style="Gray.TButton")
        clear_filter_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Search section
        search_frame = tk.Frame(selection_frame)
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(search_frame, text="Buscar materia:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Arial", 11), width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        search_btn = ttk.Button(search_frame, text="🔍", command=self.search_materias,
                               style="Blue.TButton")
        search_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        clear_btn = ttk.Button(search_frame, text="✕", command=self.clear_search,
                              style="Gray.TButton", width=3)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Results count
        self.results_label = tk.Label(selection_frame, text="", font=("Arial", 9), fg="gray")
        self.results_label.pack(pady=(0, 10))
        
        # Materia selection - UPDATED WITH PAGINATION
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create paginated materia selection table
        columns = ('Código', 'Nombre', 'Departamento', 'Créditos', 'Secciones')
        column_configs = {
            'Código': {'width': 100, 'text': 'Código'},
            'Nombre': {'width': 300, 'text': 'Nombre de la Materia'},
            'Departamento': {'width': 200, 'text': 'Departamento'},
            'Créditos': {'width': 80, 'text': 'Créditos'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        # Create paginated table for materia selection
        self.materia_table = PaginatedTreeview(table_container, columns, column_configs, page_size=15)
        self.materia_table.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.materia_table.bind_selection(self.on_materia_select)
        
        # Query button
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
        
        # Load data
        self.load_departments()
        self.load_materias()
    
    def load_departments(self):
        """Load departments for filtering"""
        try:
            departments = self.db_manager.get_departamentos()
            values = ["Todos los departamentos"] + departments
            self.department_combo['values'] = values
        except Exception as e:
            print(f"Error loading departments: {e}")
    
    def load_materias(self, filter_text=""):
        """Load materias into paginated table"""
        self.materias_data = []
        
        try:
            all_materias = self.db_manager.get_all_materias_with_stats()
            
            # Apply department filter
            dept_filter = self.get_current_department_filter()
            if dept_filter != "Todos los departamentos":
                all_materias = [m for m in all_materias if m['departamento'] == dept_filter]
            
            # Apply search filter
            if filter_text:
                filter_text = filter_text.lower()
                all_materias = [m for m in all_materias if 
                            filter_text in m['codigo'].lower() or 
                            filter_text in m['nombre'].lower()]
            
            # Prepare data for paginated table
            table_data = []
            for materia in all_materias:
                table_data.append((
                    materia['codigo'],
                    materia['nombre'],
                    materia['departamento'],
                    materia['creditos'],
                    materia['num_sections']
                ))
            
            # Store data and update paginated table
            self.materias_data = all_materias
            self.materia_table.set_data(table_data)
            
            self.update_results_count(len(all_materias), len(self.db_manager.get_all_materias()))
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar materias: {str(e)}")
    
    def update_results_count(self, filtered_count, total_count):
        """Update results count label"""
        if filtered_count == total_count:
            self.results_label.config(text=f"Mostrando {total_count} materias")
        else:
            self.results_label.config(text=f"Mostrando {filtered_count} de {total_count} materias")
    
    def get_current_department_filter(self):
        """Get current department filter"""
        return self.department_var.get()
    
    def on_department_filter_change(self, event=None):
        """Handle department filter change"""
        self.load_materias(self.search_var.get())
        self.query_btn.config(state="disabled")
        self.selected_materia = None
    
    def clear_department_filter(self):
        """Clear department filter"""
        self.department_var.set("Todos los departamentos")
        self.on_department_filter_change()
    
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
        """Handle materia selection from paginated table"""
        selected_data = self.materia_table.get_selected_item()
        if selected_data:
            # Find the materia by code
            materia_codigo = selected_data[0]  # First column is the code
            for materia in self.materias_data:
                if materia['codigo'] == materia_codigo:
                    self.selected_materia = materia
                    break
            
            self.query_btn.config(state="normal")
        else:
            self.selected_materia = None
            self.query_btn.config(state="disabled")
    
    def query_sections(self):
        """Query and display materia sections"""
        if not self.selected_materia:
            messagebox.showwarning("Selección requerida", "Por favor seleccione una materia.")
            return
        
        try:
            sections = self.db_manager.get_materia_sections(self.selected_materia['codigo'])
            summary = self.db_manager.get_materia_sections_summary(self.selected_materia['codigo'])
            
            self.show_results(sections, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar secciones: {str(e)}")
    
    def show_results(self, sections, summary):
        """Display query results"""
        # Show and configure results frame
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # COLUMN LAYOUT
        columns_container = tk.Frame(self.results_frame)
        columns_container.pack(fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN - Materia info and summary
        left_column_container = tk.Frame(columns_container, width=400)
        left_column_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_column_container.pack_propagate(False)
        
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
        
        # === LEFT COLUMN CONTENT ===
        
        # Materia info header
        materia_info_frame = ttk.LabelFrame(scrollable_frame, text="Materia", padding="10")
        materia_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        materia_name = f"{self.selected_materia['codigo']} - {self.selected_materia['nombre']}"
        
        # Materia name
        tk.Label(materia_info_frame, text=materia_name, 
                font=("Arial", 11, "bold"), fg="#2c3e50").pack(anchor=tk.W)
        
        # Department and credits info
        info_text = f"Departamento: {summary['department']}\n"
        info_text += f"Créditos: {summary['credits']} | Nivel: {summary['academic_level']}\n"
        info_text += f"Modalidad: {summary['grading_mode']} | Período: {summary['period']}"
        
        info_label = tk.Label(materia_info_frame, text=info_text, 
                             font=("Arial", 9), justify=tk.LEFT, fg="#34495e")
        info_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Summary statistics
        summary_frame = ttk.LabelFrame(scrollable_frame, text="Resumen Estadístico", padding="12")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_container = tk.Frame(summary_frame)
        stats_container.pack(fill=tk.X)
        
        # Statistics
        stats = [
            ("Total de secciones:", summary.get('total_sections', 0), "#e74c3c"),
            ("Estudiantes totales:", summary.get('total_students', 0), "#f39c12"),
            ("Capacidad total:", summary.get('total_capacity', 0), "#3498db"),
            ("Sesiones totales:", summary.get('total_sessions', 0), "#27ae60"),
            ("Profesores asignados:", len(summary.get('professors', [])), "#9b59b6")
        ]
        
        for label, value, color in stats:
            stat_frame = tk.Frame(stats_container)
            stat_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(stat_frame, text=label, font=("Arial", 9), 
                    bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(side=tk.LEFT)
            tk.Label(stat_frame, text=str(value), font=("Arial", 9, "bold"),
                    bg=self.theme_colors['bg'], fg=color).pack(side=tk.RIGHT)
        
        # Professors info
        if summary.get('professors'):
            profs_frame = ttk.LabelFrame(scrollable_frame, text="Profesores Asignados", padding="10")
            profs_frame.pack(fill=tk.X, pady=(0, 10))
            
            for i, prof in enumerate(summary['professors'][:10]):  # Show first 10
                tk.Label(profs_frame, text=f"• {prof}", font=("Arial", 8),
                        bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(anchor=tk.W)
            
            if len(summary['professors']) > 10:
                tk.Label(profs_frame, text=f"... y {len(summary['professors']) - 10} más",
                        font=("Arial", 8, "italic"), fg="gray").pack(anchor=tk.W)
        
        # Campus info
        if summary.get('campus_list'):
            campus_text = "Campus: " + ", ".join(summary['campus_list'])
            tk.Label(scrollable_frame, text=campus_text, font=("Arial", 9),
                    bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(pady=(5, 0))
        
        # Export button
        export_btn = ttk.Button(scrollable_frame, text="📄 Exportar", 
                              command=lambda: self.export_results(sections, summary),
                              style="Teal.TButton")
        export_btn.pack(fill=tk.X, pady=(10, 5))
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")
        
        configure_canvas_dark_mode(canvas, scrollable_frame, self.theme_colors)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # === RIGHT COLUMN CONTENT - UPDATED WITH PAGINATION ===
    
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
        
        # UPDATED: Use paginated treeview
        columns = ('NRC', 'Indicador', 'Profesores', 'Estudiantes', 'Sesiones')
        column_configs = {
            'NRC': {'width': 80, 'text': 'NRC'},
            'Indicador': {'width': 100, 'text': 'Indicador'},
            'Profesores': {'width': 250, 'text': 'Profesores'},
            'Estudiantes': {'width': 100, 'text': 'Estudiantes'},
            'Sesiones': {'width': 80, 'text': 'Sesiones'}
        }
        
        # Create paginated table
        self.sections_table = PaginatedTreeview(right_column, columns, column_configs, page_size=15)
        self.sections_table.pack(fill=tk.BOTH, expand=True)
        
        # Prepare data for pagination
        table_data = []
        for section in sections:
            estudiantes = f"{section['inscritos']}/{section['cupo']}"
            
            table_data.append((
                section['nrc'],
                section['indicador'],
                section['profesores'],
                estudiantes,
                section['num_sessions']
            ))
        
        # Set data in paginated table
        self.sections_table.set_data(table_data)
    
    def export_results(self, sections, summary):
        """Export results to console"""
        try:
            materia_name = f"{self.selected_materia['codigo']} - {self.selected_materia['nombre']}"
            
            print("\n" + "="*100)
            print(f"SECCIONES DE LA MATERIA: {materia_name}")
            print(f"DEPARTAMENTO: {summary['department']}")
            print("="*100)
            
            # Print summary
            print(f"\nRESUMEN:")
            print(f"• Total de secciones: {summary['total_sections']}")
            print(f"• Estudiantes totales: {summary['total_students']}")
            print(f"• Capacidad total: {summary['total_capacity']}")
            print(f"• Sesiones totales: {summary['total_sessions']}")
            print(f"• Profesores: {len(summary['professors'])}")
            
            # Print sections
            print(f"\nDETALLE DE SECCIONES:")
            print("-" * 100)
            print(f"{'NRC':<8} {'Indicador':<12} {'Estudiantes':<12} {'Sesiones':<10} {'Profesores'}")
            print("-" * 100)
            
            for section in sections:
                estudiantes = f"{section['inscritos']}/{section['cupo']}"
                profesores = section['profesores'][:50] + "..." if len(section['profesores']) > 50 else section['profesores']
                
                print(f"{section['nrc']:<8} {section['indicador']:<12} {estudiantes:<12} {section['num_sessions']:<10} {profesores}")
            
            print("="*100)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola.")
            
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
        self.selected_department = None
        self.current_step = 1
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Consultar Profesores por Departamento")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
    def setup_ui(self):
        """Setup the UI"""
        # Main container
        self.main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button
        title_frame = tk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.title_label = tk.Label(title_frame, text="Consultar Profesores por Departamento", 
                                    font=("Arial", 16, "bold"))
        self.title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Content frame (will be replaced for each step)
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Start with step 1
        self.show_step_1()
    
    def show_step_1(self):
        """Show department selection step"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update title
        self.title_label.config(text="Paso 1: Seleccione un Departamento")
        
        # Step 1 content
        step_frame = tk.Frame(self.content_frame)
        step_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = tk.Label(step_frame, 
                               text="Seleccione un departamento para ver sus profesores:",
                               font=("Arial", 12))
        instructions.pack(pady=(0, 20))
        
        # Department table container
        table_container = tk.Frame(step_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create paginated department table
        columns = ('Departamento', 'Profesores', 'Secciones', 'Estudiantes')
        column_configs = {
            'Departamento': {'width': 300, 'text': 'Departamento'},
            'Profesores': {'width': 100, 'text': 'Profesores'},
            'Secciones': {'width': 100, 'text': 'Secciones'},
            'Estudiantes': {'width': 100, 'text': 'Estudiantes'}
        }
        
        # Create paginated table for department selection
        self.department_table = PaginatedTreeview(table_container, columns, column_configs, page_size=10)
        self.department_table.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.department_table.bind_selection(self.on_department_select)
        
        # Load departments
        self.load_departments()
        
        # Navigation
        self.setup_step_1_navigation()
    
    def load_departments(self):
        """Load departments into paginated table"""
        try:
            departments = self.db_manager.get_departamentos_with_professor_stats()
            
            # Prepare data for paginated table
            table_data = []
            for dept in departments:
                table_data.append((
                    dept['nombre'],
                    dept['num_professors'],
                    dept['num_sections'],
                    dept['total_students']
                ))
            
            # Store data and update paginated table
            self.departments_data = departments
            self.department_table.set_data(table_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar departamentos: {str(e)}")
    
    def on_department_select(self, event=None):
        """Handle department selection from paginated table"""
        selected_data = self.department_table.get_selected_item()
        if selected_data:
            # Find the department by name
            dept_name = selected_data[0]  # First column is the name
            for dept in self.departments_data:
                if dept['nombre'] == dept_name:
                    self.selected_department = dept
                    break
            
            # Enable next button
            if hasattr(self, 'next_btn'):
                self.next_btn.config(state="normal")
        else:
            self.selected_department = None
            if hasattr(self, 'next_btn'):
                self.next_btn.config(state="disabled")
    
    def setup_step_1_navigation(self):
        """Setup navigation for step 1"""
        nav_frame = tk.Frame(self.content_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Next button
        self.next_btn = ttk.Button(nav_frame, text="Siguiente →", 
                                  command=self.go_to_step_2,
                                  state="disabled",
                                  style="Green.TButton")
        self.next_btn.pack(side=tk.RIGHT)
    
    def go_to_step_2(self):
        """Navigate to step 2"""
        if not self.selected_department:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un departamento.")
            return
        
        self.current_step = 2
        self.show_step_2()
    
    def show_step_2(self):
        """Show professor selection step with filters"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update title
        dept_name = self.selected_department['nombre']
        self.title_label.config(text=f"Paso 2: Profesores de {dept_name}")
        
        # Step 2 content
        step_frame = tk.Frame(self.content_frame)
        step_frame.pack(fill=tk.BOTH, expand=True)
        
        # Department info with type statistics
        info_frame = ttk.LabelFrame(step_frame, text="Departamento Seleccionado", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Get type statistics
        try:
            type_stats = self.db_manager.get_professor_type_stats_for_department(dept_name)
            levels = self.db_manager.get_available_academic_levels_for_department(dept_name)
            
            dept_info = (
                f"📍 Departamento: {dept_name}\n"
                f"👥 Total profesores: {self.selected_department['num_professors']} "
                f"(Planta: {type_stats['planta']}, Cátedra: {type_stats['catedra']})\n"
                f"📚 Total secciones: {self.selected_department['num_sections']} | "
                f"🎓 Estudiantes: {self.selected_department['total_students']}\n"
                f"📊 Niveles disponibles: {', '.join(levels) if levels else 'Ninguno'}"
            )
            
        except Exception as e:
            dept_info = f"Departamento: {dept_name}\nError al cargar estadísticas: {str(e)}"
        
        tk.Label(info_frame, text=dept_info, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # FILTERS SECTION - NEW
        filters_frame = ttk.LabelFrame(step_frame, text="Filtros", padding="15")
        filters_frame.pack(fill=tk.X, pady=(0, 15))
        
        # First row of filters
        filters_row1 = tk.Frame(filters_frame)
        filters_row1.pack(fill=tk.X, pady=(0, 10))
        
        # Professor type filter
        tk.Label(filters_row1, text="Tipo de profesor:", font=("Arial", 10)).pack(side=tk.LEFT)
        
        self.tipo_var = tk.StringVar(value="Todos los tipos")
        self.tipo_combo = ttk.Combobox(filters_row1, textvariable=self.tipo_var,
                                      values=["Todos los tipos", "Planta", "Cátedra"],
                                      state="readonly", width=15)
        self.tipo_combo.pack(side=tk.LEFT, padx=(5, 20))
        self.tipo_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Academic level filter
        tk.Label(filters_row1, text="Nivel académico:", font=("Arial", 10)).pack(side=tk.LEFT)
        
        self.nivel_var = tk.StringVar(value="Todos los niveles")
        
        # Get available levels for this department
        try:
            available_levels = self.db_manager.get_available_academic_levels_for_department(dept_name)
            nivel_values = ["Todos los niveles"] + available_levels
        except:
            nivel_values = ["Todos los niveles", "PREGRADO", "MAGISTER"]
        
        self.nivel_combo = ttk.Combobox(filters_row1, textvariable=self.nivel_var,
                                       values=nivel_values,
                                       state="readonly", width=15)
        self.nivel_combo.pack(side=tk.LEFT, padx=(5, 20))
        self.nivel_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Clear filters button
        clear_filters_btn = ttk.Button(filters_row1, text="🔄 Limpiar Filtros", 
                                      command=self.clear_filters,
                                      style="Gray.TButton")
        clear_filters_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Second row - Search section
        search_frame = tk.Frame(filters_frame)
        search_frame.pack(fill=tk.X)
        
        tk.Label(search_frame, text="Buscar profesor:").pack(side=tk.LEFT)
        
        self.prof_search_var = tk.StringVar()
        self.prof_search_entry = tk.Entry(search_frame, textvariable=self.prof_search_var, width=30)
        self.prof_search_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.prof_search_entry.bind('<KeyRelease>', self.on_prof_search_change)
        
        clear_search_btn = ttk.Button(search_frame, text="✕", command=self.clear_prof_search,
                                     style="Gray.TButton", width=3)
        clear_search_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # RESULTS COUNT - NEW
        self.results_count_label = tk.Label(step_frame, text="", font=("Arial", 9), fg="gray")
        self.results_count_label.pack(pady=(0, 10))
        
        # Professor table container
        table_container = tk.Frame(step_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create paginated professor table with updated columns
        columns = ('Nombre', 'Tipo', 'Sesiones', 'Secciones')
        column_configs = {
            'Nombre': {'width': 280, 'text': 'Profesor'},
            'Tipo': {'width': 120, 'text': 'Tipo'},  # Now shows Planta/Cátedra
            'Sesiones': {'width': 80, 'text': 'Sesiones'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        # Create paginated table for professor selection
        self.professor_table = PaginatedTreeview(table_container, columns, column_configs, page_size=15)
        self.professor_table.pack(fill=tk.BOTH, expand=True)
        
        # Load professors with filters
        self.load_professors_with_filters()
        
        # Navigation
        self.setup_step_2_navigation()
    
    def load_professors_with_filters(self, name_filter=""):
        """Load professors for selected department with type and level filters"""
        if not self.selected_department:
            return
        
        try:
            # Get current filter values
            tipo_filter = getattr(self, 'tipo_var', tk.StringVar()).get() or "Todos los tipos"
            nivel_filter = getattr(self, 'nivel_var', tk.StringVar()).get() or "Todos los niveles"
            
            # Use new filtered method
            all_professors = self.db_manager.get_profesores_by_departamento_with_filters(
                self.selected_department['nombre'],
                tipo_filter,
                nivel_filter,
                name_filter
            )
            
            # Prepare data for paginated table
            table_data = []
            for prof in all_professors:
                table_data.append((
                    prof['full_name'],
                    prof['actual_tipo'],  # Show Planta/Cátedra instead of original tipo
                    prof.get('num_sessions', 0),
                    prof.get('num_sections', 0)
                ))
            
            # Store data and update paginated table
            self.professors_data = all_professors
            self.professor_table.set_data(table_data)
            
            # Update results count
            self.update_results_count(len(all_professors))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
            print(f"Debug - Error loading professors with filters: {e}")
    
    def update_results_count(self, filtered_count):
        """Update results count display"""
        try:
            total_profs = self.selected_department['num_professors']
            
            if hasattr(self, 'results_count_label'):
                if filtered_count == total_profs:
                    self.results_count_label.config(text=f"Mostrando {total_profs} profesores")
                else:
                    self.results_count_label.config(text=f"Mostrando {filtered_count} de {total_profs} profesores")
        except:
            pass
    
    def on_filter_change(self, event=None):
        """Handle filter changes"""
        search_text = getattr(self, 'prof_search_var', tk.StringVar()).get().strip()
        self.load_professors_with_filters(search_text)
    
    def clear_filters(self):
        """Clear all filters"""
        if hasattr(self, 'tipo_var'):
            self.tipo_var.set("Todos los tipos")
        if hasattr(self, 'nivel_var'):
            self.nivel_var.set("Todos los niveles")
        if hasattr(self, 'prof_search_var'):
            self.prof_search_var.set("")
        
        self.load_professors_with_filters()
    
    def search_professors_in_dept(self):
        """Search professors in selected department with filters"""
        search_text = getattr(self, 'prof_search_var', tk.StringVar()).get().strip()
        self.load_professors_with_filters(search_text)
    
    def clear_prof_search(self):
        """Clear professor search"""
        if hasattr(self, 'prof_search_var'):
            self.prof_search_var.set("")
        self.load_professors_with_filters()
    
    def on_prof_search_change(self, event=None):
        """Handle professor search text change with delay"""
        if hasattr(self, 'prof_search_timer'):
            self.dialog.after_cancel(self.prof_search_timer)
        
        self.prof_search_timer = self.dialog.after(300, self.search_professors_in_dept)
    
    def setup_step_2_navigation(self):
        """Setup navigation for step 2"""
        nav_frame = tk.Frame(self.content_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Back button
        back_btn = ttk.Button(nav_frame, text="← Atrás", 
                             command=self.go_back_to_step_1,
                             style="Gray.TButton")
        back_btn.pack(side=tk.LEFT)
        
        # View sections button
        sections_btn = ttk.Button(nav_frame, text="📚 Ver Secciones", 
                                 command=self.show_professor_sections,
                                 style="Green.TButton")
        sections_btn.pack(side=tk.RIGHT, padx=(5, 0))
    
    def go_back_to_step_1(self):
        """Navigate back to step 1"""
        self.current_step = 1
        self.selected_department = None
        self.show_step_1()
    
    def show_professor_sections(self):
        """Show sections for a selected professor"""
        selected_data = self.professor_table.get_selected_item()
        if not selected_data:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un profesor para ver sus secciones.")
            return
        
        # Find the selected professor
        prof_name = selected_data[0]
        selected_prof = None
        for prof in self.professors_data:
            if prof['full_name'] == prof_name:
                selected_prof = prof
                break
        
        if not selected_prof:
            messagebox.showerror("Error", "No se pudo encontrar la información del profesor seleccionado.")
            return
        
        try:
            # Get professor sections
            sections = self.db_manager.get_profesor_sections(selected_prof['id'])
            summary = self.db_manager.get_profesor_sections_summary(selected_prof['id'])
            
            # Create a simple results window
            self.show_sections_results(selected_prof, sections, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar secciones: {str(e)}")
    
    def show_professor_sections(self):
        """Show sections for a selected professor"""
        selected_data = self.professor_table.get_selected_item()
        if not selected_data:
            messagebox.showwarning("Selección requerida", 
                                  "Por favor seleccione un profesor para ver sus secciones.")
            return
        
        # Find the selected professor
        prof_name = selected_data[0]
        selected_prof = None
        for prof in self.professors_data:
            if prof['full_name'] == prof_name:
                selected_prof = prof
                break
        
        if not selected_prof:
            messagebox.showerror("Error", 
                               "No se pudo encontrar la información del profesor seleccionado.")
            return
        
        try:
            # Get professor sections
            sections = self.db_manager.get_profesor_sections(selected_prof['id'])
            summary = self.db_manager.get_profesor_sections_summary(selected_prof['id'])
            
            # Create a simple results window
            self.show_sections_results(selected_prof, sections, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar secciones: {str(e)}")
    
    def show_sections_results(self, professor, sections, summary):
        """Show professor sections in a new window with improved layout"""
        # Create results window
        results_window = tk.Toplevel(self.dialog)
        results_window.title(f"Secciones de {professor['full_name']}")
        results_window.geometry("1100x650")  # Wider window
        results_window.transient(self.dialog)
        
        # Main frame with proper padding
        main_frame = tk.Frame(results_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # HEADER SECTION
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title with close button
        title_frame = tk.Frame(header_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, 
                              text=f"Secciones de {professor['full_name']}", 
                              font=("Arial", 14, "bold"), fg="#2c3e50")
        title_label.pack(side=tk.LEFT)
        
        # Close button in header
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", 
                              command=results_window.destroy,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # SUMMARY INFO - Two column layout
        summary_frame = ttk.LabelFrame(header_frame, text="Resumen", padding="15")
        summary_frame.pack(fill=tk.X)
        
        summary_container = tk.Frame(summary_frame)
        summary_container.pack(fill=tk.X)
        
        # Left column
        left_summary = tk.Frame(summary_container)
        left_summary.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        left_text = (
            f"📍 Departamento: {self.selected_department['nombre']}\n"
            f"📚 Total secciones: {summary['total_sections']}\n"
            f"🎓 Total créditos: {summary['total_credits']}"
        )
        tk.Label(left_summary, text=left_text, font=("Arial", 10), 
                 justify=tk.LEFT, fg="#34495e").pack(anchor=tk.W)
        
        # Right column
        right_summary = tk.Frame(summary_container)
        right_summary.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        right_text = (
            f"👥 Total estudiantes: {summary['total_students']}\n"
            f"📊 Capacidad total: {summary.get('total_capacity', 'N/A')}\n"
            f"🏫 Campus: {len(summary.get('campus_list', []))} diferentes"
        )
        tk.Label(right_summary, text=right_text, font=("Arial", 10), 
                 justify=tk.LEFT, fg="#34495e").pack(anchor=tk.W)
        
        # SECTIONS TABLE - Using PaginatedTreeview for consistency
        table_frame = ttk.LabelFrame(main_frame, text="Detalle de Secciones", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Section count badge
        count_frame = tk.Frame(table_frame)
        count_frame.pack(fill=tk.X, pady=(0, 10))
        
        count_label = tk.Label(count_frame, text=f"{len(sections)} secciones", 
                              font=("Arial", 9), bg="#e3f2fd", fg="#1976d2", 
                              padx=8, pady=2, relief="solid", bd=1)
        count_label.pack(side=tk.LEFT)
        
        # Create paginated table for sections
        columns = ('NRC', 'Materia', 'Nombre', 'Créditos', 'Estudiantes', 'Campus', 'Sesiones')
        column_configs = {
            'NRC': {'width': 70, 'text': 'NRC'},
            'Materia': {'width': 100, 'text': 'Código'},
            'Nombre': {'width': 250, 'text': 'Nombre Materia'},
            'Créditos': {'width': 70, 'text': 'Créditos'},
            'Estudiantes': {'width': 90, 'text': 'Estudiantes'},
            'Campus': {'width': 100, 'text': 'Campus'},
            'Sesiones': {'width': 70, 'text': 'Sesiones'}
        }
        
        # Create paginated table
        sections_table = PaginatedTreeview(table_frame, columns, column_configs, page_size=12)
        sections_table.pack(fill=tk.BOTH, expand=True)
        
        # Prepare data for the table
        table_data = []
        for section in sections:
            estudiantes = f"{section['inscritos']}/{section['cupo']}"
            
            # Get materia name if available
            materia_nombre = section.get('materia_nombre', 'Sin nombre')
            if len(materia_nombre) > 35:
                materia_nombre = materia_nombre[:32] + "..."
            
            table_data.append((
                section['nrc'],
                section['materia_codigo'],
                materia_nombre,
                section['creditos'],
                estudiantes,
                section['campus'],
                section['num_sessions']
            ))
        
        # Set data in paginated table
        sections_table.set_data(table_data)
        
        # Apply dark mode to the entire window
        apply_dark_mode_to_dialog(results_window, self.theme_colors)
    
    def on_prof_search_change(self, event=None):
        """Handle professor search text change with delay"""
        if hasattr(self, 'prof_search_timer'):
            self.dialog.after_cancel(self.prof_search_timer)
        
        self.prof_search_timer = self.dialog.after(300, self.search_professors_in_dept)
    
    def search_professors_in_dept(self):
        """Search professors in selected department"""
        search_text = self.prof_search_var.get().strip()
        self.load_professors(search_text)
    
    def clear_prof_search(self):
        """Clear professor search"""
        self.prof_search_var.set("")
        self.load_professors()
    
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
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
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
        
        # Statistics summary - RESTORED to original simple layout
        stats_frame = ttk.LabelFrame(self.content_frame, text="Resumen de Coincidencias", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create two columns for statistics
        stats_container = tk.Frame(stats_frame)
        stats_container.pack(fill=tk.X)
        
        stats_left = tk.Frame(stats_container)
        stats_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        stats_right = tk.Frame(stats_container)
        stats_right.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Get statistics from the matching process
        stats = self.linking_engine.processor.get_match_statistics(self.linking_engine.current_matches)
        
        # LEFT COLUMN - Updated with new perspective
        left_text = (
            f"📊 Profesores existentes: {stats['existing_professors_matched'] + stats['existing_professors_unmatched']}\n"
            f"✅ Con coincidencias: {stats['existing_professors_matched']}\n"
            f"❌ Sin coincidencias: {stats['existing_professors_unmatched']}\n"
            f"⚡ Automáticas (≥95%): {stats['automatic_matches']}"
        )
        
        tk.Label(stats_left, text=left_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # RIGHT COLUMN - File info
        right_text = (
            f"📄 Registros procesados: {stats.get('file_info', {}).get('total_rows', 0)}\n"
            f"📊 Registros de ingeniería: {stats.get('file_info', {}).get('engineering_faculty_rows', 0)}\n"
            f"🔍 Requieren revisión: {stats['review_needed']}\n"
            f"📈 Confianza promedio: {stats['avg_confidence']:.1%}"
        )
        
        tk.Label(stats_right, text=right_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Quick actions section - RESTORED to original
        summary_frame = ttk.LabelFrame(self.content_frame, text="Acciones Rápidas", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Quick actions row
        actions_row = tk.Frame(summary_frame)
        actions_row.pack(fill=tk.X, pady=(0, 10))
        
        # Approve automatic matches button
        ttk.Button(actions_row, text="✓ Aprobar Automáticas", 
                  command=self.approve_automatic_matches, 
                  style="Green.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # Export report button
        ttk.Button(actions_row, text="📋 Exportar Reporte", 
                  command=self.export_report, 
                  style="Teal.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear all approvals button
        ttk.Button(actions_row, text="🔄 Limpiar Aprobaciones", 
                  command=self.clear_all_approvals, 
                  style="Orange.TButton").pack(side=tk.LEFT)
        
        # Approval status display
        self.approval_status_var = tk.StringVar()
        self.approval_status_label = tk.Label(actions_row, textvariable=self.approval_status_var,
                                            font=("Arial", 9), fg="blue")
        self.approval_status_label.pack(side=tk.RIGHT)
        
        # Update approval status
        self.update_approval_status()
        
        # Matches review table - RESTORED to original simple layout
        table_frame = ttk.LabelFrame(self.content_frame, text="Revisar Coincidencias", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions for the table
        instructions_text = (
            "💡 Instrucciones: Doble clic para cambiar estado | Revise las coincidencias antes de aplicar\n"
            "🟢 Verde = Aprobado | 🟡 Amarillo = Pendiente | 🔴 Rojo = Rechazado"
        )
        
        instructions_label = tk.Label(table_frame, text=instructions_text, 
                                     font=("Arial", 8), fg="gray", justify=tk.LEFT)
        instructions_label.pack(pady=(0, 10))
        
        # Create matches table with scrollbar
        table_container = tk.Frame(table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for matches - FIXED: Define columns including match_id
        columns = ('Estado', 'Profesor Existente', 'Datos Personales', 'Confianza', 'Nuevo Tipo', 'match_id')
        self.matches_tree = ttk.Treeview(table_container, columns=columns, show='headings', height=15)
        
        # Define column headings and widths (don't show match_id column)
        self.matches_tree.heading('Estado', text='Estado')
        self.matches_tree.heading('Profesor Existente', text='Profesor Existente')
        self.matches_tree.heading('Datos Personales', text='Datos Personales')
        self.matches_tree.heading('Confianza', text='Confianza')
        self.matches_tree.heading('Nuevo Tipo', text='Nuevo Tipo')
        self.matches_tree.heading('match_id', text='')  # Hidden column
        
        self.matches_tree.column('Estado', width=80)
        self.matches_tree.column('Profesor Existente', width=200)
        self.matches_tree.column('Datos Personales', width=200)
        self.matches_tree.column('Confianza', width=80)
        self.matches_tree.column('Nuevo Tipo', width=150)
        self.matches_tree.column('match_id', width=0, stretch=False)  # Hidden column
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.matches_tree.yview)
        self.matches_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.matches_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to toggle approval
        self.matches_tree.bind('<Double-1>', self.toggle_match_approval)
        
        # Load matches data
        self.load_matches_data()
        
        # Navigation buttons
        self.setup_step_2_navigation()
    
    def clear_all_approvals(self):
        """Clear all approved and rejected matches"""
        if not self.linking_engine.current_matches:
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirmar", 
                                "¿Está seguro de que desea limpiar todas las aprobaciones y rechazos?"):
            return
        
        # Clear all approvals and rejections
        self.linking_engine.approved_matches.clear()
        self.linking_engine.rejected_matches.clear()
        
        # Reload the matches table
        self.load_matches_data()
        self.update_approval_status()
        
        messagebox.showinfo("Completado", "Todas las aprobaciones han sido limpiadas.")
    
    def load_matches_data(self):
        """Load matches data into the tree"""
        # Clear existing items
        for item in self.matches_tree.get_children():
            self.matches_tree.delete(item)
        
        # Load matches
        for match in self.linking_engine.current_matches:
            existing_prof = match['existing_professor']
            personal_data = match['personal_data']
            position_info = match['position_info']
            confidence = match['match_confidence']
            
            # Determine status
            if match in self.linking_engine.approved_matches:
                status = "✅ Aprobado"
                tag = "approved"
            elif match in self.linking_engine.rejected_matches:
                status = "❌ Rechazado"
                tag = "rejected"
            else:
                status = "⏳ Pendiente"
                tag = "pending"
            
            # Insert into tree - Store match reference in values, not as a separate column
            match_id = id(match)
            self.matches_tree.insert('', tk.END, values=(
                status,
                existing_prof['full_name'],
                personal_data['full_name_standardized'],
                f"{confidence:.1%}",
                position_info['tipo'] or 'N/A',
                match_id  # Store match_id as the last value
            ), tags=(tag,))
        
        # Configure tags for colors
        self.matches_tree.tag_configure('approved', background='#d4edda')
        self.matches_tree.tag_configure('rejected', background='#f8d7da')
        self.matches_tree.tag_configure('pending', background='#fff3cd')
    
    def approve_automatic_matches(self):
        """Approve all high confidence matches (>= 0.95)"""
        if not self.linking_engine.current_matches:
            messagebox.showwarning("Sin datos", "No hay coincidencias para aprobar.")
            return
        
        count = self.linking_engine.approve_all_high_confidence()
        
        if count > 0:
            self.load_matches_data()
            self.update_approval_status()
            messagebox.showinfo("Aprobación automática", 
                            f"Se aprobaron {count} coincidencias automáticas (confianza ≥ 95%).")
        else:
            messagebox.showinfo("Sin cambios", 
                            "No se encontraron coincidencias con confianza ≥ 95% para aprobar automáticamente.")
    
    def toggle_match_approval(self, event=None):
        """Toggle match approval status on double-click"""
        selection = self.matches_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.matches_tree.item(item, 'values')
        if len(values) < 6:  # Should have at least 6 values including match_id
            return
        
        match_id = int(values[5])  # match_id is the last value
        
        # Find the match object
        match = None
        for m in self.linking_engine.current_matches:
            if id(m) == match_id:
                match = m
                break
        
        if not match:
            return
        
        # Toggle status
        if match in self.linking_engine.approved_matches:
            # Currently approved, change to rejected
            self.linking_engine.approved_matches.remove(match)
            self.linking_engine.rejected_matches.append(match)
        elif match in self.linking_engine.rejected_matches:
            # Currently rejected, change to pending
            self.linking_engine.rejected_matches.remove(match)
        else:
            # Currently pending, change to approved
            self.linking_engine.approved_matches.append(match)
        
        # Reload data and update status
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
        
        preview = self.linking_engine.get_match_preview(match)
        detail_dialog = tk.Toplevel(self.dialog)
        detail_dialog.title("Detalles de Coincidencia")
        detail_dialog.geometry("700x600")
        detail_dialog.transient(self.dialog)
        
        colors = get_theme_colors()
        apply_dark_mode_to_dialog(detail_dialog, colors)
        
        # Create scrollable frame
        main_frame = tk.Frame(detail_dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        preview = self.linking_engine.get_match_preview(match)
        
        # Title
        title_label = tk.Label(main_frame, text="Detalles de Coincidencia", 
                              font=("Arial", 16, "bold"))
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
            f"Departamento oficial: {preview['personal']['departamento_oficial']}\n"
            f"Dependencia: {preview['personal'].get('dependencia', 'No especificada')}\n"
            f"Tipo de contrato: {preview['personal'].get('tipo_contrato', 'No especificado')}"
        )
        
        tk.Label(personal_frame, text=personal_text, font=("Arial", 10), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Proposed changes
        changes_frame = ttk.LabelFrame(main_frame, text="Cambios Propuestos", padding="10")
        changes_frame.pack(fill=tk.X, pady=(0, 15))
        
        changes_text = (
            f"Nuevo tipo: {preview['changes']['new_tipo']}\n"
            f"Subcategoría: {preview['changes']['subcategoria'] or 'Sin subcategoría'}\n"
            f"Número de persona: {preview['changes']['person_id']}\n"
            f"Dependencia: {preview['changes'].get('dependencia') or 'No especificada'}\n"  # NEW
            f"Contrato: {preview['changes'].get('contrato') or 'No especificado'}"
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
        
        # Color coding based on status
        if summary['approved'] > 0:
            color = "green"
        elif summary['rejected'] > 0:
            color = "red"
        else:
            color = "gray"
        
        status_text = (
            f"✓ Aprobadas: {summary['approved']} | "
            f"✗ Rechazadas: {summary['rejected']} | "
            f"⏳ Pendientes: {summary['pending']}"
        )
        
        self.approval_status_var.set(status_text)
        self.approval_status_label.config(fg=color)
    
    def export_report(self):
        """Export matching report"""
        if not self.linking_engine.current_matches:
            messagebox.showwarning("Sin datos", "No hay coincidencias para exportar.")
            return
        
        try:
            file_path = self.linking_engine.export_match_report()
            
            # Show success message with option to open file location
            if messagebox.askyesno("Reporte exportado", 
                                f"Reporte guardado exitosamente en:\n{file_path}\n\n¿Desea abrir la ubicación del archivo?"):
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(f'explorer /select,"{file_path}"')
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", "-R", file_path])
                else:  # Linux
                    subprocess.run(["xdg-open", os.path.dirname(file_path)])
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar reporte: {str(e)}")

    
    def proceed_to_apply(self):
        """Proceed to apply approved matches"""
        if not self.linking_engine:
            messagebox.showerror("Error", "No hay motor de enlace activo.")
            return
        
        summary = self.linking_engine.get_approval_summary()
        
        if summary['approved'] == 0:
            messagebox.showwarning("Sin aprobaciones", 
                                "No hay coincidencias aprobadas para aplicar.\n\n"
                                "Por favor apruebe al menos una coincidencia antes de continuar.")
            return
        
        # Enhanced confirmation dialog
        confirm_msg = (
            f"¿Aplicar {summary['approved']} coincidencias aprobadas?\n\n"
            f"Esta acción:\n"
            f"• Actualizará {summary['approved']} registros de profesores\n"
            f"• Agregará información personal y de cargo\n"
            f"• Marcará los profesores como vinculados\n\n"
            f"Los cambios se pueden verificar en el visor de base de datos.\n"
            f"¿Desea continuar?"
        )
        
        if not messagebox.askyesno("Confirmar aplicación", confirm_msg, icon='question'):
            return
        
        # Proceed to step 3
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
        
class PaginatedTreeview:
    """Reusable paginated treeview component"""
    
    def __init__(self, parent, columns, column_configs, page_size=20):
        self.parent = parent
        self.columns = columns
        self.column_configs = column_configs
        self.page_size = page_size
        self.current_page = 0
        self.total_records = 0
        self.total_pages = 0
        self.all_data = []  # Store all data
        self.filtered_data = []  # Store filtered data
        self.search_term = ""
        
        self.setup_ui()
    
        # Update the setup_ui method in PaginatedTreeview class in ui_components.py:
    
    def setup_ui(self):
        """Setup the paginated treeview UI - UPDATED: No internal search functionality"""
        # Main container
        self.container = tk.Frame(self.parent)
        
        # Results info only (no search)
        self.info_frame = tk.Frame(self.container)
        self.info_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.results_info_label = tk.Label(self.info_frame, text="", font=("Arial", 9), fg="gray")
        self.results_info_label.pack(side=tk.LEFT)
        
        # Table frame
        table_frame = tk.Frame(self.container)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show='headings', height=10)
        
        # Configure columns
        for col, config in self.column_configs.items():
            self.tree.heading(col, text=config['text'])
            self.tree.column(col, width=config['width'], minwidth=50)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pagination frame
        pagination_frame = tk.Frame(self.container)
        pagination_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Page navigation buttons
        self.first_btn = ttk.Button(pagination_frame, text="<<", command=self.first_page,
                                   state="disabled", style="Gray.TButton")
        self.first_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.prev_btn = ttk.Button(pagination_frame, text="<", command=self.prev_page,
                                  state="disabled", style="Gray.TButton")
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.page_label = tk.Label(pagination_frame, text="Página 0 de 0", font=("Arial", 9))
        self.page_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_btn = ttk.Button(pagination_frame, text=">", command=self.next_page,
                                  state="disabled", style="Gray.TButton")
        self.next_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.last_btn = ttk.Button(pagination_frame, text=">>", command=self.last_page,
                                  state="disabled", style="Gray.TButton")
        self.last_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Page size selector
        tk.Label(pagination_frame, text="Por página:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_combo = ttk.Combobox(pagination_frame, textvariable=self.page_size_var,
                                      values=["10", "15", "20", "50"], width=5, state="readonly")
        page_size_combo.pack(side=tk.LEFT, padx=(2, 0))
        page_size_combo.bind('<<ComboboxSelected>>', self.on_page_size_change)
    
    def set_data(self, data):
        """Set the data for the paginated view"""
        self.all_data = data[:]
        self.filtered_data = self.all_data[:] 
        self.total_records = len(self.all_data)
        self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
        self.current_page = 0
        self.update_display()
        
    
    def update_display(self):
        """Update the treeview display with current page data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.filtered_data:
            self.update_pagination_controls()
            self.update_info_labels()
            return
        
        # Calculate page range
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_data))
        
        # Add current page data
        page_data = self.filtered_data[start_idx:end_idx]
        
        for i, row_data in enumerate(page_data):
            tags = ('evenrow' if i % 2 == 0 else 'oddrow',)
            self.tree.insert('', tk.END, values=row_data, tags=tags)
        
        # Apply dark mode styling
        colors = get_theme_colors()
        configure_treeview_dark_mode(self.tree, colors)
        
        self.update_pagination_controls()
        self.update_info_labels()
    
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
        if self.total_records == 0:
            self.results_info_label.config(text="No hay resultados")
            return
        
        start_record = self.current_page * self.page_size + 1
        end_record = min((self.current_page + 1) * self.page_size, self.total_records)
        
        if len(self.filtered_data) < len(self.all_data):
            self.results_info_label.config(
                text=f"Mostrando {start_record}-{end_record} de {self.total_records} resultados filtrados (de {len(self.all_data)} totales)"
            )
        else:
            self.results_info_label.config(
                text=f"Mostrando {start_record}-{end_record} de {self.total_records} resultados"
            )
    
    def on_page_size_change(self, event=None):
        """Handle page size change"""
        try:
            new_size = int(self.page_size_var.get())
            self.page_size = new_size
            self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
            self.current_page = 0
            self.update_display()
        except ValueError:
            pass
    
    def first_page(self):
        """Go to first page"""
        self.current_page = 0
        self.update_display()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_display()
    
    def last_page(self):
        """Go to last page"""
        if self.total_pages > 0:
            self.current_page = self.total_pages - 1
            self.update_display()
    
    def pack(self, **kwargs):
        """Pack the container"""
        self.container.pack(**kwargs)
    
    def get_selected_item(self):
        """Get currently selected item data"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            return self.tree.item(item, 'values')
        return None
    
    def bind_selection(self, callback):
        """Bind selection event"""
        self.tree.bind('<<TreeviewSelect>>', callback)
        

class ProfessorMateriasDialog:
    """Dialog for querying professor materias/subjects"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.selected_professor = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Consultar Materias de Profesor")
        self.dialog.geometry("1200x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
    def setup_ui(self):
        """Setup the UI"""
        # Main container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with Close button
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="Consultar Materias de Profesor", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                              style="Red.TButton")
        close_btn.pack(side=tk.RIGHT)
        
        # Selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Selección de Profesor", padding="15")
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Department filter section - UPDATED: Now includes department filter
        filter_frame = tk.Frame(selection_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Department filter
        dept_filter_frame = tk.Frame(filter_frame)
        dept_filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(dept_filter_frame, text="Filtrar por departamento:").pack(side=tk.LEFT)
        
        self.department_var = tk.StringVar(value="Todos los departamentos")
        self.department_combo = ttk.Combobox(dept_filter_frame, textvariable=self.department_var,
                                           state="readonly", width=40)
        self.department_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.department_combo.bind('<<ComboboxSelected>>', self.on_department_filter_change)
        
        clear_filter_btn = ttk.Button(dept_filter_frame, text="Limpiar", command=self.clear_department_filter,
                                     style="Gray.TButton")
        clear_filter_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Search section
        search_frame = tk.Frame(filter_frame)
        search_frame.pack(fill=tk.X)
        
        tk.Label(search_frame, text="Buscar profesor:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Arial", 11), width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        search_btn = ttk.Button(search_frame, text="🔍", command=self.search_professors,
                               style="Blue.TButton")
        search_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        clear_btn = ttk.Button(search_frame, text="✕", command=self.clear_search,
                              style="Gray.TButton", width=3)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Professor selection - PAGINATED
        table_container = tk.Frame(selection_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create paginated professor selection table
        columns = ('Nombre', 'Departamentos', 'Materias', 'Secciones')
        column_configs = {
            'Nombre': {'width': 250, 'text': 'Profesor'},
            'Departamentos': {'width': 300, 'text': 'Departamentos'},
            'Materias': {'width': 80, 'text': 'Materias'},
            'Secciones': {'width': 80, 'text': 'Secciones'}
        }
        
        # Create paginated table for professor selection
        self.professor_table = PaginatedTreeview(table_container, columns, column_configs, page_size=15)
        self.professor_table.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.professor_table.bind_selection(self.on_professor_select)
        
        # Query button
        self.query_btn = ttk.Button(
            selection_frame, 
            text="📚 CONSULTAR MATERIAS", 
            command=self.query_materias,
            state="disabled",
            style="Green.TButton"
        )
        self.query_btn.pack(pady=(5, 0))
        
        # Results frame
        self.results_frame = tk.Frame(main_frame)
        
        # Load data
        self.load_departments()
        self.load_professors()
    
    def load_departments(self):
        """Load departments for filtering"""
        try:
            departments = self.db_manager.get_departamentos()
            dept_values = ["Todos los departamentos"] + sorted(departments)
            self.department_combo['values'] = dept_values
        except Exception as e:
            print(f"Error loading departments: {e}")
    
    def load_professors(self, filter_text=""):
        """Load professors into paginated table with department filtering"""
        self.professors_data = []
        
        try:
            all_professors = self.db_manager.get_all_profesores_with_materia_stats()
            
            # Apply department filter
            dept_filter = self.get_current_department_filter()
            if dept_filter != "Todos los departamentos":
                filtered_professors = []
                for prof in all_professors:
                    # Check if the professor belongs to the selected department
                    prof_departments = prof['departamentos'].split(', ')
                    if dept_filter in prof_departments:
                        filtered_professors.append(prof)
                all_professors = filtered_professors
            
            # Apply search filter if provided
            if filter_text:
                filter_text = filter_text.lower()
                filtered_professors = []
                for prof in all_professors:
                    if (filter_text in prof['full_name'].lower() or 
                        filter_text in prof['departamentos'].lower()):
                        filtered_professors.append(prof)
                all_professors = filtered_professors
            
            # Prepare data for paginated table
            table_data = []
            for prof in all_professors:
                table_data.append((
                    prof['full_name'],
                    prof['departamentos'],
                    prof['num_materias'],
                    prof['num_sections']
                ))
            
            # Store data and update paginated table
            self.professors_data = all_professors
            self.professor_table.set_data(table_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar profesores: {str(e)}")
    
    def get_current_department_filter(self):
        """Get current department filter"""
        return self.department_var.get()
    
    def on_department_filter_change(self, event=None):
        """Handle department filter change"""
        self.load_professors(self.search_var.get())
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
    def clear_department_filter(self):
        """Clear department filter"""
        self.department_var.set("Todos los departamentos")
        self.on_department_filter_change()
    
    def on_professor_select(self, event=None):
        """Handle professor selection from paginated table"""
        selected_data = self.professor_table.get_selected_item()
        if selected_data:
            # Find the professor by name
            prof_name = selected_data[0]  # First column is the name
            for prof in self.professors_data:
                if prof['full_name'] == prof_name:
                    self.selected_professor = prof
                    break
            
            self.query_btn.config(state="normal")
        else:
            self.selected_professor = None
            self.query_btn.config(state="disabled")
    
    def search_professors(self):
        """Search professors based on input"""
        search_text = self.search_var.get().strip()
        self.load_professors(search_text)
        self.query_btn.config(state="disabled")
        self.selected_professor = None
    
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
    
    def query_materias(self):
        """Query and display professor materias"""
        if not self.selected_professor:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un profesor.")
            return
        
        try:
            materias = self.db_manager.get_profesor_materias(self.selected_professor['id'])
            summary = self.db_manager.get_profesor_materias_summary(self.selected_professor['id'])
            
            self.show_results(materias, summary)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al consultar materias: {str(e)}")
    
    def show_results(self, materias, summary):
        """Display query results with scrollable dialog and improved table"""
        # Show and configure results frame
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # CREATE MAIN SCROLLABLE CONTAINER
        main_canvas = tk.Canvas(self.results_frame, highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=main_canvas.yview)
        scrollable_main_frame = tk.Frame(main_canvas)
        
        # Configure scrolling
        scrollable_main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Pack main canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # COLUMN LAYOUT - Now inside the scrollable container
        columns_container = tk.Frame(scrollable_main_frame)
        columns_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LEFT COLUMN - Professor info and summary
        left_column = tk.Frame(columns_container, width=400)
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_column.pack_propagate(False)
        
        # RIGHT COLUMN - Materias table
        right_column = tk.Frame(columns_container)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === LEFT COLUMN CONTENT ===
        
        # Professor info header
        prof_info_frame = ttk.LabelFrame(left_column, text="Profesor", padding="10")
        prof_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        prof_name = self.selected_professor['full_name']
        prof_depts = self.selected_professor['departamentos']
        
        # Professor name
        tk.Label(prof_info_frame, text=prof_name, 
                font=("Arial", 11, "bold"), fg="#2c3e50").pack(anchor=tk.W)
        
        # Department info
        dept_label = tk.Label(prof_info_frame, text=f"Departamentos: {prof_depts}", 
                font=("Arial", 10), wraplength=350, justify=tk.LEFT, fg="#34495e")
        dept_label.pack(anchor=tk.W, pady=(3, 0))
        
        # Summary statistics
        summary_frame = ttk.LabelFrame(left_column, text="Resumen Estadístico", padding="12")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_container = tk.Frame(summary_frame)
        stats_container.pack(fill=tk.X)
        
        # Statistics
        main_stats = [
            ("Total de materias:", summary.get('total_materias', 0), "#e74c3c"),
            ("Secciones totales:", summary.get('total_sections', 0), "#3498db"),
            ("Créditos totales:", summary.get('total_credits', 0), "#27ae60"),
            ("Estudiantes totales:", summary.get('total_students', 0), "#f39c12"),
            ("Departamentos:", len(summary.get('departments', [])), "#9b59b6"),
            ("Niveles académicos:", len(summary.get('academic_levels', [])), "#e67e22")
        ]
        
        for label, value, color in main_stats:
            stat_frame = tk.Frame(stats_container)
            stat_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(stat_frame, text=label, font=("Arial", 9), 
                    bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(side=tk.LEFT)
            tk.Label(stat_frame, text=str(value), font=("Arial", 9, "bold"),
                    bg=self.theme_colors['bg'], fg=color).pack(side=tk.RIGHT)
        
        # Academic levels breakdown
        if summary.get('academic_levels'):
            levels_frame = ttk.LabelFrame(left_column, text="Niveles Académicos", padding="10")
            levels_frame.pack(fill=tk.X, pady=(0, 10))
            
            for level in summary['academic_levels']:
                tk.Label(levels_frame, text=f"• {level}", font=("Arial", 9),
                        bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(anchor=tk.W)
        
        # Campus breakdown
        if summary.get('campus_list'):
            campus_frame = ttk.LabelFrame(left_column, text="Campus", padding="10")
            campus_frame.pack(fill=tk.X, pady=(0, 10))
            
            for campus in summary['campus_list']:
                tk.Label(campus_frame, text=f"• {campus}", font=("Arial", 9),
                        bg=self.theme_colors['bg'], fg=self.theme_colors['fg']).pack(anchor=tk.W)
        
        # Export button
        export_btn = ttk.Button(left_column, text="📄 Exportar", 
                              command=lambda: self.export_results(materias, summary),
                              style="Teal.TButton")
        export_btn.pack(fill=tk.X, pady=(10, 5))
        
        # === RIGHT COLUMN CONTENT ===
        
        # Materias table title
        table_title_frame = tk.Frame(right_column)
        table_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(table_title_frame, text="Detalle de Materias", 
                font=("Arial", 14, "bold"), fg="#2c3e50").pack(side=tk.LEFT)
        
        # Materia count badge
        count_label = tk.Label(table_title_frame, text=f"{len(materias)} materias", 
                              font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d", 
                              padx=8, pady=2, relief="solid", bd=1)
        count_label.pack(side=tk.RIGHT)
        
        # Create paginated table with better column configuration
        columns = ('Código', 'Nombre', 'Departamento', 'Créditos', 'Nivel', 'Secciones', 'Estudiantes')
        column_configs = {
            'Código': {'width': 90, 'text': 'Código'},
            'Nombre': {'width': 300, 'text': 'Nombre'},
            'Departamento': {'width': 150, 'text': 'Departamento'},
            'Créditos': {'width': 80, 'text': 'Créditos'},
            'Nivel': {'width': 100, 'text': 'Nivel'},
            'Secciones': {'width': 90, 'text': 'Secciones'},
            'Estudiantes': {'width': 100, 'text': 'Estudiantes'}
        }
        
        # Create paginated table - NO fixed height container
        self.materias_table = PaginatedTreeview(right_column, columns, column_configs, page_size=15)
        self.materias_table.pack(fill=tk.BOTH, expand=True)
        
        # Prepare data for pagination
        table_data = []
        for materia in materias:
            # Don't truncate names - let the wider column handle it
            materia_name = materia['nombre']
            
            # Only truncate if extremely long
            if len(materia_name) > 50:
                materia_name = materia_name[:47] + "..."
            
            table_data.append((
                materia['codigo'],
                materia_name,
                materia['departamento'],
                materia['creditos'],
                materia['nivel'] if materia['nivel'] else 'N/A',
                materia['num_sections'],
                materia['total_students']
            ))
        
        # Set data in paginated table
        self.materias_table.set_data(table_data)
        
        # Configure dark mode for main canvas
        main_canvas.configure(bg=self.theme_colors['bg'])
        scrollable_main_frame.configure(bg=self.theme_colors['bg'])
        
        # Enable mouse wheel scrolling for main canvas
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind("<MouseWheel>", _on_mousewheel)
        main_canvas.bind("<Button-4>", lambda e: main_canvas.yview_scroll(-1, "units"))
        main_canvas.bind("<Button-5>", lambda e: main_canvas.yview_scroll(1, "units"))
    
    def export_results(self, materias, summary):
        """Export results to console"""
        try:
            prof_name = self.selected_professor['full_name']
            prof_depts = self.selected_professor['departamentos']
            
            print("\n" + "="*100)
            print(f"MATERIAS DEL PROFESOR: {prof_name}")
            print(f"DEPARTAMENTOS: {prof_depts}")
            print("="*100)
            
            # Print summary
            print(f"\nRESUMEN:")
            print(f"• Total de materias: {summary['total_materias']}")
            print(f"• Secciones totales: {summary['total_sections']}")
            print(f"• Créditos totales: {summary['total_credits']}")
            print(f"• Estudiantes totales: {summary['total_students']}")
            print(f"• Departamentos involucrados: {len(summary['departments'])}")
            print(f"• Niveles académicos: {', '.join(summary['academic_levels'])}")
            
            # Print detailed materias
            print(f"\nDETALLE DE MATERIAS:")
            print("-" * 100)
            print(f"{'Código':<12} {'Nombre':<35} {'Departamento':<25} {'Créditos':<9} {'Nivel':<12} {'Secciones':<10} {'Estudiantes'}")
            print("-" * 100)
            
            for materia in materias:
                codigo = materia['codigo']
                nombre = materia['nombre'][:34]  # Truncate for table
                departamento = materia['departamento'][:24]  # Truncate for table
                creditos = str(materia['creditos'])
                nivel = (materia['nivel'] or 'N/A')[:11]  # Truncate for table
                secciones = str(materia['num_sections'])
                estudiantes = str(materia['total_students'])
                
                print(f"{codigo:<12} {nombre:<35} {departamento:<25} {creditos:<9} {nivel:<12} {secciones:<10} {estudiantes}")
            
            print("="*100)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def close_dialog(self):
        """Close the dialog"""
        if self.callback:
            self.callback()
        self.dialog.destroy()
        
class DedicationDataLinkingDialog:
    """Dialog for dedication data linking process"""
    
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.current_step = 0
        self.dedication_processor = None
        self.processing_result = None
        self.approved_matches = []
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Actualizar Dedicaciones de Profesores")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress indicator
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Paso 1 de 3: Seleccionar Archivo",
                                       font=("Arial", 12, "bold"))
        self.progress_label.pack()
        
        # Content frame
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        self.btn_frame = ttk.Frame(main_frame)
        self.btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Start with step 1
        self.show_step_1()
    
    def show_step_1(self):
        """Step 1: File selection and validation"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 1 de 3: Seleccionar Archivo de Dedicaciones")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(self.content_frame, text="Instrucciones", padding="15")
        instructions_frame.pack(fill=tk.X, pady=(0, 20))
        
        instructions_text = (
            "Seleccione un archivo CSV con información de dedicaciones de profesores.\n\n"
            "El archivo debe contener las siguientes columnas:\n"
            "• seccion: NRC de la sección\n"
            "• profesor: Nombre completo del profesor\n"
            "• dedicacion: Porcentaje de dedicación (0-200%)\n"
            "• periodo: Período académico\n\n"
            "Ejemplo: 39342,DURAN AMOROCHO XAVIER HERNANDO,45,202510"
        )
        
        ttk.Label(instructions_frame, text=instructions_text, 
                 font=("Arial", 10), justify=tk.LEFT).pack()
        
        # File selection
        file_frame = ttk.LabelFrame(self.content_frame, text="Selección de Archivo", padding="15")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.file_path_var = tk.StringVar(value="Ningún archivo seleccionado")
        file_label = ttk.Label(file_frame, textvariable=self.file_path_var, 
                              font=("Arial", 10), foreground="gray")
        file_label.pack(pady=(0, 10))
        
        select_btn = ttk.Button(file_frame, text="📁 Seleccionar Archivo CSV", 
                               command=self.select_file, style="Blue.TButton")
        select_btn.pack()
        
        # File validation results
        self.validation_frame = ttk.LabelFrame(self.content_frame, text="Validación del Archivo", padding="15")
        self.validation_text = tk.Text(self.validation_frame, height=8, wrap=tk.WORD)
        validation_scroll = ttk.Scrollbar(self.validation_frame, orient=tk.VERTICAL, command=self.validation_text.yview)
        self.validation_text.configure(yscrollcommand=validation_scroll.set)
        
        self.setup_step_1_navigation()
    
    def select_file(self):
        """Select dedication CSV file"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de dedicaciones",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_path_var.set(f"📄 {filename}")
            
            # Validate file
            self.validate_file()
    
    def validate_file(self):
        """Validate the selected file"""
        if not hasattr(self, 'file_path'):
            return
        
        try:
            from dedication_data_processor import validate_dedication_csv_file
            validation_result = validate_dedication_csv_file(self.file_path)
            
            # Show validation frame
            self.validation_frame.pack(fill=tk.BOTH, expand=True)
            
            # Clear previous validation text
            self.validation_text.delete(1.0, tk.END)
            
            # Display validation results
            if validation_result['valid']:
                self.validation_text.insert(tk.END, "✅ ARCHIVO VÁLIDO\n\n", "success")
                self.validation_text.tag_config("success", foreground="green")
            else:
                self.validation_text.insert(tk.END, "❌ ARCHIVO INVÁLIDO\n\n", "error")
                self.validation_text.tag_config("error", foreground="red")
            
            # Show file info
            if validation_result['file_info']:
                info = validation_result['file_info']
                self.validation_text.insert(tk.END, f"Información del archivo:\n")
                self.validation_text.insert(tk.END, f"• Total de filas: {info['total_rows']}\n")
                self.validation_text.insert(tk.END, f"• Columnas: {', '.join(info['columns'])}\n")
                self.validation_text.insert(tk.END, f"• Tamaño: {info['file_size_mb']} MB\n\n")
            
            # Show errors
            if validation_result['errors']:
                self.validation_text.insert(tk.END, "Errores:\n")
                for error in validation_result['errors']:
                    self.validation_text.insert(tk.END, f"• {error}\n")
                self.validation_text.insert(tk.END, "\n")
            
            # Show warnings
            if validation_result['warnings']:
                self.validation_text.insert(tk.END, "Advertencias:\n")
                for warning in validation_result['warnings']:
                    self.validation_text.insert(tk.END, f"• {warning}\n")
            
            self.validation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            if hasattr(self, 'validation_scroll'):  # Check if it exists
                self.validation_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            # Update navigation
            self.is_file_valid = validation_result['valid']
            self.setup_step_1_navigation()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al validar archivo: {str(e)}")
    
    def setup_step_1_navigation(self):
        """Setup navigation for step 1"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
        
        ttk.Button(self.btn_frame, text="Cancelar", command=self.close_dialog,
                  style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        
        # Enable next button only if file is valid
        next_state = "normal" if hasattr(self, 'is_file_valid') and self.is_file_valid else "disabled"
        ttk.Button(self.btn_frame, text="Siguiente", command=self.process_file,
                  style="Blue.TButton", state=next_state).pack(side=tk.RIGHT)
    
    def process_file(self):
        """Process the selected file and show matches"""
        if not hasattr(self, 'file_path') or not self.is_file_valid:
            return
        
        try:
            # Create dedication processor
            self.dedication_processor = self.db_manager.create_dedication_processor()
            if not self.dedication_processor:
                messagebox.showerror("Error", "No se pudo crear el procesador de dedicaciones.")
                return
            
            # Show processing dialog
            progress = ProgressDialog(self.parent, "Procesando dedicaciones", 
                                     "Analizando archivo y buscando coincidencias...")
            
            # Process file
            self.processing_result = self.dedication_processor.process_dedication_csv(self.file_path)
            progress.close()
            
            if not self.processing_result['success']:
                error_msg = "Errores durante el procesamiento:\n" + "\n".join(self.processing_result['errors'])
                messagebox.showerror("Error de Procesamiento", error_msg)
                return
            
            # Move to step 2
            self.current_step = 1
            self.show_step_2()
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            messagebox.showerror("Error", f"Error al procesar archivo: {str(e)}")
    
    def show_step_2(self):
        """Step 2: Review matches and approve/reject"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 2 de 3: Revisar y Aprobar Coincidencias")
        
        # Statistics summary
        stats = self.processing_result['statistics']
        summary_frame = ttk.LabelFrame(self.content_frame, text="Resumen del Procesamiento", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        summary_text = (
            f"Total de filas procesadas: {stats['total_rows']}\n"
            f"Filas válidas: {stats['valid_rows']}\n"
            f"Profesores encontrados: {stats['professor_matches']}\n"
            f"NRCs válidos: {stats['nrc_matches']}\n"
            f"Entradas duplicadas omitidas: {stats['duplicate_entries']}\n"
            f"Registros listos para aplicar: {stats['ready_to_apply']}"
        )
        
        ttk.Label(summary_frame, text=summary_text, font=("Arial", 10)).pack(anchor=tk.W)
        
        # Matches table
        matches_frame = ttk.LabelFrame(self.content_frame, text="Coincidencias Encontradas", padding="10")
        matches_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview for matches - FIXED: Include all columns including hidden ones
        columns = ('Profesor CSV', 'Profesor DB', 'NRC', 'Dedicación', 'Estado', 'Problemas', 'match_index')
        self.matches_tree = ttk.Treeview(matches_frame, columns=columns, show='headings', height=15)
        
        # Define visible columns (hide match_index)
        visible_columns = ('Profesor CSV', 'Profesor DB', 'NRC', 'Dedicación', 'Estado', 'Problemas')
        for col in visible_columns:
            self.matches_tree.heading(col, text=col)
        
        # Hide the match_index column by setting width to 0
        self.matches_tree.heading('match_index', text='')
        self.matches_tree.column('match_index', width=0, stretch=False)
        
        # Configure visible column widths
        self.matches_tree.column('Profesor CSV', width=180)
        self.matches_tree.column('Profesor DB', width=180)
        self.matches_tree.column('NRC', width=80)
        self.matches_tree.column('Dedicación', width=80)
        self.matches_tree.column('Estado', width=100)
        self.matches_tree.column('Problemas', width=200)
        
        # Add matches data
        self.load_matches_data()
        
        # Scrollbar
        matches_scroll = ttk.Scrollbar(matches_frame, orient=tk.VERTICAL, command=self.matches_tree.yview)
        self.matches_tree.configure(yscrollcommand=matches_scroll.set)
        
        self.matches_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        matches_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Approval controls
        controls_frame = ttk.Frame(self.content_frame)
        controls_frame.pack(fill=tk.X)
        
        ttk.Button(controls_frame, text="✅ Aprobar Todos los Válidos", 
                  command=self.approve_all_valid, style="Green.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(controls_frame, text="❌ Rechazar Todos", 
                  command=self.clear_all_approvals, style="Red.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(controls_frame, text="📋 Ver Detalles", 
                  command=self.show_match_details, style="Blue.TButton").pack(side=tk.LEFT)
        
        # Bind double-click to toggle approval
        self.matches_tree.bind('<Double-1>', self.toggle_match_approval)
        
        self.setup_step_2_navigation()
    
    def load_matches_data(self):
        """Load matches data into the tree"""
        matches = self.processing_result['matches']
        
        for i, match in enumerate(matches):
            # Determine professor name from DB
            if match['professor_found']:
                prof_db = match['professor_match']['professor']['full_name']
                similarity = f"({match['professor_match']['similarity']:.2f})"
                prof_db_display = f"{prof_db} {similarity}"
            else:
                prof_db_display = "No encontrado"
            
            # Determine status
            if match['can_apply']:
                status = "✅ Listo"
                status_tag = "ready"
            else:
                status = "❌ Problemas"
                status_tag = "problems"
            
            # Problems summary
            problems = "; ".join(match['issues']) if match['issues'] else "Ninguno"
            
            # FIXED: Include match_index as the last value in the tuple
            item_id = self.matches_tree.insert('', tk.END, values=(
                match['professor_name'],
                prof_db_display,
                match['nrc'],
                f"{match['dedicacion']}%",
                status,
                problems,
                i  # This is the match_index value
            ), tags=(status_tag,))
        
        # Configure tags
        self.matches_tree.tag_configure("ready", background="#d4edda")
        self.matches_tree.tag_configure("problems", background="#f8d7da")
        self.matches_tree.tag_configure("approved", background="#cce5ff")
    def toggle_match_approval(self, event=None):
        """Toggle approval status of selected match"""
        selection = self.matches_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        # FIXED: Get match_index from the values instead of using set/get
        values = self.matches_tree.item(item, 'values')
        match_index = int(values[6])  # match_index is the 7th column (index 6)
        match = self.processing_result['matches'][match_index]
        
        if not match['can_apply']:
            messagebox.showwarning("No se puede aprobar", 
                                  "Esta coincidencia tiene problemas y no puede ser aprobada.")
            return
        
        # Toggle approval
        if match in self.approved_matches:
            self.approved_matches.remove(match)
            # Remove approved tag
            current_tags = list(self.matches_tree.item(item, 'tags'))
            if 'approved' in current_tags:
                current_tags.remove('approved')
            self.matches_tree.item(item, tags=current_tags)
        else:
            self.approved_matches.append(match)
            # Add approved tag
            current_tags = list(self.matches_tree.item(item, 'tags'))
            current_tags.append('approved')
            self.matches_tree.item(item, tags=current_tags)
        
        self.update_approval_status()
    
    def approve_all_valid(self):
        """Approve all valid matches"""
        self.approved_matches = [match for match in self.processing_result['matches'] if match['can_apply']]
        
        # Update tree display
        for item in self.matches_tree.get_children():
            values = self.matches_tree.item(item, 'values')
            match_index = int(values[6])  # FIXED: Get from values
            match = self.processing_result['matches'][match_index]
            
            if match['can_apply']:
                current_tags = list(self.matches_tree.item(item, 'tags'))
                if 'approved' not in current_tags:
                    current_tags.append('approved')
                self.matches_tree.item(item, tags=current_tags)
        
        self.update_approval_status()
    
    def show_match_details(self):
        """Show detailed information about selected match"""
        selection = self.matches_tree.selection()
        if not selection:
            messagebox.showinfo("Selección requerida", "Por favor seleccione una coincidencia para ver detalles.")
            return
        
        item = selection[0]
        values = self.matches_tree.item(item, 'values')
        match_index = int(values[6])  # FIXED: Get from values
        match = self.processing_result['matches'][match_index]
        
        self.show_match_detail_dialog(match)
    
    def clear_all_approvals(self):
        """Clear all approvals"""
        self.approved_matches = []
        
        # Update tree display
        for item in self.matches_tree.get_children():
            current_tags = list(self.matches_tree.item(item, 'tags'))
            if 'approved' in current_tags:
                current_tags.remove('approved')
            self.matches_tree.item(item, tags=current_tags)
        
        self.update_approval_status()
    
    def show_match_detail_dialog(self, match):
        """Show detailed match information in a dialog"""
        detail_window = tk.Toplevel(self.dialog)
        detail_window.title("Detalles de Coincidencia")
        detail_window.geometry("600x500")
        detail_window.transient(self.dialog)
        detail_window.grab_set()
        
        main_frame = ttk.Frame(detail_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Detalles de la Coincidencia", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Details text
        details_text = tk.Text(main_frame, wrap=tk.WORD, height=20)
        details_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=details_text.yview)
        details_text.configure(yscrollcommand=details_scroll.set)
        
        # Build details content
        content = f"INFORMACIÓN DEL CSV:\n"
        content += f"• Profesor: {match['professor_name']}\n"
        content += f"• NRC: {match['nrc']}\n"
        content += f"• Dedicación: {match['dedicacion']}%\n"
        content += f"• Período: {match['periodo']}\n\n"
        
        if match['professor_found']:
            prof_info = match['professor_match']['professor']
            content += f"COINCIDENCIA EN BASE DE DATOS:\n"
            content += f"• Profesor encontrado: {prof_info['full_name']}\n"
            content += f"• ID: {prof_info['id']}\n"
            content += f"• Tipo: {prof_info['tipo']}\n"
            content += f"• Similitud: {match['professor_match']['similarity']:.3f}\n\n"
        else:
            content += f"COINCIDENCIA EN BASE DE DATOS:\n"
            content += f"• No se encontró profesor con nombre similar\n\n"
        
        content += f"VALIDACIONES:\n"
        content += f"• Profesor encontrado: {'✅ Sí' if match['professor_found'] else '❌ No'}\n"
        content += f"• NRC existe: {'✅ Sí' if match['nrc_exists'] else '❌ No'}\n"
        content += f"• Puede aplicarse: {'✅ Sí' if match['can_apply'] else '❌ No'}\n\n"
        
        if match['issues']:
            content += f"PROBLEMAS DETECTADOS:\n"
            for issue in match['issues']:
                content += f"• {issue}\n"
        
        details_text.insert(tk.END, content)
        details_text.config(state=tk.DISABLED)
        
        details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        ttk.Button(main_frame, text="Cerrar", 
                  command=detail_window.destroy).pack(pady=(20, 0))
    
    def update_approval_status(self):
        """Update the approval status display"""
        # This method can be extended to show approval counts, etc.
        pass
    
    def setup_step_2_navigation(self):
        """Setup navigation for step 2"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
        
        ttk.Button(self.btn_frame, text="Atrás", command=self.show_step_1,
                  style="Gray.TButton").pack(side=tk.LEFT)
        
        ttk.Button(self.btn_frame, text="Cancelar", command=self.close_dialog,
                  style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        
        self.apply_btn = ttk.Button(self.btn_frame, text="Aplicar Cambios", 
                                   command=self.show_step_3, style="Green.TButton")
        self.apply_btn.pack(side=tk.RIGHT)
        
        # Show approval count
        approved_count = len(self.approved_matches)
        total_valid = len([m for m in self.processing_result['matches'] if m['can_apply']])
        
        count_label = ttk.Label(self.btn_frame, 
                               text=f"Aprobados: {approved_count} de {total_valid} válidos")
        count_label.pack(side=tk.RIGHT, padx=(0, 20))
    
    def show_step_3(self):
        """Step 3: Apply changes and show results"""
        if not self.approved_matches:
            messagebox.showwarning("Sin cambios", "No hay coincidencias aprobadas para aplicar.")
            return
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 3 de 3: Aplicando Cambios")
        
        # Show what will be applied
        summary_frame = ttk.LabelFrame(self.content_frame, text="Cambios a Aplicar", padding="15")
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        summary_text = (
            f"Se aplicarán {len(self.approved_matches)} actualizaciones de dedicación.\n\n"
            f"Esto actualizará los porcentajes de dedicación de profesores en las secciones correspondientes.\n"
            f"Los profesores deben estar previamente asignados a las secciones para que la actualización sea exitosa."
        )
        
        ttk.Label(summary_frame, text=summary_text, font=("Arial", 10)).pack()
        
        # Apply button and results
        apply_frame = ttk.LabelFrame(self.content_frame, text="Aplicar Actualizaciones", padding="15")
        apply_frame.pack(fill=tk.BOTH, expand=True)
        
        self.apply_changes_btn = ttk.Button(apply_frame, text="🚀 Aplicar Actualizaciones", 
                                           command=self.apply_changes, style="Green.TButton")
        self.apply_changes_btn.pack(pady=(0, 15))
        
        # Results area
        self.results_text = tk.Text(apply_frame, wrap=tk.WORD, height=15)
        results_scroll = ttk.Scrollbar(apply_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.setup_step_3_navigation()
    
    def apply_changes(self):
        """Apply the approved dedication changes"""
        if not self.approved_matches:
            return
        
        try:
            # Disable apply button
            self.apply_changes_btn.config(state="disabled")
            
            # Show progress
            self.results_text.insert(tk.END, "Aplicando actualizaciones de dedicación...\n\n")
            self.results_text.update()
            
            # Apply changes using the processor
            results = self.dedication_processor.apply_dedication_matches(self.approved_matches)
            
            # Display results
            if results['updated'] > 0:
                self.results_text.insert(tk.END, f"✅ ACTUALIZACIÓN EXITOSA\n\n")
                self.results_text.insert(tk.END, f"Secciones actualizadas: {results['updated']}\n\n")
                
                # Show details of updated sections
                self.results_text.insert(tk.END, "DETALLES DE ACTUALIZACIONES:\n")
                self.results_text.insert(tk.END, "=" * 50 + "\n")
                
                for section_update in results['updated_sections']:
                    self.results_text.insert(tk.END, f"\nSección NRC: {section_update['nrc']}\n")
                    self.results_text.insert(tk.END, f"Total dedicación: {section_update['total_dedicacion']}%\n")
                    self.results_text.insert(tk.END, f"Profesores actualizados:\n")
                    
                    for prof_update in section_update['professor_updates']:
                        self.results_text.insert(tk.END, 
                            f"  • {prof_update['profesor_name']}: {prof_update['dedicacion']}%\n")
                
                # Show success message
                messagebox.showinfo("Actualización Exitosa", 
                                   f"Se actualizaron {results['updated']} secciones con información de dedicación.")
                
                # Call callback if provided
                if self.callback:
                    self.callback()
            
            else:
                self.results_text.insert(tk.END, f"❌ NO SE APLICARON CAMBIOS\n\n")
                self.results_text.insert(tk.END, "No se pudo actualizar ninguna sección.\n")
            
            # Show errors if any
            if results['errors']:
                self.results_text.insert(tk.END, f"\nERRORES ENCONTRADOS:\n")
                for error in results['errors']:
                    self.results_text.insert(tk.END, f"• {error}\n")
            
            self.results_text.insert(tk.END, f"\n" + "=" * 50 + "\n")
            self.results_text.insert(tk.END, f"Proceso completado.\n")
            
        except Exception as e:
            self.results_text.insert(tk.END, f"❌ ERROR: {str(e)}\n")
            messagebox.showerror("Error", f"Error al aplicar cambios: {str(e)}")
        finally:
            self.apply_changes_btn.config(state="normal")
    
    def setup_step_3_navigation(self):
        """Setup navigation for step 3"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
        
        ttk.Button(self.btn_frame, text="Atrás", command=self.show_step_2,
                  style="Gray.TButton").pack(side=tk.LEFT)
        
        ttk.Button(self.btn_frame, text="Finalizar", command=self.close_dialog,
                  style="Green.TButton").pack(side=tk.RIGHT)
    
    def close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()
        
class DedicationViewerDialog:
    """Dialog for viewing dedication information across the system"""
    
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Visor de Dedicaciones")
        self.dialog.geometry("1200x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.theme_colors = get_theme_colors()
        self.style = setup_ttk_styles(self.dialog)
        
        self.setup_ui()
        apply_dark_mode_to_dialog(self.dialog, self.theme_colors)
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Visor de Dedicaciones", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="✕ Cerrar", command=self.close_dialog,
                  style="Red.TButton").pack(side=tk.RIGHT)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: By Section
        self.create_sections_tab()
        
        # Tab 2: By Professor
        self.create_professors_tab()
        
        # Tab 3: Summary Statistics
        self.create_summary_tab()
    
    def create_sections_tab(self):
        """Create tab showing dedicaciones by section"""
        sections_frame = ttk.Frame(self.notebook)
        self.notebook.add(sections_frame, text="Por Sección")
        
        # Load sections with dedication info
        self.load_sections_view(sections_frame)
    
    def create_professors_tab(self):
        """Create tab showing dedicaciones by professor"""
        professors_frame = ttk.Frame(self.notebook)
        self.notebook.add(professors_frame, text="Por Profesor")
        
        # Load professors with dedication info
        self.load_professors_view(professors_frame)
    
    def create_summary_tab(self):
        """Create tab showing dedication statistics"""
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Resumen")
        
        # Load summary statistics
        self.load_summary_view(summary_frame)
    
    def load_sections_view(self, parent):
        """Load sections view with dedication information"""
        try:
            sections = self.db_manager.get_sections_with_dedication_info()
            
            # Create table
            columns = ('NRC', 'Materia', 'Departamento', 'Profesores', 'Dedicación Total', 'Estudiantes')
            tree = ttk.Treeview(parent, columns=columns, show='headings', height=25)
            
            # Configure columns
            tree.heading('NRC', text='NRC')
            tree.heading('Materia', text='Materia')
            tree.heading('Departamento', text='Departamento')
            tree.heading('Profesores', text='Profesores')
            tree.heading('Dedicación Total', text='Total Dedic.%')
            tree.heading('Estudiantes', text='Estudiantes')
            
            tree.column('NRC', width=80)
            tree.column('Materia', width=120)
            tree.column('Departamento', width=180)
            tree.column('Profesores', width=60)
            tree.column('Dedicación Total', width=100)
            tree.column('Estudiantes', width=80)
            
            # Add data
            for section in sections:
                professor_count = len(section['dedicaciones']) if section['dedicaciones'] else 0
                
                tree.insert('', tk.END, values=(
                    section['nrc'],
                    section['materia_codigo'],
                    section['departamento'],
                    professor_count,
                    f"{section['total_dedicacion']}%",
                    f"{section['inscritos']}/{section['cupo']}"
                ))
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            ttk.Label(parent, text=f"Error cargando datos: {str(e)}").pack()
    
    def load_professors_view(self, parent):
        """Load professors view with dedication information"""
        try:
            professors = self.db_manager.get_professor_dedication_summary()
            
            # Create table
            columns = ('Profesor', 'Secciones', 'Dedicación Total', 'Secciones con Dedicación', 'Promedio por Sección')
            tree = ttk.Treeview(parent, columns=columns, show='headings', height=25)
            
            # Configure columns
            tree.heading('Profesor', text='Profesor')
            tree.heading('Secciones', text='Secciones')
            tree.heading('Dedicación Total', text='Total Dedic.%')
            tree.heading('Secciones con Dedicación', text='Con Dedicación')
            tree.heading('Promedio por Sección', text='Promedio%')
            
            tree.column('Profesor', width=200)
            tree.column('Secciones', width=80)
            tree.column('Dedicación Total', width=100)
            tree.column('Secciones con Dedicación', width=120)
            tree.column('Promedio por Sección', width=100)
            
            # Add data
            for prof in professors:
                avg_dedication = (prof['total_dedicacion'] / prof['total_sections']) if prof['total_sections'] > 0 else 0
                
                tree.insert('', tk.END, values=(
                    prof['full_name'],
                    prof['total_sections'],
                    f"{prof['total_dedicacion']}%",
                    prof['sections_with_dedicacion'],
                    f"{avg_dedication:.1f}%"
                ))
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            ttk.Label(parent, text=f"Error cargando datos: {str(e)}").pack()
    
    def load_summary_view(self, parent):
        """Load summary statistics view"""
        try:
            # Get summary data
            sections = self.db_manager.get_sections_with_dedication_info()
            professors = self.db_manager.get_professor_dedication_summary()
            
            # Calculate statistics
            total_sections = len(sections)
            sections_with_dedication = len([s for s in sections if s['total_dedicacion'] > 0])
            total_professors = len(professors)
            professors_with_dedication = len([p for p in professors if p['total_dedicacion'] > 0])
            
            # Over/under dedication analysis
            over_100_sections = len([s for s in sections if s['total_dedicacion'] > 100])
            under_50_sections = len([s for s in sections if 0 < s['total_dedicacion'] < 50])
            
            # Create summary display
            summary_text = tk.Text(parent, wrap=tk.WORD, height=30, width=80)
            scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=summary_text.yview)
            summary_text.configure(yscrollcommand=scrollbar.set)
            
            # Build summary content
            content = "RESUMEN DE DEDICACIONES\n"
            content += "=" * 50 + "\n\n"
            
            content += "ESTADÍSTICAS GENERALES:\n"
            content += f"• Total de secciones: {total_sections}\n"
            content += f"• Secciones con dedicación asignada: {sections_with_dedication}\n"
            content += f"• Porcentaje de cobertura: {(sections_with_dedication/total_sections*100):.1f}%\n\n"
            
            content += f"• Total de profesores: {total_professors}\n"
            content += f"• Profesores con dedicación asignada: {professors_with_dedication}\n"
            content += f"• Porcentaje de profesores activos: {(professors_with_dedication/total_professors*100):.1f}%\n\n"
            
            content += "ANÁLISIS DE DEDICACIÓN:\n"
            content += f"• Secciones con sobrededicación (>100%): {over_100_sections}\n"
            content += f"• Secciones con baja dedicación (<50%): {under_50_sections}\n"
            content += f"• Secciones sin dedicación: {total_sections - sections_with_dedication}\n\n"
            
            if sections_with_dedication > 0:
                avg_dedication = sum(s['total_dedicacion'] for s in sections if s['total_dedicacion'] > 0) / sections_with_dedication
                content += f"• Promedio de dedicación por sección: {avg_dedication:.1f}%\n\n"
            
            content += "TOP 10 SECCIONES POR DEDICACIÓN:\n"
            content += "-" * 30 + "\n"
            top_sections = sorted([s for s in sections if s['total_dedicacion'] > 0], 
                                key=lambda x: x['total_dedicacion'], reverse=True)[:10]
            
            for i, section in enumerate(top_sections, 1):
                content += f"{i:2d}. NRC {section['nrc']} ({section['materia_codigo']}): {section['total_dedicacion']}%\n"
            
            content += "\nTOP 10 PROFESORES POR DEDICACIÓN:\n"
            content += "-" * 30 + "\n"
            top_professors = sorted([p for p in professors if p['total_dedicacion'] > 0], 
                                  key=lambda x: x['total_dedicacion'], reverse=True)[:10]
            
            for i, prof in enumerate(top_professors, 1):
                content += f"{i:2d}. {prof['full_name']}: {prof['total_dedicacion']}% ({prof['total_sections']} secciones)\n"
            
            summary_text.insert(tk.END, content)
            summary_text.config(state=tk.DISABLED)
            
            summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            ttk.Label(parent, text=f"Error cargando resumen: {str(e)}").pack()
    
    def close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()
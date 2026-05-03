import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from database import Validator

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("User Management System")
        self.root.geometry("950x600")
        self.root.configure(bg="#f0f4f8")

        try:
            self.db = Database()
        except Exception as e:
            messagebox.showerror("Erreur de connexion", str(e))
            self.root.destroy()
            return

        self.selected_id = None
        self._build_ui()
        self.load_users()

    # ── Construction de l'interface ──────────────────────────
    def _build_ui(self):
        # ---- Titre ----
        title = tk.Label(self.root, text="👤 User Management System",
                         font=("Helvetica", 18, "bold"),
                         bg="#2c3e50", fg="white", pady=10)
        title.pack(fill="x")

        main_frame = tk.Frame(self.root, bg="#f0f4f8")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- Formulaire (gauche) ----
        form_frame = tk.LabelFrame(main_frame, text="📋 Formulaire",
                                   font=("Helvetica", 11, "bold"),
                                   bg="#f0f4f8", padx=10, pady=10)
        form_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        fields = [
            ("Prénom",              "first_name"),
            ("Nom",                 "last_name"),
            ("Date de naissance\n(JJ/MM/AAAA)", "birth_date"),
            ("Lieu de naissance",   "birth_place"),
            ("Téléphone",           "phone_number"),
        ]

        self.entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form_frame, text=label, bg="#f0f4f8",
                     font=("Helvetica", 10)).grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(form_frame, width=25, font=("Helvetica", 10))
            entry.grid(row=i, column=1, padx=8, pady=5)
            self.entries[key] = entry

        # Boutons CRUD
        btn_frame = tk.Frame(form_frame, bg="#f0f4f8")
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=12)

        buttons = [
            ("➕ Ajouter",     "#27ae60", self.add_user),
            ("✏️ Modifier",    "#2980b9", self.update_user),
            ("🗑️ Supprimer",   "#e74c3c", self.delete_user),
            ("🔄 Réinitialiser","#7f8c8d", self.clear_form),
        ]
        for text, color, cmd in buttons:
            tk.Button(btn_frame, text=text, bg=color, fg="white",
                      font=("Helvetica", 10, "bold"), width=14,
                      command=cmd, relief="flat", cursor="hand2"
                      ).pack(pady=3)

        # ---- Tableau + Recherche (droite) ----
        right_frame = tk.Frame(main_frame, bg="#f0f4f8")
        right_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)

        # Barre de recherche
        search_frame = tk.Frame(right_frame, bg="#f0f4f8")
        search_frame.pack(fill="x", pady=(0, 6))

        tk.Label(search_frame, text="🔍 Recherche :", bg="#f0f4f8",
                 font=("Helvetica", 10)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.search_users())
        tk.Entry(search_frame, textvariable=self.search_var,
                 width=30, font=("Helvetica", 10)).pack(side="left", padx=8)
        tk.Button(search_frame, text="Tout afficher", command=self.load_users,
                  bg="#8e44ad", fg="white", relief="flat", cursor="hand2"
                  ).pack(side="left")

        # Treeview
        columns = ("Prénom", "Nom", "Date naissance", "Lieu naissance", "Téléphone")
        self.tree = ttk.Treeview(right_frame, columns=columns,
                                  show="headings", height=20)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("Treeview", font=("Helvetica", 10), rowheight=26)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical",
                                   command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ── Chargement / Affichage ───────────────────────────────
    def load_users(self, users=None):
        self.tree.delete(*self.tree.get_children())
        self._user_map = {}  # iid -> _id MongoDB

        data = users if users is not None else self.db.get_all_users()
        for user in data:
            iid = self.tree.insert("", "end", values=(
                user.get("first_name"),
                user.get("last_name"),
                user.get("birth_date"),
                user.get("birth_place"),
                user.get("phone_number"),
            ))
            self._user_map[iid] = str(user["_id"])

    # ── Sélection dans le tableau ────────────────────────────
    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        iid = selected[0]
        values = self.tree.item(iid, "values")
        keys = ["first_name", "last_name", "birth_date", "birth_place", "phone_number"]
        self.clear_form(keep_id=True)
        for key, val in zip(keys, values):
            self.entries[key].insert(0, val)
        self.selected_id = self._user_map[iid]

    # ── CRUD ─────────────────────────────────────────────────
    def _get_form_data(self):
        return {k: e.get().strip() for k, e in self.entries.items()}

    def add_user(self):
        data = self._get_form_data()
        errors = Validator.validate_user(data)
        if errors:
            messagebox.showerror("Erreurs de validation", "\n".join(errors))
            return
        try:
            self.db.add_user(data)
            messagebox.showinfo("Succès", "✅ Utilisateur ajouté avec succès !")
            self.clear_form()
            self.load_users()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def update_user(self):
        if not self.selected_id:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un utilisateur.")
            return
        data = self._get_form_data()
        errors = Validator.validate_user(data)
        if errors:
            messagebox.showerror("Erreurs de validation", "\n".join(errors))
            return
        try:
            self.db.update_user(self.selected_id, data)
            messagebox.showinfo("Succès", "✅ Utilisateur modifié avec succès !")
            self.clear_form()
            self.load_users()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def delete_user(self):
        if not self.selected_id:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un utilisateur.")
            return
        confirm = messagebox.askyesno("Confirmation",
                                       "⚠️ Voulez-vous vraiment supprimer cet utilisateur ?")
        if confirm:
            self.db.delete_user(self.selected_id)
            messagebox.showinfo("Succès", "✅ Utilisateur supprimé.")
            self.clear_form()
            self.load_users()

    def search_users(self):
        query = self.search_var.get().strip()
        if not query:
            self.load_users()
            return
        results = self.db.search_users(query)
        self.load_users(users=results)

    def clear_form(self, keep_id=False):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        if not keep_id:
            self.selected_id = None
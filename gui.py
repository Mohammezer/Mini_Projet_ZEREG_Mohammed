from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
            self.client.admin.command('ping')  # test connexion
            self.db = self.client["user_management"]
            self.collection = self.db["users"]
            # Index unique sur phone_number
            self.collection.create_index("phone_number", unique=True)
            print("✅ Connexion MongoDB réussie")
        except ConnectionFailure:
            raise Exception(" Impossible de se connecter à MongoDB. Vérifiez que le serveur est lancé.")

    # ── CREATE ──────────────────────────────────────────────
    def add_user(self, user_data):
        try:
            result = self.collection.insert_one(user_data)
            return result.inserted_id
        except DuplicateKeyError:
            raise Exception(" Ce numéro de téléphone existe déjà.")

    # ── READ ─────────────────────────────────────────────────
    def get_all_users(self):
        return list(self.collection.find())

    def search_users(self, query):
        """Recherche dans tous les champs (insensible à la casse)."""
        regex = {"$regex": query, "$options": "i"}
        return list(self.collection.find({
            "$or": [
                {"first_name": regex},
                {"last_name": regex},
                {"birth_place": regex},
                {"phone_number": regex},
                {"birth_date": regex},
            ]
        }))

    # ── UPDATE ───────────────────────────────────────────────
    def update_user(self, user_id, updated_data):
        from bson import ObjectId
        try:
            self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updated_data}
            )
        except DuplicateKeyError:
            raise Exception("❌ Ce numéro de téléphone est déjà utilisé.")

    # ── DELETE ───────────────────────────────────────────────
    def delete_user(self, user_id):
        from bson import ObjectId
        self.collection.delete_one({"_id": ObjectId(user_id)})

import re
from datetime import datetime

class Validator:
    @staticmethod
    def validate_user(data):
        errors = []

        if not data.get("first_name", "").strip():
            errors.append("Le prénom est obligatoire.")

        if not data.get("last_name", "").strip():
            errors.append("Le nom est obligatoire.")

        if not data.get("birth_place", "").strip():
            errors.append("Le lieu de naissance est obligatoire.")

        # Format date : DD/MM/YYYY
        birth_date = data.get("birth_date", "").strip()
        if not birth_date:
            errors.append("La date de naissance est obligatoire.")
        else:
            try:
                datetime.strptime(birth_date, "%d/%m/%Y")
            except ValueError:
                errors.append("Format de date invalide. Utilisez JJ/MM/AAAA.")

        # Téléphone : 10 chiffres (adaptable)
        phone = data.get("phone_number", "").strip()
        if not phone:
            errors.append("Le numéro de téléphone est obligatoire.")
        elif not re.match(r"^\+?[0-9]{9,15}$", phone):
            errors.append("Numéro de téléphone invalide.")

        return errors
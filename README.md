# 💹 FinanceIQ — Backend Django

Application de Gestion Financière Simplifiée & Intelligente  
**Stack :** Python · Django REST Framework · MySQL · JWT

---

## 📋 Description

FinanceIQ est une API REST développée avec Django permettant aux PME, TPE et entrepreneurs de gérer leurs finances en temps réel — sans compétences comptables.

---

## ⚙️ Technologies utilisées

- Python 3.10+
- Django 4.x
- Django REST Framework
- SimpleJWT (authentification)
- MySQL
- Django Signals (alertes automatiques)

---

## 🚀 Installation rapide

### 1. Cloner le projet
```bash
git clone https://github.com/KARAGA-creat/gestion_financiere.git
cd gestion_financiere
```

### 2. Créer et activer l'environnement virtuel
```bash
python -m venv env
env\Scripts\activate        # Windows
source env/bin/activate     # Mac/Linux
```

### 3. Installer les dépendances
```bash
pip install django djangorestframework djangorestframework-simplejwt mysqlclient django-cors-headers python-decouple Pillow
```

### 4. Configurer le fichier .env
Créez un fichier `.env` à la racine :

SECRET_KEY=votre-cle-secrete
DEBUG=True
DB_NAME=gestion_financiere
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

### 5. Créer la base de données MySQL
```sql
CREATE DATABASE gestion_financiere CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 6. Appliquer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Démarrer le serveur
```bash
python manage.py runserver
```
API disponible sur : **http://127.0.0.1:8000**

---

## 📡 Principaux endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/inscription/` | Créer un compte Admin |
| POST | `/api/auth/login/` | Connexion |
| GET | `/api/transactions/` | Liste des transactions |
| POST | `/api/transactions/` | Créer une transaction |
| GET | `/api/budgets/` | Liste des budgets |
| GET | `/api/alertes/` | Liste des alertes |
| POST | `/api/rapports/generer/` | Générer un rapport mensuel |

---

## 🗄️ Modèle de données

9 entités principales :
`Entreprise` · `Utilisateur` · `Transaction` · `Categorie` · `Tiers` · `DetteFacture` · `Budget` · `Alerte` · `RapportSnapshot`

---

## 👥 Rôles utilisateurs

| Rôle | Accès |
|------|-------|
| **Admin** | Accès complet — gère l'entreprise et les utilisateurs |
| **Gestionnaire** | Gère les opérations financières quotidiennes |

---

## 🔗 Frontend
👉 [github.com/KARAGA-creat/frontend](https://github.com/KARAGA-creat/frontend)

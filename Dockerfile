# Utilise une image Python officielle
FROM python:3.11-slim

# Crée un utilisateur non-root avec l'ID 1000 (requis par Hugging Face)
RUN useradd -m -u 1000 user

# Définit le répertoire de travail
WORKDIR /app

# Installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie le fichier des requirements
COPY requirements.txt .

# Installe les librairies Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le code dans le conteneur
COPY --chown=user . .

# IMPORTANT : Crée le dossier databases s'il n'existe pas et donne les droits à l'utilisateur
# Cela permet au script d'écrire le fichier pharmacies_cache.json
RUN mkdir -p databases && chown -R user:user /app

# Bascule sur l'utilisateur non-root
USER user

# Définit les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose le port 7860 (Standard Hugging Face)
EXPOSE 7860

# Lance l'application sur le port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
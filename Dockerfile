FROM python:3.11-slim

RUN useradd -m -u 1000 user

# Définir le répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier des requirements
COPY requirements.txt .

# Installe les librairies Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le code dans le conteneur
COPY --chown=user . .


RUN mkdir -p databases && chown -R user:user /app

# Bascule sur l'utilisateur non-root
USER user

# Définit les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose le port 7860 
EXPOSE 7860

# Lance l'application sur le port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
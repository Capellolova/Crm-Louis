# CRM Louis — MVP local

MVP codé en Streamlit, basé sur les spécifications validées :
- fiche client
- 2 contacts clés
- pipeline affaires
- dashboard
- urgences / relances
- upload de PDF par affaire
- génération d'un brouillon email `.eml` avec la proposition principale jointe

## Lancer l'app

```bash
cd /mnt/data/crm_app_mvp
pip install -r requirements.txt
streamlit run app.py
```

## Ce que fait déjà cette version

- importe automatiquement la base du fichier `AFFAIRES CHAUDES LLD  .xlsx` si la base est vide
- stocke les données dans `data/crm.sqlite3`
- stocke les documents dans `data/uploads/`
- crée les brouillons email dans `data/drafts/`

## Limite actuelle importante

L'app génère un brouillon `.eml` téléchargeable avec pièce jointe.
L'ouverture directe dans Outlook/Gmail avec PJ depuis le navigateur n'est pas fiable en version web simple. J'ai donc choisi une version robuste : brouillon prêt à ouvrir / envoyer.

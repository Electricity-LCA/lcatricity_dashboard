LCAtricity Dashboard
===================

# How to run
```commandline
python -m streamlit run lcatricity_dashboard/main.py
```

# Building 
1. Build with Docker
```bash
cd lcatricity_dashboard
docker build . -t lcatricity_dashboard:latest
docker image save --output ../lcatricity_dashboard.tar lcatricity_dashboard:latest
```

Tip: If you repeatedly run docker build commands the created image gets progressively bigger.
To avoid this run `docker buildx prune -f`

# Running with Docker
```bash
docker compose up -d
```
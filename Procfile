web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
vitrine: gunicorn --bind 0.0.0.0:5000 --workers=2 --access-logfile - --error-logfile - vitrine_railway:app

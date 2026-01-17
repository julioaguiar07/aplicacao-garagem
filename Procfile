web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
vitrine: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 vitrine_railway:app

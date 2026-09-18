web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
vitrine_web: gunicorn --bind 0.0.0.0:$PORT --workers=2 --access-logfile - --error-logfile - vitrine_railway:app

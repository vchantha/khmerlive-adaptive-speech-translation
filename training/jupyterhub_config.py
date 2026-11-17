import os
from jupyterhub.auth import SharedPasswordAuthenticator
from jupyterhub.spawner import SimpleLocalProcessSpawner

c = get_config()  # noqa: F821
c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/jupyterhub.sqlite"
c.JupyterHub.authenticator_class = SharedPasswordAuthenticator
c.JupyterHub.spawner_class = SimpleLocalProcessSpawner
c.JupyterHub.allow_named_servers = True
c.SharedPasswordAuthenticator.user_password = os.environ.get("JUPYTERHUB_PASSWORD","change-me-jupyter")
c.SharedPasswordAuthenticator.admin_password = os.environ.get("JUPYTERHUB_ADMIN_PASSWORD","change-me-admin")
c.Authenticator.admin_users = {"admin"}
c.Spawner.cmd = ["jupyter-labhub"]
c.Spawner.notebook_dir = "/workspace"
c.Spawner.default_url = "/lab"
c.Spawner.environment = {
  "DATABASE_URL": os.environ.get("DATABASE_URL",""),
  "KAFKA_BOOTSTRAP_SERVERS": os.environ.get("KAFKA_BOOTSTRAP_SERVERS","kafka:19092"),
  "MINIO_ENDPOINT": os.environ.get("MINIO_ENDPOINT","minio:9000"),
  "MINIO_ACCESS_KEY": os.environ.get("MINIO_ACCESS_KEY",""),
  "MINIO_SECRET_KEY": os.environ.get("MINIO_SECRET_KEY",""),
  "MINIO_BUCKET": os.environ.get("MINIO_BUCKET","khmerlive"),
  "MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI","http://mlflow:5000"),
}

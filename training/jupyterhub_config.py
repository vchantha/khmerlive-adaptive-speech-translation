import os

<<<<<<< HEAD
from jupyterhub.authenticators.shared import SharedPasswordAuthenticator
=======
>>>>>>> 8629d56567555d3caa84d091a4851d5880b03128
from jupyterhub.spawner import SimpleLocalProcessSpawner

c = get_config()  # noqa: F821
c.JupyterHub.bind_url = "https://0.0.0.0:8000"
c.JupyterHub.ssl_key = "/etc/jupyterhub/tls/tls.key"
c.JupyterHub.ssl_cert = "/etc/jupyterhub/tls/tls.crt"
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/jupyterhub.sqlite"
c.JupyterHub.authenticator_class = "shared-password"
c.JupyterHub.spawner_class = SimpleLocalProcessSpawner
c.JupyterHub.allow_named_servers = True

c.Authenticator.allowed_users = {"researcher", "admin"}
c.Authenticator.admin_users = {"admin"}
c.SharedPasswordAuthenticator.user_password = os.environ.get(
    "JUPYTERHUB_PASSWORD", "change-me-jupyter"
)
c.SharedPasswordAuthenticator.admin_password = os.environ.get(
<<<<<<< HEAD
    "JUPYTERHUB_ADMIN_PASSWORD", "change-me-admin-password-min-32-chars"
=======
    "JUPYTERHUB_ADMIN_PASSWORD", "change-me-jupyter-admin-password-32chars"
>>>>>>> 8629d56567555d3caa84d091a4851d5880b03128
)

c.Spawner.cmd = ["jupyter-labhub"]
c.Spawner.notebook_dir = "/workspace"
c.Spawner.default_url = "/lab"
c.Spawner.environment = {
    "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
    "KAFKA_BOOTSTRAP_SERVERS": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:19093"),
    "KAFKA_SECURITY_PROTOCOL": os.environ.get("KAFKA_SECURITY_PROTOCOL", "SSL"),
    "KAFKA_SSL_CA_LOCATION": os.environ.get(
        "KAFKA_SSL_CA_LOCATION", "/etc/khmerlive/tls/ca.crt"
    ),
    "SILO_ENDPOINT": os.environ.get("SILO_ENDPOINT", "silo:9000"),
    "SILO_ACCESS_KEY": os.environ.get("SILO_ACCESS_KEY", ""),
    "SILO_SECRET_KEY": os.environ.get("SILO_SECRET_KEY", ""),
    "SILO_BUCKET": os.environ.get("SILO_BUCKET", "khmerlive"),
    "SILO_SECURE": os.environ.get("SILO_SECURE", "true"),
    "SILO_CA_FILE": os.environ.get("SILO_CA_FILE", "/etc/khmerlive/tls/ca.crt"),
    "MINIO_ENDPOINT": os.environ.get("SILO_ENDPOINT", "silo:9000"),
    "MINIO_ACCESS_KEY": os.environ.get("SILO_ACCESS_KEY", ""),
    "MINIO_SECRET_KEY": os.environ.get("SILO_SECRET_KEY", ""),
    "MINIO_BUCKET": os.environ.get("SILO_BUCKET", "khmerlive"),
    "MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
    "AWS_CA_BUNDLE": "/etc/khmerlive/tls/ca.crt",
}

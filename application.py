# Ponte de compatibilidade para AWS Elastic Beanstalk/Gunicorn.
# Mantém suporte caso o ambiente tente iniciar como application:application.
from app import app as application

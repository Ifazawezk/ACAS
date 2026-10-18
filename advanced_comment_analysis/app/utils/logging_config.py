import logging

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def configure_logging(level=logging.INFO):
    logging.basicConfig(level=level, format=LOG_FORMAT)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

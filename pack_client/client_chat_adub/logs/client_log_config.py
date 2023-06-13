import logging
import os

# log_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.getcwd()
log_path = os.path.join(log_path, 'client_logs/client.log')

logger_client = logging.getLogger('client')

formatter_client = logging.Formatter("%(asctime)s - %(levelname)s  %(module)s: %(message)s ")

timed_rotating_fhc = logging.FileHandler(log_path, encoding='utf8')
timed_rotating_fhc.setLevel(logging.DEBUG)
timed_rotating_fhc.setFormatter(formatter_client)

logger_client.addHandler(timed_rotating_fhc)
logger_client.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger_client.debug('testing client logging system')

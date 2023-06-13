import logging
import logging.handlers
import os

# log_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.getcwd()
log_path = os.path.join(log_path, 'server_logs/server.log')

logger_server = logging.getLogger('server')

formatter_server = logging.Formatter("%(asctime)s - %(levelname)s  %(module)s: %(message)s ")

timed_rotating_fhs = logging.handlers.TimedRotatingFileHandler(log_path,
                                                               encoding='utf8',
                                                               when='midnight',
                                                               interval=1)
timed_rotating_fhs.setLevel(logging.DEBUG)
timed_rotating_fhs.setFormatter(formatter_server)

logger_server.addHandler(timed_rotating_fhs)
logger_server.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # logger_server.debug('testing server logging system')
    print(log_path)

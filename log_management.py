import logging
import os
from datetime import datetime, timedelta


def setup_logger(logger_name="dnpsaber_logger", log_dir_name="logs"):
    """
    配置日志记录器，避免重复初始化
    :param logger_name: 日志记录器名称
    :param log_dir_name: 日志目录名称
    """
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():  # 检查是否已绑定处理器
        # 创建日志目录
        if os.name == 'nt':
            log_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'dnpsaber', log_dir_name)
        elif os.name == 'posix':
            log_dir = os.path.join(os.getenv('HOME'), 'dnpsaber', log_dir_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # 设置日志文件路径
        log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")

        # 配置日志记录器
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # 调用日志清理函数
        clean_old_logs(log_dir, days=30)

    return logger


def clean_old_logs(log_dir, days=30):
    """
    清理超过指定天数的日志文件
    :param log_dir: 日志目录
    :param days: 保留的天数
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    for log_file in os.listdir(log_dir):
        file_path = os.path.join(log_dir, log_file)
        if os.path.isfile(file_path) and log_file.endswith(".log"):  # 确保是日志文件
            try:
                file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_creation_time < cutoff_date:
                    os.remove(file_path)
                    logger.info(f"已删除日志文件: {file_path}")
            except Exception as e:
                logger.error(f"删除日志文件失败: {file_path}, 错误: {e}")


logger = setup_logger()

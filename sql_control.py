import pymysql
import openpyxl

from datetime import datetime
from log_management import logger



class sql_Management:
    """
    一个用于管理 MySQL 数据库的类，支持用户登录、用户管理、数据库检查与创建、表查询等功能。
    """

    def __init__(self, sql_user=None, sql_user_passwd=None):
        """
        初始化 sql_Management 类。

        :param sql_user: 数据库用户名
        :param sql_user_passwd: 数据库用户密码
        """
        self.user = sql_user
        self.user_passwd = sql_user_passwd
        self.host = "127.0.0.1"
        self.port = 3306
        self.conn = None
        self.userType = None

    def __enter__(self):
        """
        上下文管理器的进入方法，返回当前实例。
        
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        上下文管理器的退出方法，关闭数据库连接。
        """
        if self.conn:
            self.conn.close()
            logger.info(f"用户{self.user}的数据库连接已关闭")

    def sql_connect(self):
        """
        根据用户类型（管理员或普通用户）选择登录方法。
        :return: 登录结果信息
        """
        if self.user == "root":
            return self.__sql_root_connect()
        else:
            return self.__sql_user_connect()

    def __sql_root_connect(self):
        """
        管理员用户登录数据库。
        :return: 登录结果信息
        """
        try:
            self.conn = pymysql.connect(host=self.host, user=self.user, password=self.user_passwd, port=self.port)
            message = "管理员登录成功"
            logger.info(f'管理员{self.user}登录成功')
            self.userType = "root"
            self.check_database_exists()
        except pymysql.MySQLError as e:
            message = f"登录失败，用户名或密码错误"
            logger.error(f"{message}:{e}", exc_info=False)
        print(message)
        return message

    def __sql_user_connect(self):
        """
        普通用户登录数据库。
        :return: 登录结果信息
        """
        try:
            self.conn = pymysql.connect(host=self.host, user=self.user, password=self.user_passwd, port=self.port)
            message = "登录成功"
            logger.info(f'用户{self.user}登录成功')
            self.userType = "user"
        except pymysql.MySQLError as e:
            message = f"登录失败，用户名或密码错误"
            logger.error(f"{message}:{e}", exc_info=False)
        print(message)
        return message

    def check_database_exists(self, database_name='dnpsaber'):
        """
        检查指定数据库是否存在，如果不存在则创建。

        :param database_name: 要检查的数据库名称，默认为 'dnpsaber'
        :return: 数据库是否存在的布尔值
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"SHOW DATABASES LIKE '{database_name}';")
                logger.info(f'用户{self.user}检测默认数据库是否存在')
                result = cursor.fetchone()
                if result:
                    logger.info(f"默认数据库 {database_name} 存在")
                    # 切换到目标数据库并自动创建总表
                    cursor.execute(f"USE `{database_name}`;")
                    self.auto_create_main_table()
                    # 新增：自动创建今日出库表和入库表
                    today_str = datetime.now().strftime("%Y%m%d")
                    self.auto_create_daily_out_table(today_str)
                    self.auto_create_daily_in_table(today_str)
                    return True
                else:
                    logger.info(f"默认数据库 {database_name} 不存在，需要创建")
                    self.sql_defaultDatabaseCreation()
                    return False
        except pymysql.MySQLError as e:
            logger.error(f"检查数据库失败: {e}", exc_info=False)
            print(f"检查数据库失败: {e}")
            return False

    def sql_defaultDatabaseCreation(self):
        """
        创建默认数据库 'dnpsaber'。
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "CREATE DATABASE IF NOT EXISTS `dnpsaber` CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci';")
                logger.info(f"用户{self.user} 默认数据库 dnpsaber 创建成功")
            self.conn.commit()
        except pymysql.MySQLError as e:
            logger.error(f"用户{self.user} 创建数据库失败: {e}", exc_info=False)

    def auto_create_main_table(self, table_name='总表'):
        """
        检查并自动创建总表（如不存在）。
        表结构：
        - ID: 主键，自增长
        - uuid: 字符串
        - 名称: 字符串
        - 位置: 字符串
        - 图片url: 字符串
        - 数量: 字符串
        - 最后更新时间: 字符串
        - 备注: 字符串
        所有字段支持中文。
        """
        try:
            with self.conn.cursor() as cursor:
                # 检查表是否存在
                cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
                result = cursor.fetchone()
                if result:
                    logger.info(f"用户{self.user} 总表 {table_name} 已存在，无需创建")
                    return
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS `{table_name}` (
                        `ID` INT AUTO_INCREMENT PRIMARY KEY,
                        `uuid` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `名称` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `位置` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `图片url` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `数量` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `最后更新时间` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `备注` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                logger.info(f"用户{self.user} 检查并自动创建总表 {table_name} 成功")
            self.conn.commit()
        except pymysql.MySQLError as e:
            logger.error(f"用户{self.user} 创建总表失败: {e}", exc_info=False)

    def auto_create_daily_out_table(self, date_str):
        """
        检查并自动创建每日出库表（如不存在）。
        表名为“出库+年月日”，如“出库20240622”。
        字段结构与总表一致，全部为字符串类型，支持中文。
        :param date_str: 年月日字符串，如20240622
        """
        table_name = f"出库{date_str}"
        try:
            with self.conn.cursor() as cursor:
                # 检查表是否存在
                cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
                result = cursor.fetchone()
                if result:
                    logger.info(f"用户{self.user} 每日出库表 {table_name} 已存在，无需创建")
                    return
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS `{table_name}` (
                        `ID` INT AUTO_INCREMENT PRIMARY KEY,
                        `uuid` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `名称` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `价格` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `位置` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `图片url` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `数量` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `最后更新时间` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `备注` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                logger.info(f"用户{self.user} 检查并自动创建每日出库表 {table_name} 成功")
            self.conn.commit()
        except pymysql.MySQLError as e:
            logger.error(f"用户{self.user} 创建每日出库表失败: {e}", exc_info=False)

    def auto_create_daily_in_table(self, date_str):
        """
        检查并自动创建每日入库表（如不存在）。
        表名为“入库+年月日”，如“入库20240622”。
        字段结构与总表一致，全部为字符串类型，支持中文。
        :param date_str: 年月日字符串，如20240622
        """
        table_name = f"入库{date_str}"
        try:
            with self.conn.cursor() as cursor:
                # 检查表是否存在
                cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
                result = cursor.fetchone()
                if result:
                    logger.info(f"用户{self.user} 每日入库表 {table_name} 已存在，无需创建")
                    return
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS `{table_name}` (
                        `ID` INT AUTO_INCREMENT PRIMARY KEY,
                        `uuid` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `名称` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `位置` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `图片url` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `数量` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `最后更新时间` VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                        `备注` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                logger.info(f"用户{self.user} 检查并自动创建每日入库表 {table_name} 成功")
            self.conn.commit()
        except pymysql.MySQLError as e:
            logger.error(f"用户{self.user} 创建每日入库表失败: {e}", exc_info=False)

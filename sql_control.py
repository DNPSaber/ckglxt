import pymysql
import openpyxl

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

    def list_tables(self):
        """
        列出当前数据库中的所有表。
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("USE dnpsaber;")
                cursor.execute("SHOW TABLES;")
                logger.info(f'用户{self.user}查询表')
                result = cursor.fetchall()
                if result:
                    logger.info("查询表成功")
                    print("数据库中的表如下：")
                    for table in result:
                        print(table[0])
                else:
                    logger.info("数据库中没有表")
                    print("数据库中没有表")
        except pymysql.MySQLError as e:
            logger.error(f"查询表失败: {e}", exc_info=False)
            print(f"查询表失败: {e}")


if __name__ == "__main__":
    # 示例代码：创建 sql_Management 实例并执行相关操作
    sql = sql_Management("root", "8507181ZZZzzz")
    sql.sql_connect()
    sql.check_database_exists()
    sql.list_tables()

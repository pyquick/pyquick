import logging
import logging.config
import os
import gzip
import shutil
import time
import traceback
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler, SMTPHandler

# 定义日志级别常量
VERBOSE = 5  # 比DEBUG更详细的级别

class CompressedRotatingFileHandler(RotatingFileHandler):
    """
    扩展的日志处理器，在轮转时自动压缩旧日志文件
    """
    def doRollover(self):
        """
        执行日志轮转并压缩旧日志文件
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            # 移动旧文件
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d" % (self.baseFilename, i))
                dfn = self.rotation_filename("%s.%d" % (self.baseFilename, i + 1))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            dfn = self.rotation_filename(self.baseFilename + ".1")
            if os.path.exists(dfn):
                os.remove(dfn)
            
            # 压缩日志文件
            os.rename(self.baseFilename, dfn)
            with open(dfn, 'rb') as f_in:
                with gzip.open(f'{dfn}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(dfn)  # 删除未压缩的文件
        
        self.mode = 'w'
        self.stream = self._open()

class PyQuickFilter(logging.Filter):
    """
    自定义日志过滤器，用于过滤特定的日志消息
    """
    def __init__(self, exclude_patterns=None):
        super().__init__()
        self.exclude_patterns = exclude_patterns or []
    
    def filter(self, record):
        # 排除匹配指定模式的日志记录
        message = record.getMessage()
        for pattern in self.exclude_patterns:
            if pattern in message:
                return False
        return True

def setup_logger(
    email_notifications=False, 
    email_config=None, 
    log_level=logging.DEBUG, 
    compress_logs=True,
    exclude_patterns=None,
    use_console=False  # 新增参数，默认不使用控制台输出
):
    """
    设置日志记录器
    
    参数:
        email_notifications (bool): 是否启用邮件通知
        email_config (dict): 邮件配置，包括 host, port, from_addr, to_addrs, subject, credentials
        log_level (int): 日志级别
        compress_logs (bool): 是否压缩旧日志
        exclude_patterns (list): 要排除的日志消息模式列表
        use_console (bool): 是否启用控制台输出（GUI应用中应设为False）
    
    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 注册自定义日志级别
    logging.addLevelName(VERBOSE, "VERBOSE")
    
    def verbose(self, message, *args, **kwargs):
        """
        记录详细日志的方法
        """
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, message, args, **kwargs)
    
    # 为 Logger 类添加 verbose 方法
    logging.Logger.verbose = verbose
    
    version_pyquick = "2050"
    config_path_base = os.path.join(os.environ["APPDATA"], "pyquick")
    config_path = os.path.join(config_path_base, version_pyquick)
    log_dir = os.path.join(config_path, "log")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 读取用户配置的日志大小限制
    max_log_size_mb = 10  # 默认10MB
    try:
        log_size_file = os.path.join(config_path, "log_size.txt")
        if os.path.exists(log_size_file):
            with open(log_size_file, "r") as f:
                size_str = f.read().strip()
                if size_str and size_str.isdigit():
                    max_log_size_mb = int(size_str)
    except Exception as e:
        print(f"读取日志大小配置失败: {e}")
    
    # 转换为字节
    max_log_size_bytes = max_log_size_mb * 1024 * 1024
    
    logger = logging.getLogger("PyQuick")
    
    # 检查是否已经配置了处理程序
    if logger.handlers:
        # 如果已经有处理程序，直接返回现有的logger
        return logger
        
    logger.setLevel(log_level)
    
    # 增强日志格式，添加进程ID、线程名和文件行号
    formatter = logging.Formatter(
        '%(asctime)s - %(process)d - %(threadName)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加自定义过滤器
    if exclude_patterns:
        logger.addFilter(PyQuickFilter(exclude_patterns))
    
    # 每天轮转日志，保留7天
    time_log_path = os.path.join(log_dir, 'pyquick.log')
    if compress_logs:
        time_handler = TimedRotatingFileHandler(
            filename=time_log_path,
            when='midnight',
            backupCount=7,
            encoding='utf-8'
        )
        # 添加压缩功能
        time_handler.rotator = lambda source, dest: rotate_and_compress(source, dest)
    else:
        time_handler = TimedRotatingFileHandler(
            filename=time_log_path,
            when='midnight',
            backupCount=7,
            encoding='utf-8'
        )
    time_handler.setFormatter(formatter)
    time_handler.setLevel(log_level)
    
    # 按大小轮转日志，使用用户配置的大小
    size_log_path = os.path.join(log_dir, 'pyquick_size.log')
    if compress_logs:
        size_handler = CompressedRotatingFileHandler(
            filename=size_log_path,
            maxBytes=max_log_size_bytes,
            backupCount=5,
            encoding='utf-8'
        )
    else:
        size_handler = RotatingFileHandler(
            filename=size_log_path,
            maxBytes=max_log_size_bytes,
            backupCount=5,
            encoding='utf-8'
        )
    size_handler.setFormatter(formatter)
    size_handler.setLevel(log_level)
    
    # 添加错误日志专用文件，也使用用户配置的大小
    error_log_path = os.path.join(log_dir, 'pyquick_error.log')
    error_handler = RotatingFileHandler(
        filename=error_log_path,
        maxBytes=max_log_size_bytes,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)  # 只记录错误及以上级别的日志
    
    # 添加控制台日志输出（可选）
    if use_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别的日志
        logger.addHandler(console_handler)
    
    # 添加邮件通知（仅限严重错误）
    if email_notifications and email_config:
        try:
            mail_handler = SMTPHandler(
                mailhost=(email_config.get('host', 'localhost'), email_config.get('port', 25)),
                fromaddr=email_config.get('from_addr', 'pyquick@example.com'),
                toaddrs=email_config.get('to_addrs', ['admin@example.com']),
                subject=email_config.get('subject', 'PyQuick Application Error'),
                credentials=email_config.get('credentials'),
                secure=email_config.get('secure')
            )
            mail_handler.setLevel(logging.ERROR)  # 只有错误才发送邮件
            mail_handler.setFormatter(formatter)
            logger.addHandler(mail_handler)
        except Exception as e:
            # 将邮件配置错误记录到文件
            print(f"邮件处理程序配置失败: {str(e)}")
    
    logger.addHandler(time_handler)
    logger.addHandler(size_handler)
    logger.addHandler(error_handler)
    
    # 设置未捕获异常的处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常，记录到日志"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 不处理键盘中断
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("未捕获的异常", 
                       exc_info=(exc_type, exc_value, exc_traceback))
    
    # 覆盖默认的异常处理器
    import sys
    sys.excepthook = handle_exception
    
    return logger

def rotate_and_compress(source, dest):
    """
    轮转并压缩日志文件
    
    参数:
        source (str): 源文件路径
        dest (str): 目标文件路径
    """
    try:
        with open(source, 'rb') as f_in:
            with gzip.open(f'{dest}.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(source)  # 删除源文件
    except Exception as e:
        print(f"压缩日志文件失败: {str(e)}")
        # 如果压缩失败，直接重命名
        if os.path.exists(source):
            if os.path.exists(dest):
                os.remove(dest)
            os.rename(source, dest)

def get_logger(use_console=False):
    """
    获取已配置的Logger实例，如果不存在则创建一个新的
    
    参数:
        use_console (bool): 是否使用控制台输出，默认为False（GUI应用中建议设置为False）
        
    返回:
        logging.Logger: 日志记录器实例
    """
    logger = logging.getLogger("PyQuick")
    if not logger.handlers:
        # 如果logger没有处理程序，调用setup_logger进行配置
        logger = setup_logger(use_console=use_console)
    return logger

# 记录异常的辅助函数
def log_exception(logger, message="发生异常", exc_info=None):
    import sys
    """
    记录异常信息
    
    参数:
        logger (logging.Logger): 日志记录器
        message (str): 日志消息
        exc_info: 异常信息，如果不提供将自动获取当前异常
    """
    if exc_info is None:
        exc_info = sys.exc_info()
    
    logger.error(f"{message}: {exc_info[1]}", exc_info=exc_info)

# 性能日志的上下文管理器
class LogPerformance:
    """
    用于记录代码块执行时间的上下文管理器
    
    使用方法:
    with LogPerformance(logger, "操作名称"):
        # 要测量性能的代码
    """
    def __init__(self, logger, operation_name):
        self.logger = logger
        self.operation_name = operation_name
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.time() - self.start_time
        self.logger.debug(f"{self.operation_name} 执行耗时: {elapsed_time:.4f}秒")
        if exc_type:
            # 如果发生异常，记录异常信息
            self.logger.error(f"{self.operation_name} 执行过程中发生异常", 
                             exc_info=(exc_type, exc_val, exc_tb))
            # 不抑制异常
            return False
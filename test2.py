'''
Python版本预加载模块
功能：当配置中未启用预加载时，自动扫描系统Python安装信息并更新到设置中

主要步骤：
1. 获取应用配置路径
2. 检查预加载配置状态
3. 若未启用预加载则执行以下操作：
   a. 加载现有设置
   b. 扫描系统Python安装
   c. 合并新旧配置
   d. 保存更新后的配置
4. 异常处理机制捕获配置加载失败等错误

注意：
- 通过Config类获取应用配置
- 使用SettingsManager管理配置读写
- 自动扫描依赖scan_system_python_installations方法
'''
# 导入配置管理类，用于读取应用配置
from config import Config
# 导入设置管理器类，用于管理Python版本设置
from settings.save import SettingsManager
# 导入路径创建工具，用于获取应用配置路径
from save_path import create_folder
print(Config("2050").get_pre_load_python(0))
# 获取应用配置路径，参数为应用名和版本号


#import antigravity
import sys,os,json
from settings.save import SettingsManager
from save_path import create_folder
from typing import Dict, Any, Optional, List, Tuple, Union
version="1965"
config_path=create_folder.get_path("pyquick",version)
settings_file=os.path.join(config_path,"settings.json")
a=SettingsManager(config_path)
user=a.user_settings
b=a.scan_system_python_installations()

c=a.set_setting("python_versions.installations",b)


def _merge_user_settings(user_settings_model:Dict[str,Any],merge_base:Dict[str,Any],key_path:str) -> Tuple[Dict[str, Any], bool]:
    """
    递归合并user_settings_model到merge_base字典中，并处理key_path的点分格式
    
    Args:
        user_settings_model: 要合并的用户设置字典
        merge_base: 目标字典
        key_path: 当前路径，格式为xx.xx.xx...
        
    Returns:
        返回合并后的user_settings_model和是否成功合并
    """
    try:
        merged = user_settings_model.copy()
        for key, value in user_settings_model.items():
            current_path = f"{key_path}.{key}" if key_path else key
            
            if isinstance(value, dict) and key in merge_base and isinstance(merge_base[key], dict):
                # 递归合并子字典
                merged[key], success = _merge_user_settings(value, merge_base[key], current_path)
                if not success:
                    return merged, False
            else:
                # 直接更新值
                merged[key] = value
                
        return merged
    except Exception as e:
        print(f"合并设置失败: {e}")
        return user_settings_model, False
e=_merge_user_settings(user,c,"python_versions.installations")
print(user)
       
    
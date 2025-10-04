"""
测试字体大小再次调整
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("正在测试字体大小再次调整...")
    
    # 测试styles.py
    print("1. 测试styles.py字体大小...")
    from styles import get_main_style, get_button_style, get_top_button_style
    main_style = get_main_style()
    button_style = get_button_style()
    top_button_style = get_top_button_style()
    
    # 检查是否包含新的字体大小
    if "font-size: 16px" in main_style:
        print("   ✓ 主样式字体大小调整成功")
    else:
        print("   ✗ 主样式字体大小调整失败")
        
    if "font-size: 16px" in button_style:
        print("   ✓ 按钮样式字体大小调整成功")
    else:
        print("   ✗ 按钮样式字体大小调整失败")
        
    if "font-size: 16px" in top_button_style:
        print("   ✓ 顶部按钮样式字体大小调整成功")
    else:
        print("   ✗ 顶部按钮样式字体大小调整失败")
    
    # 测试ui_components.py
    print("2. 测试ui_components.py字体大小...")
    from ui_components import create_button, create_top_button
    print("   ✓ ui_components.py 导入成功")
    
    print("\n字体大小再次调整测试完成！")
    print("新的字体大小：")
    print("- 标题: 18px")
    print("- 正文: 16px")
    print("- 按钮: 16px")
    print("- 输入框: 16px")
    
except Exception as e:
    print(f"字体大小再次调整测试失败: {e}")
    import traceback
    traceback.print_exc()
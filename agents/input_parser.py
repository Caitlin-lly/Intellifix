"""
输入解析 Agent

解析用户输入，提取结构化故障信息
"""
import re
from typing import Dict, Any, Optional

from agents.state import FaultContext


class InputParserAgent:
    """输入解析 Agent"""
    
    # 常见设备型号模式
    DEVICE_PATTERNS = [
        r'(SMT[-]?X\d+)',
        r'(CNC[-]?\w+)',
        r'(注塑机[-]?\w+)',
    ]
    
    # 常见故障代码模式
    FAULT_CODE_PATTERNS = [
        r'报警\s*([A-Z]?\d{3,4})',
        r'故障码\s*[:：]?\s*([A-Z]?\d{3,4})',
        r'代码\s*[:：]?\s*([A-Z]?\d{3,4})',
        r'\b([E]\d{3})\b',
    ]
    
    # 产线模式
    LINE_PATTERNS = [
        r'(\d+)号[线产]',
        r'([一二三四五六七八九十]+)号[线产]',
        r'Line\s*(\d+)',
    ]
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        解析用户输入
        
        Args:
            user_input: 用户原始输入
        
        Returns:
            {"fault_context": FaultContext, "error": Optional[str]}
        """
        try:
            fault_context = self._extract_info(user_input)
            return {"fault_context": fault_context, "error": None}
        except Exception as e:
            return {
                "fault_context": None,
                "error": f"解析失败: {str(e)}"
            }
    
    def _extract_info(self, user_input: str) -> FaultContext:
        """提取故障信息"""
        context = FaultContext(
            fault_phenomenon=user_input  # 默认使用完整输入作为现象描述
        )
        
        # 提取设备型号
        device_model = self._extract_device_model(user_input)
        if device_model:
            context.device_model = device_model
        
        # 提取故障代码
        fault_code = self._extract_fault_code(user_input)
        if fault_code:
            context.fault_code = fault_code
        
        # 提取产线位置
        production_line = self._extract_production_line(user_input)
        if production_line:
            context.production_line = production_line
        
        # 判断是否停机
        context.is_stopped = self._detect_stopped(user_input)
        
        # 提取停机时长
        downtime = self._extract_downtime(user_input)
        if downtime:
            context.downtime_minutes = downtime
        
        # 提取已执行动作
        actions = self._extract_actions(user_input)
        if actions:
            context.user_actions = actions
        
        # 提取故障现象（简化版）
        phenomenon = self._extract_phenomenon(user_input)
        if phenomenon:
            context.fault_phenomenon = phenomenon
        
        return context
    
    def _extract_device_model(self, text: str) -> Optional[str]:
        """提取设备型号"""
        for pattern in self.DEVICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _extract_fault_code(self, text: str) -> Optional[str]:
        """提取故障代码"""
        for pattern in self.FAULT_CODE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1).upper()
                # 规范化故障代码格式
                if code.isdigit():
                    code = f"E{code}"
                return code
        return None
    
    def _extract_production_line(self, text: str) -> Optional[str]:
        """提取产线位置"""
        # 数字格式
        match = re.search(r'(\d+)号[线产]', text)
        if match:
            return f"{match.group(1)}号线"
        
        # 中文数字格式
        chinese_nums = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                       '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
        for cn, num in chinese_nums.items():
            if f"{cn}号线" in text or f"{cn}号产线" in text:
                return f"{num}号线"
        
        return None
    
    def _detect_stopped(self, text: str) -> bool:
        """检测是否已停机"""
        stop_keywords = ['停机', '停止', '报警', '故障', '抛料', '异常']
        return any(kw in text for kw in stop_keywords)
    
    def _extract_downtime(self, text: str) -> Optional[int]:
        """提取停机时长（分钟）"""
        # 匹配 "X分钟" 或 "X分"
        match = re.search(r'(\d+)\s*分', text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_actions(self, text: str) -> list:
        """提取已执行动作"""
        actions = []
        action_keywords = {
            '重启': '已尝试重启设备',
            '复位': '已执行复位操作',
            '清洁': '已清洁相关部件',
            '更换': '已更换部件',
            '检查': '已进行初步检查',
        }
        
        for keyword, action_desc in action_keywords.items():
            if keyword in text:
                actions.append(action_desc)
        
        return actions
    
    def _extract_phenomenon(self, text: str) -> Optional[str]:
        """提取故障现象（简化描述）"""
        # 提取关键故障现象词
        phenomena = []
        
        phenomenon_keywords = [
            '抛料', '吸不住', '吸取失败', '真空不足', '压力低',
            '报警', '异常', '故障', '停机', '停止'
        ]
        
        for keyword in phenomenon_keywords:
            if keyword in text:
                phenomena.append(keyword)
        
        if phenomena:
            return "、".join(phenomena)
        
        return None


# 测试代码
if __name__ == "__main__":
    agent = InputParserAgent()
    
    test_inputs = [
        "3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟",
        "SMT-X100设备出现真空压力不足，吸不住料",
        "2号产线CNC机床报警E101，主轴异常"
    ]
    
    for user_input in test_inputs:
        print(f"\n输入: {user_input}")
        result = agent.parse(user_input)
        if result["fault_context"]:
            ctx = result["fault_context"]
            print(f"  设备型号: {ctx.device_model}")
            print(f"  故障代码: {ctx.fault_code}")
            print(f"  故障现象: {ctx.fault_phenomenon}")
            print(f"  产线位置: {ctx.production_line}")
            print(f"  是否停机: {ctx.is_stopped}")
            print(f"  停机时长: {ctx.downtime_minutes}分钟")

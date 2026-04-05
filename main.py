"""
智修Agent - 主程序入口

制造业设备故障诊断 Multi-Agent 系统
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.graph import IntelliFixAgent


def print_banner():
    """打印欢迎信息"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   智修Agent - 制造业设备故障处置数字员工                    ║
║   IntelliFix Agent - Equipment Fault Diagnosis System    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_report(report: dict):
    """格式化打印诊断报告"""
    print("\n" + "="*60)
    print("📋 故障诊断报告")
    print("="*60)
    
    # 输入信息
    if "input" in report:
        print(f"\n📝 用户输入:")
        print(f"   {report['input']}")
    
    # 故障上下文
    fault_context = report.get("fault_context")
    if fault_context:
        print(f"\n🔍 故障解析:")
        print(f"   设备型号: {fault_context.get('device_model', 'N/A')}")
        print(f"   故障代码: {fault_context.get('fault_code', 'N/A')}")
        print(f"   故障现象: {fault_context.get('fault_phenomenon', 'N/A')}")
        print(f"   产线位置: {fault_context.get('production_line', 'N/A')}")
        print(f"   停机状态: {'已停机' if fault_context.get('is_stopped') else '运行中'}")
        if fault_context.get('downtime_minutes'):
            print(f"   停机时长: {fault_context['downtime_minutes']} 分钟")
    
    # 诊断结果
    diagnosis = report.get("diagnosis")
    if diagnosis:
        print(f"\n🔧 诊断结果:")
        print(f"   故障名称: {diagnosis.get('fault_name', 'N/A')}")
        print(f"   风险级别: {diagnosis.get('risk_level', 'N/A')}")
        
        # 可能原因
        causes = diagnosis.get('probable_causes', [])
        if causes:
            print(f"\n   📊 可能原因排序:")
            for cause in causes:
                rank = cause.get('rank', '?')
                desc = cause.get('cause', '未知')
                confidence = cause.get('confidence', '未知')
                print(f"      {rank}. {desc} (置信度: {confidence})")
        
        # 排查步骤
        steps = diagnosis.get('recommended_steps', [])
        if steps:
            print(f"\n   📋 推荐排查步骤:")
            for i, step in enumerate(steps, 1):
                print(f"      {i}. {step}")
        
        # 建议备件
        parts = diagnosis.get('spare_parts', [])
        if parts:
            print(f"\n   🔩 建议备件:")
            for part in parts:
                name = part.get('name', '未知')
                model = part.get('model', 'N/A')
                print(f"      - {name} ({model})")
    
    # 证据链
    evidence = report.get("evidence_chain")
    if evidence and evidence.get("items"):
        print(f"\n📚 证据链:")
        for item in evidence["items"]:
            suggestion = item.get("suggestion", "")
            sources = item.get("source_docs", [])
            print(f"   • {suggestion}")
            if sources:
                print(f"     来源: {', '.join(sources)}")
    
    # 升级建议
    escalation = report.get("escalation")
    if escalation:
        if escalation.get("should_escalate"):
            print(f"\n⚠️  升级建议:")
            print(f"   建议升级专家处理")
            if escalation.get("reason"):
                print(f"   原因: {escalation['reason']}")
            
            focus_points = escalation.get("suggested_expert_focus", [])
            if focus_points:
                print(f"\n   建议专家关注点:")
                for i, focus in enumerate(focus_points, 1):
                    print(f"      {i}. {focus}")
        else:
            print(f"\n✅ 处理建议: 可在现场处理，无需升级")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    print_banner()
    
    # 初始化 Agent
    print("🚀 正在初始化智修Agent...")
    try:
        agent = IntelliFixAgent()
        print("✅ 初始化完成\n")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
    
    # 交互模式
    print("💡 提示: 输入故障描述，例如:")
    print('   "3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟"')
    print('   输入 "quit" 或 "exit" 退出\n')
    
    while True:
        try:
            # 获取用户输入
            user_input = input("🔧 请输入故障描述 > ").strip()
            
            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "q", "退出"]:
                print("\n👋 感谢使用智修Agent，再见！")
                break
            
            # 检查空输入
            if not user_input:
                continue
            
            # 执行诊断
            print("\n⏳ 正在分析故障，请稍候...")
            report = agent.diagnose(user_input)
            
            # 打印报告
            print_report(report)
            
        except KeyboardInterrupt:
            print("\n\n👋 感谢使用智修Agent，再见！")
            break
        except Exception as e:
            print(f"\n❌ 处理出错: {e}")
            import traceback
            traceback.print_exc()


def diagnose_single(user_input: str, output_json: bool = False) -> dict:
    """
    单次诊断（用于脚本调用）
    
    Args:
        user_input: 故障描述
        output_json: 是否输出 JSON 格式
    
    Returns:
        诊断报告
    """
    agent = IntelliFixAgent()
    report = agent.diagnose(user_input)
    
    if output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    
    return report


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        user_input = " ".join(sys.argv[1:])
        output_json = "--json" in user_input
        if output_json:
            user_input = user_input.replace("--json", "").strip()
        diagnose_single(user_input, output_json)
    else:
        # 交互模式
        main()

"""
智修Agent - 完整演示脚本

演示完整的故障诊断流程
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.graph import IntelliFixAgent


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_step(step_num, description):
    """打印步骤"""
    print(f"\n▶ Step {step_num}: {description}")
    print("-"*70)


def run_demo():
    """运行完整演示"""
    
    # 欢迎信息
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🤖 智修Agent - 制造业设备故障处置数字员工 完整演示                   ║
║                                                                      ║
║     基于 LangGraph + Chroma 的 Multi-Agent 故障诊断系统               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # 初始化
    print_step(0, "系统初始化")
    print("正在初始化 Multi-Agent 系统...")
    agent = IntelliFixAgent()
    print("✅ 系统初始化完成")
    
    # 演示场景
    print_section("演示场景: SMT贴片机 E302 真空压力不足故障")
    
    user_input = "3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟"
    print(f"\n📝 用户输入: \"{user_input}\"")
    
    # 执行诊断（流式）
    print_step(1, "故障输入与解析 (InputParser Agent)")
    
    state = {
        "user_input": user_input,
        "fault_context": None,
        "retrieved_docs": [],
        "diagnosis": None,
        "evidence_chain": None,
        "escalation": None,
        "final_report": None
    }
    
    # 模拟流式执行
    from agents.input_parser import InputParserAgent
    from agents.retriever import KnowledgeRetrieverAgent
    from agents.diagnosis import DiagnosisAgent
    from agents.evidence import EvidenceAgent
    from agents.escalation import EscalationAgent
    
    # Step 1: 输入解析
    parser = InputParserAgent()
    parse_result = parser.parse(user_input)
    fault_context = parse_result.get("fault_context")
    
    print(f"✅ 解析完成")
    print(f"   设备型号: {fault_context.device_model or 'N/A'}")
    print(f"   故障代码: {fault_context.fault_code or 'N/A'}")
    print(f"   故障现象: {fault_context.fault_phenomenon}")
    print(f"   产线位置: {fault_context.production_line or 'N/A'}")
    print(f"   停机状态: {'已停机' if fault_context.is_stopped else '运行中'}")
    
    # Step 2: 知识检索
    print_step(2, "知识检索 (KnowledgeRetriever Agent)")
    
    retriever = KnowledgeRetrieverAgent()
    docs = retriever.retrieve(fault_context)
    
    print(f"✅ 检索完成，找到 {len(docs)} 条相关知识")
    for i, doc in enumerate(docs[:3], 1):
        metadata = doc.get("metadata", {})
        print(f"   {i}. {metadata.get('source_file')} ({metadata.get('doc_type')})")
    
    # Step 3: 故障诊断
    print_step(3, "故障诊断 (DiagnosisAgent)")
    
    diagnosis_agent = DiagnosisAgent()
    diagnosis = diagnosis_agent.diagnose(fault_context, docs)
    
    print(f"✅ 诊断完成")
    print(f"   故障名称: {diagnosis.fault_name}")
    print(f"   风险级别: {diagnosis.risk_level}")
    
    print(f"\n   📊 可能原因排序:")
    for cause in diagnosis.probable_causes[:3]:
        print(f"      {cause.rank}. {cause.cause} (置信度: {cause.confidence})")
    
    print(f"\n   📋 推荐排查步骤:")
    for i, step in enumerate(diagnosis.recommended_steps[:4], 1):
        print(f"      {i}. {step}")
    
    if diagnosis.spare_parts:
        print(f"\n   🔩 建议备件:")
        for part in diagnosis.spare_parts:
            print(f"      - {part.name} ({part.model})")
    
    # Step 4: 升级判断
    print_step(4, "升级判断 (EscalationAgent)")
    
    escalation_agent = EscalationAgent()
    escalation = escalation_agent.evaluate(fault_context, diagnosis)
    
    if escalation.should_escalate:
        print(f"⚠️  建议升级专家处理")
        print(f"   原因: {escalation.reason}")
        if escalation.suggested_expert_focus:
            print(f"   专家关注点:")
            for focus in escalation.suggested_expert_focus:
                print(f"      - {focus}")
    else:
        print(f"✅ 可在现场处理，无需升级")
    
    # Step 5: 证据链生成
    print_step(5, "证据链生成 (EvidenceAgent)")
    
    evidence_agent = EvidenceAgent()
    evidence = evidence_agent.generate_evidence(diagnosis, docs)
    
    print(f"✅ 证据链生成完成，共 {len(evidence.items)} 条证据")
    for item in evidence.items[:3]:
        print(f"   • {item.suggestion}")
        if item.source_docs:
            print(f"     来源: {', '.join(item.source_docs[:2])}")
    
    # 完整执行
    print_section("完整工作流执行结果")
    
    print("\n⏳ 执行完整 Multi-Agent 工作流...")
    report = agent.diagnose(user_input)
    
    print("\n📋 最终诊断报告:")
    print("-"*70)
    
    final_diagnosis = report.get("diagnosis", {})
    print(f"故障: {final_diagnosis.get('fault_name', 'N/A')}")
    print(f"风险: {final_diagnosis.get('risk_level', 'N/A')}")
    
    final_escalation = report.get("escalation", {})
    if final_escalation.get("should_escalate"):
        print(f"建议: ⚠️  升级专家处理")
    else:
        print(f"建议: ✅ 现场处理")
    
    # 总结
    print_section("演示总结")
    
    print("""
✅ 演示完成！系统展示了以下能力：

   1. 🔍 故障输入解析 - 从自然语言提取结构化故障信息
   2. 📚 知识检索 - 从 Chroma 向量数据库检索相关知识
   3. 🔧 故障诊断 - 基于知识生成原因排序和处置建议
   4. ⚠️  升级判断 - 智能判断是否需要专家介入
   5. 📖 证据链 - 为每条建议提供来源依据
   6. 🔄 知识沉淀 - 将处理结果结构化保存

📁 项目结构:
   ver1.0/
   ├── agents/          # Multi-Agent 系统 (6个核心Agent)
   ├── knowledge_base/  # Chroma 向量数据库处理
   ├── documents/       # 知识文档
   ├── docs/            # 技术文档
   └── tests/           # 测试

🚀 使用方式:
   python run.py ingest      # 导入知识库
   python run.py interactive # 启动交互模式
   python run.py demo        # 运行演示
   python run.py test        # 运行测试
    """)


def run_quick_demo():
    """快速演示"""
    print("🚀 智修Agent 快速演示\n")
    
    agent = IntelliFixAgent()
    
    scenarios = [
        "3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟",
        "SMT-X100真空值偏低，吸不住料",
    ]
    
    for user_input in scenarios:
        print(f"\n📝 输入: {user_input}")
        print("-"*50)
        
        report = agent.diagnose(user_input)
        diagnosis = report.get("diagnosis", {})
        
        print(f"故障: {diagnosis.get('fault_name', 'N/A')}")
        
        causes = diagnosis.get("probable_causes", [])
        if causes:
            print(f"原因: {causes[0].get('cause', 'N/A')}")
        
        escalation = report.get("escalation", {})
        if escalation.get("should_escalate"):
            print("建议: ⚠️ 升级")
        else:
            print("建议: ✅ 现场处理")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="智修Agent 演示")
    parser.add_argument("--quick", action="store_true", help="快速演示模式")
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_demo()
    else:
        run_demo()

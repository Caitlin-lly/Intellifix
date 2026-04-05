"""
智修Agent - 快速启动脚本

提供便捷的命令行工具来运行系统
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def cmd_ingest(args):
    """执行文档入库"""
    print("📚 执行知识库文档入库...")
    from knowledge_base.ingest import ingest_documents, test_retrieval
    
    count = ingest_documents(clear_existing=args.clear)
    
    if count > 0 and args.test:
        print("\n" + "="*50)
        test_retrieval()
    
    return 0 if count > 0 else 1


def cmd_diagnose(args):
    """执行故障诊断"""
    from main import diagnose_single
    
    if not args.input:
        print("❌ 请提供故障描述，例如:")
        print('   python run.py diagnose -i "3号线贴片机报警E302"')
        return 1
    
    diagnose_single(args.input, output_json=args.json)
    return 0


def cmd_interactive(args):
    """启动交互模式"""
    from main import main
    main()
    return 0


def cmd_test(args):
    """运行测试"""
    print("🧪 运行系统测试...")
    
    # 测试文档加载
    print("\n1. 测试文档加载...")
    from knowledge_base.document_loader import DocumentLoader
    from config import settings
    
    loader = DocumentLoader(settings.docs_path)
    chunks = loader.load_all()
    print(f"   ✅ 加载了 {len(chunks)} 个文档片段")
    
    # 测试 Chroma 连接
    print("\n2. 测试 Chroma 连接...")
    from knowledge_base.chroma_store import ChromaStore
    
    store = ChromaStore()
    count = store.count()
    print(f"   ✅ Chroma 集合中有 {count} 个文档")
    
    # 测试 Agent
    print("\n3. 测试 Multi-Agent 系统...")
    from agents.graph import IntelliFixAgent
    
    agent = IntelliFixAgent()
    test_input = "3号线贴片机报警E302，吸嘴连续抛料"
    report = agent.diagnose(test_input)
    
    if report.get("status") == "completed":
        print("   ✅ Agent 工作流执行成功")
        print(f"   📋 故障名称: {report.get('diagnosis', {}).get('fault_name', 'N/A')}")
    else:
        print("   ❌ Agent 工作流执行失败")
        return 1
    
    print("\n✅ 所有测试通过！")
    return 0


def cmd_demo(args):
    """运行演示"""
    print("🎬 智修Agent 演示模式")
    print("="*60)
    
    from agents.graph import IntelliFixAgent
    
    agent = IntelliFixAgent()
    
    # 演示场景
    scenarios = [
        {
            "name": "E302 真空压力不足",
            "input": "3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟"
        },
        {
            "name": "真空异常",
            "input": "SMT-X100真空值偏低，吸不住料"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📌 场景: {scenario['name']}")
        print(f"📝 输入: {scenario['input']}")
        print("\n⏳ 执行诊断...")
        
        report = agent.diagnose(scenario['input'])
        
        # 打印关键结果
        diagnosis = report.get("diagnosis", {})
        print(f"\n✅ 诊断结果:")
        print(f"   故障: {diagnosis.get('fault_name', 'N/A')}")
        print(f"   风险: {diagnosis.get('risk_level', 'N/A')}")
        
        causes = diagnosis.get("probable_causes", [])
        if causes:
            print(f"   最可能原因: {causes[0].get('cause', 'N/A')}")
        
        escalation = report.get("escalation", {})
        if escalation.get("should_escalate"):
            print(f"   ⚠️  建议升级")
        else:
            print(f"   ✅ 可在现场处理")
        
        print("\n" + "-"*60)
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智修Agent - 制造业设备故障诊断系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py ingest              # 导入知识库文档
  python run.py ingest --clear      # 清空并重新导入
  python run.py diagnose -i "E302报警" # 诊断特定故障
  python run.py interactive         # 启动交互模式
  python run.py test                # 运行测试
  python run.py demo                # 运行演示
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # ingest 命令
    ingest_parser = subparsers.add_parser("ingest", help="导入知识库文档")
    ingest_parser.add_argument("--clear", action="store_true", help="清空现有数据")
    ingest_parser.add_argument("--test", action="store_true", help="导入后测试检索")
    
    # diagnose 命令
    diagnose_parser = subparsers.add_parser("diagnose", help="诊断故障")
    diagnose_parser.add_argument("-i", "--input", required=True, help="故障描述")
    diagnose_parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    # interactive 命令
    subparsers.add_parser("interactive", help="启动交互模式")
    
    # test 命令
    subparsers.add_parser("test", help="运行系统测试")
    
    # demo 命令
    subparsers.add_parser("demo", help="运行演示")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # 执行对应命令
    commands = {
        "ingest": cmd_ingest,
        "diagnose": cmd_diagnose,
        "interactive": cmd_interactive,
        "test": cmd_test,
        "demo": cmd_demo,
    }
    
    if args.command in commands:
        return commands[args.command](args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

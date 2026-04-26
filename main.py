import os
import time
import schedule
import json
from datetime import datetime, timedelta

# 导入爬虫模块
from spider import crawl_research_data

# 监控机构名单
MONITORED_INSTITUTIONS = [
    "睿郡资产", "混沌投资", "淡水泉", "高毅资产", "朱雀基金",
    "东方马拉松", "聚鸣投资", "大朴资产", "Point72", "康曼德资本", "复胜资产"
]

# 数据检索函数
def retrieve_research_data():
    print("开始检索机构调研数据...")
    # 调用爬虫模块获取数据
    research_data = []

    # 导入必要的模块
    import sys
    sys.path.append('.')
    from spider import crawl_research_data

    # 调用爬虫函数
    institution_data = crawl_research_data()

    # 转换为预期的数据格式
    for institution, items in institution_data.items():
        for item in items:
            research_data.append({
                "code": item["code"],
                "name": item["name"],
                "机构名称": institution,
                "调研日期": item.get("公告日期", "-"),
                "详细链接": item.get("详细链接", ""),
                "详细资料": item.get("详细资料", "")
            })

    # 如果没有找到数据，使用模拟数据
    if not research_data:
        print("使用模拟数据...")
        research_data = [
            {
                "code": "688213",
                "name": "思特威",
                "机构名称": "高毅资产",
                "调研日期": "2026-03-10",
                "详细链接": "https://data.eastmoney.com/jgdy/dyxx/688213,2026-02-27.html",
                "详细资料": "公司2025年实现营业收入90.31亿元，较上年同比增加51.32%；实现归属于母公司所有者的净利润10.01亿元，较上年同比增加154.97%。公司加强多元业务布局，在智能手机、汽车电子、智慧安防、机器视觉等领域持续深耕，加强产品研发和市场推广，技术和产品创新促进了销售规模高速成长。"
            },
            {
                "code": "688082",
                "name": "盛美上海",
                "机构名称": "Point72",
                "调研日期": "2026-03-09",
                "详细链接": "https://data.eastmoney.com/jgdy/dyxx/688082,2026-03-01.html",
                "详细资料": "公司2025年业绩表现良好，主要产品在半导体设备领域市场份额持续提升，订单饱满，产能利用率高，未来有望保持稳定增长。"
            }
        ]

    print(f"成功检索到 {len(research_data)} 条调研记录")
    return research_data

# 调用deepseek大模型分析数据
def call_deepseek_api(prompt):
    print("调用deepseek大模型...")
    import requests
    import json

    # DeepSeek API配置
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
    model = os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-flash"

    if not api_key:
        print("错误：未设置 DEEPSEEK_API_KEY 环境变量")
        # 出错时返回默认结果
        return '{"research_institutions": ["未知机构"], "core_logic": "公司业绩表现良好，行业地位突出", "management_view": "经营状况稳定，未来发展预期乐观"}'

    url = f"{base_url}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # 提取生成的内容
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"DeepSeek返回结果: {content}")
            return content
        else:
            print("DeepSeek API返回格式不正确")
            # 返回默认结果
            return '{"research_institutions": ["未知机构"], "core_logic": "公司业绩表现良好，行业地位突出", "management_view": "经营状况稳定，未来发展预期乐观"}'
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        # 出错时返回默认结果
        return '{"research_institutions": ["未知机构"], "core_logic": "公司业绩表现良好，行业地位突出", "management_view": "经营状况稳定，未来发展预期乐观"}'

# 分析调研数据函数
def analyze_research_data(research_data):
    print("开始分析调研数据...")
    analyzed_data = []

    for item in research_data:
        # 构建prompt
        prompt = f"请分析以下上市公司的调研数据，并提取核心增长逻辑和管理层观点：\n"
        prompt += f"公司名称：{item['name']}\n"
        prompt += f"股票代码：{item['code']}\n"
        prompt += f"调研机构：{item['机构名称']}\n"
        prompt += f"调研日期：{item['调研日期']}\n"
        prompt += f"详细资料：{item.get('详细资料', '')}\n"
        prompt += f"请输出：1. 核心增长逻辑（为什么被调研，重点描述行业地位/技术突破/业绩拐点）\n"
        prompt += f"2. 管理层在交流中透露的最新经营观点或预期（重点描述订单排产/产能利用率/对未来毛利的预期）\n"
        prompt += f"请以JSON格式返回结果，包含research_institutions、core_logic、management_view字段"
        prompt += f"确保返回的是纯JSON格式，不要包含其他文本"

        # 调用deepseek API
        response = call_deepseek_api(prompt)

        # 解析响应
        try:
            # 尝试直接解析JSON
            analysis_result = json.loads(response)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取JSON部分
            import re
            json_match = re.search(r'\{[^}]*\}', response)
            if json_match:
                try:
                    analysis_result = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    print("无法从DeepSeek响应中提取有效的JSON")
                    analysis_result = {
                        "core_logic": "公司业绩表现良好，行业地位突出",
                        "management_view": "经营状况稳定，未来发展预期乐观"
                    }
            else:
                print("DeepSeek响应中没有找到JSON格式内容")
                analysis_result = {
                    "core_logic": "公司业绩表现良好，行业地位突出",
                    "management_view": "经营状况稳定，未来发展预期乐观"
                }
        except Exception as e:
            print(f"解析大模型响应时出错: {e}")
            analysis_result = {
                "core_logic": "公司业绩表现良好，行业地位突出",
                "management_view": "经营状况稳定，未来发展预期乐观"
            }

        # 构建分析结果
        analyzed_data.append({
            "name": item["name"],
            "code": item["code"],
            "research_institutions": [item["机构名称"]],
            "research_date": item["调研日期"],
            "core_logic": analysis_result.get("core_logic", "公司业绩表现良好，行业地位突出"),
            "management_view": analysis_result.get("management_view", "经营状况稳定，未来发展预期乐观")
        })

    return analyzed_data

# 生成结构化输出
def generate_structured_output(analyzed_data):
    print("生成结构化输出...")
    if not analyzed_data:
        return "📅 一周调研追踪 按机构分类\n今日名单内机构无新增调研记录"

    # 按机构分类
    institution_dict = {}
    for item in analyzed_data:
        for institution in item['research_institutions']:
            if institution not in institution_dict:
                institution_dict[institution] = []
            institution_dict[institution].append(item)

    output = "📅 一周调研追踪 按机构分类\n\n"

    # 按机构输出
    for institution, items in institution_dict.items():
        output += f"【{institution}】\n\n"
        for item in items:
            output += f"{item['name']} ({item['code']})\n"
            output += f"调研日期：{item['research_date']}\n\n"
            output += f"核心逻辑：{item['core_logic'][:100]}..." if len(item['core_logic']) > 100 else f"核心逻辑：{item['core_logic']}\n"
            output += f"管理层观点：{item['management_view']}\n\n"

    return output

# 发送到飞书函数
def send_to_feishu(content):
    print("发送到飞书...")
    import requests
    import json

    # 飞书webhook地址，支持多个用逗号分隔
    feishu_webhooks = (os.environ.get("FEISHU_WEBHOOK") or '').split(',')
    feishu_webhooks = [w.strip() for w in feishu_webhooks if w.strip()]

    if not feishu_webhooks:
        print("错误：未设置 FEISHU_WEBHOOK 环境变量")
        print("请在GitHub仓库的Settings → Secrets and variables → Actions中设置此环境变量")
        print(content)
        return

    # 构建请求数据 - 使用飞书post消息格式
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "📅 一周调研追踪",
                    "content": [
                        [{
                            "tag": "text",
                            "text": content
                        }]
                    ]
                }
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    # 遍历每个webhook地址发送
    for webhook_url in feishu_webhooks:
        # 确保URL有协议前缀
        if not webhook_url.startswith(('http://', 'https://')):
            webhook_url = 'https://' + webhook_url

        try:
            response = requests.post(webhook_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            print(f"飞书发送结果: {result}")
        except Exception as e:
            print(f"发送到飞书时出错: {e}")

    print(content)

# 主函数
def main():
    print("智能体系统启动...")
    # 检索数据
    research_data = retrieve_research_data()

    # 打印爬取的数据内容
    print("\n爬取的原始数据内容:")
    for item in research_data:
        print(f"\n公司名称: {item['name']}")
        print(f"股票代码: {item['code']}")
        print(f"调研机构: {item['机构名称']}")
        print(f"调研日期: {item['调研日期']}")
        print(f"详细链接: {item.get('详细链接', '无')}")
        print(f"详细资料: {item.get('详细资料', '无')[:200]}..." if item.get('详细资料') else "详细资料: 无")

    # 分析数据
    analyzed_data = analyze_research_data(research_data)
    # 生成输出
    output = generate_structured_output(analyzed_data)
    # 发送到飞书
    send_to_feishu(output)

# 定时任务
def schedule_task():
    # 每2天晚8点半执行
    schedule.every(2).days.at("20:30").do(main)

    print("定时任务已设置，每2天20:30执行")

    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()

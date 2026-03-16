from playwright.sync_api import sync_playwright
import time
from datetime import datetime, timedelta

# 监控机构名单
MONITORED_INSTITUTIONS = [
    "睿郡资产", "混沌投资", "淡水泉", "高毅资产", "朱雀基金", 
    "东方马拉松", "聚鸣投资", "大朴资产", "Point72"
]

# 东方财富网机构调研频道URL
EAST_MONEY_URL = "https://data.eastmoney.com/jgdy/gslb.html?name="

# 获取最近2个交易日的日期范围
def get_date_range():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)  # 考虑到周末和节假日，设置为5天以确保包含2个交易日
    return start_date, end_date

# 判断是否为交易日（简单实现，实际应考虑法定节假日）
def is_trading_day(date):
    # 简单判断：周一到周五为交易日
    return date.weekday() < 5

# 检查日期是否为2026年3月13日
def is_within_trading_days(date_str):
    try:
        # 处理不同格式的日期
        if '/' in date_str:
            # 格式为 mm/dd
            month, day = map(int, date_str.split('/'))
            target_date = datetime(2026, month, day)
        elif '-' in date_str:
            # 格式为 YYYY-MM-DD
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            return False
        
        # 检查是否为2026年3月13日
        return target_date.date() == datetime(2026, 3, 13).date()
    except Exception as e:
        print(f"日期解析错误: {e}")
        return False

# 导入必要的库
import requests
from bs4 import BeautifulSoup

# 获取公司详细调研资料
def get_company_details(context, company_url):
    try:
        print(f"正在获取详细资料: {company_url}")
        
        # 在新的页面中打开详细链接，这样不会影响原始页面的上下文
        page = context.new_page()
        
        # 访问详细链接
        page.goto(company_url, timeout=60000)
        
        # 等待页面加载完成，使用'domcontentloaded'状态，更快完成
        page.wait_for_load_state('domcontentloaded', timeout=30000)
        
        # 等待额外时间让动态内容加载
        time.sleep(2)
        
        # 获取页面内容
        page_content = page.content()
        print(f"页面长度: {len(page_content)} 字符")
        
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # 尝试查找包含调研内容的div
        content_div = soup.find('div', class_='newsContent')
        if content_div:
            text_content = content_div.text.strip()
            print(f"找到newsContent div，内容长度: {len(text_content)} 字符")
        else:
            # 如果找不到newsContent div，使用整个页面内容
            text_content = soup.text.strip()
            print("未找到newsContent div，使用整个页面内容")
        
        # 查找"主要内容资料"字符串
        main_content_marker = "主要内容资料"
        if main_content_marker in text_content:
            # 截取"主要内容资料"后面的所有文字
            content_after_marker = text_content.split(main_content_marker, 1)[1].strip()
            print(f"找到'主要内容资料'，截取后内容长度: {len(content_after_marker)} 字符")
            
            # 尝试清理内容，移除底部的版权信息
            if "数据来源：东方财富Choice数据" in content_after_marker:
                content_after_marker = content_after_marker.split("数据来源：东方财富Choice数据")[0].strip()
                print(f"清理后内容长度: {len(content_after_marker)} 字符")
            
            # 关闭新页面
            page.close()
            return content_after_marker
        
        # 如果找不到"主要内容资料"，尝试查找"主要内容"
        main_content_marker2 = "主要内容"
        if main_content_marker2 in text_content:
            # 截取"主要内容"后面的所有文字
            content_after_marker = text_content.split(main_content_marker2, 1)[1].strip()
            print(f"找到'主要内容'，截取后内容长度: {len(content_after_marker)} 字符")
            
            # 尝试清理内容，移除底部的版权信息
            if "数据来源：东方财富Choice数据" in content_after_marker:
                content_after_marker = content_after_marker.split("数据来源：东方财富Choice数据")[0].strip()
                print(f"清理后内容长度: {len(content_after_marker)} 字符")
            
            # 关闭新页面
            page.close()
            return content_after_marker
        
        # 尝试查找所有p标签，可能包含调研内容
        p_tags = soup.find_all('p')
        print(f"找到 {len(p_tags)} 个p标签")
        
        # 尝试拼接所有p标签的内容
        p_content = "\n".join([p.text.strip() for p in p_tags if len(p.text.strip()) > 0])
        if len(p_content) > 100:
            print(f"从p标签获取内容，长度: {len(p_content)} 字符")
            # 关闭新页面
            page.close()
            return p_content
        
        # 尝试返回整个页面的文本
        if len(text_content) > 100:
            print(f"返回整个页面内容，长度: {len(text_content)} 字符")
            # 关闭新页面
            page.close()
            return text_content
        
        # 如果所有尝试都失败，返回空字符串
        print("未找到有效内容")
        # 关闭新页面
        page.close()
        return ""
    except Exception as e:
        print(f"获取公司详细资料时出错: {e}")
        return ""

# 爬虫主函数
def crawl_research_data():
    print("开始爬取机构调研数据...")
    # 按机构分类存储结果
    institution_data = {}
    
    with sync_playwright() as p:
        # 启动浏览器（headless=False可以观察运行过程）
        browser = p.chromium.launch(headless=True)  # 部署时改为True
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 遍历每个监控机构
        for institution in MONITORED_INSTITUTIONS:
            print(f"\n正在爬取 {institution} 的调研数据...")
            institution_data[institution] = []
            
            try:
                # 构建URL，对机构名称进行URL编码
                import urllib.parse
                encoded_institution = urllib.parse.quote(institution)
                url = f"{EAST_MONEY_URL}{encoded_institution}"
                print(f"访问URL: {url}")
                
                # 访问页面
                page.goto(url, timeout=30000)
                
                # 关键：等待表格数据加载（等待第一个数据行出现）
                try:
                    page.wait_for_selector("table tbody tr", timeout=10000)
                except:
                    print("表格未加载或数据为空")
                    continue
                
                # 可选：等待一点额外时间让所有数据渲染完
                time.sleep(2)
                
                # 提取数据
                rows = page.query_selector_all("table tbody tr")
                print(f"找到 {len(rows)} 条调研记录")
                
                for row in rows:
                    cells = row.query_selector_all("td")
                    if len(cells) >= 13:  # 确保有足够的列
                        try:
                            code = cells[1].inner_text().strip()  # 列1：代码
                            name = cells[2].inner_text().strip()  # 列2：公司名称
                            机构名称 = cells[6].inner_text().strip()  # 列6：机构名称
                            公告日期 = cells[12].inner_text().strip()  # 列12：公告日期
                            
                            # 查找详细链接（在列3中）
                            detail_link = cells[3].query_selector("a")
                            detail_url = ""
                            if detail_link:
                                detail_url = detail_link.get_attribute("href")
                                if detail_url and not detail_url.startswith('http'):
                                    detail_url = f"https://data.eastmoney.com{detail_url}"
                            
                            print(f"处理记录: {name} ({code}) - 公告日期: {公告日期}")
                            
                            # 检查是否在过去2个交易日内（基于公告日期）
                            if 公告日期 and is_within_trading_days(公告日期):
                                # 获取详细链接内容
                                details = ""
                                if detail_url:
                                    print(f"获取详细资料: {detail_url}")
                                    details = get_company_details(context, detail_url)
                                    print(f"详细资料长度: {len(details)} 字符")
                                
                                institution_data[institution].append({
                                    "code": code,
                                    "name": name,
                                    "机构名称": 机构名称,
                                    "公告日期": 公告日期,
                                    "详细链接": detail_url,
                                    "详细资料": details
                                })
                        except Exception as e:
                            print(f"解析行数据时出错: {e}")
                            continue
            except Exception as e:
                print(f"爬取 {institution} 数据时出错: {e}")
                continue
        
        browser.close()
    
    # 输出结果
    total_count = 0
    for institution, data in institution_data.items():
        count = len(data)
        total_count += count
        print(f"\n{institution} 共获取 {count} 条符合条件的调研记录")
        
        for i, item in enumerate(data, 1):
            print(f"\n{i}. 公司名称: {item['name']}")
            print(f"   详细链接: {item['详细链接']}")
            if item.get('详细资料'):
                print(f"   详细资料: {item['详细资料'][:200]}..." if len(item['详细资料']) > 200 else f"   详细资料: {item['详细资料']}")
    
    print(f"\n爬取完成，总计获取 {total_count} 条符合条件的调研记录")
    
    # 返回按机构分类的数据
    return institution_data

if __name__ == "__main__":
    crawl_research_data()

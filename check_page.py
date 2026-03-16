import requests
from bs4 import BeautifulSoup

# 测试URL
url = "https://data.eastmoney.com/jgdy/gslb.html?name=%E6%B7%A1%E6%B0%B4%E6%B3%89"

print(f"访问URL: {url}")
response = requests.get(url)
response.encoding = 'utf-8'

# 解析HTML
soup = BeautifulSoup(response.text, 'html.parser')

# 查找所有表格
tables = soup.find_all('table')
print(f"找到 {len(tables)} 个表格")

for i, table in enumerate(tables):
    print(f"\n表格 {i}:")
    print(f"  类: {table.get('class', [])}")
    print(f"  ID: {table.get('id', '无')}")
    
    # 查找所有行
    rows = table.find_all('tr')
    print(f"  行数: {len(rows)}")
    
    # 打印前3行的内容
    for j, row in enumerate(rows[:3]):
        cols = row.find_all(['td', 'th'])
        print(f"  行 {j} 列数: {len(cols)}")
        for k, col in enumerate(cols):
            print(f"    列 {k}: {col.text.strip()[:50]}")

# 查找所有链接
links = soup.find_all('a')
print(f"\n找到 {len(links)} 个链接")

# 打印包含"详细"的链接
print("\n包含'详细'的链接:")
detail_links = [link for link in links if '详细' in link.text]
for link in detail_links[:5]:
    print(f"  文本: {link.text}")
    print(f"  链接: {link.get('href', '无')}")

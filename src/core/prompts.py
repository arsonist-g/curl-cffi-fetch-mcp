"""AI 提示词模板

用于生成和验证 HTML 提取规则的提示词
"""

# 规则生成提示词模板
RULE_GENERATION_PROMPT = """你是一个专业的网页结构分析专家。请分析以下 HTML 内容，为该网页生成 CSS Selector 提取规则。

目标 URL: {url}

HTML 内容:
{html}

请分析页面结构，识别以下关键内容区域：
1. **标题区域** - 页面的主标题（如文章标题、产品名称等）
2. **正文内容区域** - 页面的主要内容（如文章正文、产品描述等）
3. **需要排除的区域** - 导航栏、侧边栏、广告、页脚等噪音内容
4. **URL 路径模式** - 分析 URL 路径，推断哪些部分是固定的，哪些是变量

URL 路径模式分析示例：
- URL: https://blog.csdn.net/liulin_521/article/details/155862222
  分析: /liulin_521/article/details/155862222
  - liulin_521 是用户名（变量）
  - article/details 是固定路径
  - 155862222 是文章 ID（变量）
  推断模式: /*/article/details/*

- URL: https://news.example.com/2024/01/15/tech-news-title
  分析: /2024/01/15/tech-news-title
  - 2024/01/15 是日期（变量）
  - tech-news-title 是文章标题（变量）
  推断模式: /*/*/*/*

- URL: https://shop.example.com/product/12345
  分析: /product/12345
  - product 是固定路径
  - 12345 是产品 ID（变量）
  推断模式: /product/*

输出要求：
1. 使用 CSS Selector 语法
2. 选择器应尽可能具体和稳定（优先使用 class、id，避免过度依赖标签层级）
3. 输出格式必须是 JSON，包含以下字段：
   - path_pattern: URL 路径模式（字符串，使用 * 表示变量部分）
   - title: 标题选择器（字符串）
   - content: 正文内容选择器（字符串）
   - exclude: 需要排除的选择器列表（字符串数组）

4. 将 JSON 包裹在 <rule-{tag}> 标签中

示例输出格式：
<rule-{tag}>
{{
  "path_pattern": "/*/article/details/*",
  "title": "h1.article-title",
  "content": "div.article-body",
  "exclude": ["nav.navbar", "aside.sidebar", "footer", "div.ads"]
}}
</rule-{tag}>

现在请分析上述 HTML 和 URL，生成规则。
"""

# 规则验证提示词模板
RULE_VALIDATION_PROMPT = """你是一个专业的网页结构分析专家。请验证现有的 HTML 提取规则是否仍然适用于当前页面。

目标 URL: {url}

当前规则:
{existing_rule}

HTML 内容:
{html}

请判断：
1. 现有规则的选择器是否仍然能够正确匹配页面元素
2. 页面结构是否发生了重大变化
3. 是否需要更新规则

输出要求：
1. 如果规则仍然有效，返回原规则的 JSON（包括 path_pattern）
2. 如果规则需要更新，返回更新后的规则 JSON
3. JSON 格式与生成规则相同：
   - path_pattern: URL 路径模式（字符串，使用 * 表示变量部分）
   - title: 标题选择器（字符串）
   - content: 正文内容选择器（字符串）
   - exclude: 需要排除的选择器列表（字符串数组）
4. 将 JSON 包裹在 <rule-{tag}> 标签中

示例输出格式：
<rule-{tag}>
{{
  "path_pattern": "/*/article/details/*",
  "title": "h1.article-title",
  "content": "div.article-body",
  "exclude": ["nav.navbar", "aside.sidebar", "footer", "div.ads"]
}}
</rule-{tag}>

现在请验证规则并输出结果。
"""

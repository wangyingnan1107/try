# Python代码注释指南（Java开发者）

本指南帮助Java开发者理解Python代码的语法差异和设计思路。

## 已完成的文件

1. ✅ `text_processor.py` - 已添加完整注释
2. ⏳ `scraper.py` - 正在添加注释
3. ⏳ `main.py` - 待添加注释

## Python vs Java 核心语法对比

### 1. 导入模块
```python
# Python
import requests
from bs4 import BeautifulSoup

# Java等价写法
import com.example.requests;
import com.example.bs4.BeautifulSoup;
```

### 2. 类定义和方法
```python
# Python - 使用缩进代替大括号
class WebScraper:
    def __init__(self):  # 构造函数
        self.headers = {}  # 实例变量
        
    def method(self):  # 实例方法
        pass

# Java等价写法
public class WebScraper {
    private Map<String, String> headers;
    
    public WebScraper() {  // 构造函数
        this.headers = new HashMap<>();
    }
    
    public void method() {
        // 方法体
    }
}
```

### 3. 类型提示
```python
# Python类型提示（可选，主要用于IDE和类型检查）
def method(url: str) -> str:  # url是字符串，返回值是字符串
    return url

# Java（强制类型）
public String method(String url) {
    return url;
}
```

### 4. 异常处理
```python
# Python
try:
    # 可能出错的代码
    result = risky_operation()
except SpecificError as e:  # 捕获特定异常
    # 处理异常
    logger.error(f"错误: {e}")
except Exception as e:  # 捕获所有异常
    # 处理其他异常
finally:
    # 清理代码
    cleanup()

# Java等价写法
try {
    String result = riskyOperation();
} catch (SpecificException e) {
    logger.error("错误: " + e);
} catch (Exception e) {
    // 处理其他异常
} finally {
    cleanup();
}
```

### 5. 列表推导式
```python
# Python - 列表推导式（非常常用）
lines = [line.strip() for line in text.split('\n') if line.strip()]

# Java等价写法
List<String> lines = new ArrayList<>();
for (String line : text.split("\n")) {
    String trimmed = line.trim();
    if (!trimmed.isEmpty()) {
        lines.add(trimmed);
    }
}
```

### 6. 字典（类似Java的Map）
```python
# Python字典
dict = {'key': 'value', 'key2': 'value2'}
dict['key']  # 访问
dict.get('key', 'default')  # 安全访问

# Java Map
Map<String, String> map = new HashMap<>();
map.put("key", "value");
map.get("key");  // 访问
map.getOrDefault("key", "default");  // 安全访问
```

### 7. 字符串格式化
```python
# Python f-string（推荐方式）
name = "张三"
message = f"你好，{name}"  # 类似Java: String.format("你好，%s", name)

# 或使用format()
message = "你好，{}".format(name)
```

### 8. 装饰器
```python
# Python装饰器（@staticmethod类似Java的static）
@staticmethod
def static_method():
    pass
```

### 9. None vs null
```python
# Python使用None（类似Java的null）
if value is None:  # 检查None
    pass

# Java
if (value == null) {
    // ...
}
```

### 10. 模块导入的特殊情况
```python
# Python - try/except用于可选依赖
try:
    import optional_library
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
```

## 项目中的关键Python特性

### scraper.py 中的特殊语法

1. **字典推导式**
```python
# {k: v for k, v in items if condition}
tag.attrs = {k: v for k, v in tag.attrs.items() if k in attrs_to_keep}
```

2. **生成器表达式**
```python
# sum()配合生成器表达式
chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
```

3. **切片操作**
```python
text[:500]  # 前500个字符
response.content[:5000]  # 前5000字节
```

4. **函数参数解包**
```python
soup.find(**selector)  # **用于解包字典作为关键字参数
```

5. **条件表达式**
```python
encoding = response.apparent_encoding or 'utf-8'  # 类似Java的三元运算符
```

## 查看详细注释

每个文件的详细注释已直接添加在代码中，请查看：
- `text_processor.py` - 已添加完整注释
- `scraper.py` - 注释将添加到代码中
- `main.py` - 注释将添加到代码中


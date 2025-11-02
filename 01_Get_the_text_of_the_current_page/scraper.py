"""
网页抓取模块
处理网页抓取、文本提取、错误处理等功能

Java vs Python 说明：
- Python的模块导入：import 模块名 或 from 模块名 import 类/函数
- Python的try/except类似Java的try/catch，但可以捕获多种异常类型
- Python使用缩进代替Java的大括号{}来定义代码块
- Python的变量不需要声明类型，但可以使用类型提示（如 str, int）
"""

# 导入requests库，用于发送HTTP请求
# 类似Java: import org.apache.http.client.HttpClient;
import requests

# 导入BeautifulSoup，用于解析HTML
# 类似Java: import org.jsoup.Jsoup;
from bs4 import BeautifulSoup

# 导入日志模块，用于记录程序运行信息
# 类似Java: import java.util.logging.Logger;
import logging

# 导入类型提示模块（主要用于IDE和类型检查，不强制类型）
# Optional[str] 表示可能为str或None
# Dict[str, int] 表示字典，键为str，值为int
# 类似Java的泛型：Optional<String>, Map<String, Integer>
from typing import Optional, Dict

# 导入URL解析工具
# urlparse用于解析URL，urljoin用于拼接URL
from urllib.parse import urlparse, urljoin

# 导入时间模块，用于延时等功能
import time

# Python的try/except用于可选依赖检测
# 如果chardet库未安装，不会报错，而是设置CHARDET_AVAILABLE = False
# 类似Java: 需要先检查类是否存在，或使用反射
try:
    import chardet  # 字符编码检测库
    CHARDET_AVAILABLE = True  # 模块级变量（类似Java的类常量或静态变量）
except ImportError:  # 捕获导入异常（类似Java的catch ImportException）
    CHARDET_AVAILABLE = False

# 同样的方式检测Selenium是否可用
# Selenium用于JavaScript渲染的网页抓取
try:
    from selenium import webdriver  # WebDriver接口
    from selenium.webdriver.chrome.service import Service  # Chrome服务
    from selenium.webdriver.chrome.options import Options  # Chrome选项
    from selenium.webdriver.common.by import By  # 元素定位方式
    from selenium.webdriver.support.ui import WebDriverWait  # 等待工具
    from selenium.webdriver.support import expected_conditions as EC  # 等待条件
    from webdriver_manager.chrome import ChromeDriverManager  # ChromeDriver管理
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# 配置日志系统
# basicConfig用于配置日志的基本设置
# level=logging.INFO：设置日志级别为INFO（类似Java的Logger.setLevel(Level.INFO)）
# format：日志格式，%(asctime)s表示时间，%(levelname)s表示级别，%(message)s表示消息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取当前模块的日志记录器
# __name__是Python的特殊变量，表示当前模块名
# 类似Java: Logger logger = Logger.getLogger(ClassName.class.getName());
logger = logging.getLogger(__name__)


class WebScraper:
    """
    网页抓取器类
    类似Java: public class WebScraper { }
    
    Python的类不需要显式声明public/private（默认都是public）
    私有成员用单下划线开头（约定），如 _private_var
    """
    
    def __init__(self):
        """
        初始化方法（构造函数）
        类似Java: public WebScraper() { }
        
        Python的构造函数固定命名为__init__
        self表示当前实例（类似Java的this）
        """
        # self.headers：实例变量（类似Java的实例字段）
        # 字典字面量：用{}创建字典，类似Java的Map或HashMap
        # 键值对用冒号分隔，类似Java的map.put("key", "value")
        # 设置请求头，模拟浏览器访问，避免反爬虫
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        # Python可以直接给实例变量赋值，不需要先声明
        # 类似Java: this.timeout = 30;
        self.timeout = 30  # 请求超时时间（秒）
        self.max_retries = 3  # 最大重试次数
        self.use_selenium = False  # 是否使用Selenium（用于JavaScript渲染）
        
    def validate_url(self, url: str) -> bool:
        """
        验证URL格式的方法
        类似Java: public boolean validateUrl(String url)
        
        类型提示：
        - url: str 表示参数url是字符串类型
        - -> bool 表示返回值是布尔类型
        注意：Python的类型提示是可选的，主要用于IDE和类型检查，不强制类型
        
        Args:
            url: 待验证的URL字符串
            
        Returns:
            bool: URL是否有效
        """
        try:
            # urlparse()：解析URL，返回包含scheme、netloc等字段的对象
            # 类似Java: URI uri = new URI(url);
            result = urlparse(url)
            
            # all()：判断列表中所有元素是否为True
            # result.scheme in ['http', 'https']：检查协议是否为http或https
            # result.netloc：检查是否有网络位置（域名等）
            # 类似Java: return uri.getScheme().equals("http") || uri.getScheme().equals("https") && uri.getHost() != null;
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception as e:
            # f-string：Python 3.6+的字符串格式化方式
            # f"URL验证失败: {e}" 等价于 "URL验证失败: " + str(e)
            # 类似Java: logger.error("URL验证失败: " + e.toString());
            logger.error(f"URL验证失败: {e}")
            return False
    
    def fetch_html(self, url: str) -> str:
        """
        获取网页HTML文本内容（已自动处理编码）
        
        Args:
            url: 网页URL
            
        Returns:
            str: HTML文本内容，失败返回None
        """
        if not self.validate_url(url):
            logger.error(f"无效的URL: {url}")
            return None
        
        # for循环：range(self.max_retries)生成0到max_retries-1的整数序列
        # 类似Java: for (int attempt = 0; attempt < maxRetries; attempt++)
        for attempt in range(self.max_retries):
            try:
                # f-string：Python 3.6+的字符串格式化
                # f"正在请求网页 (尝试 {attempt + 1}/{self.max_retries}): {url}"
                # 等价于: "正在请求网页 (尝试 " + str(attempt+1) + "/" + str(max_retries) + "): " + url
                logger.info(f"正在请求网页 (尝试 {attempt + 1}/{self.max_retries}): {url}")
                
                # requests.get()：发送HTTP GET请求
                # 类似Java: HttpClient.get(url, headers, timeout)
                # Python支持关键字参数（命名参数），提高了代码可读性
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=True  # SSL验证
                )
                
                # 检查HTTP状态码
                response.raise_for_status()
                
                # 方法1：优先使用response.apparent_encoding（最准确）
                # apparent_encoding是requests基于内容自动检测的编码
                if response.apparent_encoding:
                    response.encoding = response.apparent_encoding
                    logger.info(f"使用apparent_encoding: {response.apparent_encoding}")
                
                # 方法2：如果apparent_encoding不可用，尝试检测HTML中的charset声明
                if not response.encoding or response.encoding.lower() in ['iso-8859-1', 'latin1']:
                    # 尝试从HTML中提取charset（先使用临时编码解码前5000字节）
                    import re
                    # 先用apparent_encoding或UTF-8尝试解码前5000字节来查找charset
                    try_temp_encoding = response.apparent_encoding or 'utf-8'
                    try:
                        temp_html = response.content[:5000].decode(try_temp_encoding, errors='ignore')
                    except:
                        temp_html = response.content[:5000].decode('utf-8', errors='ignore')
                    
                    charset_match = re.search(r'<meta[^>]*charset=["\']?([^"\'>\s]+)', temp_html, re.I)
                    if charset_match:
                        html_charset = charset_match.group(1).strip().lower()
                        logger.info(f"从HTML中检测到charset: {html_charset}")
                        try:
                            # 验证这个编码是否有效
                            test_text = response.content.decode(html_charset)
                            # 简单验证解码后的文本质量
                            if test_text and len(test_text) > 0:
                                response.encoding = html_charset
                                logger.info(f"使用HTML声明的charset: {html_charset}")
                        except Exception as e:
                            logger.warning(f"HTML声明的charset {html_charset} 无效: {e}，继续使用apparent_encoding")
                
                # 方法3：如果还是没有，尝试常见编码
                if not response.encoding or response.encoding.lower() in ['iso-8859-1', 'latin1', 'cp1252']:
                    # 对于中文网站，常见编码
                    for try_encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
                        try:
                            test_text = response.content.decode(try_encoding)
                            # 生成器表达式：Python的高级特性
                            # sum(1 for c in test_text[:500] if 条件)
                            # 等价于Java:
                            #   int count = 0;
                            #   for (char c : testText.substring(0, 500).toCharArray()) {
                            #       if (条件) count++;
                            #   }
                            # test_text[:500]：切片操作，获取前500个字符（类似Java的substring(0, 500)）
                            # '\u4e00' <= c <= '\u9fff'：检查是否为中文字符（Unicode范围）
                            # c.isalnum()：检查是否为字母或数字
                            # c.isspace()：检查是否为空白字符
                            chinese_chars = sum(1 for c in test_text[:500] if '\u4e00' <= c <= '\u9fff' or c.isalnum() or c.isspace())
                            if chinese_chars > 50:  # 如果前500个字符中有50个以上有效字符
                                response.encoding = try_encoding
                                logger.info(f"通过测试验证使用编码: {try_encoding}")
                                break
                        except:
                            continue
                
                # 如果以上都失败，使用apparent_encoding或UTF-8
                if not response.encoding or response.encoding.lower() in ['iso-8859-1', 'latin1']:
                    response.encoding = response.apparent_encoding or 'utf-8'
                    logger.info(f"最终使用编码: {response.encoding}")
                
                # 直接使用response.text，requests会自动按照response.encoding解码
                html_text = response.text
                
                logger.info(f"成功获取网页内容，文本长度: {len(html_text)} 字符，使用编码: {response.encoding}")
                return html_text
                
            except requests.exceptions.Timeout:
                logger.error(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # 等待后重试
                else:
                    raise Exception("请求超时，请检查网络连接或稍后重试")
                    
            except requests.exceptions.ConnectionError:
                logger.error(f"连接错误 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                else:
                    raise Exception("无法连接到服务器，请检查网络连接")
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP错误: {e}")
                status_code = e.response.status_code if hasattr(e, 'response') else None
                if status_code == 403:
                    raise Exception("访问被拒绝（403），网站可能阻止了爬虫访问")
                elif status_code == 404:
                    raise Exception("网页不存在（404）")
                elif status_code == 500:
                    raise Exception("服务器错误（500），请稍后重试")
                else:
                    raise Exception(f"HTTP错误: {status_code or str(e)}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {e}")
                raise Exception(f"请求失败: {str(e)}")
            except Exception as e:
                logger.error(f"未知错误: {e}")
                raise Exception(f"发生错误: {str(e)}")
        
        return None
    
    def fetch_html_with_selenium(self, url: str) -> str:
        """
        使用Selenium获取网页HTML内容（支持JavaScript渲染）
        
        Args:
            url: 网页URL
            
        Returns:
            str: HTML文本内容，失败返回None
        """
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium未安装，无法处理JavaScript渲染的网页。请运行: pip install selenium webdriver-manager")
        
        driver = None
        try:
            logger.info(f"使用Selenium获取网页: {url}")
            
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            
            # 创建WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置超时
            driver.set_page_load_timeout(self.timeout)
            
            # 访问网页
            driver.get(url)
            
            # 等待页面加载（等待主要内容出现）
            try:
                # 等待body标签出现
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # 额外等待JavaScript执行
                import time
                time.sleep(2)  # 等待JavaScript渲染
            except Exception as e:
                logger.warning(f"等待页面加载超时: {e}")
            
            # 获取页面源码
            html_text = driver.page_source
            
            logger.info(f"成功获取网页内容（Selenium），文本长度: {len(html_text)} 字符")
            return html_text
            
        except Exception as e:
            logger.error(f"Selenium获取网页失败: {e}")
            raise Exception(f"Selenium获取网页失败: {str(e)}")
        finally:
            if driver:
                driver.quit()
    
    def extract_text(self, html_text: str) -> str:
        """
        从HTML文本中提取文本内容
        
        Args:
            html_text: HTML文本内容（已经是字符串，不需要解码）
            
        Returns:
            str: 提取的文本内容
        """
        try:
            # html_text已经是解码后的字符串，直接使用BeautifulSoup解析
            # 优先使用lxml，如果失败则使用html.parser
            try:
                soup = BeautifulSoup(html_text, 'lxml')
            except Exception as e:
                logger.warning(f"使用lxml解析失败，尝试html.parser: {e}")
                soup = BeautifulSoup(html_text, 'html.parser')
            
            # 移除不需要的标签（脚本、样式、注释等）
            for element in soup(['script', 'style', 'meta', 'link', 'noscript', 'iframe', 'embed', 'svg', 'canvas', 'head']):
                element.decompose()
            
            # 移除注释
            from bs4 import Comment
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            
            # 移除所有script标签内的文本内容（可能包含编码错误的数据）
            for script in soup.find_all('script'):
                script.decompose()
            
            # 移除data-*属性中的内容（可能包含乱码数据）
            for tag in soup.find_all(True):
                # 保留必要的属性，移除可能包含乱码数据的属性
                attrs_to_keep = ['id', 'class', 'href', 'src', 'alt', 'title']
                if hasattr(tag, 'attrs'):
                    tag.attrs = {k: v for k, v in tag.attrs.items() if k in attrs_to_keep}
            
            # 移除隐藏的元素
            for tag in soup.find_all(['noscript', 'template']):
                tag.decompose()
            
            # 移除style属性（可能包含乱码）
            for tag in soup.find_all(True):
                if hasattr(tag, 'attrs') and 'style' in tag.attrs:
                    del tag.attrs['style']
            
            # 优先提取主要内容区域的文本
            # 尝试找到常见的正文容器
            main_content = None
            content_selectors = [
                {'name': 'article'},
                {'name': 'main'},
                {'class': 'content'},
                {'class': 'post-content'},
                {'class': 'entry-content'},
                {'id': 'content'},
                {'id': 'main'},
            ]
            
            for selector in content_selectors:
                try:
                    found = soup.find(**selector)
                    if found and len(found.get_text(strip=True)) > 100:
                        main_content = found
                        logger.info(f"找到主要内容区域: {selector}")
                        break
                except Exception:
                    continue
            
            # 获取文本内容
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                # 如果找不到特定区域，获取整个页面的文本
                text = soup.get_text(separator='\n', strip=True)
            
            # 检查提取的文本是否主要是乱码或JavaScript代码
            # 如果文本中包含大量异常字符，说明可能是JavaScript/JSON数据
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            alnum_chars = sum(1 for c in text if c.isalnum())
            weird_chars = sum(1 for c in text if ord(c) > 127 and not ('\u4e00' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f' or '\uff00' <= c <= '\uffef'))
            total_chars = len(text)
            
            # 如果文本太短或主要是乱码，返回提示
            if total_chars > 0:
                valid_ratio = (chinese_chars + alnum_chars) / total_chars
                weird_ratio = weird_chars / total_chars
                
                # 判断是否为乱码：奇怪字符比例高，有效字符比例低
                is_gibberish = weird_ratio > 0.2 and valid_ratio < 0.5
                
                if is_gibberish or (total_chars < 100 and chinese_chars < 5):
                    # 这可能是JavaScript渲染的网页，文本内容很少
                    logger.warning(f"提取的文本可能是乱码或JavaScript代码：总字符{total_chars}，中文字符{chinese_chars}，有效比例{valid_ratio:.2%}，奇怪字符比例{weird_ratio:.2%}")
                    
                    # 尝试过滤出可能有用的文本
                    filtered_lines = []
                    for line in text.split('\n'):
                        line = line.strip()
                        if not line or len(line) < 2:
                            continue
                        
                        line_chinese = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
                        line_alnum = sum(1 for c in line if c.isalnum())
                        line_total = len(line)
                        
                        # 如果行中包含中文或大量有效字符，保留
                        if line_total > 0:
                            line_valid_ratio = (line_chinese + line_alnum) / line_total
                            # 计算奇怪字符（不在常见Unicode范围内的字符）
                            line_weird = 0
                            for c in line:
                                code = ord(c)
                                # 检查是否为奇怪的字符：在Latin1范围内但不是可读字符，或者超出常用范围
                                if 127 < code < 256:
                                    # Latin1范围，但不是常见标点，可能是乱码
                                    if c not in '€‚ƒ„…†‡ˆ‰Š‹ŒŽ''""•–—˜™š›œžŸ ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿':
                                        line_weird += 1
                                elif code > 65535:
                                    line_weird += 1
                            
                            line_weird_ratio = line_weird / line_total if line_total > 0 else 0
                            
                            # 更严格的保留条件：必须有中文，或者有效字符比例很高且奇怪字符很少
                            if line_chinese >= 3:  # 至少3个中文字符
                                filtered_lines.append(line)
                            elif line_valid_ratio > 0.8 and line_weird_ratio < 0.1:  # 80%以上有效字符且奇怪字符<10%
                                filtered_lines.append(line)
                    
                    filtered_text = '\n'.join(filtered_lines)
                    
                    # 检查过滤后的文本质量
                    if filtered_text.strip():
                        # 重新检查过滤后的文本
                        filtered_chinese = sum(1 for c in filtered_text if '\u4e00' <= c <= '\u9fff')
                        filtered_weird = sum(1 for c in filtered_text if ord(c) > 127 and not ('\u4e00' <= c <= '\u9fff'))
                        filtered_total = len(filtered_text)
                        
                        # 如果过滤后仍然乱码多或中文少，返回提示
                        if filtered_total > 0:
                            filtered_weird_ratio = filtered_weird / filtered_total
                            # 如果中文字符少于10个，或者奇怪字符比例仍然很高
                            if filtered_chinese < 10 or filtered_weird_ratio > 0.3:
                                logger.warning(f"过滤后文本质量仍然较差：中文字符{filtered_chinese}，奇怪字符比例{filtered_weird_ratio:.2%}")
                                # 返回提示信息
                                return "⚠️ 该网页内容通过JavaScript动态加载，无法直接提取文本。\n请使用Selenium模式（在侧边栏勾选\"使用JavaScript渲染\"选项）来获取完整内容。"
                    
                    # 如果过滤后文本很少或为空，返回提示
                    if len(filtered_text.strip()) < 100:
                        logger.warning("过滤后文本仍然很少，可能是JavaScript渲染的网页")
                        if filtered_text.strip() and filtered_chinese >= 5:
                            return filtered_text.strip()
                        else:
                            return "⚠️ 该网页内容通过JavaScript动态加载，无法直接提取文本。\n请使用Selenium模式（在侧边栏勾选\"使用JavaScript渲染\"选项）来获取完整内容。"
                    else:
                        return filtered_text
            
            # 正常情况，返回过滤后的文本
            logger.info(f"成功提取文本，长度: {len(text)} 字符，中文字符: {chinese_chars}")
            return text
            
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            raise Exception(f"文本提取失败: {str(e)}")
    
    def scrape_webpage_text(self, url: str, use_selenium: bool = None) -> str:
        """
        抓取网页并提取文本（主要方法）
        
        Args:
            url: 网页URL
            use_selenium: 是否使用Selenium（None时自动检测）
            
        Returns:
            str: 提取的文本内容
            
        Raises:
            Exception: 抓取失败时抛出异常
        """
        # 自动检测是否需要使用Selenium
        if use_selenium is None:
            use_selenium = self.use_selenium
        
        # 如果指定使用Selenium或者首次尝试失败且Selenium可用
        if use_selenium:
            if not SELENIUM_AVAILABLE:
                logger.warning("Selenium不可用，回退到普通方法")
                html_text = self.fetch_html(url)
            else:
                html_text = self.fetch_html_with_selenium(url)
        else:
            html_text = self.fetch_html(url)
            if html_text:
                # 检查提取的文本是否太少或是乱码（可能是JavaScript渲染的内容）
                text_sample = self.extract_text(html_text)
                
                # 检查是否为有效的文本
                sample_stripped = text_sample.strip()
                is_valid = len(sample_stripped) >= 100 and not sample_stripped.startswith("⚠️")
                chinese_in_sample = sum(1 for c in sample_stripped[:1000] if '\u4e00' <= c <= '\u9fff')
                
                # 检查是否包含大量乱码字符
                weird_in_sample = sum(1 for c in sample_stripped[:1000] if ord(c) > 127 and not ('\u4e00' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f' or '\uff00' <= c <= '\uffef'))
                sample_total = min(1000, len(sample_stripped))
                weird_ratio = weird_in_sample / sample_total if sample_total > 0 else 0
                
                # 如果文本太少、是提示信息、包含极少中文、或乱码比例高，可能是JavaScript渲染的网页
                is_gibberish = weird_ratio > 0.3 and chinese_in_sample < 20
                if not is_valid or (len(sample_stripped) < 200 and chinese_in_sample < 10) or is_gibberish:
                    logger.info(f"检测到文本内容异常（长度: {len(sample_stripped)}, 中文: {chinese_in_sample}），可能是JavaScript渲染，尝试使用Selenium...")
                    if SELENIUM_AVAILABLE:
                        try:
                            html_text = self.fetch_html_with_selenium(url)
                            logger.info("成功使用Selenium获取网页内容")
                        except Exception as e:
                            logger.warning(f"Selenium获取失败: {e}，使用原始结果")
                            # 如果Selenium失败，返回原始结果或提示
                            if len(sample_stripped) < 50:
                                raise Exception(f"无法获取网页内容：文本内容过少（{len(sample_stripped)}字符）。这可能是JavaScript渲染的网页，需要安装Chrome浏览器并使用Selenium模式。")
                            html_text = self.fetch_html(url)
                    else:
                        # Selenium不可用，如果文本太少则抛出异常
                        if len(sample_stripped) < 50:
                            raise Exception("无法获取网页内容：文本内容过少。这可能是JavaScript渲染的网页，请安装selenium和webdriver-manager，然后在设置中勾选\"使用JavaScript渲染\"选项。")
        
        if html_text is None:
            raise Exception("无法获取网页内容")
        
        # 从HTML文本中提取文本内容
        text = self.extract_text(html_text)
        return text


def scrape_webpage_text(url: str) -> str:
    """
    便捷函数：抓取网页文本
    
    Args:
        url: 网页URL
        
    Returns:
        str: 提取的文本内容
    """
    scraper = WebScraper()
    return scraper.scrape_webpage_text(url)


if __name__ == "__main__":
    # 测试代码
    test_url = "https://ilia8.lofter.com/post/1f8051f3_1c7b3077d"
    try:
        text = scrape_webpage_text(test_url)
        print("提取的文本内容：")
        print(text[:500])  # 只打印前500个字符
    except Exception as e:
        print(f"错误: {e}")


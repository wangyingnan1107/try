"""
文本处理模块
处理文本格式化、清理、分段等功能

Java vs Python 说明：
- Python使用缩进代替Java的大括号{}
- Python的类方法可以使用@staticmethod装饰器，类似Java的static方法
- Python的类型提示：str表示字符串类型，类似Java的String
- Python的函数参数：text: str表示参数text是字符串类型，-> str表示返回值是字符串
"""

# 导入正则表达式模块，用于文本模式匹配
# 类似Java: import java.util.regex.Pattern;
import re

# 导入类型提示模块，用于类型注解
# 类似Java: List<String>，但在Python中主要用于类型检查，不强制类型
from typing import List


class TextProcessor:
    """
    文本处理器类
    类似Java: public class TextProcessor { }
    
    Python类不需要显式声明public，默认就是public
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本内容
        静态方法，类似Java的: public static String cleanText(String text)
        
        @staticmethod装饰器：表示这是静态方法，可以通过类名直接调用，不需要创建实例
        类似Java: public static方法
        
        Args: 参数说明
            text: 原始文本（字符串类型）
            
        Returns: 返回值说明
            str: 清理后的文本（字符串类型）
        """
        # Python的空值检查：if not text 相当于Java的 if (text == null || text.isEmpty())
        # Python中空字符串、None、空列表等都被认为是False
        if not text:
            # 返回空字符串，类似Java的return "";
            return ""
        
        # re.sub()：正则表达式替换
        # r'\n{3,}'：原始字符串，匹配3个或更多的换行符
        # '\n\n'：替换为2个换行符（保留段落分隔）
        # 类似Java: text.replaceAll("\\n{3,}", "\n\n")
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 列表推导式：Python的特色语法
        # [line.strip() for line in text.split('\n')]
        # 等价于Java:
        #   String[] lines = text.split("\n");
        #   List<String> trimmedLines = new ArrayList<>();
        #   for (String line : lines) {
        #       trimmedLines.add(line.trim());
        #   }
        # text.split('\n')：按换行符分割字符串，返回列表
        # line.strip()：移除行首行尾空白字符，类似Java的trim()
        lines = [line.strip() for line in text.split('\n')]
        
        # 初始化空列表，类似Java: List<String> cleanedLines = new ArrayList<>();
        cleaned_lines = []
        # 标记前一行是否为空
        prev_empty = False
        
        # for循环：遍历列表，类似Java的 for (String line : lines)
        for line in lines:
            # if line：判断是否非空，类似Java的 !line.isEmpty()
            if line:
                # 列表的append方法，类似Java的list.add()
                cleaned_lines.append(line)
                prev_empty = False
            # elif：Python的else if缩写
            elif not prev_empty:
                # 保留第一个空行作为段落分隔
                cleaned_lines.append('')
                prev_empty = True
        
        # while循环：当列表不为空且最后一个元素为空时，移除最后一个元素
        # cleaned_lines：列表不为空（在Python中空列表是False）
        # not cleaned_lines[-1]：最后一个元素为空（-1表示最后一个索引）
        # 类似Java: while (!cleanedLines.isEmpty() && cleanedLines.get(cleanedLines.size()-1).isEmpty())
        #     cleanedLines.remove(cleanedLines.size()-1);
        while cleaned_lines and not cleaned_lines[-1]:
            # pop()：移除并返回最后一个元素，类似Java的remove(list.size()-1)
            cleaned_lines.pop()
        
        # '\n'.join()：用换行符连接列表中的元素，形成字符串
        # 类似Java: String.join("\n", cleanedLines)
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def split_paragraphs(text: str) -> List[str]:
        """
        将文本分割为段落
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 段落列表（字符串列表）
            Python的List[str]类似Java的List<String>
        """
        if not text:
            # 返回空列表，类似Java的return new ArrayList<>();
            return []
        
        # re.split()：正则表达式分割
        # r'\n{2,}'：匹配2个或更多换行符（段落分隔符）
        # 类似Java: text.split("\\n{2,}")
        paragraphs = re.split(r'\n{2,}', text)
        
        # 列表推导式：过滤并清理每个段落
        # [p.strip() for p in paragraphs if p.strip()]
        # 等价于Java:
        #   List<String> result = new ArrayList<>();
        #   for (String p : paragraphs) {
        #       String trimmed = p.trim();
        #       if (!trimmed.isEmpty()) {
        #           result.add(trimmed);
        #       }
        #   }
        # p.strip()：清理段落前后空白
        # if p.strip()：只保留非空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    @staticmethod
    def format_text(text: str, preserve_formatting: bool = True) -> str:
        """
        格式化文本
        
        Args:
            text: 原始文本
            preserve_formatting: 是否保留基本格式（默认值为True）
            Python支持默认参数，类似Java的方法重载
        
        Returns:
            str: 格式化后的文本
        """
        if not text:
            return ""
        
        # 调用同一个类的静态方法，类似Java的TextProcessor.cleanText(text)
        text = TextProcessor.clean_text(text)
        
        # if条件判断，类似Java的if语句
        if preserve_formatting:
            # 保留段落格式
            paragraphs = TextProcessor.split_paragraphs(text)
            # '\n\n'.join()：用双换行符连接段落，保留段落分隔
            return '\n\n'.join(paragraphs)
        else:
            # 移除所有换行，合并为单行文本
            # text.split()：默认按空白字符分割（包括空格、换行、制表符等）
            # ' '.join()：用单个空格连接
            return ' '.join(text.split())
    
    @staticmethod
    def remove_empty_lines(text: str) -> str:
        """
        移除空行
        
        Args:
            text: 文本内容
            
        Returns:
            str: 移除空行后的文本
        """
        if not text:
            return ""
        
        # 列表推导式：过滤掉空行
        # [line for line in text.split('\n') if line.strip()]
        # 只保留非空行（去除空白后不为空的行）
        lines = [line for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    @staticmethod
    def count_words(text: str) -> int:
        """
        统计文本字数（中英文混合）
        
        Args:
            text: 文本内容
            
        Returns:
            int: 字数（整数类型）
        """
        if not text:
            return 0
        
        # re.sub(r'\s+', '', text)：移除所有空白字符（空格、换行、制表符等）
        # 类似Java: text.replaceAll("\\s+", "")
        text = re.sub(r'\s+', '', text)
        # len()：获取字符串长度，类似Java的text.length()
        return len(text)
    
    @staticmethod
    def count_lines(text: str) -> int:
        """
        统计文本行数
        
        Args:
            text: 文本内容
            
        Returns:
            int: 行数
        """
        if not text:
            return 0
        
        # text.split('\n')：按换行符分割，返回列表
        # len()：获取列表长度，类似Java的list.size()
        return len(text.split('\n'))
    
    @staticmethod
    def get_text_stats(text: str) -> dict:
        """
        获取文本统计信息
        
        Args:
            text: 文本内容
            
        Returns:
            dict: 统计信息字典（类似Java的Map<String, Object>）
            Python的dict类似Java的HashMap或Map
        """
        # 字典字面量：用{}创建字典
        # 类似Java:
        #   Map<String, Object> stats = new HashMap<>();
        #   stats.put("字符数", text.length());
        return {
            '字符数': len(text),  # 字典的键值对，类似Java的map.put("键", 值)
            '字数': TextProcessor.count_words(text),
            '行数': TextProcessor.count_lines(text),
            '段落数': len(TextProcessor.split_paragraphs(text))
        }


# 模块级函数：不在类中定义的函数，可以在导入后直接使用
# 类似Java的工具类中的静态方法

def clean_text(text: str) -> str:
    """
    便捷函数：清理文本
    这是一个模块级函数，可以直接导入使用，不需要通过类调用
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    # 调用类的静态方法，类似Java的TextProcessor.cleanText(text)
    return TextProcessor.clean_text(text)


def format_text(text: str) -> str:
    """
    便捷函数：格式化文本
    
    Args:
        text: 原始文本
        
    Returns:
        str: 格式化后的文本
    """
    return TextProcessor.format_text(text)


# Python的特殊变量：__name__
# 当文件作为脚本直接运行时，__name__ == "__main__"
# 当文件作为模块被导入时，__name__ == "模块名"
# 类似Java的main方法，用于测试代码
if __name__ == "__main__":
    # 三引号字符串：可以包含多行的字符串，类似Java的多行字符串（Java 15+）
    # 在Python中，三引号可以保持字符串中的换行符
    test_text = """
    这是一段测试文本。
    
    这是第二段。
    
    
    这是第三段。
    """
    
    # print()：输出到控制台，类似Java的System.out.println()
    print("原始文本:")
    # repr()：获取对象的字符串表示（包含引号等），用于调试
    # 类似Java的toString()或Arrays.toString()
    print(repr(test_text))
    print("\n清理后:")
    print(repr(clean_text(test_text)))
    print("\n格式化后:")
    print(format_text(test_text))
    print("\n统计信息:")
    print(TextProcessor.get_text_stats(test_text))

"""
网页文字提取工具 - 主程序
使用Streamlit构建的Web界面

Java vs Python 说明：
- Streamlit是Python的Web框架，用于快速构建交互式Web应用
- 类似Java的Spring Boot + Thymeleaf，但更简单
- st.xxx是Streamlit的组件，会自动生成HTML和JavaScript
- 不需要手动编写HTML/CSS/JS，Streamlit会自动处理
"""

# 导入Streamlit库，用于构建Web界面
# st是Streamlit的主模块，所有界面组件都通过st调用
# 类似Java的Spring MVC框架
import streamlit as st

# 导入系统模块，用于系统相关操作
import sys

# 导入traceback模块，用于获取完整的错误堆栈信息
# 类似Java的异常堆栈跟踪
import traceback

# 从自定义模块导入类 and 函数
# 类似Java: import com.example.Scraper.WebScraper;
from scraper import WebScraper, scrape_webpage_text
from text_processor import TextProcessor, clean_text, format_text

# 导入io模块，用于字符串IO操作（类似Java的StringWriter）
import io

# Streamlit页面配置
# set_page_config()：设置页面标题、图标、布局等
# 类似Java的Spring Boot中的@Configuration或配置类
st.set_page_config(
    page_title="网页文字提取工具",  # 页面标题（浏览器标签页显示）
    page_icon="📄",  # 页面图标（emoji表情）
    layout="wide",  # 布局方式：wide（宽屏）或centered（居中）
    initial_sidebar_state="expanded"  # 侧边栏初始状态：expanded（展开）或collapsed（折叠）
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .stat-box {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """
    初始化会话状态函数
    类似Java: public static void initSessionState(HttpSession session)
    
    Streamlit的会话状态（session_state）：
    - 类似于Java Web应用的Session对象
    - 用于在页面刷新之间保存数据
    - st.session_state是字典类型，可以存储任意数据
    """
    # Python的in操作符：检查键是否存在于字典中
    # 类似Java: !session.containsKey("extracted_text")
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'edited_text' not in st.session_state:
        st.session_state.edited_text = ""
    if 'current_url' not in st.session_state:
        st.session_state.current_url = ""


def display_text_stats(text: str):
    """显示文本统计信息"""
    if text:
        stats = TextProcessor.get_text_stats(text)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("字符数", stats['字符数'])
        with col2:
            st.metric("字数", stats['字数'])
        with col3:
            st.metric("行数", stats['行数'])
        with col4:
            st.metric("段落数", stats['段落数'])


def main():
    """主函数"""
    init_session_state()
    
    # 标题
    st.markdown('<div class="main-header">📄 网页文字提取工具</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 文本处理选项
        st.subheader("文本处理选项")
        auto_clean = st.checkbox("自动清理文本", value=True, 
                                help="自动移除多余空白和空行")
        preserve_formatting = st.checkbox("保留段落格式", value=True,
                                         help="保留段落之间的分隔")
        
        # JavaScript渲染选项
        st.subheader("网页类型")
        use_selenium = st.checkbox("使用JavaScript渲染（Selenium）", value=False,
                                  help="如果网页内容是通过JavaScript动态加载的，请勾选此项。需要安装Chrome浏览器。")
        
        st.markdown("---")
        
        # 使用说明
        st.subheader("📖 使用说明")
        st.markdown("""
        1. 在下方输入框中输入网页URL
        2. 点击"提取文字"按钮
        3. 等待网页内容提取完成
        4. 在文本框中查看和编辑文字
        5. 可以复制、下载或保存文本
        """)
        
        st.markdown("---")
        
        # 提示信息
        st.subheader("ℹ️ 提示")
        st.info("""
        如果遇到无法提取的情况：
        - 检查URL是否正确
        - 某些网站可能禁止爬虫访问
        - 需要JavaScript渲染的页面可能需要特殊处理
        """)


    # 主界面
    # URL输入区域
    st.subheader("🌐 输入网页地址")
    
    default_url = "https://ilia8.lofter.com/post/1f8051f3_1c7b3077d"
    url_input = st.text_input(
        "网页URL：",
        value=st.session_state.current_url or default_url,
        placeholder="请输入完整的网页地址，例如：https://example.com",
        help="请输入要提取文字的网页完整地址"
    )
    
    col1, col2, col3 = st.columns([2, 2, 8])
    with col1:
        extract_button = st.button("🔍 提取文字", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ 清空", use_container_width=True)
    
    # 清空按钮处理
    if clear_button:
        st.session_state.extracted_text = ""
        st.session_state.edited_text = ""
        st.session_state.current_url = ""
        st.rerun()
    
    # 提取文字
    if extract_button:
        if not url_input or url_input.strip() == "":
            st.error("❌ 请输入有效的网页地址！")
        else:
            st.session_state.current_url = url_input.strip()
            with st.spinner("⏳ 正在抓取网页，请稍候..."):
                try:
                    # 创建抓取器并获取文本
                    scraper = WebScraper()
                    raw_text = scraper.scrape_webpage_text(url_input.strip(), use_selenium=use_selenium)
                    
                    # 文本处理
                    if auto_clean:
                        processed_text = clean_text(raw_text)
                    else:
                        processed_text = raw_text
                    
                    if preserve_formatting:
                        processed_text = format_text(processed_text)
                    
                    # 保存到会话状态
                    st.session_state.extracted_text = processed_text
                    st.session_state.edited_text = processed_text
                    
                    st.success(f"✅ 成功提取文字！共 {len(processed_text)} 个字符")
                    
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ 提取失败：{error_msg}")
                    
                    # 如果是JavaScript渲染相关错误，提示使用Selenium
                    if 'Selenium' in error_msg or 'JavaScript' in error_msg.lower():
                        st.info("💡 提示：这个网页可能需要JavaScript渲染才能获取完整内容。请在侧边栏勾选\"使用JavaScript渲染（Selenium）\"选项。")
                    
                    # 显示详细错误信息（可展开）
                    with st.expander("查看详细错误信息"):
                        st.code(traceback.format_exc())
                
                # 检查提取的文本是否太少（可能是JavaScript渲染的网页）
                if 'extracted_text' in st.session_state and st.session_state.extracted_text:
                    text_length = len(st.session_state.extracted_text.strip())
                    if text_length < 200 and not use_selenium:
                        st.warning("⚠️ 提取的文本内容较少（少于200字符）。如果内容不完整，可能是JavaScript渲染的网页。请在侧边栏勾选\"使用JavaScript渲染（Selenium）\"选项后重试。")
    
    # 显示提取的文字
    if st.session_state.extracted_text:
        st.markdown("---")
        st.subheader("📝 提取的文字内容")
        
        # 文本统计信息
        display_text_stats(st.session_state.extracted_text)
        
        st.markdown("---")
        
        # 可编辑文本框
        edited_text = st.text_area(
            "编辑文字内容：",
            value=st.session_state.edited_text,
            height=400,
            help="您可以在这里编辑提取的文字内容",
            key="text_editor"
        )
        
        # 更新编辑后的文本
        if edited_text != st.session_state.edited_text:
            st.session_state.edited_text = edited_text
        
        # 操作按钮区域
        st.markdown("---")
        st.subheader("💾 操作")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 复制到剪贴板
            if st.button("📋 复制文字", use_container_width=True):
                st.code(edited_text, language=None)
                st.info("提示：请手动选择上方代码框中的文字并按 Ctrl+C 复制")
        
        with col2:
            # 下载为TXT文件
            txt_buffer = io.StringIO(edited_text)
            st.download_button(
                label="⬇️ 下载TXT",
                data=txt_buffer.getvalue(),
                file_name="extracted_text.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
            # 重新处理文本
            if st.button("🔄 重新处理", use_container_width=True):
                processed = clean_text(edited_text) if auto_clean else edited_text
                if preserve_formatting:
                    processed = format_text(processed)
                st.session_state.edited_text = processed
                st.rerun()
        
        with col4:
            # 清空当前文本
            if st.button("🗑️ 清空文本", use_container_width=True):
                st.session_state.edited_text = ""
                st.rerun()
        
        # 显示编辑后的文本统计
        if edited_text != st.session_state.extracted_text:
            st.markdown("---")
            st.subheader("📊 编辑后文本统计")
            display_text_stats(edited_text)
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "网页文字提取工具 v1.0 | "
        "支持网页文字提取、编辑和导出"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()


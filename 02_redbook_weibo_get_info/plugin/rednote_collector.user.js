// ==UserScript==
// @name         RedNote Insight Collector
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Collect inspiration from Xiaohongshu to local server
// @author       You
// @match        https://www.xiaohongshu.com/*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// ==/UserScript==

(function() {
    'use strict';

    const API_URL = "http://127.0.0.1:8000/api/collect";
    let buttonInserted = false;

    // --- UI Helpers ---
    function createButton() {
        if (buttonInserted) return; // 避免重复添加
        
        const btn = document.createElement('button');
        btn.id = "rednote-collect-btn"; // 给个 ID 方便查找
        btn.innerText = "✨ 采集灵感";
        btn.style.position = "fixed";
        btn.style.bottom = "20px";
        btn.style.right = "20px";
        btn.style.zIndex = "999999"; // 增加 z-index
        btn.style.padding = "10px 20px";
        btn.style.backgroundColor = "#ff2442";
        btn.style.color = "white";
        btn.style.border = "none";
        btn.style.borderRadius = "20px";
        btn.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
        btn.style.cursor = "pointer";
        btn.style.fontWeight = "bold";
        btn.style.transition = "all 0.3s";
        
        btn.onmouseover = () => { btn.style.transform = "scale(1.05)"; };
        btn.onmouseout = () => { btn.style.transform = "scale(1)"; };
        
        btn.onclick = collectData;
        document.body.appendChild(btn);
        buttonInserted = true;
    }

    function checkPage() {
        // 检查当前 URL 是否是笔记详情页
        // 详情页 URL 通常包含 /explore/ 或者 /discovery/item/
        // 但有时候也是弹窗模式，URL 不变。
        // 所以我们更倾向于检查页面元素特征：是否有“笔记容器”
        
        // 只要不是纯列表页，或者是弹窗打开了笔记，我们都尝试显示按钮
        // 简单策略：总是显示按钮，点击时再判断是否能提取到数据
        if (!document.getElementById("rednote-collect-btn")) {
             buttonInserted = false;
             createButton();
        }
    }

    // ... (rest of the code)

    function showToast(msg, isError = false) {
        const toast = document.createElement('div');
        toast.innerText = msg;
        toast.style.position = "fixed";
        toast.style.bottom = "70px";
        toast.style.right = "20px";
        toast.style.zIndex = "9999";
        toast.style.padding = "10px 20px";
        toast.style.backgroundColor = isError ? "#ff4d4f" : "#52c41a";
        toast.style.color = "white";
        toast.style.borderRadius = "8px";
        toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // --- Data Extraction ---
    function extractData() {
        // 小红书页面结构经常变，这里需要根据实际 DOM 调整
        
        const currentUrl = window.location.href;
        const noteId = currentUrl.split('/').pop().split('?')[0];

        // 核心修复：优先锁定“笔记详情容器”，避免抓取到背景列表中的元素
        // 详情页通常包裹在 #noteContainer 或 .note-container 中
        const container = document.querySelector('#noteContainer') || 
                          document.querySelector('.note-container') || 
                          document.querySelector('.note-detail-mask') ||
                          document.body; // 降级方案
        
        // 辅助函数：在容器内查找
        const find = (selector) => container.querySelector(selector)?.innerText;
        const findAll = (selector) => container.querySelectorAll(selector);

        // 尝试获取标题
        // 优先使用 ID 选择器 (通常唯一)，然后是容器内的类选择器
        let title = document.getElementById("detail-title")?.innerText || 
                    find(".title") || 
                    find(".note-title") ||
                    "无标题";
        
        // 尝试获取正文
        let content = document.getElementById("detail-desc")?.innerText || 
                      find(".desc") || 
                      find(".note-desc") || 
                      "";

        // 尝试获取作者
        let authorName = find(".author-container .name") || 
                         find(".username") ||
                         "未知作者";
        let authorId = "";

        // 尝试获取图片
        let images = [];
        // 只在容器内查找图片，避免抓到推荐流的图
        const imgElements = findAll(".note-slider-img, .swiper-slide img, .img-container img");
        imgElements.forEach(img => {
            let src = img.getAttribute("src") || img.style.backgroundImage?.slice(5, -2);
            if (src && !src.includes("avatar") && src.startsWith("http")) {
                images.push(src);
            }
        });
        
        // 尝试获取点赞收藏数
        let likes = 0, collects = 0, comments = 0;
        const interactItems = findAll(".interact-container .interact-item");
        if (interactItems.length >= 3) {
            likes = parseInt(interactItems[0].innerText) || 0;
            collects = parseInt(interactItems[1].innerText) || 0;
            comments = parseInt(interactItems[2].innerText) || 0;
        }

        // 尝试获取神评论
        let topComments = [];
        const commentElements = findAll(".comment-item .content");
        for (let i = 0; i < Math.min(commentElements.length, 3); i++) {
            topComments.push(commentElements[i].innerText);
        }

        return {
            source_id: noteId,
            platform: "xiaohongshu",
            url: currentUrl,
            title: title.trim(),
            content: content.trim(),
            author: {
                name: authorName.trim(),
                uid: authorId
            },
            media: {
                images: [...new Set(images)], 
                video_cover: null
            },
            stats: {
                likes: likes,
                collects: collects,
                comments_count: comments
            },
            top_comments: topComments,
            tags: [] 
        };
    }

    // --- Action ---
    function collectData() {
        try {
            const data = extractData();
            console.log("Extracted Data:", data);
            
            // 使用 GM_xmlhttpRequest 以避开跨域限制 (虽然我们后端开了 CORS，但油猴更稳)
            GM_xmlhttpRequest({
                method: "POST",
                url: API_URL,
                headers: {
                    "Content-Type": "application/json"
                },
                data: JSON.stringify(data),
                onload: function(response) {
                    if (response.status === 200) {
                        showToast("✅ 采集成功！");
                    } else {
                        console.error(response);
                        showToast("❌ 采集失败: " + response.statusText, true);
                    }
                },
                onerror: function(err) {
                    console.error(err);
                    showToast("❌ 网络错误", true);
                }
            });

        } catch (e) {
            console.error(e);
            showToast("❌ 提取数据出错", true);
        }
    }

    // 初始化
    // 使用 MutationObserver 监听页面变化 (应对 SPA 路由跳转)
    const observer = new MutationObserver((mutations) => {
        checkPage();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // 首次检查
    setTimeout(checkPage, 1000);

})();

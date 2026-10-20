import sys
import re
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
import time

# 🔐 填入你的学号和密码
MY_STUDENT_ID = "这里改成你学号"
MY_PASSWORD = "这里改成你密码"

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        
        print("正在打开抢票页面...")
        page.goto("https://onewechat.bnu.edu.cn/site/ticket/detail?id=1730")
        
        # ================= 自动登录部分 =================
        print("等待页面跳转到登录界面...")
        try:
            page.wait_for_selector("input[placeholder*='账号']", timeout=10000)
            
            account_input = page.locator("input[placeholder*='账号']")
            account_input.click()
            account_input.press_sequentially(MY_STUDENT_ID, delay=50)
            
            password_input = page.locator("input[placeholder*='密码']")
            password_input.click()
            password_input.press_sequentially(MY_PASSWORD, delay=50)
            
            print("✅ 账号密码已填入，尝试登录...")
            page.wait_for_timeout(500)
            
            try:
                login_btn = page.get_by_text("登 录", exact=True)
                if login_btn.count() > 0:
                    login_btn.click(force=True, timeout=3000)
                else:
                    password_input.press("Enter")
            except Exception:
                page.keyboard.press("Enter")
            
            try:
                page.wait_for_url("**/ticket/detail**", timeout=15000)
                print("✅ 登录成功，已返回抢票页！")
            except Exception:
                print("⚠️ 等待跳转超时。如果有滑块请手动完成，等待 20 秒...")
                page.wait_for_timeout(20000)
            
            page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"⚠️ 登录异常: {str(e).splitlines()[0]}")
            print("请手动完成登录，程序等待 30 秒...")
            page.wait_for_timeout(30000) 
        # ================= 自动登录结束 =================
        
        
        # ================= 核心抢票逻辑 =================
        print("\n🚀 登录完成，开始监控并执行抢票...")
        click_count = 0
        target_url = "https://onewechat.bnu.edu.cn/site/ticket/detail?id=1730"
        
        while True:
            try:
                body_text = page.locator("body").inner_text()
                
                # 1. 检查是否抢票成功
                if "取消订阅" in body_text or "已抢到" in body_text or "查看订单" in body_text:
                    print(f"\n🎉🎉 抢票成功！程序已停止。")
                    break 
                
                # 2. 检查是否触发了风控（你截图里的情况）
                if "您的操作过于频繁" in body_text or "稍后再试" in body_text:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ 触发风控限制，等待 2 秒后刷新页面...")
                    page.wait_for_timeout(2000) # 冷却2秒，防止IP被封
                    page.goto(target_url)
                    continue
                
                # 3. 寻找抢票按钮
                btn = page.locator("button, div, a, span").filter(
                    has_text=re.compile(r"^(抢票|立即抢票|立即订阅|订阅)$")
                ).last
                
                # 4. 逻辑分支：如果有按钮（可以抢） vs 没有按钮（还没开始/已抢光）
                if btn.count() > 0 and btn.is_visible():
                    btn_text = btn.inner_text().strip()
                    
                    # 极速暴力点击
                    btn.evaluate("el => el.click()")
                    click_count += 1
                    print(f"[{time.strftime('%H:%M:%S')}] 第 {click_count} 次点击，目标：【{btn_text}】")
                    
                    # 点击时的极速间隔（50ms）
                    page.wait_for_timeout(50)
                    
                else:
                    # 如果没找到按钮（说明票还没放出来，或者页面还在加载）
                    # 这里不要用极速刷新，否则会提前触发风控，建议 1 秒检查一次
                    print(f"[{time.strftime('%H:%M:%S')}] 未发现可抢按钮，等待或刷新中...")
                    page.wait_for_timeout(1000)
                    page.goto(target_url)
                    
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] 循环异常: {str(e).splitlines()[0]}")
                try:
                    page.goto(target_url)
                except:
                    pass
                page.wait_for_timeout(1000)
            
        # ================= 成功后的保持 =================
        print("\n✅ 流程结束，浏览器保持开启。按 Ctrl+C 退出终端。")
        try:
            while True:
                page.wait_for_timeout(10000)
        except KeyboardInterrupt:
            print("程序已退出。")

if __name__ == "__main__":
    run_test()
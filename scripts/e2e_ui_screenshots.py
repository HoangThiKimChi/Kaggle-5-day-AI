import asyncio
import os
import subprocess
import time
import sys
from playwright.async_api import async_playwright

async def main():
    print("Starting FastAPI Backend...")
    env = os.environ.copy()
    env["MOCK_GEMINI"] = "1"
    env["PORT"] = "8000"
    
    # Check if API KEY is set
    if not env.get("GEMINI_API_KEY"):
        # Load from .env
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
            env["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")
        except ImportError:
            pass

    backend = subprocess.Popen(["python3", "scripts/server.py"], env=env, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("Starting Vite Frontend...")
    frontend = subprocess.Popen(["npm", "run", "dev"], cwd=os.path.join(os.path.dirname(os.path.dirname(__file__)), "UI ver 2"))
    
    print("⏳ Waiting 15 seconds for servers to start...")
    await asyncio.sleep(15)
    
    try:
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets/screenshots"), exist_ok=True)
        async with async_playwright() as p:
            print("Launching headless Chromium...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1280, 'height': 900})
            page = await context.new_page()
            
            print("Navigating to http://localhost:5173")
            await page.goto("http://localhost:5173")
            await page.wait_for_timeout(3000)
            
            # Click guest button
            print("Logging in as Guest...")
            await page.click("text=Tiếp tục dùng thử với tư cách khách")
            await page.wait_for_timeout(2000)
            
            scenarios = [
                {
                    "name": "01_classify.png",
                    "text": "Some people think that the best way to reduce crime is to give longer prison sentences. Others, however, believe there are better alternative ways of reducing crime. Discuss both views and give your own opinion.",
                    "wait": 20000
                },
                {
                    "name": "02a_intro_copy_prompt.png",
                    "text": "Some people think that the best way to reduce crime is to give longer prison sentences. Others, however, believe there are better alternative ways of reducing crime.",
                    "wait": 15000
                },
                {
                    "name": "02b_intro_grammar_errors.png",
                    "text": "In nowsaday, crime is become more and more serous in the world. Some peoples think that long prision sentences is the good way to reducing crime but other believe diferent way is more better.",
                    "wait": 15000
                },
                {
                    "name": "02c_intro_off_topic.png",
                    "text": "Education is very important for children in modern society. Schools should focus more on teaching practical skills rather than academic subjects.",
                    "wait": 15000
                },
                {
                    "name": "02d_intro_incomplete.png",
                    "text": "In today's society, crime has become a major concern for many countries around the world.",
                    "wait": 15000
                },
                {
                    "name": "02e_intro_complete.png",
                    "text": "In today's society, the issue of crime and punishment has become a topic of great concern. While some argue that imposing longer prison sentences is the most effective way to reduce crime, others contend that alternative approaches may yield better results. This essay will discuss both perspectives before presenting my own viewpoint.",
                    "wait": 15000
                },
                {
                    "name": "03_brainstorm.png",
                    "text": "Em cần brainstorm ý cho body 1 và body 2",
                    "wait": 15000
                },
                {
                    "name": "04_body1_feedback.png",
                    "text": "On the one hand, supporters of longer prison sentences argue that harsh penalties act as a strong deterrent. When potential criminals are aware that committing a crime could result in many years behind bars, they may think twice before breaking the law. For example, in countries like Singapore, strict punishments have contributed to remarkably low crime rates.",
                    "wait": 15000
                },
                {
                    "name": "05_body2_feedback.png",
                    "text": "On the other hand, many experts believe that addressing the root causes of crime is more effective than simply locking people up. Investing in education programs and community support can help prevent individuals from turning to crime in the first place. Additionally, rehabilitation programs within the justice system can reduce reoffending rates significantly.",
                    "wait": 15000
                },
                {
                    "name": "06_conclusion_feedback.png",
                    "text": "In conclusion, while longer prison sentences may serve as a deterrent in some cases, I believe that a combination of preventive measures and rehabilitation programs would be more effective in reducing crime in the long term.",
                    "wait": 15000
                },
                {
                    "name": "07_scoring_result.png",
                    "text": "Chấm điểm bài viết của em",
                    "wait": 25000,
                    "click_evaluate_tab": True
                }
            ]
            
            for step in scenarios:
                print(f"\n[Scenario] Executing step: {step['name']}")
                
                await page.fill("textarea", step["text"])
                await page.press("textarea", "Enter")
                
                print(f"⏳ Waiting {step['wait']//1000}s for AI response...")
                await page.wait_for_timeout(step["wait"])
                
                # if scoring, maybe we need to click the score tab to show it
                if step.get("click_evaluate_tab"):
                    try:
                        print("Clicking 'Chấm điểm bài viết' button to see score...")
                        await page.click("text=Chấm điểm bài viết")
                        await page.wait_for_timeout(15000)
                    except Exception as e:
                        print(f"Could not click scoring button: {e}")

                screenshot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"assets/screenshots/{step['name']}")
                await page.screenshot(path=screenshot_path)
                print(f"📸 Captured: {screenshot_path}")

            print("✅ All screenshots captured successfully!")
            await browser.close()
    except Exception as e:
        print(f"❌ Automation Error: {e}")
    finally:
        print("Terminating servers...")
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    asyncio.run(main())

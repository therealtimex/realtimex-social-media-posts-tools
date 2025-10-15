# server.py
from fastmcp import FastMCP, Client, Context

import os
import json
import asyncio

from typing import List, Dict, Optional, Union

from .utils import get_cache_dir, crawl4ai_crawl, get_dict_from_content

mcp = FastMCP("RealTimeX.AI Social Media Posts")

@mcp.tool
async def get_brand_list() -> List:
    """Get list of available brands name."""

    brands = None

    brands_data_path = os.path.join(get_cache_dir(),"brands.json")
    if not os.path.exists(brands_data_path):
        return []
    with open(brands_data_path,"r") as f:
        brands = json.load(f)

    return [brand_name for brand_name in brands]

async def func_draft_brand_profile(brand_name:str, homepage_url:str = "", brand_description:str = "") -> Dict:
    """Draft a brand profile based on homepage url or brand description."""

    content = f"Brand name: {brand_name}"
    if brand_description:
        content = f"{content}\nBrand description: {brand_description}"
    if homepage_url:
        homepage_data = await crawl4ai_crawl(homepage_url)
        content = f"{content}\nHome page url: {homepage_url}"
        content = f"{content}\nHome page content: {homepage_data}"
    

    schema = {"name":"brand_profile","title":"Brand Profile","description":"Schema defining brand, content, voice, and platform guidelines.","type":"object","additionalProperties":False,"properties":{"brand_name":{"type":"string","description":"The official product or brand name."},"voice":{"type":"object","description":"Defines the brand's tone, personality, and communication style.","additionalProperties":False,"properties":{"description":{"type":"string","description":"Summary of the voice's overall character."},"traits":{"type":"array","description":"Specific traits or guidelines that define the brand's communication tone.","items":{"type":"string"}}},"required":["description","traits"]},"content_requirements":{"type":"array","description":"Guidelines for creating compliant content for the brand.","items":{"type":"string"}},"prohibited_content":{"type":"array","description":"Types of content or topics that should be strictly avoided.","items":{"type":"string"}},"visual_style":{"type":"object","description":"Describes the visual and design style of brand assets.","additionalProperties":False,"properties":{"description":{"type":"string"},"colors":{"type":"array","items":{"type":"string","pattern":"^#([A-Fa-f0-9]{6})$"},"description":"List of brand colors in hex format."},"preferred_imagery":{"type":"string"},"diagrams":{"type":"string"}},"required":["description","colors","preferred_imagery","diagrams"]},"product_mentions":{"type":"object","description":"Rules for referring to the product in content.","additionalProperties":False,"properties":{"first_mention":{"type":"string"},"subsequent_mentions":{"type":"array","items":{"type":"string"}},"emphasis":{"type":"string"}},"required":["first_mention","subsequent_mentions","emphasis"]},"platforms":{"type":"object","description":"Platform-specific tone, hashtags, and calls to action.","additionalProperties":False,"properties":{"twitter":{"type":"object","additionalProperties":False,"properties":{"tone":{"type":"string"},"hashtags":{"type":"array","items":{"type":"string"}},"cta":{"type":"string"}},"required":["tone","hashtags","cta"]},"instagram":{"type":"object","additionalProperties":False,"properties":{"tone":{"type":"string"},"hashtags":{"type":"array","items":{"type":"string"}},"cta":{"type":"string"}},"required":["tone","hashtags","cta"]},"linkedin":{"type":"object","additionalProperties":False,"properties":{"tone":{"type":"string"},"hashtags":{"type":"array","items":{"type":"string"}},"cta":{"type":"string"}},"required":["tone","hashtags","cta"]}},"required":["twitter","instagram","linkedin"]},"product_features":{"type":"array","description":"List of key product features with benefits and descriptions.","items":{"type":"object","additionalProperties":False,"properties":{"name":{"type":"string"},"description":{"type":"string"},"benefit":{"type":"string"}},"required":["name","description","benefit"]}},"target_audience":{"type":"object","description":"Primary and secondary audiences targeted by the brand.","additionalProperties":False,"properties":{"primary":{"type":"array","items":{"type":"string"}},"secondary":{"type":"array","items":{"type":"string"}}},"required":["primary","secondary"]}},"required":["brand_name","voice","content_requirements","prohibited_content","visual_style","product_mentions","platforms","product_features","target_audience"]}

    brand_profile = get_dict_from_content(prompt=f"Make brand profile for:\n{content}", schema=schema)

    await func_save_brand_profile(brand_name,brand_profile)
    
    return brand_profile

@mcp.tool
async def create_brand_profile(brand_name:str, homepage_url:str = "", brand_description:str = "") -> Dict:
    """Create a brand profile based on homepage url or brand description."""

    return await func_draft_brand_profile(brand_name, homepage_url, brand_description)

async def func_save_brand_profile(brand_name:str, brand_profile:Dict) -> Dict:
    """Save a brand profile by name"""

    brands = None

    brands_data_path = os.path.join(get_cache_dir(),"brands.json")
    try:
        with open(brands_data_path,"r") as f:
            brands = json.load(f)
    except:
        pass

    if not brands:
        brands = {}
    
    brands[brand_name] = brand_profile

    with open(brands_data_path,"w") as f:
        json.dump(brands,f)

    return {"status":"success"}

@mcp.tool
async def save_brand_profile(brand_name:str, brand_profile:Dict) -> Dict:
    """Save a brand profile by name"""

    return await func_save_brand_profile(brand_name,brand_profile)

async def func_get_brand_profile(brand_name:str) -> Union[Dict,None]:
    """Get a brand profile by name"""

    brands = None

    brands_data_path = os.path.join(get_cache_dir(),"brands.json")
    if not os.path.exists(brands_data_path):
        return None

    with open(brands_data_path,"r") as f:
        brands = json.load(f)
    
    if brand_name in brands:
        return brands[brand_name]

    return None

@mcp.tool
async def get_brand_profile(brand_name:str) -> Union[Dict,None]:
    """Get a brand profile by name"""

    return await func_get_brand_profile(brand_name)

@mcp.tool
async def check_linkedin_logged_in() -> Dict:
    """Check if the user is logged in to LinkedIn."""

    from playwright.async_api import async_playwright

    fullname = None
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        if "login" in page.url:
            return {"is_logged_in": False}

        fullname_div = page.locator(".profile-card-name.text-heading-large")
        fullname = await fullname_div.text_content()
        
    return {"is_logged_in": True, "fullname": fullname}

@mcp.tool
async def create_linkedin_post(post_content: str) -> Dict:
    """Create a LinkedIn post."""

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        if "login" in page.url:
            return {
                "status":"failed",
                "errors":[
                    {
                        "message":"Not logged in to LinkedIn."
                    }
                ]
            }
            

        # Click “Start a post”
        post_button = page.locator("#ember53")
        await post_button.click()
        await asyncio.sleep(2)
        await page.wait_for_selector("div.ql-editor")

        # Type the post content
        editor = page.locator("div.ql-editor")
        await editor.fill(post_content)
        await asyncio.sleep(2)

        # Click “Post” button
        post_submit = page.locator("button.share-actions__primary-action")
        await post_submit.click()

        return {
            "status":"success",
            "errors":[
            ],
            "message":"Post published successfully."
        }

# @mcp.tool
# async def check_twitter_logged_in() -> Dict:
#     """Check if the user is logged in to Twitter/X."""

#     from playwright.async_api import async_playwright

#     fullname = None
#     async with async_playwright() as p:
#         browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
#         context = browser.contexts[0] if browser.contexts else await browser.new_context()
#         page = await context.new_page()

#         await page.goto("https://x.com/home", wait_until="domcontentloaded")
#         await asyncio.sleep(2)

#         if "login" in page.url:
#             return {"is_logged_in": False}

#         fullname_div = page.locator(".css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3")
#         fullname = await fullname_div.text_content()
        
#     return {"is_logged_in": True, "fullname": fullname}

# @mcp.tool
# async def create_twitter_post(post_content: str) -> Dict:
#     """Create a Twitter/X post."""

#     from playwright.async_api import async_playwright

#     async with async_playwright() as p:
#         browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
#         context = browser.contexts[0] if browser.contexts else await browser.new_context()
#         page = await context.new_page()

#         await page.goto("https://x.com/home", wait_until="domcontentloaded")
#         await asyncio.sleep(2)

#         if "login" in page.url:
#             return {
#                 "status":"failed",
#                 "errors":[
#                     {
#                         "message":"Not logged in to LinkedIn."
#                     }
#                 ]
#             }
            

#         # Click “Start a post”
#         post_button = page.locator('a[href="/compose/post"]')
#         await post_button.click()
#         await asyncio.sleep(2)
#         await page.wait_for_selector("div.public-DraftEditor-content")

#         # Type the post content
#         editor = page.locator("div.public-DraftEditor-content")
#         await editor.fill(post_content)
#         await asyncio.sleep(2)

#         # Click “Post” button
#         post_submit = page.locator("#layers > div:nth-child(2) > div > div > div > div > div > div.css-175oi2r.r-1ny4l3l.r-18u37iz.r-1pi2tsx.r-1777fci.r-1xcajam.r-ipm5af.r-g6jmlv.r-1habvwh > div.css-175oi2r.r-1wbh5a2.r-htvplk.r-1udh08x.r-1867qdf.r-rsyp9y.r-1pjcn9w.r-1potc6q > div > div > div > div:nth-child(3) > div.css-175oi2r.r-1h8ys4a.r-dq6lxq.r-hucgq0 > div:nth-child(1) > div > div > div > div.css-175oi2r.r-kemksi.r-jumn1c.r-xd6kpl.r-gtdqiz.r-ipm5af.r-184en5c > div:nth-child(2) > div > div > div > button.css-175oi2r.r-sdzlij.r-1phboty.r-rs99b7.r-lrvibr.r-1cwvpvk.r-2yi16.r-1qi8awa.r-3pj75a.r-1loqt21.r-o7ynqc.r-6416eg.r-1ny4l3l")
#         await post_submit.click()

#         return {
#             "status":"success",
#             "errors":[
#             ],
#             "message":"Post published successfully."
#         }

@mcp.tool
async def draft_post_content(brand_name:str, post_content_language:str, platform:str, content_urls: List[str], user_request: Union[str,None] = "") -> Dict:
    """Draft/Create/Write/Rewite a social media post."""

    from .content_creator.content_creator import ContentCreator

    brand_profile = await func_get_brand_profile(brand_name)

    data = ""
    for content_url in content_urls:
        data_url = await crawl4ai_crawl(content_url)
        data = f"{data}\n\n{data_url}"
    if user_request:
        data = f"{data}\n\n{user_request}"
    if post_content_language:
        data = f"{data}\n\nPost Content's Language MUST BE in {post_content_language}"

    if platform.lower() == "x":
        platform = "twitter"

    content_creator = ContentCreator(brand_guidelines=brand_profile,image_generation_enabled=False)
    content = content_creator.generate_content(platform=platform, trend_data={"content":data}, product_info=brand_profile["product_features"])
    return content

# async def run():
#     brand_profile = await func_draft_brand_profile(brand_name="RealTimeX.AI" ,homepage_url="https://realtimex.ai/")
#     print(brand_profile)
#     func_save_brand_profile(brand_name="RealTimeX.AI",brand_profile=brand_profile)

# #     trend_data = {
# #         "content":"""MCP (Model Context Protocol) servers benefit AI agents by providing a standardized way to securely access and integrate with external tools and real-time data, allowing the agents to perform complex, context-aware tasks autonomously. This enables AI agents to be more capable, accurate, and efficient by moving beyond static knowledge to interact with live systems like databases, APIs, and enterprise software. 
# # Key benefits for AI agents
# # Real-time data access: MCP servers connect AI agents to current data from live systems, eliminating reliance on outdated training data for more accurate decisions. 
# # Standardized integration: They provide a common, standardized protocol to connect the AI agent to various tools and systems without needing to write custom API wrappers for each one. 
# # Enhanced capabilities: Agents can perform complex, multi-turn, context-sensitive interactions with external APIs and handle sophisticated workflows that require real-time information. 
# # Improved security and control: MCP servers act as a secure gateway, enforcing authentication, permissions, and auditing to control what the AI agent can access and do. 
# # Faster development: By simplifying integration, MCP servers allow developers to focus on the agent's core logic rather than spending time on custom integrations. 
# # Scalability and flexibility: MCP is a model-agnostic standard that allows agents to use any tool with an MCP server. This promotes a community ecosystem where pre-built servers for common services can be plugged into different AI systems. 
# # Example use case
# # An AI agent tasked with analyzing sales performance could use an MCP server to autonomously perform the following steps: 
# # Use an MCP server to query a sales database for summary statistics.
# # Receive the results and, if more detail is needed, use the same or another MCP server to perform follow-up queries for specific product data.
# # Use a different MCP server to access a CRM to pull customer context for a specific region.
# # Communicate the final, data-rich analysis to the user or another system, all without manual intervention."""
# #     }

# #     product_info = [ { "name": "RealTimeX.AI", "description": "Create, share, and discover new Agents, tools and more to make RealTimeX the only AI tool you need.", "benefit": "Connect to powerful Model Context Protocol servers for enhanced AI capabilities and integrations." } ]

# #     post_content = draft_post_content(brand_profile,trend_data,product_info)
# #     await linkedin_create_post(post_content["text"])

# def main():
#     asyncio.run(run())

def main():
    mcp.run()
    # import asyncio
    # asyncio.run(test())
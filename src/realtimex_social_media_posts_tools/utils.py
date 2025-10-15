import os
import requests

def get_base_user_dir():
    return os.path.expanduser("~")

def get_realtimex_dir():
    return os.path.join(os.path.expanduser("~"),".realtimex.ai")

def get_cache_dir():
    cache_dir = os.path.join(os.path.expanduser("~"),".cache","realtimex-social-media-posts-tools")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def load_env_configs():
    from dotenv import dotenv_values

    env_file_path = os.path.join(get_realtimex_dir(),"Resources","server",".env.development")
    if os.path.exists(env_file_path):
        env_configs = dotenv_values(env_file_path)
        return env_configs
        # if not "LLM_PROVIDER" in env_configs:
        #     return None
        # if env_configs["LLM_PROVIDER"] == "openai":
        #     if "OPEN_AI_KEY" in env_configs:
        #         os.environ['OPENAI_API_KEY'] = env_configs["OPEN_AI_KEY"]
        #         os.environ['OPENAI_BASE_URL'] = "https://api.openai.com/v1"
        # if env_configs["LLM_PROVIDER"] == "realtimexai":
        #     if "REALTIMEX_AI_BASE_PATH" in env_configs and "REALTIMEX_AI_API_KEY" in env_configs:
        #         os.environ['OPENAI_API_KEY'] = env_configs["REALTIMEX_AI_API_KEY"]
        #         os.environ['OPENAI_BASE_URL'] = env_configs["REALTIMEX_AI_BASE_PATH"]
        # if env_configs["LLM_PROVIDER"] == "ollama":
        #     if "OLLAMA_BASE_PATH" in env_configs:
        #         os.environ['OPENAI_API_KEY'] = ""
        #         os.environ['OPENAI_BASE_URL'] = env_configs["OLLAMA_BASE_PATH"]
    return None

def load_llm_configs():
    env_configs = load_env_configs()

    api_key = os.environ.get("OPENAI_API_KEY", default=None)
    base_url = os.environ.get("OPENAI_BASE_URL", default=None)
    
    if env_configs:
        if "LLM_PROVIDER" in env_configs:
            if env_configs["LLM_PROVIDER"] == "openai":
                if "OPEN_AI_KEY" in env_configs:
                    api_key= env_configs["OPEN_AI_KEY"]
                    base_url = "https://api.openai.com/v1"
            if env_configs["LLM_PROVIDER"] == "realtimexai":
                if "REALTIMEX_AI_BASE_PATH" in env_configs and "REALTIMEX_AI_API_KEY" in env_configs:
                    api_key = env_configs["REALTIMEX_AI_API_KEY"]
                    base_url = env_configs["REALTIMEX_AI_BASE_PATH"]
            if env_configs["LLM_PROVIDER"] == "ollama":
                if "OLLAMA_BASE_PATH" in env_configs:
                    api_key = ""
                    base_url= env_configs["OLLAMA_BASE_PATH"]
    return {"api_key":api_key, "base_url":base_url}

async def crawl4ai_crawl(url,format="markdown"):
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

    content = None
    browser_config = BrowserConfig(
        headless=False,
        browser_mode="cdp",
        cdp_url="http://localhost:9222",
        # debugging_port=9222
        verbose=False,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
        )
        if format == "markdown":
            content = result.markdown
    return content

def get_dict_from_content(prompt,schema,system_prompt=None):
    from openai import OpenAI
    import json
    import os

    llm_configs = load_llm_configs()

    client = OpenAI(
        api_key=llm_configs["api_key"],
        base_url=llm_configs["base_url"]
    )
    
    response_format = { "type": "json_schema", "json_schema": {"strict": True, "name": schema["name"], "schema": schema}}

    if not system_prompt:
        system_prompt = f"""You are best at extracting/generating data from content."""
    completion = client.beta.chat.completions.parse(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],

        response_format=response_format,
    )



    data = json.loads(completion.choices[0].message.content)


    return data
"""
Text Generator - Module for generating text content using OpenAI's GPT models.

Handles creating prompts, calling the OpenAI API, and processing responses
for different content types and platforms.
"""

import logging
import os
import json
from openai import OpenAI
from typing import Dict, List, Any, Optional, Union
import time

from .brand_guidelines_manager import BrandGuidelinesManager

from realtimex_social_media_posts_tools.utils import load_llm_configs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TextGenerator")

class TextGenerator:
    """
    Generates text content using OpenAI's GPT models.
    Incorporates brand guidelines and platform-specific requirements.
    """
    
    def __init__(
        self, 
        brand_manager: BrandGuidelinesManager,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        """
        Initialize the TextGenerator.
        
        Args:
            brand_manager: Brand guidelines manager instance
            model: OpenAI model to use
            temperature: Creativity parameter (0.0-1.0)
            max_retries: Maximum number of API call retries
        """
        self.brand_manager = brand_manager
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Load API key from environment variable
        llm_configs = load_llm_configs()
        self.openai = OpenAI(api_key=llm_configs["api_key"],base_url=llm_configs["base_url"])
        
        logger.info("TextGenerator initialized with model: %s", model)
    
    def generate_text(
        self, 
        prompt: str,
        max_length: int = 1000,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text content using the OpenAI API.
        
        Args:
            prompt: The prompt to send to the API
            max_length: Maximum length of generated text
            temperature: Optional override for creativity parameter
            
        Returns:
            Generated text content
        """
        # if not openai.api_key:
        #     raise ValueError("OpenAI API key not configured")
        
        # Use instance temperature if not overridden
        temp = temperature if temperature is not None else self.temperature
        
        # Track retries
        retries = 0
        while retries <= self.max_retries:
            logger.info("Generating text with prompt: %s", prompt[:100] + "..." if len(prompt) > 100 else prompt)
            
            # Call the OpenAI API
            response = self.openai.chat.completions.create(

                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_message()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=temp,
                n=1,
                stop=None
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content.strip()
            
            logger.info("Successfully generated text (%d characters)", len(generated_text))
            return generated_text
                
            
        
        raise Exception(f"Failed to generate text after {self.max_retries} retries")
    
    def _get_system_message(self) -> str:
        """
        Create a system message that includes brand guidelines.
        
        Returns:
            System message string for the OpenAI API
        """
        # Start with a base message
        system_message = (
            "You are a professional social media content creator."
            "Your goal is to create factually accurate, informative, and engaging content "
            "that resonates with the target audience while following brand guidelines."
        )
        
        # Add brand guidelines if available
        if self.brand_manager.guidelines:
            brand_name = self.brand_manager.get_guidelines()["brand_name"]
            if brand_name:
                system_message += f"\n\nALWAYS REMEMBER: You are make social content for {brand_name}, other contents JUST are meterials to make post, ONLY promote {brand_name}."

            brand_voice = self.brand_manager.get_brand_voice()
            if brand_voice:
                system_message += f"\n\nBrand Voice: {brand_voice}"
            
            brand_requirements = self.brand_manager.get_content_requirements()
            if brand_requirements:
                system_message += f"\n\nContent Requirements: {brand_requirements}"
            
            prohibited_content = self.brand_manager.get_prohibited_content()
            if prohibited_content:
                system_message += f"\n\nProhibited Content: {prohibited_content}"
        
        return system_message
    
    def moderate_content(self, content: str) -> bool:
        """
        Use OpenAI's moderation endpoint to check content.
        
        Args:
            content: Text content to check
            
        Returns:
            True if content passes moderation, False otherwise
        """
        try:
            logger.info("Checking content moderation")
            response = openai.Moderation.create(input=content)
            
            # Check if the content was flagged
            result = response.results[0]
            if result.flagged:
                # Log which categories were flagged
                flagged_categories = [
                    category for category, flagged in result.categories.items() 
                    if flagged
                ]
                logger.warning("Content flagged for: %s", ", ".join(flagged_categories))
                return False
            
            return True
            
        except Exception as e:
            logger.error("Error checking content moderation: %s", str(e))
            # Default to True if moderation check fails
            return True 
import datetime
import os
from typing import Union
from dotenv import load_dotenv
from strenum import LowercaseStrEnum
import time

from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, BaseLLMOutputParser
from langchain_core.prompt_values import PromptValue
from langchain.globals import set_llm_cache
from src.config import GOOGLE_API_KEY, OPEN_AI_KEY
# from langchain.cache import InMemoryCache
from langchain_community.cache import InMemoryCache

set_llm_cache(InMemoryCache())

# do you need ChatMessage from langchain? Or pydantic
# todo: shift out google specific stuff. This should have more generic code that can wrap around openai, gemini, etc

class ModelId(LowercaseStrEnum):
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"

DEFAULT_MODEL = ModelId.GEMINI_1_5_FLASH


# load API keys
NUTRI_PROMPT_TEMPLATE_STRING = ("You are a search assistant. The human user will give you a description of their meals, portion size and the time they consumed it. Your task is to analyse the meals, log the date and time of each meal,"
    "and then decompose the meal and its ingredients into their nutrient content. Use google search tool to get nutrient data from https://www.fatsecret.com/calories-nutrition/ if possible. MAke sensible guesses about portions where user does not provide"
    "Output the amount of carbohydrates, fats, proteins in grams, and calories in integer without making unit explicit"
    # "Please give a unique id to each meal, that is repeated across its components."
    "Answer with the nutritional breakdown of the meal in a json format (and nothing else) as "
    "[\{{\'Column1': 'Value1', 'Column2': 'Value2', 'Column3': 'Value3'\}},"
    "\{{\'Column1': 'Value4', 'Column2': 'Value5', 'Column3': 'Value6'\}}]"
    "The following are the key/column names, and you must extract the value from the meal analysis"
    #"- meal_id"
    "- date"
    "- time"
    "- meal_component"
    "- quantity_per_serving"
    "- carbohydrates"
    "- protein"
    "- fat"
    "- calories"
    "Only answer with the json key-value list, and nothing else.")


SAMPLE_MEAL_DESCRIPTION_STRING = ("Today is 2025-02-25. At noon I ate 1 sandwich made from 2 slices brown bread, tomato,"
                        "1 slice of cheese and cucumber. At dinner 9pm, I ate 2 rotis with 1 bowl (100g) of chicken curry and 1 bowl of raita.")


def prepare_prompt(prompt_template_string: str = NUTRI_PROMPT_TEMPLATE_STRING,
                   meal_description_string: str = SAMPLE_MEAL_DESCRIPTION_STRING,
                   system_date: Union[None, str, datetime.datetime.date] = None,
                   parser: BaseLLMOutputParser = JsonOutputParser) -> PromptValue:

    prompt_template = PromptTemplate(
        template=prompt_template_string + "{format_instructions}" + "\n{meal_description_string}\n"
        + f" If and only if the user is not specific about the date, then instead use the knowledge that the system logged date is {system_date}",
        input_variables=["meal_description_string", "system_date"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    # Generate the prompt
    filled_prompt = prompt_template.invoke({"meal_description_string": meal_description_string,
                                            "system_date": system_date})

    return filled_prompt


def prompt_llm_for_response(user_input_meal_description_string: str,
                            user_input_date: Union[None, datetime.datetime] = None,
                            model = DEFAULT_MODEL,
                            api_key = GOOGLE_API_KEY):
    # Define custom GenerateContentConfig parameters
    client_options = {
        "temperature": 0.0,  # Controls randomness
        "max_output_tokens": 1000,  # Limit on output tokens
        # "stop_sequences": ["STOP"],  # Optional stop sequences,
        "top_p": 0.95,
        "top_k": 20,
    }

    parser = JsonOutputParser()
    filled_prompt = prepare_prompt(meal_description_string=user_input_meal_description_string,
                                   system_date = user_input_date,
                                   parser=parser,
                                   prompt_template_string=NUTRI_PROMPT_TEMPLATE_STRING
                                   )

    google_search_tool = Tool(
        google_search=GoogleSearch()
    )

    start_time = time.time()
    # Initialize ChatGoogleGenerativeAI with client options
    llm = ChatGoogleGenerativeAI(
        model = model,
        google_api_key = api_key,
        config = GenerateContentConfig(
            tools = [google_search_tool],
            response_modalities=["TEXT"]
        ),
        **client_options,
    )
    # client_options =  {'generate_content_config': {'max_output_tokens': 100}})

    # Invoke the model with a prompt
    response = llm.invoke(filled_prompt.text)

    # print(response.content)
    end_time = time.time()
    print(f"Execution time duration: {end_time - start_time} ")
    parsed_json = parser.parse(response.content)
    return parsed_json

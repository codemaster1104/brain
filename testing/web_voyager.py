import asyncio
import base64
import platform
import re
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
import requests
from langchain.llms.base import LLM
from langchain.schema import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables import chain as chain_decorator
from langgraph.graph import END, START, StateGraph
from playwright.async_api import Page, async_playwright

# Custom LLM implementations
class CustomLLM(LLM):
    api_base_url: str = "https://llama.us.gaianet.network/v1"
    model_name: str = "llama"
    api_key: str = "GAIA"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000  
        }
        if stop:
            payload["stop"] = stop

        response = requests.post(f"{self.api_base_url}/completions", json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["text"].strip()  
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    @property
    def _identifying_params(self):
        return {"model_name": self.model_name}

    @property
    def _llm_type(self):
        return "custom_llama"

class CustomLLM2(LLM): 
    api_base_url: str = "https://llamatool.us.gaianet.network/v1"
    model_name: str = "llama"
    api_key: str = "GAIA"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 1000  
        }
        if stop:
            payload["stop"] = stop

        response = requests.post(f"{self.api_base_url}/completions", json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["text"].strip() 
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    @property
    def _llm_type(self) -> str:
        return "custom_llama"
    
llama_llm = CustomLLM()
llama_tool = CustomLLM2()

# Type definitions
class BBox(TypedDict):
    x: float
    y: float
    text: str
    type: str
    ariaLabel: str

class Prediction(TypedDict):
    action: str
    args: Optional[List[str]]

class AgentState(TypedDict):
    page: Page
    input: str
    img: str
    bboxes: List[BBox]
    prediction: Prediction
    scratchpad: List[BaseMessage]
    observation: str

# Tools
async def click(state: AgentState):
    page = state["page"]
    click_args = state["prediction"]["args"]
    if click_args is None or len(click_args) != 1:
        return f"Failed to click bounding box labeled as number {click_args}"
    bbox_id = int(click_args[0])
    try:
        bbox = state["bboxes"][bbox_id]
    except IndexError:
        return f"Error: no bbox for : {bbox_id}"
    x, y = bbox["x"], bbox["y"]
    await page.mouse.click(x, y)
    return f"Clicked {bbox_id}"

async def type_text(state: AgentState):
    page = state["page"]
    type_args = state["prediction"]["args"]
    if type_args is None or len(type_args) != 2:
        return f"Failed to type in element from bounding box labeled as number {type_args}"
    bbox_id = int(type_args[0])
    bbox = state["bboxes"][bbox_id]
    x, y = bbox["x"], bbox["y"]
    text_content = type_args[1]
    await page.mouse.click(x, y)
    select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
    await page.keyboard.press(select_all)
    await page.keyboard.press("Backspace")
    await page.keyboard.type(text_content)
    await page.keyboard.press("Enter")
    return f"Typed {text_content} and submitted"

async def scroll(state: AgentState):
    page = state["page"]
    scroll_args = state["prediction"]["args"]
    if scroll_args is None or len(scroll_args) != 2:
        return "Failed to scroll due to incorrect arguments."

    target, direction = scroll_args
    scroll_amount = 500 if target.upper() == "WINDOW" else 200
    scroll_direction = -scroll_amount if direction.lower() == "up" else scroll_amount

    if target.upper() == "WINDOW":
        await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
    else:
        target_id = int(target)
        bbox = state["bboxes"][target_id]
        x, y = bbox["x"], bbox["y"]
        await page.mouse.move(x, y)
        await page.mouse.wheel(0, scroll_direction)

    return f"Scrolled {direction} in {'window' if target.upper() == 'WINDOW' else 'element'}"

async def wait(state: AgentState):
    sleep_time = 5
    await asyncio.sleep(sleep_time)
    return f"Waited for {sleep_time}s."

async def go_back(state: AgentState):
    page = state["page"]
    await page.go_back()
    return f"Navigated back a page to {page.url}."

async def to_google(state: AgentState):
    page = state["page"]
    await page.goto("https://www.google.com/")
    return "Navigated to google.com."

# Helper functions
with open("testing/mark_page.js") as f:
    mark_page_script = f.read()

@chain_decorator
async def mark_page(page):
    await page.evaluate(mark_page_script)
    for _ in range(10):
        try:
            bboxes = await page.evaluate("markPage()")
            break
        except Exception:
            await asyncio.sleep(3)
    else:
        raise Exception("Failed to mark page after multiple attempts")
    screenshot = await page.screenshot()
    await page.evaluate("unmarkPage()")
    return {
        "img": base64.b64encode(screenshot).decode(),
        "bboxes": bboxes,
    }

async def annotate(state):
    marked_page = await mark_page.with_retry().ainvoke(state["page"])
    return {**state, **marked_page}

def format_descriptions(state):
    labels = []
    for i, bbox in enumerate(state["bboxes"]):
        text = bbox.get("ariaLabel") or bbox["text"]
        el_type = bbox.get("type")
        labels.append(f'{i} (<{el_type}/>): "{text}"')
    bbox_descriptions = "\nValid Bounding Boxes:\n" + "\n".join(labels)
    return {**state, "bbox_descriptions": bbox_descriptions}

def parse(text: str) -> dict:
    action_prefix = "Action: "
    if not text.strip().split("\n")[-1].startswith(action_prefix):
        return {"action": "retry", "args": f"Could not parse LLM Output: {text}"}
    action_block = text.strip().split("\n")[-1]
    action_str = action_block[len(action_prefix):]
    split_output = action_str.split(" ", 1)
    action = split_output[0].strip()
    action_input = split_output[1].strip().strip("[]").split(";") if len(split_output) > 1 else None
    return {"action": action, "args": action_input}

def update_scratchpad(state: AgentState):
    old = state.get("scratchpad")
    if old:
        txt = old[0].content
        last_line = txt.rsplit("\n", 1)[-1]
        step = int(re.match(r"\d+", last_line).group()) + 1
    else:
        txt = "Previous action observations:\n"
        step = 1
    txt += f"\n{step}. {state['observation']}"
    return {**state, "scratchpad": [SystemMessage(content=txt)]}

def observation(state: AgentState, observation: str):
    return {**state, "observation": observation}

def create_next_prompt(state: AgentState):
    return {
        **state,
        "input": f"""
You are controlling a browser. You need to select UI elements and input text as requested.
Goal: {state['input']}

{state['bbox_descriptions']}
{state['scratchpad'][0].content}
What will you do next?
Respond in the format: Action: [action] [args].\n"""
    }

graph_builder = (
    StateGraph.builder()
    .add_node(START, annotate)
    .add_node("annotate", annotate)
    .add_node("describe", format_descriptions)
    .add_node("llm", llama_llm)
    .add_node("parse", RunnableLambda(lambda x: parse(x["input"])))
    .add_node("call_agent", llama_tool)
    .add_node(END, lambda _: "done")
    .add_edge(START, "annotate")
    .add_edge("annotate", "describe")
    .add_edge("describe", "llm")
    .add_edge("llm", "parse")
    .add_edge("parse", "call_agent")
    .add_edge("call_agent", END)
)

# Compile the graph
graph = graph_builder.compile()

# The function to call the agent
async def call_agent(state: AgentState):
    updated_state = await graph(state)
    return updated_state

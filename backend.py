import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Literal
from datetime import datetime
from pydantic import BaseModel
import os
import pandas as pd
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from openai import OpenAI
from langchain_openai import ChatOpenAI
import base64
from langchain_openai import ChatOpenAI
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3
)

class EventAnalysis(BaseModel):
    intent: str
    sentiment: str
    painpoints: List[str]

class AdState(TypedDict):
    user_id: str
    event: dict
    user_data: dict
    intent: str
    sentiment: str
    painpoints: List[str]
    campaign_strategy: str
    selected_channel: Literal["Email", "SMS", "Whatsapp"]
    message_content: str
    image_prompt: str
    image_url: dict


def log_event(state: AdState):
    logger.info("📌 Event logged")
    return {}

def crm_verifier(state: AdState):
    try:
        crm = pd.read_csv("crm.csv")
        row = crm[crm["user_id"] == state["user_id"]]
        logger.info("👤 CRM verified")
        return {"user_data": row.iloc[0].to_dict()} if not row.empty else {"user_data": {}}
    except:
        logger.warning("⚠️ CRM not found")
        return {"user_data": {}}

def extract_event(state: AdState):
    logger.info("🧠 Extracting intent")
    structured = llm.with_structured_output(EventAnalysis)
    prompt=f'''You are a marketing expert and you have been assigned the task of extracting the intent,sentiment 
    and painpoints from the {state['event']} and the {state['user_data']}.
    Give the output in structured output format only.'''
    response = structured.invoke(prompt)
    return {
        'intent':response.intent,
        'painpoints':response.painpoints,
        'sentiment':response.sentiment
    }

def campaign_strategy(state: AdState):
    logger.info("📈 Creating campaign strategy")
    prompt=f'''You are a marketing expert and 
    your task is to extract the campaign strategy from the {state['intent']},{state['sentiment']},{state['event']} 
    and the {state["user_data"]}.Return the answer like you are a pro marketing head'''

    response = llm.invoke(prompt)
    return {"campaign_strategy": response.content}

def select_channel(state: AdState):
    logger.info("📡 Selecting channel")
    return {"selected_channel": "Email"}

def generate_message(state: AdState):
    logger.info("✉️ Generating professional marketing email content")

    prompt = f"""
You are a senior marketing copywriter at a premium e-commerce brand.

Write a COMPLETE, READY-TO-SEND marketing email using the information below.

STRICT RULES (VERY IMPORTANT):
- Do NOT use placeholders like [Customer Name], [Insert Date], [Your Company]
- Do NOT ask the user to fill anything
- Do NOT mention social media handles unless relevant
- Do NOT include unnecessary fluff
- Write in a confident, professional, polished tone
- Use short paragraphs (2–3 lines max)
- Make it feel personalized but generic-safe
- Assume the recipient already knows the brand

Campaign Strategy:
{state['campaign_strategy']}

User Intent:
{state['intent']}

User Sentiment:
{state['sentiment']}

Pain Points:
{state['painpoints']}

STRUCTURE THE EMAIL EXACTLY LIKE THIS:
1. Strong subject-style opening line
2. Short intro paragraph
3. Value proposition paragraph
4. Offer / benefit paragraph (mention limited-time urgency if relevant)
5. Clear call-to-action sentence
6. Polite closing line

Output ONLY the email body text.
No subject line.
No markdown.
No bullet points.
"""

    response = llm.invoke(prompt)
    return {"message_content": response.content}


def generate_image_prompts(state: AdState):
    logger.info("🖼️ Generating image prompts")
    prompt = f"""
You are a senior creative director designing high-converting digital advertisement images for an e-commerce brand.

Your task is to generate a SINGLE, DETAILED image prompt for an AI image generation model.

IMAGE OBJECTIVE:
Create a professional marketing advertisement image that clearly promotes the product and highlights a special offer.

CONTEXT:
Campaign Strategy:
{state["campaign_strategy"]}

Marketing Message:
{state["message_content"]}

MANDATORY REQUIREMENTS:
- The product must be the visual focus of the image
- The image must clearly display a promotional offer such as:
  “Flat 10% OFF”, “Limited Time Offer”, “This Friday Only”, or “Seasonal Sale”
- Offer text must be bold, readable, and visually prominent
- Image must look like a real e-commerce ad banner
- Clean, premium, modern aesthetic
- Studio lighting, high clarity, sharp details
- No cluttered background

DESIGN STYLE GUIDELINES:
- Professional marketing photography style
- Balanced composition with space for offer text
- Product centered or slightly offset for visual appeal
- Brand-safe, minimal, high-conversion design
- No people unless appropriate for the product
- White or soft gradient background preferred

TEXT IN IMAGE (IMPORTANT):
Include visible ad-style text such as:
“Special Offer”
“10% OFF – Limited Time”
“Shop Now”

OUTPUT FORMAT:
Return ONLY a single, complete image generation prompt.
Do NOT explain.
Do NOT add variations.
"""

    response = llm.invoke(prompt)
    return {"image_prompt": response.content}

client = OpenAI()

def generate_images(state: AdState):
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=state["image_prompt"],
            size="1024x1024"
            )
        img = base64.b64decode(response.data[0].b64_json)
        path = "ad.png"
        with open(path, "wb") as f:
            f.write(img)
    except Exception as e:
        logger.warning(f"⚠️ Image fallback: {e}")
    return{
        'image_url':path
    }


from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
    ContentId
)
import base64
import os

def send_email(state: AdState):
    logger.info("📧 Sending email with image")

    try:

        image_path = state["image_url"] 

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        encoded_image = base64.b64encode(image_bytes).decode()

        attachment = Attachment(
            FileContent(encoded_image),
            FileName("ad.png"),
            FileType("image/png"),
            Disposition("inline"),
            ContentId("adimage")
        )

        html_content = f"""
        <html>
        <body style="font-family:Arial, sans-serif;">
            <h2>🎯 Personalized Offer Just For You</h2>

            <p>{state["message_content"]}</p>

            <br>

            <img src="cid:adimage" width="600" style="border-radius:12px;" />

            <br><br>
            <p style="color:gray;font-size:12px;">
                Offer valid for a limited time only.
            </p>
        </body>
        </html>
        """

        msg = Mail(
            from_email="aryushtripathi11@gmail.com",
            to_emails="22mm02002@iitbbs.ac.in",
            subject="🎯 Personalized Offer",
            html_content=html_content
        )

        msg.attachment = attachment

        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(msg)

        logger.info("✅ Email sent with embedded image")

    except Exception as e:
        logger.error(f"❌ Email failed: {e}")

    return {}



graph = StateGraph(AdState)

graph.add_node("Log_Event", log_event)
graph.add_node("CRM_Verifier", crm_verifier)
graph.add_node("Extract_Event", extract_event)
graph.add_node("Campaign_Strategy", campaign_strategy)
graph.add_node("Select_Channel", select_channel)
graph.add_node("Generate_Message", generate_message)
graph.add_node("Generate_Image_Prompts", generate_image_prompts)
graph.add_node("Generate_Images", generate_images)
graph.add_node("Send_Email", send_email)

graph.add_edge(START, "Log_Event")
graph.add_edge("Log_Event", "CRM_Verifier")
graph.add_edge("CRM_Verifier", "Extract_Event")
graph.add_edge("Extract_Event", "Campaign_Strategy")
graph.add_edge("Campaign_Strategy", "Select_Channel")
graph.add_edge("Select_Channel", "Generate_Message")
graph.add_edge("Generate_Message", "Generate_Image_Prompts")
graph.add_edge("Generate_Image_Prompts", "Generate_Images")
graph.add_edge("Generate_Images", "Send_Email")
graph.add_edge("Send_Email", END)

workflow = graph.compile(checkpointer=MemorySaver())

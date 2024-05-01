import asyncio
import aiohttp
import uuid
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from datetime import datetime
import discord
from redbot.core import commands
import uvicorn

baseURL = "https://chat.openai.com"
tokenURL = f"{baseURL}/backend-anon/sentinel/chat-requirements"
apiURL = f"{baseURL}/backend-anon/conversation"
sessionID = ""
token = ""
sessionReset = 60
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "oai-language": "en-US",
    "origin": baseURL,
    "pragma": "no-cache",
    "referer": baseURL,
    "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
}

def getnewUUID():
    newDeviceID = uuid.uuid1()
    return str(newDeviceID)

async def getNewSessionToken():
    newID = getnewUUID()
    global sessionID, token, sessionReset
    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            try:
                async with session.post(tokenURL, headers={"oai-device-id": newID}) as response:
                    res = await response.json()
                    sessionID = newID
                    token = res["token"]
                await asyncio.sleep(sessionReset)
            except Exception as e:
                await asyncio.sleep(sessionReset)

async def conversation(message:str):
    global sessionID, token
    
    convHeaders = headers
    
    convHeaders["accept"] = "text/event-stream"
    convHeaders["oai-device-id"] = sessionID
    convHeaders["openai-sentinel-chat-requirements-token"] = token
    
    body = {
        "action": "next",
        "messages": [
            {
                "id": getnewUUID(),
                "author": {
                    "role": "user"
                },
                "content": {
                    "content_type": "text",
                    "parts": [
                        message
                    ]
                },
                "metadata": {}
            }
        ],
        "parent_message_id": getnewUUID(),
        "model": "text-davinci-002-render-sha",
        "timezone_offset_min": -420,
        "suggestions": [],
        "history_and_training_disabled": False,
        "conversation_mode": {
            "kind": "primary_assistant"
        },
        "force_paragen": False,
        "force_paragen_model_slug": "",
        "force_nulligen": False,
        "force_rate_limit": False,
        "websocket_request_id": getnewUUID()
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(apiURL, headers=convHeaders, data=json.dumps(body)) as response:
                async for event in response.content:
                    event_json = json.dumps(event.decode("utf-8").replace("data: ", "").replace("\n", ""))
                    event_json = json.loads(event_json)
                    if str(event_json).startswith("{"):
                        lineDict = json.loads(event_json)
                        data = {
                            "id": "chatcmpl-free",
                            "object": "chat.completion",
                            "created": datetime.now().strftime("%d%m%Y%H%M%S"),
                            "model": "gpt-3.5-turbo-0613",
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0
                            },
                            "choices": [
                                {
                                    "message": {
                                        "role": "assistant",
                                        "content": lineDict["message"]["content"]["parts"][0]
                                    },
                                    "finish_reason": "stop",
                                    "index": 0
                                }
                            ]
                        }
                        yield json.dumps(data).encode("utf-8")
                        yield "\n"
                else:
                    yield "[DONE]".encode("utf-8")
    except Exception as e:
        data = json.dumps({
            "id": "chatcmpl-free",
            "object": "chat.completion",
            "created": datetime.now().strftime("%d%m%Y%H%M%S"),
            "model": "gpt-3.5-turbo-0613",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "There's a problem when requesting to ChatGPT"
                    },
                    "finish_reason": "error",
                    "index": 0
                }
            ]
        }).encode("utf-8")
        yield data
        yield "\n"

app = FastAPI()

@app.post("/v1/chat/completions")
async def conversationStream(message):
    return StreamingResponse(conversation(message), media_type="text/event-stream")
    
@app.on_event("startup")
async def startup():
    asyncio.create_task(getNewSessionToken())

class BetaAlpha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start_fastapi(self):
        config = uvicorn.Config(app, host="localhost", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def cog_unload(self):
        asyncio.create_task(self.stop_fastapi())

    async def stop_fastapi(self):
        # Implement the logic to gracefully stop the FastAPI server here
        pass

    @commands.command()
    async def testgpt(self, ctx, *, message: str):
        """Query the ChatGPT API with the provided message."""
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8000/v1/chat/completions", data=message) as response:
                if response.status == 200:
                    async for chunk in response.content:
                        chunk = chunk.decode("utf-8")
                        if chunk.strip() == "[DONE]":
                            break
                        if chunk.startswith("data:"):
                            chunk = chunk[5:]
                        chunk_data = json.loads(chunk)
                        content = chunk_data["choices"][0]["message"]["content"]
                        await ctx.send(content)
                else:
                    await ctx.send("An error occurred while querying the ChatGPT API.")

def setup(bot):
    cog = BetaAlpha(bot)
    asyncio.create_task(cog.start_fastapi())
    bot.add_cog(cog)

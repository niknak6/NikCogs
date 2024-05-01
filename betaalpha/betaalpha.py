import asyncio
import aiohttp
import uuid
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import discord
from redbot.core import commands
import uvicorn
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('red.betaalpha')

# Define the FastAPI app
app = FastAPI()

# Global variables for session management
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
    return str(uuid.uuid1())

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
                logger.error(f"Error in getNewSessionToken: {e}")
                await asyncio.sleep(sessionReset)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(getNewSessionToken())

@app.post("/v1/chat/completions")
async def conversationStream(message: str):
    logger.info(f"Received message for completion: {message}")
    return StreamingResponse(conversation(message), media_type="text/event-stream")

async def conversation(message: str):
    global sessionID, token
    
    convHeaders = headers.copy()
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
    
    async with aiohttp.ClientSession(headers=convHeaders) as session:
        async with session.post(apiURL, json=body) as response:
            async for line in response.content:
                line = line.decode("utf-8")
                if line == "[DONE]":
                    break
                else:
                    data = json.loads(line)
                    try:
                        content = data["choices"][0]["message"]["content"]
                        yield content
                    except Exception as e:
                        logger.error(f"Error processing conversation stream: {e}")

class BetaAlpha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_task = None

    async def start_fastapi(self):
        try:
            config = uvicorn.Config(app=app, host="localhost", port=8000, log_level="info")
            server = uvicorn.Server(config)
            logger.info("Starting FastAPI server...")
            await server.serve()
            logger.info("FastAPI server started successfully.")
        except Exception as e:
            logger.error(f"Failed to start FastAPI server: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.server_task = asyncio.create_task(self.start_fastapi())
        logger.info("FastAPI server task started.")

    @commands.Cog.listener()
    async def on_cog_unload(self):
        if self.server_task:
            logger.info("Cancelling server task.")
            self.server_task.cancel()

    @commands.command()
    async def testgpt(self, ctx, *, message: str):
        if self.server_task and not self.server_task.done():
            await ctx.send("Server is still starting, please wait a moment and try again.")
            return
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post("http://localhost:8000/v1/chat/completions", params={"message": message}, timeout=None) as response:
                        if response.status == 200:
                            fulltext = ""
                            async for chunk in response.content:
                                chunk = chunk.decode("utf-8")
                                if chunk == "[DONE]":
                                    break
                                else:
                                    data = json.loads(chunk)
                                    try:
                                        fulltext += data["choices"][0]["message"]["content"]
                                    except Exception as e:
                                        logger.error(f"Error processing response from server: {e}")
                            await ctx.send(fulltext)
                            break
                        else:
                            await ctx.send("An error occurred while querying the ChatGPT API.")
            except aiohttp.ClientConnectorError as e:
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(1)  # Wait a second before retrying
                    continue
                else:
                    await ctx.send("Failed to connect to the server after several attempts.")
                    logger.error(f"Connection to server failed: {e}")
                    break

def setup(bot):
    bot.add_cog(BetaAlpha(bot))

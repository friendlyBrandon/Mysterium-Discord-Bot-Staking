import discord
import asyncio
import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import os
import tempfile
import concurrent.futures
from datetime import datetime

# Replace these with your bot token and channel ID
TOKEN = 'YOUR_BOT_TOKEN' # Replace with your own bot its token, also give the bot admin perms
CHANNEL_ID = 123456789  # Replace with the actual channel ID

intents = discord.Intents.default()
intents.messages = True  # Required for sending messages
intents.guilds = True    # Required for accessing channels

client = discord.Client(intents=intents)

# Initialize history for each metric
history = {
    'myst_balance': [],
    'myst_staked_amount': [],
    'myst_pending_rewards': []
}

# Store the latest message object
latest_message = None

# Store the latest graph message object
graph_message = None

# Helper to delete error messages after 5 minutes
async def delete_error_message(message):
    try:
        await asyncio.sleep(300)  # 5 minutes
        await message.delete()
    except discord.NotFound:
        pass  # Message was deleted already
    except Exception as e:
        print(f"Failed to delete error message: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found! Check the ID and permissions.")
        return
    asyncio.create_task(fetch_and_send(channel))

async def fetch_and_send(channel):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get('http://localhost:8000') as response:
                    if response.status == 200:
                        data = await response.text()
                        metrics = parse_metrics(data)
                        for metric_name, value in metrics.items():
                            if metric_name in history:
                                history[metric_name].append(value)
                                if len(history[metric_name]) > 30:
                                    history[metric_name].pop(0)
                        await send_message(channel, metrics)
                        await send_graphs(channel)
                    else:
                        await channel.send(f"Failed to fetch data. HTTP Status: {response.status}")
            except Exception as e:
                error_message = await channel.send(f"Error fetching data: {str(e)}")
                asyncio.create_task(delete_error_message(error_message))
            await asyncio.sleep(60)  # Wait 1 minute

def parse_metrics(data):
    lines = data.splitlines()
    metrics = {}
    for line in lines:
        if line.startswith('myst_balance'):
            metrics['myst_balance'] = float(line.split()[1])
        elif line.startswith('myst_staked_amount'):
            metrics['myst_staked_amount'] = float(line.split()[1])
        elif line.startswith('myst_pending_rewards'):
            metrics['myst_pending_rewards'] = float(line.split()[1])
    return metrics

async def send_message(channel, metrics):
    message = "**Current Data from localhost:8000**\n"
    for metric_name, value in metrics.items():
        if len(history[metric_name]) >= 2:
            delta = value - history[metric_name][-2]
            message += f"{metric_name}: {value:.10f} MYST. +{delta:.10f} MYST in the last minute.\n"
        else:
            message += f"{metric_name}: {value:.10f} MYST.\n"
    
    # Add USD values for staked and pending rewards
    if 'myst_staked_amount' in metrics and 'myst_pending_rewards' in metrics:
        try:
            price = await get_myst_price()
            staked_usd = metrics['myst_staked_amount'] * price
            pending_usd = metrics['myst_pending_rewards'] * price
            message += f"Staked USD Value: ${staked_usd:.2f}\n"
            message += f"Pending Rewards USD Value: ${pending_usd:.2f}\n"
        except Exception as e:
            message += f"Failed to fetch USD value for staked MYST: {str(e)}\n"
    
    # Add timestamp
    message += f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # Update the latest message if it exists, else send a new one
    global latest_message
    if latest_message:
        await latest_message.edit(content=message)
    else:
        latest_message = await channel.send(message)

async def get_myst_price():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.coingecko.com/api/v3/simple/price?ids=mysterium&vs_currencies=usd') as response:
            if response.status == 200:
                data = await response.json()
                return data['mysterium']['usd']
            else:
                raise Exception(f"Failed to fetch price: HTTP {response.status}")

async def send_graphs(channel):
    global graph_message
    if graph_message:
        await graph_message.delete()
    
    if 'myst_pending_rewards' in history and len(history['myst_pending_rewards']) > 0:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tmpfile_path = await asyncio.get_event_loop().run_in_executor(
                executor, generate_graph, 'myst_pending_rewards', history['myst_pending_rewards']
            )
            graph_message = await channel.send(file=discord.File(tmpfile_path))

def generate_graph(metric_name, values):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
        tmpfile_path = tmpfile.name
        plt.figure(figsize=(10, 5))
        plt.plot(values, marker='o', linestyle='-', color='blue')
        plt.title(f"{metric_name} Over Time")
        plt.xlabel("Time (minutes)")
        plt.ylabel("Value")
        plt.grid(True)
        plt.savefig(tmpfile_path)
        plt.close()
        return tmpfile_path

# Run the bot
client.run(TOKEN)

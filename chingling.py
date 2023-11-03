import discord
from discord.ext import commands, tasks
import datetime
import requests
import json

def load_config():
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        print("Arquivo config.json não encontrado.")
        return None
    except json.JSONDecodeError:
        print("Erro ao decodificar o arquivo config.json.")
        return None

config = load_config()

if config is None:
    exit()

repository_owner = config.get("repository_owner")
repository_name = config.get("repository_name")
github_token = config.get("github_token")
bot_token = config.get("bot_token")

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

pulls = "pulls_cache.json"

try:
    with open(pulls, "r") as f:
        notified_pull_requests = set(json.load(f))
except (FileNotFoundError, json.JSONDecodeError):
    notified_pull_requests = set()

merges = "merge_cache.json"

try:
    with open(merges, "r") as f:
        notified_merges = set(json.load(f))
except (FileNotFoundError, json.JSONDecodeError):
    notified_merges = set()

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    check_pull_requests.start() 
    print("Verificação de pull requests iniciada.")

@tasks.loop(minutes=1)
async def check_pull_requests():
    try:
        channel_id = #ID do Canal do Discord

        channel = bot.get_channel(channel_id)
        if channel:
            print(f"Verificando pull requests e merges em {repository_owner}/{repository_name}...")

            pull_requests = get_pull_requests()
            for pr in pull_requests:
                if pr['id'] not in notified_pull_requests:
                    await channel.send(format_pull_request(pr))
                    notified_pull_requests.add(pr['id'])

            closed_pulls = get_merges()
            for pr in closed_pulls:
                if pr['id'] not in notified_merges:
                    await channel.send(format_merges(pr))
                    notified_merges.add(pr['id'])

        with open(pulls, "w") as f:
            json.dump(list(notified_pull_requests), f)
                    
        with open(merges, "w") as f:
            json.dump(list(notified_merges), f)

    except Exception as e:
        print(f"Erro na tarefa de verificação de pull requests: {e}")

def format_pull_request(pr):
    body = pr['body'] if pr['body'] else "Nenhuma descrição fornecida."
    return f"**Pull Request Aberto #{pr['number']}**\n" \
           f"Título: {pr['title']}\n" \
           f"Autor: {pr['user']['login']}\n" \
           f"Comentário: {body}\n" \
           f"--------------------------"

def format_merges(pr):
    body = pr['body'] if pr['body'] else "Nenhuma descrição fornecida."
    merged_time = datetime.datetime.strptime(pr['merged_at'], "%Y-%m-%dT%H:%M:%SZ") if pr.get("merged_at") else None
    formatted_time = merged_time.strftime("%Y-%m-%d %H:%M:%S") if merged_time else "Não encontrado."
    return f"**Merged with Main #{pr['number']}**\n" \
           f"Título: {pr['title']}\n" \
           f"Autor: {pr['user']['login']}\n" \
           f"Comentário: {body}\n" \
           f"Data de merge: {formatted_time}\n" \
           f"--------------------------"

def get_pull_requests():
    url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/pulls"
    headers = {"Authorization": f"Bearer {github_token}"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_merges():
    url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/pulls?state=closed&sort=updated&direction=desc"
    headers = {"Authorization": f"Bearer {github_token}"}
    response = requests.get(url, headers=headers)
    return response.json()

bot.run(bot_token)

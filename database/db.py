import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Fonction synchronisée pour récupérer les configurations utilisateur.
def fetch_user_configs_sync():
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')
    table = dynamodb.Table('Users') 
    response = table.scan()
    return response['Items']

# Wrapper asynchrone autour de la fonction synchronisée.
async def fetch_user_configs():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, fetch_user_configs_sync)

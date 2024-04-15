import asyncio
from database.db import fetch_user_configs
from strategies.envelopes.strategie_a import execute_strategy_a_for_user
from utilities.bitget_perp import PerpBitget


async def main():
    # Assurez-vous que fetch_user_configs est une fonction asynchrone si nécessaire
    user_configs = fetch_user_configs()

    for account_config in user_configs:
        # Initialiser l'objet PerpBitget une seule fois par utilisateur
        exchange = PerpBitget(
            public_api=account_config["public_key"],
            secret_api=account_config["secret_key"],
            password=account_config.get("password_api", ""),
        )


        if account_config["strategy"] == "A":
            await execute_strategy_a_for_user(account_config, exchange)
        else:    
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())



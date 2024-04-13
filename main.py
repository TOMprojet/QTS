import asyncio
from database.db import fetch_user_configs
from strategies.envelopes.strategie_a import execute_strategy_a_for_user
from strategies.bolltrend.strategie_b import execute_strategy_b_for_user
from utilities.bitget_perp import PerpBitget

async def main():
    print(f"--- Exécution commencée pour {account_config['user_id']} ---")
    user_configs = await fetch_user_configs()  # Assurez-vous que fetch_user_configs est une fonction asynchrone si nécessaire

    for account_config in user_configs:
        # Initialiser l'objet PerpBitget une seule fois par utilisateur
        exchange = PerpBitget(
            public_api=account_config["public_key"],
            secret_api=account_config["secret_key"],
            password=account_config.get("password_api", ""),
        )

        # Exécuter la stratégie A ou B selon la configuration de l'utilisateur
        if account_config["strategy"] == "A":
            await execute_strategy_a_for_user(account_config, exchange)
        elif account_config["strategy"] == "B":
            await execute_strategy_b_for_user(account_config, exchange)

        # Assurez-vous de fermer l'échange après l'exécution de la stratégie
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())


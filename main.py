import asyncio
from database.db import fetch_user_configs
from strategies.envelopes.strategie_a import execute_strategy_a_for_user
from strategies.bolltrend.strategie_b import execute_strategy_b_for_user
from utilities.bitget_perp import PerpBitget1
from utilities.perp_bitget import PerpBitget2

async def main():
    # Assurez-vous que fetch_user_configs est une fonction asynchrone si nécessaire
    user_configs = fetch_user_configs()

    for account_config in user_configs:
        # Initialiser l'objet PerpBitget une seule fois par utilisateur
        exchange1 = PerpBitget1(
            public_api=account_config["public_key"],
            secret_api=account_config["secret_key"],
            password=account_config.get("password_api", ""),
        )
        exchange2 = PerpBitget2(
            public_api=account_config["public_key"],
            secret_api=account_config["secret_key"],
            password=account_config.get("password_api", ""),
        )

        # Exécuter la stratégie A ou B selon la configuration de l'utilisateur
        try:
            if account_config["strategy"] == "A":
                await execute_strategy_a_for_user(account_config, exchange1)
            elif account_config["strategy"] == "B":
                await execute_strategy_b_for_user(account_config, exchange2)
        finally:
            # Assurez-vous de fermer les échanges après l'exécution de la stratégie
            if 'close' in dir(exchange1):
                await exchange1.close()
            if 'close' in dir(exchange2):
                await exchange2.close()

if __name__ == "__main__":
    asyncio.run(main())



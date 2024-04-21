import asyncio
from database.db import fetch_user_configs
from strategies.envelopes.strategie_a import execute_strategy_a_for_user
from strategies.bolltrend.strategie_b import execute_strategy_b_for_user
from utilities.bitget_perp import PerpBitget

async def main():
    user_configs = await fetch_user_configs()
    tasks = []
    exchanges = []

    for account_config in user_configs:
        exchange = PerpBitget(
            public_api=account_config["public_key"],
            secret_api=account_config["secret_key"],
            password=account_config.get("password_api", ""),
        )
        if account_config["strategy"] == "A":
            tasks.append(execute_strategy_a_for_user(account_config, exchange))
        elif account_config["strategy"] == "B":
            tasks.append(execute_strategy_b_for_user(account_config, exchange))

    # Exécutez toutes les tâches en parallèle
    await asyncio.gather(*tasks)

    # Fermez toutes les instances d'échange après leur utilisation
    for exchange in exchanges:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())



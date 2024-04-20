import datetime
import asyncio
import sys
import ta
from utilities.bitget_perp import PerpBitget
from database.db import fetch_user_configs
from config.config_strat_b import params2
from utilities.var import ValueAtRisk
import copy

# Ajustement pour la compatibilité Windows avec asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def execute_strategy_b_for_user(account_config, exchange):
    print(f"--- Exécution commencée pour {account_config['user_id']} à {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

    # Exemple de configuration de stratégie. Adaptez ceci selon votre logique de trading spécifique.
    margin_mode = "crossed"  # Ou 'isolated'
    exchange_leverage = 5  # Exemple de levier
    tf = "1h"  # Intervalle de temps pour les données OHLCV
    sl = 0.3  # Stop loss en pourcentage
    size_leverage = 5
    max_var = 1
    max_side_exposition = 1
    production = True


    # Configuration initiale de l'échange, telle que le chargement des marchés
    try:
        await exchange.load_markets()

        #Get Data
        for pair in params2.copy():
            info = exchange.get_pair_info(pair)
            if info is None:
                print(f"Pair {pair} not found, removing from params...")
                del params2[pair]

        pairs = list(params2.keys())

        try:
            print(f"Setting {margin_mode} x{exchange_leverage} on {len(pairs)} pairs...")
            tasks = [
                exchange.set_margin_mode_and_leverage(
                    pair, margin_mode, exchange_leverage
                )
                for pair in pairs
            ]
            await asyncio.gather(*tasks)  # set leverage and margin mode for all pairs
        except Exception as e:
            print(e)

        print(f"Getting data and indicators on {len(pairs)} pairs...")
        tasks = [exchange.get_last_ohlcv(pair, tf, 50) for pair in pairs]
        dfs = await asyncio.gather(*tasks)
        df_list = dict(zip(pairs, dfs))

        def open_long(row):
            if (
                row['n1_close'] < row['n1_higher_band'] 
                and (row['close'] > row['higher_band']) 
                and (row['close'] > row['long_ma'])
            ):
                return True
            else:
                return False

        def close_long(row):
            if (row['close'] < row['ma_band']):
                return True
            else:
                return False

        def open_short(row):
            if (
                row['n1_close'] > row['n1_lower_band'] 
                and (row['close'] < row['lower_band']) 
                and (row['close'] < row['long_ma'])        
            ):
                return True
            else:
                return False

        def close_short(row):
            if (row['close'] > row['ma_band']):
                return True
            else:
                return False

        print(f"--- Bollinger Trend on {len(params2)} tokens {tf} Leverage x{exchange_leverage} ---")

        for pair in df_list:
            df = df_list[pair]
            params = params2[pair]
            bol_band = ta.volatility.BollingerBands(close=df["close"], window=params["bb_window"], window_dev=params["bb_std"])
            df["lower_band"] = bol_band.bollinger_lband()
            df["higher_band"] = bol_band.bollinger_hband()
            df["ma_band"] = bol_band.bollinger_mavg()

            df['long_ma'] = ta.trend.sma_indicator(close=df['close'], window=params["long_ma_window"])
            
            df["n1_close"] = df["close"].shift(1)
            df["n1_lower_band"] = df["lower_band"].shift(1)
            df["n1_higher_band"] = df["higher_band"].shift(1)

            df['iloc'] = range(len(df))

        print("Indicators loaded 100%")

        var = ValueAtRisk(df_list=df_list.copy())
        var.update_cov(current_date=df_list["BTC/USDT"].index[-1], occurance_data=989)
        print("Value At Risk loaded 100%")

        usd_balance = await exchange.get_balance()
        usd_balance = usd_balance.total
        print(f"Balance: {round(usd_balance, 2)} USDT")

        positions_data = await exchange.get_open_positions(pairs)
        position_list = [
            {
                "pair": position.pair,  # Supposant que symbol est un attribut de l'objet position
                "side": position.side,
                "size": exchange.amount_to_precision(position.pair, position.size),
                "market_price": position.current_price,
                "usd_size": float(exchange.amount_to_precision(position.pair, position.size)) * float(position.current_price),
                "open_price": position.entry_price
            }
            for position in positions_data if position.pair in df_list  # Vérifiez les noms d'attributs corrects
        ]


        positions = {}
        for pos in position_list:
            positions[pos["pair"]] = {"side": pos["side"], "size": pos["size"], "market_price": pos["market_price"], "usd_size": pos["usd_size"], "open_price": pos["open_price"]}

        print(f"{len(positions)} active positions ({list(positions.keys())})")

        # Check for closing positions...
        positions_to_delete = []
        for pair in positions:
            row = df_list[pair].iloc[-2]
            last_price = float(df_list[pair].iloc[-1]["close"])
            position = positions[pair]

            if position["side"] == "long" and close_long(row):
                close_long_market_price = last_price
                close_long_quantity = float(
                    exchange.convert_amount_to_precision(pair, position["size"])
                )
                exchange_close_long_quantity = close_long_quantity * close_long_market_price
                print(
                    f"Place Close Long Market Order: {close_long_quantity} {pair[:-5]} at the price of {close_long_market_price}$ ~{round(exchange_close_long_quantity, 2)}$"
                )
                if production:
                    exchange.place_market_order(pair, "sell", close_long_quantity, reduce=True)
                    positions_to_delete.append(pair)

            elif position["side"] == "short" and close_short(row):
                close_short_market_price = last_price
                close_short_quantity = float(
                    exchange.convert_amount_to_precision(pair, position["size"])
                )
                exchange_close_short_quantity = close_short_quantity * close_short_market_price
                print(
                    f"Place Close Short Market Order: {close_short_quantity} {pair[:-5]} at the price of {close_short_market_price}$ ~{round(exchange_close_short_quantity, 2)}$"
                )
                if production:
                    exchange.place_market_order(pair, "buy", close_short_quantity, reduce=True)
                    positions_to_delete.append(pair)

        for pair in positions_to_delete:
            del positions[pair]

        # Check current VaR risk
        positions_exposition = {}
        long_exposition = 0
        short_exposition = 0
        for pair in df_list:
            positions_exposition[pair] = {"long":0, "short":0}

        positions_data = await exchange.get_open_positions(pairs)
        for pos in positions_data:
            if pos["symbol"] in df_list and pos["side"] == "long":
                pct_exposition = (float(pos["contracts"]) * float(pos["contractSize"]) * float(pos["info"]["marketPrice"])) / usd_balance
                positions_exposition[pos["symbol"]]["long"] += pct_exposition
                long_exposition += pct_exposition
            elif pos["symbol"] in df_list and pos["side"] == "short":
                pct_exposition = (float(pos["contracts"]) * float(pos["contractSize"]) * float(pos["info"]["marketPrice"])) / usd_balance
                positions_exposition[pos["symbol"]]["short"] += pct_exposition
                short_exposition += pct_exposition

        current_var = var.get_var(positions=positions_exposition)
        print(f"Current VaR rsik 1 period: - {round(current_var, 2)}%, LONG exposition {round(long_exposition * 100, 2)}%, SHORT exposition {round(short_exposition * 100, 2)}%")

        for pair in df_list:
            if pair not in positions:
                try:
                    row = df_list[pair].iloc[-2]
                    last_price = float(df_list[pair].iloc[-1]["close"])
                    pct_sizing = params2[pair]["wallet_exposure"]
                    if open_long(row) and "long" in type:
                        long_market_price = float(last_price)
                        long_quantity_in_usd = usd_balance * pct_sizing * size_leverage
                        temp_positions = copy.deepcopy(positions_exposition)
                        temp_positions[pair]["long"] += (long_quantity_in_usd / usd_balance)
                        temp_long_exposition = long_exposition + (long_quantity_in_usd / usd_balance)
                        temp_var = var.get_var(positions=temp_positions)
                        if temp_var > max_var or temp_long_exposition > max_side_exposition:
                            print(f"Blocked open LONG on {pair}, because next VaR: - {round(current_var, 2)}%")
                        else:
                            long_quantity = float(exchange.convert_amount_to_precision(pair, float(
                                exchange.convert_amount_to_precision(pair, long_quantity_in_usd / long_market_price)
                            )))
                            exchange_long_quantity = long_quantity * long_market_price
                            print(
                                f"Place Open Long Market Order: {long_quantity} {pair[:-5]} at the price of {long_market_price}$ ~{round(exchange_long_quantity, 2)}$"
                            )
                            if production:
                                exchange.place_market_order(pair, "buy", long_quantity, reduce=False)
                                positions_exposition[pair]["long"] += (long_quantity_in_usd / usd_balance)
                                long_exposition += (long_quantity_in_usd / usd_balance)

                    elif open_short(row) and "short" in type:
                        short_market_price = float(last_price)
                        short_quantity_in_usd = usd_balance * pct_sizing * size_leverage
                        temp_positions = copy.deepcopy(positions_exposition)
                        temp_positions[pair]["short"] += (short_quantity_in_usd / usd_balance)
                        temp_short_exposition = short_exposition + (short_quantity_in_usd / usd_balance)
                        temp_var = var.get_var(positions=temp_positions)
                        if temp_var > max_var or temp_short_exposition > max_side_exposition:
                            print(f"Blocked open SHORT on {pair}, because next VaR: - {round(current_var, 2)}%")
                        else:
                            short_quantity = float(exchange.convert_amount_to_precision(pair, float(
                                exchange.convert_amount_to_precision(pair, short_quantity_in_usd / short_market_price)
                            )))
                            exchange_short_quantity = short_quantity * short_market_price
                            print(
                                f"Place Open Short Market Order: {short_quantity} {pair[:-5]} at the price of {short_market_price}$ ~{round(exchange_short_quantity, 2)}$"
                            )
                            if production:
                                exchange.place_market_order(pair, "sell", short_quantity, reduce=False)
                                positions_exposition[pair]["short"] += (short_quantity_in_usd / usd_balance)
                                short_exposition += (short_quantity_in_usd / usd_balance)
                    
                except Exception as e:
                    print(f"Error on {pair} ({e}), skip {pair}")

    except Exception as e:
        await exchange.close()
        raise e
    print(f"--- Exécution terminée pour {account_config['user_id']} à {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

async def main():
    user_configs = fetch_user_configs()  # Récupère les configs utilisateur depuis DynamoDB
    tasks = [execute_strategy_b_for_user(config) for config in user_configs]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

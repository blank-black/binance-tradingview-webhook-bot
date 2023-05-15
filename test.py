from flask import Flask, request, abort
from api.binance_future import BinanceFutureHttpClient, OrderSide, OrderType
from decimal import Decimal, ROUND_DOWN

app = Flask(__name__)

api_key = "JABA77DGFIEa0qBJCoUzQGA5tUEGrRcTdpuNyriBdszqScQ40H78nhlHTt5KVKSp"
api_secret = "vsWaajlF6pHCsubTGtC7HEsuZE4uYyc7F3gtizQyjOZadRUbz9Ra7QMwLKvP1NlG"
client = BinanceFutureHttpClient(api_key, api_secret)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            payload = request.json
            print(f'Webhook Received -> {payload}')
            position_amt = 0
            signal = payload['alert_action']
            symbol = payload['ticker']

            if symbol == "BTCUSDT":

                # Get account balance
                _, balance_info = client.get_balance()
                print('balance_info:', balance_info)
                _, price_info = client.get_latest_price(symbol)
                print('price_info:', price_info)
                price = Decimal(price_info['price'])
                usdt_balance = [bal for bal in balance_info if bal['asset'] == 'USDT'][0]['balance']
                usdt_balance = Decimal(usdt_balance)

                if signal == "long":
                    # Close all short positions
                    _, positions = client.get_position_info(symbol)
                    if positions:
                        position_amt = Decimal(positions[0]['positionAmt'])

                    # Open long position
                    quantity = (usdt_balance * 3 / price - position_amt).quantize(Decimal('0.001'), rounding=ROUND_DOWN)
                    print(client.place_order(symbol, OrderSide.BUY, OrderType.MARKET, quantity))

                elif signal == "short":
                    # Close all long positions
                    _, positions = client.get_position_info(symbol)
                    if positions:
                        position_amt = Decimal(positions[0]['positionAmt'])

                    # Open short position
                    quantity = (usdt_balance * 3 / price + position_amt).quantize(Decimal('0.001'), rounding=ROUND_DOWN)
                    print(client.place_order(symbol, OrderSide.SELL, OrderType.MARKET, quantity))

                elif signal == "tp":
                    # Close half of the current position
                    _, positions = client.get_position_info(symbol)
                    if positions:
                        position_amt = Decimal(positions[0]['positionAmt'])
                        if position_amt != 0:
                            quantity = (abs(position_amt) / 2).quantize(Decimal('0.001'), rounding=ROUND_DOWN)
                            order_side = OrderSide.BUY if position_amt < 0 else OrderSide.SELL  # Adjust side based on position
                            print(client.place_order(symbol, order_side, OrderType.MARKET, quantity))

            return '', 200
        except Exception as error:
            # handle the exception
            print("An exception occurred:", error)
            return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
#     symbol = "BTCUSDT"
#     print(client.get_latest_price(symbol))
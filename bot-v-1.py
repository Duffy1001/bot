from binance.client import Client
from binance.websockets import BinanceSocketManager
import os
import time

class Bot:

    def __init__(self):

        self.api_key = 'YOurPkNfpbVkUz8ASSQ5eZBskdyqwRpGgJK65iRHT4V5uJJkFiGQJgucxn8Ty4tJ'

        self.api_secret_key = 'QhPC8xIkcGtt3Xj9adT6ZJrtOiFopSdIb57V5X4Y5dKo7AEMcEHHjVhDdPxHCM7z'

        self.client = Client(self.api_key, self.api_secret_key, tld='us')

        self.fee = .00075

        self.running_profit = 0

        self.loop_time = 0

        bm = BinanceSocketManager(self.client)

        bm.start_book_ticker_socket(self.process_market_message)

        bm.start_user_socket(self.process_account_message)

        self.build_pair_data()

        self.build_chains()

        self.build_wallet()

        bm.start()

        self.main()

    def main(self):

        while True:

            self.simulateChain()

    def process_market_message(self, msg):

        pair = msg['s']

        if pair in self.pair_data:

            self.pair_data[pair]['best_ask_price'] = msg['a']

            self.pair_data[pair]['best_ask_qty'] = msg['A']

            self.pair_data[pair]['best_bid_price'] = msg['b']

            self.pair_data[pair]['best_bid_qty'] = msg['B']

        else:

            print('Unknown Pair!')

            input()

    def process_account_message(self, msg):

        type = msg['e']

        if type == 'outboundAccountPosition':

            positions = msg['B']

            for position in positions:

                asset = position['a']

                free = position['f']

                locked = position['l']

                t = time.time()

                self.wallet[asset]['last_updated'] = t

                self.wallet[asset]['asset'] = asset

                self.wallet[asset]['free'] = free

                self.wallet[asset]['locked'] = locked

            print(self.wallet)

            input()

    def build_wallet(self):

        self.wallet = {}

        amounts = self.client.get_account()['balances']

        for a in amounts:

            asset = a['asset']

            free = a['free']

            locked = a['locked']

            self.wallet[asset] = {}

            t = time.time()

            self.wallet[asset]['last_updated'] = t

            self.wallet[asset]['asset'] = asset

            self.wallet[asset]['free'] = free

            self.wallet[asset]['locked'] = locked


    def build_pair_data(self):

        self.pair_data = {}

        self.pairs = []

        response = self.client.get_exchange_info()

        for r in response['symbols']:

            symbol = r['symbol']

            self.pairs.append(symbol)

            self.pair_data[symbol] = {}

            self.pair_data[symbol]['base_precision'] = r['baseAssetPrecision']

            self.pair_data[symbol]['quote_precision'] = r['quoteAssetPrecision']

            self.pair_data[symbol]['base_asset'] = r['baseAsset']

            self.pair_data[symbol]['quote_asset'] = r['quoteAsset']

            self.pair_data[symbol]['symbol'] = symbol

            filters = r['filters']

            order_types = r['orderTypes']

            if not('MARKET' in order_types):

                print('MARKET ORDERS NOT AVAILABLE FOR {}'.format(symbol))

                input()

            for filter in filters:

                if filter['filterType'] == 'PRICE_FILTER':

                    self.pair_data[symbol]['quote_min_qty'] = filter['minPrice']

                elif filter['filterType'] == 'LOT_SIZE':

                    self.pair_data[symbol]['base_min_qty'] = filter['minQty']


        price_data = self.client.get_orderbook_tickers()

        for pair in price_data:

            symbol = pair['symbol']

            best_bid_price = pair['bidPrice']

            best_bid_qty = pair['bidQty']

            best_ask_price = pair['askPrice']

            best_ask_qty = pair['askQty']

            self.pair_data[symbol]['best_bid_price'] = best_bid_price

            self.pair_data[symbol]['best_bid_qty'] = best_bid_qty

            self.pair_data[symbol]['best_ask_price'] = best_ask_price

            self.pair_data[symbol]['best_ask_qty'] = best_ask_qty

    def build_chains(self):

        self.chains = []

        for pair in self.pairs:

            if self.pair_data[pair]['quote_asset'] != 'USD' and self.pair_data[pair]['base_asset'] + 'USD' in self.pairs and self.pair_data[pair]['quote_asset'] + 'USD' in self.pairs:

                self.chains.append([self.pair_data[pair]['base_asset'] + 'USD', pair, self.pair_data[pair]['quote_asset'] + 'USD', 'buy-sell-sell'])

                self.chains.append([self.pair_data[pair]['quote_asset'] + 'USD', pair, self.pair_data[pair]['base_asset'] + 'USD', 'buy-buy-sell'])


    def simulateChain(self):

        t1 = time.time()

        original_start_amount = float(self.wallet['USD']['free'])

        chain_results = []

        for chain in self.chains:

            start_amount = original_start_amount

            actions = chain[3].split('-')

            tradeable = []

            for x in range(3):

                action = actions[x]

                pair = chain[x]

                quote_asset = self.pair_data[pair]['quote_asset']

                base_asset = self.pair_data[pair]['base_asset']

                base_min = float(self.pair_data[pair]['base_min_qty'])

                quote_min = float(self.pair_data[pair]['quote_min_qty'])


                if action == 'buy':

                    price = float(self.pair_data[pair]['best_ask_price'])

                    new_start_amount = start_amount / price

                    qty_at_price = float(self.pair_data[pair]['best_ask_qty'])


                    if start_amount >= quote_min and new_start_amount <= qty_at_price:

                        tradeable.append(True)

                    else:

                        tradeable.append(False)

                elif action == 'sell':

                    price = float(self.pair_data[pair]['best_bid_price'])

                    new_start_amount = start_amount * price

                    qty_at_price = float(self.pair_data[pair]['best_bid_qty'])


                    if start_amount >= base_min and start_amount <= qty_at_price:

                        tradeable.append(True)

                    else:

                        tradeable.append(False)

                start_amount = new_start_amount

            if tradeable[0] and tradeable[1] and tradeable[2]:

                trade_possible = True

            else:

                trade_possible = False

            net_profit = start_amount

            gross_profit = net_profit * self.fee

            if gross_profit > original_start_amount:

                chain_results.append('{} : {} -> {}  Tradable : {}'.format(chain,original_start_amount,start_amount, trade_possible))

        t2 = time.time()

        loop_time = t2 - t1

        if len(chain_results) > 0:

            os.system('clear')

            for chain in chain_results:

                print(chain)

            print(loop_time)

            input('...')


Bot()

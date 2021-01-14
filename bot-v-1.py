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

            if 'XRP' not in symbol:

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

                    # if filter['filterType'] == 'PRICE_FILTER':
                    #
                    #     self.pair_data[symbol]['quote_min_price'] = filter['minPrice']

                    if filter['filterType'] == 'LOT_SIZE':

                        self.pair_data[symbol]['base_min_qty'] = filter['minQty']

                    elif filter['filterType'] == 'PRICE_FILTER':

                        self.pair_data[symbol]['quote_min_price'] = filter['minPrice']


        price_data = self.client.get_orderbook_tickers()

        for pair in price_data:

            symbol = pair['symbol']

            if 'XRP' not in symbol:

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

        original_start_amount = 15

        chain_results = []

        for chain in self.chains:

            start_amount = original_start_amount

            actions = chain[3].split('-')

            tradeable = []

            fee_total = 0

            for x in range(3):

                action = actions[x]

                pair = chain[x]

                quote_asset = self.pair_data[pair]['quote_asset']

                base_asset = self.pair_data[pair]['base_asset']

                base_min = float(self.pair_data[pair]['base_min_qty'])

                quote_min = float(self.pair_data[pair]['quote_min_price'])


                if action == 'buy':

                    price = float(self.pair_data[pair]['best_ask_price'])

                    new_start_amount = start_amount / price

                    qty_at_price = float(self.pair_data[pair]['best_ask_qty'])

                    if quote_asset == 'USD':

                        fee_total += self.fee * start_amount

                    else:

                        usd_price_of_new_start_amount = float(self.pair_data[quote_asset+'USD']['best_bid_price'])

                        quote_asset_fee = start_amount * self.fee

                        fee_total += quote_asset_fee * usd_price_of_new_start_amount


                    if start_amount >= quote_min and new_start_amount <= qty_at_price:

                        tradeable.append(True)

                    else:

                        tradeable.append(False)

                elif action == 'sell':

                    price = float(self.pair_data[pair]['best_bid_price'])

                    new_start_amount = start_amount * price

                    qty_at_price = float(self.pair_data[pair]['best_bid_qty'])

                    if base_asset == 'USD':

                        fee_total += self.fee * start_amount

                    else:

                        usd_price_of_new_start_amount = float(self.pair_data[base_asset+'USD']['best_bid_price'])

                        base_asset_fee = self.fee * start_amount

                        fee_total += base_asset_fee * usd_price_of_new_start_amount


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

            gross_profit = net_profit - fee_total

            if (gross_profit > original_start_amount+.01) and trade_possible:

                self.execute_chain(chain, fee_total)

        t2 = time.time()

        self.loop_time = t2 - t1

        # if len(chain_results) > 0:
        #
        #     os.system('clear')
        #
        #     for chain in chain_results:
        #
        #         print(chain)
        #
        #     print(loop_time)
        #
        #     input('...')

    def wait_for_order(self, t, quote_asset, base_asset):

        order_filled = False

        t = float(t)

        while not order_filled:

            quote_last_updated = float(self.wallet[quote_asset]['last_updated'])

            base_last_updated = float(self.wallet[base_asset]['last_updated'])

            if quote_last_updated > t and base_last_updated > t:

                order_filled = True

        return True

    def execute_chain(self, chain, fee_total):

        actions = chain[3].split('-')

        initial_usd = 15

        initial_wallet = float(self.wallet['USD']['free'])

        orders = []

        for x in range(3):

            action = actions[x]

            pair = chain[x]

            quote_asset = self.pair_data[pair]['quote_asset']

            base_asset = self.pair_data[pair]['base_asset']

            if action == 'buy':

                start_amount = float(self.wallet[quote_asset]['free'])

                quote_precision = int(self.pair_data[pair]['quote_precision'])

                start_amount = '{:0.0{}f}'.format(start_amount, quote_precision)

                t = time.time()

                order = self.client.order_market(
                symbol=pair,
                side=action,
                quoteOrderQty=start_amount)

                orders.append(order)

            elif action == 'sell':

                start_amount = float(self.wallet[base_asset]['free'])

                precision = int(self.pair_data[pair]['quote_precision'])

                desired_amount = start_amount * float(self.pair_data[pair]['best_bid_price'])

                desired_amount = float('{:0.0{}f}'.format(desired_amount, precision))

                t = time.time()

                order = self.client.order_market(
                symbol=pair,
                side=action,
                quoteOrderQty=desired_amount)

                orders.append(order)

            t1 = time.time()

            self.wait_for_order(t, quote_asset, base_asset)

            t2 = time.time()

            print(t2-t1)

            #time.sleep(.1)

        self.running_profit += float(self.wallet['USD']['free']) - (initial_wallet + fee_total)

        if self.running_profit <= -2:

            print('HAULTING!')

            input('...')

        print('{} Running Profit {}'.format(chain,self.running_profit))

        time.sleep(.5)




Bot()

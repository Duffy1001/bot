from binance.client import Client
from binance.websockets import BinanceSocketManager
import os
import time
from sympy import Rational
import math

class Bot:

    def __init__(self):

        self.api_key = 'YOurPkNfpbVkUz8ASSQ5eZBskdyqwRpGgJK65iRHT4V5uJJkFiGQJgucxn8Ty4tJ'

        self.api_secret_key = 'QhPC8xIkcGtt3Xj9adT6ZJrtOiFopSdIb57V5X4Y5dKo7AEMcEHHjVhDdPxHCM7z'

        self.client = Client(self.api_key, self.api_secret_key, tld='us')

        self.fee = .00075

        self.startAmount = 20

        self.running_profit = 0

        self.profitable_chains = {}

        bm = BinanceSocketManager(self.client)

        bm.start_book_ticker_socket(self.process_message)

        self.build_pair_data()

        self.build_chains()

        self.build_chain_data()

        bm.start()

        self.main()

    def main(self):

        while True:

            self.simulateChain()

    def process_message(self, msg):

        pair = msg['s']

        if pair in self.pair_data:

            self.pair_data[pair]['best_ask_price'] = msg['a']

            self.pair_data[pair]['best_ask_qty'] = msg['A']

            self.pair_data[pair]['best_bid_price'] = msg['b']

            self.pair_data[pair]['best_bid_qty'] = msg['B']

        else:

            print('Unknown Pair!')

            input()

    def build_chain_data(self):

        self.chain_data = {}

        for chain in self.chains:

            chain = chain[0] + chain[1] + chain[2]

            self.chain_data[chain] = {}

            self.chain_data[chain]['longest_profitable_time'] = 0

            self.chain_data[chain]['currently_profitable'] = False

            self.chain_data[chain]['start_time'] = 0

            self.chain_data[chain]['current_profitable_time'] = 0


    def build_pair_data(self):

        self.pair_data = {}

        self.pairs = []

        response = self.client.get_exchange_info()

        for r in response['symbols']:

            symbol = r['symbol']

            self.pairs.append(symbol)

            self.pair_data[symbol] = {}

            for property in r:

                if property == 'filters':

                    filters = r[property]

                    for f in filters:

                        if f['filterType'] == 'PRICE_FILTER':

                            quote_precision = f['minPrice']

                        elif f['filterType'] == 'LOT_SIZE':

                            base_precision = f['minQty']

                    self.pair_data[symbol]['quote_precision'] = quote_precision

                    self.pair_data[symbol]['base_precision'] = base_precision

                self.pair_data[symbol][property] = r[property]


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

            if self.pair_data[pair]['quoteAsset'] != 'USD' and self.pair_data[pair]['baseAsset'] + 'USD' in self.pairs and self.pair_data[pair]['quoteAsset'] + 'USD' in self.pairs:

                self.chains.append([self.pair_data[pair]['baseAsset'] + 'USD', pair, self.pair_data[pair]['quoteAsset'] + 'USD', 'buy-sell-sell'])

                self.chains.append([self.pair_data[pair]['quoteAsset'] + 'USD', pair, self.pair_data[pair]['baseAsset'] + 'USD', 'buy-buy-sell'])

    def price_in_usd(amount, pair):

        base_asset = self.pair_data[pair]['baseAsset']

        result = float(self.pair_data[base_asset+'USD']['best_bid_price']) * amount

        return result

    def simulateChain(self):

        t1 = time.time()

        for chain in self.chains:

            if chain[3] == 'buy-buy-sell':

                price1 = float(self.pair_data[chain[0]]['best_ask_price'])

                amount1 = float(self.pair_data[chain[0]]['best_ask_qty'])

                amount1 = price_in_usd(amount1, chain[0])

                price2 = float(self.pair_data[chain[1]]['best_ask_price'])

                amount2 = float(self.pair_data[chain[1]]['best_ask_qty'])

                amount2 = price_in_usd(amount2, chain[1])

                price3 = float(self.pair_data[chain[2]]['best_bid_price'])

                amount3 = float(self.pair_data[chain[2]]['best_bid_qty'])

                amount3 = price_in_usd(amount3, chain[2])

                pricex = float(self.pair_data[self.pair_data[chain[1]]['baseAsset'] + 'USD']['best_ask_price'])

                result = (price3*self.startAmount)/(price1*price2)

            elif chain[3] == 'buy-sell-sell':

                price1 = float(self.pair_data[chain[0]]['best_ask_price'])

                amount1 = float(self.pair_data[chain[0]]['best_ask_qty'])

                amount1 = price_in_usd(amount1, chain[0])

                price2 = float(self.pair_data[chain[1]]['best_bid_price'])

                amount2 = float(self.pair_data[chain[1]]['best_bid_qty'])

                amount2 = price_in_usd(amount2, chain[1])

                price3 = float(self.pair_data[chain[2]]['best_bid_price'])

                amount3 = float(self.pair_data[chain[2]]['best_bid_qty'])

                amount3 = price_in_usd(amount3, chain[2])

                pricex = float(self.pair_data[self.pair_data[chain[1]]['baseAsset'] + 'USD']['best_ask_price'])

                result = (price2*price3*self.startAmount)/price1

            fees = (self.startAmount*self.fee) + ((self.startAmount/price1)*pricex*self.fee) + (self.startAmount*self.fee)

            theoreticalFees = (self.startAmount*.0004) + ((self.startAmount/price1)*pricex*.0004) + (self.startAmount*.0004)

            grossProfit = result - fees

            chain_string = chain[0] + chain[1] + chain[2]

            if (grossProfit > self.startAmount) and amount1 > 10 and amount2 > 10 and amount3 > 10:

                try:
                    self.profitable_chains[chain_string]
                    self.profitable_chains[chain_string] += 1
                except:
                    self.profitable_chains[chain_string] = 1

                # print('Net Profit {}  Gross Profit {}  {}'.format(result, grossProfit, chain))
                if self.chain_data[chain_string]['currently_profitable'] == False:


                    self.chain_data[chain_string]['start_time'] = time.time()

                    self.chain_data[chain_string]['currently_profitable'] = True

                else:

                    self.chain_data[chain_string]['current_profitable_time'] = time.time() - self.chain_data[chain_string]['start_time']

                self.running_profit += grossProfit - self.startAmount
                # time.sleep(.2)
                # os.system('clear')

                print('Running Profit {} and Current Profit {} for {} currently lasted for {} record lasted for {} occured {} times'.format(self.running_profit, grossProfit, chain, self.chain_data[chain_string]['current_profitable_time'],self.chain_data[chain_string]['longest_profitable_time'], self.profitable_chains[chain_string]))
            else:

                if self.chain_data[chain_string]['currently_profitable'] == True:

                    if self.chain_data[chain_string]['longest_profitable_time'] < self.chain_data[chain_string]['current_profitable_time']:

                        self.chain_data[chain_string]['longest_profitable_time'] = self.chain_data[chain_string]['current_profitable_time']

                    self.chain_data[chain_string]['start_time'] = 0

                    self.chain_data[chain_string]['current_profitable_time'] = 0

                    self.chain_data[chain_string]['currently_profitable'] = False


    def findOptimalStartAmount(self, chain):

        if chain[3] == 'buy-buy-sell':

            start = Rational(1)

            unequal = Rational(0)

            amounts = []

            while unequal.evalf() != 3 and len(amounts) < 9:

                print('start', start.evalf())

                endOfFirstTradeAmount = start/Rational(float(self.pair_data[chain[0]]['best_ask_price']))

                left_over1 = self.trimDecimal(endOfFirstTradeAmount, 'base', chain[0])[1] * float(self.pair_data[self.pair_data[chain[0]]['baseAsset']+'USD']['best_bid_price'])

                if left_over1 < .01:

                    unequal += 1

                    endOfSecondTradeAmount = endOfFirstTradeAmount/Rational(float(self.pair_data[chain[1]]['best_ask_price']))

                    left_over2 = self.trimDecimal(endOfSecondTradeAmount, 'base', chain[1])[1] * float(self.pair_data[self.pair_data[chain[1]]['baseAsset']+'USD']['best_bid_price'])

                    if left_over2 < .01:

                        unequal += 1

                        endOfThirdTradeAmount = endOfSecondTradeAmount*Rational(float(self.pair_data[chain[2]]['best_bid_price']))

                        left_over3 = self.trimDecimal(endOfThirdTradeAmount, 'quote', chain[2])[1] * float(self.pair_data[self.pair_data[chain[2]]['baseAsset']+'USD']['best_bid_price'])

                        if left_over3 < .01:

                            unequal += 1

                            amounts.append([start.evalf(),left_over1+left_over2+left_over3])

                            if len(amounts) < 9:

                                unequal = Rational(0)

                                start += Rational(.01)

                        else:

                            start += Rational(.01)

                            unequal = Rational(0)

                    else:

                        start += Rational(.01)

                        unequal = Rational(0)

                else:

                    start += Rational(.01)

                    unequal = Rational(0)



            return amounts

        elif chain[3] == 'buy-sell-sell':

            start = Rational(1)

            unequal = Rational(0)

            amounts = []

            while unequal.evalf() != 3 and len(amounts) < 9:

                print('start', start.evalf())

                endOfFirstTradeAmount = start/Rational(float(self.pair_data[chain[0]]['best_ask_price']))

                left_over1 = self.trimDecimal(endOfFirstTradeAmount, 'base', chain[0])[1] * float(self.pair_data[self.pair_data[chain[0]]['baseAsset']+'USD']['best_bid_price'])

                if left_over1 < .01:

                    unequal += 1

                    endOfSecondTradeAmount = endOfFirstTradeAmount*Rational(float(self.pair_data[chain[1]]['best_bid_price']))

                    left_over2 = self.trimDecimal(endOfSecondTradeAmount, 'quote', chain[1])[1] * float(self.pair_data[self.pair_data[chain[1]]['baseAsset']+'USD']['best_bid_price'])

                    if left_over2 < .01:

                        unequal += 1

                        endOfThirdTradeAmount = endOfSecondTradeAmount*Rational(float(self.pair_data[chain[2]]['best_bid_price']))

                        left_over3 = self.trimDecimal(endOfThirdTradeAmount, 'quote', chain[2])[1] * float(self.pair_data[self.pair_data[chain[2]]['baseAsset']+'USD']['best_bid_price'])

                        if left_over3 < .01:

                            unequal += 1

                            amounts.append([start.evalf(),left_over1+left_over2+left_over3])

                            if len(amounts) < 9:

                                unequal = Rational(0)

                                start += Rational(.01)

                        else:

                            start += Rational(.01)

                            unequal = Rational(0)

                    else:

                        start += Rational(.01)

                        unequal = Rational(0)

                else:

                    start += Rational(.01)

                    unequal = Rational(0)

            return amounts


    def trimDecimal(self, val, type, symbol):


        if type == 'quote':

            quoteMag = Rational(1)/Rational(float(self.pair_data[symbol]['quote_precision']))

            quoteLeftover = float(str((((Rational(val)*quoteMag)-(math.floor(Rational(val)*quoteMag)))/quoteMag).evalf()))

            quoteTarget = float(str((math.floor(Rational(val)*quoteMag)/quoteMag).evalf()))

            print(type, quoteTarget, quoteLeftover, symbol)

            return [quoteTarget,quoteLeftover]

        elif type == 'base':

            baseMag = Rational(1)/Rational(self.pair_data[symbol]['base_precision'])

            baseLeftover = float(str((((Rational(val)*baseMag)-(math.floor(Rational(val)*baseMag)))/baseMag).evalf()))

            baseTarget = float(str((math.floor(Rational(val)*baseMag)/baseMag).evalf()))

            print(type, baseTarget, baseLeftover, symbol)


            return [baseTarget,baseLeftover]




    def test(self):

        while True:

            time.sleep(.2)

            os.system('clear')

            print(self.pair_data['BTCUSD'])
Bot()

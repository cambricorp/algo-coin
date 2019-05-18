import json
import gdax
from functools import lru_cache
from websocket import create_connection
from ..config import ExchangeConfig
from ..define import EXCHANGE_MARKET_DATA_ENDPOINT
from ..enums import OrderType, OrderSubType, PairType, TickType, ChangeReason, TradingType
from ..exchange import Exchange
from ..logging import LOG as log
from ..structs import MarketData, Instrument
from ..utils import parse_date, str_to_currency_pair_type, str_to_side, str_to_order_type, get_keys_from_environment
from .order_entry import CCXTOrderEntryMixin
from .websockets import WebsocketMixin


class CoinbaseWebsocketMixin(WebsocketMixin):
    @lru_cache(None)
    def subscription(self):
        return [json.dumps({"type": "subscribe", "product_id": CoinbaseWebsocketMixin.currencyPairToString(x)}) for x in self.options().currency_pairs]

    @lru_cache(None)
    def heartbeat(self):
        return json.dumps({"type": "heartbeat", "on": True})

    def close(self):
        '''close the websocket'''

    def seqnum(self, number: int):
        '''manage sequence numbers'''

    def ws_client(self):
        options = self.options()
        if options.trading_type == TradingType.LIVE or options.trading_type == TradingType.SIMULATION:
            key, secret, passphrase = get_keys_from_environment(options.exchange_type.value)
        elif options.trading_type == TradingType.SANDBOX:
            key, secret, passphrase = get_keys_from_environment(options.exchange_type.value + '_SANDBOX')

        if options.trading_type in (TradingType.LIVE, TradingType.SIMULATION, TradingType.SANDBOX):
            try:
                if options.trading_type in (TradingType.LIVE, TradingType.SIMULATION, TradingType.SANDBOX):
                    client = gdax.AuthenticatedClient(key,
                                                      secret,
                                                      passphrase)
            except Exception:
                raise Exception('Something went wrong with the API Key/Client instantiation')
            return client

        self._seqnum_enabled = False  # FIXME?

    def run(self, engine) -> None:
        # DEBUG
        options = self.options()

        while True:
            # startup and redundancy
            log.info('Starting....')
            self.ws = create_connection(EXCHANGE_MARKET_DATA_ENDPOINT(options.exchange_type, options.trading_type))
            log.info('Connected!')

            for sub in self.subscription():
                self.ws.send(sub)
                log.info('Sending Subscription %s' % sub)

            self.ws.send(self.heartbeat())
            log.info('Sending Heartbeat %s' % self.heartbeat())

            log.info('')
            log.info('Starting algo trading')
            try:
                while True:
                    self.receive()

            except KeyboardInterrupt:
                log.critical('Terminating program')
                return

    @staticmethod
    def tickToData(jsn: dict) -> MarketData:
        time = parse_date(jsn.get('time'))
        price = float(jsn.get('price', 'nan'))
        volume = float(jsn.get('size', 'nan'))
        typ = CoinbaseWebsocketMixin.strToTradeType(jsn.get('type'))
        currency_pair = str_to_currency_pair_type(jsn.get('product_id'))

        instrument = Instrument(underlying=currency_pair)

        order_type = str_to_order_type(jsn.get('order_type', ''))
        side = str_to_side(jsn.get('side', ''))
        remaining_volume = float(jsn.get('remaining_size', 0.0))
        reason = jsn.get('reason', '')

        if reason == 'canceled':
            reason = ChangeReason.CANCELLED
        elif reason == '':
            reason = ChangeReason.NONE
        elif reason == 'filled':
            # FIXME
            reason = ChangeReason.NONE
            # reason = ChangeReason.FILLED
        else:
            reason = ChangeReason.NONE

        sequence = int(jsn.get('sequence'))
        ret = MarketData(time=time,
                         volume=volume,
                         price=price,
                         type=typ,
                         instrument=instrument,
                         remaining=remaining_volume,
                         reason=reason,
                         side=side,
                         order_type=order_type,
                         sequence=sequence)
        return ret

    @staticmethod
    def strToTradeType(s: str) -> TickType:
        if s == 'match':
            return TickType.TRADE
        elif s == 'received':
            return TickType.RECEIVED
        elif s == 'open':
            return TickType.OPEN
        elif s == 'done':
            return TickType.DONE
        elif s == 'change':
            return TickType.CHANGE
        elif s == 'heartbeat':
            return TickType.HEARTBEAT
        else:
            return TickType.ERROR

    @staticmethod
    def tradeReqToParams(req) -> dict:
        p = {}
        p['price'] = str(req.price)
        p['size'] = str(req.volume)
        p['product_id'] = CoinbaseWebsocketMixin.currencyPairToString(req.instrument.currency_pair)
        p['type'] = CoinbaseWebsocketMixin.orderTypeToString(req.order_type)

        if req.order_sub_type == OrderSubType.FILL_OR_KILL:
            p['time_in_force'] = 'FOK'
        elif req.order_sub_type == OrderSubType.POST_ONLY:
            p['post_only'] = '1'
        return p

    @staticmethod
    def currencyPairToString(cur: PairType) -> str:
        return cur.value[0].value + '-' + cur.value[1].value

    @staticmethod
    def orderTypeToString(typ: OrderType) -> str:
        if typ == OrderType.LIMIT:
            return 'limit'
        elif typ == OrderType.MARKET:
            return 'market'


class CoinbaseExchange(CoinbaseWebsocketMixin, CCXTOrderEntryMixin, Exchange):
    def __init__(self, options: ExchangeConfig) -> None:
        super(CoinbaseExchange, self).__init__(options)
        self._last = None
        self._orders = {}

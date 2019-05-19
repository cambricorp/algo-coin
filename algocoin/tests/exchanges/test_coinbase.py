from mock import patch, MagicMock


class TestExchange:
    def setup(self):
        pass
        # setup() before each test method

    def teardown(self):
        pass
        # teardown() after each test method

    @classmethod
    def setup_class(cls):
        pass
        # setup_class() before any methods in this class

    @classmethod
    def teardown_class(cls):
        pass
        # teardown_class() after any methods in this class

    def test_init(self):
        from ...config import ExchangeConfig
        from ...exchanges.coinbase import CoinbaseExchange
        from ...enums import ExchangeType

        with patch('os.environ'), patch('gdax.AuthenticatedClient') as m:
            ec = ExchangeConfig()
            ec.exchange_type = ExchangeType.COINBASE
            m.getAccounts.return_value = []
            e = CoinbaseExchange(ec)
            e._running = True
            assert e

    def test_receive(self):
        from ...config import ExchangeConfig
        from ...exchanges.coinbase import CoinbaseExchange
        from ...enums import TickType, ExchangeType

        with patch('os.environ'), patch('gdax.AuthenticatedClient'):
            ec = ExchangeConfig()
            ec.exchange_type = ExchangeType.COINBASE
            e = CoinbaseExchange(ec)
            e._running = True
            assert e

            e.ws = MagicMock()

            with patch('json.loads') as m1:
                for i, val in enumerate([TickType.TRADE,
                                         TickType.RECEIVED,
                                         TickType.OPEN,
                                         TickType.DONE,
                                         TickType.CHANGE,
                                         TickType.ERROR]):
                    m1.return_value = {'type': val,
                                       'sequence': i,
                                       'time': '2017-02-19T18:52:17.088000Z',
                                       'product_id': 'BTCUSD'}
                    e.receive()

    # def test_seqnum_fix(self):
    #     from ...lib.config import ExchangeConfig
    #     from ...lib.exchanges.gdax import GDAXExchange
    #     from ...lib.enums import TickType, ExchangeType

    #     with patch('os.environ'), patch('gdax.AuthenticatedClient'):
    #         ec = ExchangeConfig()
    #         ec.exchange_type = ExchangeType.GDAX
    #         e = GDAXExchange(ec)
    #         e._running = True
    #         assert e

    #         e.ws = MagicMock()

    #         with patch('json.loads') as m1:
    #             m1.return_value = {'type': TickType.TRADE,
    #                                'sequence': 0,
    #                                'time': '2017-02-19T18:52:17.088000Z',
    #                                'product_id': 'BTCUSD'}
    #             e.receive()
    #             for i, val in enumerate([TickType.TRADE,
    #                                      TickType.RECEIVED,
    #                                      TickType.OPEN,
    #                                      TickType.DONE,
    #                                      TickType.CHANGE,
    #                                      TickType.ERROR]):
    #                 m1.return_value = {'type': val,
    #                                    'sequence': 6-i,
    #                                    'time': '2017-02-19T18:52:17.088000Z',
    #                                    'product_id': 'BTCUSD'}
    #                 if i != 0:
    #                     assert e._missingseqnum
    #                 e.receive()
    #             assert e._missingseqnum == set()

    def test_trade_req_to_params_coinbase(self):
        from ...exchanges.coinbase import CoinbaseExchange
        from ...enums import PairType, OrderType, OrderSubType
        from ...structs import Instrument

        class tmp:
            def __init__(self, a=True):
                self.price = 'test'
                self.volume = 'test'
                self.instrument = Instrument(underlying=PairType.BTCUSD)
                self.order_type = OrderType.LIMIT
                self.order_sub_type = OrderSubType.POST_ONLY if a \
                    else OrderSubType.FILL_OR_KILL

        res1 = CoinbaseExchange.tradeReqToParams(tmp())
        res2 = CoinbaseExchange.tradeReqToParams(tmp(False))

        assert(res1['price'] == 'test')
        assert(res1['size'] == 'test')
        assert(res1['product_id'] == 'BTC-USD')
        assert(res1['type'] == 'limit')
        assert(res1['post_only'] == '1')
        assert(res2['time_in_force'] == 'FOK')
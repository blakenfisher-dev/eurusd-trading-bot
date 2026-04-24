try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

from datetime import datetime
from typing import Optional, List
import time
import logging

from models import Trade, TradeDirection, TradeStatus, Balance, TradingSignal
from utils.risk import PortfolioManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetaTraderConnection:
    def __init__(self):
        self.connected = False
        self.symbol = "EURUSD"
        
    def connect(self) -> bool:
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 not installed")
            return False
        if not mt5.initialize():
            logger.error("Failed to initialize MetaTrader 5")
            return False
        if not mt5.login():
            logger.error("Failed to login to MetaTrader 5")
            return False
        self.connected = True
        logger.info("Connected to MetaTrader 5")
        return True
    
    def disconnect(self):
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MetaTrader 5")
    
    def get_account_info(self) -> Optional[Balance]:
        if not self.connected:
            return None
        account_info = mt5.account_info()
        if account_info is None:
            return None
        return Balance(
            equity=account_info.equity,
            balance=account_info.balance,
            margin_used=account_info.margin,
            free_margin=account_info.margin_free,
            margin_level=account_info.margin_level
        )
    
    def get_ohlc(self, timeframe: int = None, num_bars: int = 1000) -> Optional[List]:
        if not self.connected or not MT5_AVAILABLE:
            return None
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_H1
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, num_bars)
        return rates
    
    def get_current_price(self) -> tuple[Optional[float], Optional[float]]:
        if not self.connected or not MT5_AVAILABLE:
            return None, None
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return None, None
        return tick.bid, tick.ask
    
    def execute_trade(self, 
                      direction: TradeDirection,
                      volume: float,
                      stop_loss: Optional[float] = None,
                      take_profit: Optional[float] = None,
                      deviation: int = 10) -> Optional[int]:
        if not self.connected or not MT5_AVAILABLE:
            return None
        action = mt5.TRADE_ACTION_DEAL
        if direction == TradeDirection.LONG:
            trade_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(self.symbol).ask
        else:
            trade_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(self.symbol).bid
        request = {
            "action": action,
            "symbol": self.symbol,
            "volume": volume,
            "type": trade_type,
            "price": price,
            "deviation": deviation,
            "magic": 123456,
            "comment": "Algo Trading Bot",
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        if stop_loss:
            request["sl"] = stop_loss
        if take_profit:
            request["tp"] = take_profit
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Trade failed: {result.comment}")
            return None
        logger.info(f"Trade executed: {direction.name} {volume} lots at {price}")
        return result.order
    
    def close_trade(self, ticket: int, volume: float) -> bool:
        if not self.connected or not MT5_AVAILABLE:
            return False
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            return False
        position = positions[0]
        trade_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(self.symbol).bid if trade_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(self.symbol).ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": trade_type,
            "position": ticket,
            "price": price,
            "magic": 123456,
            "comment": "Close by Algo",
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Trade closed: Ticket {ticket}")
            return True
        logger.error(f"Failed to close trade: {result.comment}")
        return False
    
    def get_positions(self) -> List[dict]:
        if not self.connected or not MT5_AVAILABLE:
            return []
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return []
        return [{
            'ticket': p.ticket,
            'direction': TradeDirection.LONG if p.type == mt5.ORDER_TYPE_BUY else TradeDirection.SHORT,
            'volume': p.volume,
            'open_price': p.price_open,
            'current_price': p.price_current,
            'pnl': p.profit,
            'stop_loss': p.sl,
            'take_profit': p.tp
        } for p in positions]


class LiveTradingBot:
    def __init__(self, strategy, risk_manager, symbol: str = "EURUSD", timeframe: int = None):
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.timeframe = timeframe if timeframe else (mt5.TIMEFRAME_H1 if MT5_AVAILABLE else None)
        self.mt5 = MetaTraderConnection()
        self.portfolio = PortfolioManager(risk_manager=risk_manager)
        self.running = False
        self.last_bar_time = None
        
    def start(self):
        if not self.mt5.connect():
            logger.error("Failed to start bot - MT5 connection failed")
            return False
        self.running = True
        logger.info("Live trading bot started")
        return True
    
    def stop(self):
        self.running = False
        self.mt5.disconnect()
        logger.info("Live trading bot stopped")
    
    def tick(self) -> bool:
        current_time = datetime.now()
        rates = self.mt5.get_ohlc(self.timeframe, 100)
        if rates is None or len(rates) == 0:
            return False
        import pandas as pd
        df = pd.DataFrame(rates)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df = self.strategy.prepare_indicators(df)
        current_bar = df.iloc[-1]
        bar_time = current_bar['timestamp']
        if self.last_bar_time == bar_time:
            return False
        self.last_bar_time = bar_time
        positions = self.mt5.get_positions()
        for pos in positions:
            current_price = self.mt5.get_current_price()
            bid, ask = current_price
            check_price = bid if pos['direction'] == TradeDirection.LONG else ask
            if pos['stop_loss'] and check_price <= pos['stop_loss']:
                self.mt5.close_trade(pos['ticket'], pos['volume'])
                logger.info(f"Stop loss triggered for ticket {pos['ticket']}")
                continue
            if pos['take_profit'] and check_price >= pos['take_profit']:
                self.mt5.close_trade(pos['ticket'], pos['volume'])
                logger.info(f"Take profit triggered for ticket {pos['ticket']}")
                continue
        account = self.mt5.get_account_info()
        if account:
            can_open, _ = self.risk_manager.can_open_trade([], account.balance)
            if can_open:
                signal = self.strategy.generate_signal(df, len(df) - 1)
                if signal:
                    position_size = self.risk_manager.calculate_position_size(signal, account.balance)
                    if position_size > 0:
                        ticket = self.mt5.execute_trade(signal.direction, position_size, signal.stop_loss, signal.take_profit)
                        if ticket:
                            trade = Trade(
                                id=str(ticket),
                                direction=signal.direction,
                                entry_price=signal.price,
                                entry_time=current_time,
                                quantity=position_size,
                                stop_loss=signal.stop_loss,
                                take_profit=signal.take_profit,
                                status=TradeStatus.OPEN
                            )
                            self.portfolio.trades.append(trade)
        return True
    
    def run_loop(self, interval_seconds: int = 60):
        while self.running:
            try:
                self.tick()
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
            time.sleep(interval_seconds)
import logging
from typing import List
from .data_deriv import DerivDataProvider
from .indicators import compute_indicators
from .regime import detect_regime
from .scoring import score_data
from .risk_management import RiskManager
from .signal_combiner import combine_signals

logger = logging.getLogger(__name__)

class TradingPipeline:
    def __init__(self, symbols: List[str], db_path: str = "trading.db"):
        self.symbols = symbols
        self.risk_manager = RiskManager(db_path=db_path)
        self.data_provider = DerivDataProvider()
        
    def run(self, execute: bool = True):
        """Orchestrate data->indicators->regime->scoring->strategies->risk->execution"""
        logger.info("Starting pipeline run...")
        
        risk_status = self.risk_manager.can_trade()
        if not risk_status['allowed']:
            logger.warning(f"Trading blocked by risk manager: {risk_status['reason']}")
            return
            
        for symbol in self.symbols:
            logger.info(f"Processing symbol: {symbol}")
            
            df = self.data_provider.fetch_data(symbol)
            if df.empty:
                continue
                
            df = compute_indicators(df)
            df = detect_regime(df)
            df = score_data(df)
            df = combine_signals(df)
            
            if df.empty:
                continue
                
            from .scoring import get_ai_analysis
            ai_score = get_ai_analysis(df)
                
            latest = df.iloc[-1].copy()
            latest['AI_Score'] = ai_score
            signal = latest.get('Signal', 'HOLD')
            
            # Combine scores to determine final confidence
            tech_score = latest.get('Tech_Score', 0)
            combined_confidence = (tech_score * 0.6) + (ai_score * 0.4)
            
            from config.settings import settings
            threshold = settings.MACS_MIN_CONFIDENCE_SCORE
            
            if combined_confidence < threshold and signal == 'BUY':
                logger.info(f"{symbol} BUY signal overridden to HOLD due to combined confidence {combined_confidence:.2f} < {threshold}")
                signal = 'HOLD'
            elif (100 - combined_confidence) < threshold and signal == 'SELL':
                # For SELL, lower score is better, so (100 - combined) must beat threshold
                logger.info(f"{symbol} SELL signal overridden to HOLD due to combined confidence {(100-combined_confidence):.2f} < {threshold}")
                signal = 'HOLD'
            
            logger.info(f"{symbol} Latest Signal: {signal}, Tech Score: {tech_score:.2f}, AI Score: {ai_score:.2f}, Combined: {combined_confidence:.2f}, Threshold: {threshold:.2f}, Regime: {latest.get('Regime', 'Unknown')} (Volatile: {latest.get('Is_Volatile', False)})")
            
            if signal in ('BUY', 'SELL'):
                risk_status = self.risk_manager.can_trade()
                if risk_status['allowed']:
                    if execute:
                        self.execute_trade(symbol, signal, latest)
                    else:
                        logger.info(f"[DRY RUN] Would execute {signal} for {symbol} at {latest.get('Close', 0):.2f}")
                else:
                    logger.warning(f"Trade blocked for {symbol} right before execution: {risk_status['reason']}")
                    
        logger.info("Pipeline run completed.")

    def execute_trade(self, symbol: str, action: str, data_row):
        """Execute trade using DerivEngine."""
        logger.info(f"EXECUTING {action} FOR {symbol} at price {data_row.get('Close', 0)}")
        from execution.deriv_engine import DerivEngine
        engine = DerivEngine()
        reason = f"TechScore:{data_row.get('Tech_Score', 0.0)} AI:{data_row.get('AI_Score', 0.0)}"
        res = engine.execute_signal(
            symbol=symbol,
            signal=action,
            quantity=10.0, # Stake $10
            price=data_row.get('Close', 0.0),
            reason=reason
        )
        logger.info(f"Execution Result: {res}")

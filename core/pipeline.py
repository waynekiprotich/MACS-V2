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
        
    def run(self, execute: bool = True) -> dict:
        """Orchestrate data->indicators->regime->scoring->strategies->risk->execution"""
        logger.info("Starting pipeline run...")
        outcomes = {s: "HOLD" for s in self.symbols}
        
        # 1. Reconcile open contracts first
        from execution.deriv_engine import DerivEngine
        try:
            DerivEngine().reconcile_open_contracts()
        except Exception as e:
            logger.error(f"Failed to reconcile contracts: {e}")
            
        risk_status = self.risk_manager.can_trade()
        if not risk_status['allowed']:
            logger.warning(f"Trading blocked by risk manager: {risk_status['reason']}")
            outcomes = {s: f"BLOCKED ({risk_status['reason']})" for s in self.symbols}
            return outcomes
            
        for symbol in self.symbols:
            logger.info(f"Processing symbol: {symbol}")
            
            df = self.data_provider.fetch_data(symbol)
            if df.empty:
                outcomes[symbol] = "NO DATA"
                continue
                
            df = compute_indicators(df)
            df = detect_regime(df)
            df = score_data(df)
            df = combine_signals(df)
            
            if df.empty:
                continue
                
            from .scoring import get_ai_analysis
            ai_score = get_ai_analysis(df)
            
            if ai_score is None:
                logger.warning(f"{symbol} skipped for this cycle: AI analysis failed. Skipping is safer than executing a trade without full confirmation.")
                outcomes[symbol] = "HOLD (AI FAIL)"
                signal = "HOLD"
                tech_score = df.iloc[-1].get('Tech_Score', 0) if not df.empty else 0
                combined_confidence = tech_score * 0.6
                error_warning = "AI analysis failed (None)"
            else:
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
                outcomes[symbol] = signal
                error_warning = None
                
            from models.database import SessionLocal, SystemLog
            db = SessionLocal()
            try:
                sys_log = SystemLog(
                    symbol=symbol,
                    tech_score=float(tech_score),
                    ai_score=float(ai_score) if ai_score is not None else None,
                    combined_confidence=float(combined_confidence),
                    regime=str(df.iloc[-1].get('Regime', 'Unknown')) if not df.empty else 'Unknown',
                    is_volatile=1 if (not df.empty and df.iloc[-1].get('Is_Volatile', False)) else 0,
                    signal=signal,
                    error_warning=error_warning
                )
                db.add(sys_log)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to write to system_logs: {e}")
            finally:
                db.close()
                
            if ai_score is None:
                continue
            
            if signal in ('BUY', 'SELL'):
                risk_status = self.risk_manager.can_trade()
                if risk_status['allowed']:
                    if execute:
                        self.execute_trade(symbol, signal, latest)
                    else:
                        logger.info(f"[DRY RUN] Would execute {signal} for {symbol} at {latest.get('Close', 0):.2f}")
                else:
                    logger.warning(f"Trade blocked for {symbol} right before execution: {risk_status['reason']}")
                    outcomes[symbol] = "HOLD (RISK BLOCKED)"
                    
        logger.info("Pipeline run completed.")
        return outcomes

    def execute_trade(self, symbol: str, action: str, data_row):
        """Execute trade using DerivEngine."""
        logger.info(f"EXECUTING {action} FOR {symbol} at price {data_row.get('Close', 0)}")
        from execution.deriv_engine import DerivEngine
        engine = DerivEngine()
        
        tech_score = data_row.get('Tech_Score', 0.0)
        ai_score = data_row.get('AI_Score', 0.0)
        combined_confidence = (tech_score * 0.6) + (ai_score * 0.4)
        regime = data_row.get('Regime', 'unknown')
        reason = f"TechScore:{tech_score} AI:{ai_score}"
        
        res = engine.execute_signal(
            symbol=symbol,
            signal=action,
            quantity=10.0, # Stake $10
            price=data_row.get('Close', 0.0),
            reason=reason,
            tech_score=tech_score,
            ai_score=ai_score,
            confidence=combined_confidence,
            regime=regime
        )
        logger.info(f"Execution Result: {res}")

"""CLI commands for MACS."""

import click
import logging
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
logger = logging.getLogger("macs")
console = Console()

SYMBOLS = ["OTC_DJI", "frxXAUUSD"]


@click.group()
def cli():
    """MACS — High Win Rate Trading System."""
    pass


@cli.command()
@click.option("--symbols", "-s", default=",".join(SYMBOLS), help="Comma-separated symbols")
@click.option("--no-ai", is_flag=True, help="Skip AI analysis")
@click.option("--dry-run", is_flag=True, help="Don't execute trades")
def analyze(symbols, no_ai, dry_run):
    """Run MACS pipeline once."""
    from core.pipeline import TradingPipeline

    symbol_list = [s.strip() for s in symbols.split(",")]
    pipeline = TradingPipeline(symbol_list)

    console.print(f"[bold cyan]MACS Analyze[/] — {symbol_list}")
    results = pipeline.run(execute=not dry_run)

    if results is None:
        results = {}

    table = Table(title="MACS Signals")
    table.add_column("Symbol", style="cyan")
    table.add_column("Action", style="bold")
    table.add_column("Confidence")
    table.add_column("TP / SL")
    table.add_column("Reason")

    for sym, res in results.items():
        action = res.get("action", "error")
        conf = res.get("confidence", 0)
        tp = res.get("take_profit", "-")
        sl = res.get("stop_loss", "-")
        reason = res.get("reason", "")
        action_style = "green" if action == "buy" else "red" if action == "sell" else "yellow"
        table.add_row(sym, f"[{action_style}]{action.upper()}[/]", str(conf), f"{tp} / {sl}", reason[:60])

    console.print(table)


@cli.command()
@click.option("--symbol", default="SPY", help="Symbol to backtest")
@click.option("--days", default=365, help="Days of backtest data")
def backtest(symbol, days):
    """Run backtest simulation."""
    import yfinance as yf
    import pandas as pd
    from core.indicators import compute_all_indicators
    from core.regime import RegimeDetector
    from strategies.ultra_filtered import UltraFilteredStrategy
    from config.settings import HIGH_WIN_CONFIG

    console.print(f"[bold cyan]MACS Backtest[/] — {symbol} ({days}d)")

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=f"{days}d", interval="1d")
    df = compute_all_indicators(df)

    regime_detector = RegimeDetector()
    strategy = UltraFilteredStrategy(HIGH_WIN_CONFIG)

    trades = []
    equity = 10000
    position = 0
    entry_price = 0

    for i in range(200, len(df)):
        window = df.iloc[:i+1]
        regime = regime_detector.detect(window)

        if position == 0:
            signal = strategy.evaluate(window, regime)
            if signal["action"] == "buy":
                position = signal.get("quantity_pct", 0.01) * equity / window.iloc[-1]["Close"]
                entry_price = window.iloc[-1]["Close"]
                trades.append({
                    "date": window.index[-1],
                    "action": "BUY",
                    "price": entry_price,
                    "position": position,
                })
        else:
            last = window.iloc[-1]
            tp = entry_price + (last["atr"] * 0.4)
            sl = entry_price - (last["atr"] * 3.0)

            if last["Close"] >= tp:
                pnl = (tp - entry_price) * position
                equity += pnl
                trades.append({"date": window.index[-1], "action": "SELL (TP)", "price": tp, "pnl": pnl})
                position = 0
            elif last["Close"] <= sl:
                pnl = (sl - entry_price) * position
                equity += pnl
                trades.append({"date": window.index[-1], "action": "SELL (SL)", "price": sl, "pnl": pnl})
                position = 0

    # Stats
    wins = [t for t in trades if t.get("pnl", 0) > 0]
    losses = [t for t in trades if t.get("pnl", 0) < 0]
    win_rate = len(wins) / (len(wins) + len(losses)) * 100 if (wins or losses) else 0
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    total_pnl_pct = (total_pnl / 10000) * 100

    table = Table(title=f"Backtest Results — {symbol}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")
    table.add_row("Total Trades", str(len(wins) + len(losses)))
    table.add_row("Wins", str(len(wins)))
    table.add_row("Losses", str(len(losses)))
    win_style = "green" if win_rate > 50 else "red"
    table.add_row(f"[{win_style}]Win Rate[/]", f"[{win_style}]{win_rate:.1f}%[/]")
    pnl_style = "green" if total_pnl > 0 else "red"
    table.add_row(f"[{pnl_style}]Total P&L[/]", f"[{pnl_style}]${total_pnl:.2f} ({total_pnl_pct:.1f}%)[/]")
    table.add_row("Final Equity", f"${equity:.2f}")

    console.print(table)


@cli.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000)
def serve(host, port):
    """Start MACS API server + dashboard."""
    import uvicorn
    console.print(f"[bold cyan]MACS Server[/] — http://{host}:{port}")
    uvicorn.run("api.server:app", host=host, port=port, reload=False)


@cli.command()
def run():
    """Run MACS continuously (scheduler mode)."""
    from core.scheduler import MACSScheduler
    scheduler = MACSScheduler(SYMBOLS, interval_minutes=15)
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()
        console.print("[yellow]MACS stopped by user[/]")


if __name__ == "__main__":
    cli()
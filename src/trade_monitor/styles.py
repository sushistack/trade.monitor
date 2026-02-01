"""TradingView-style chart configuration."""
import mplfinance as mpf

def get_tradingview_style():
    """Create TradingView dark theme style for mplfinance."""
    market_colors = mpf.make_marketcolors(
        up='#26a69a',      # TradingView green
        down='#ef5350',    # TradingView red
        edge='inherit',
        wick='inherit',
        volume='in'
    )

    style = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors=market_colors,
        facecolor='#131722',   # TradingView dark background
        edgecolor='#363c4e',
        figcolor='#131722',
        gridcolor='#363c4e',
        gridstyle='-',
        gridaxis='both',
        y_on_right=True,
        rc={
            'axes.labelcolor': '#787b86',
            'xtick.color': '#787b86',
            'ytick.color': '#787b86',
        }
    )

    return style

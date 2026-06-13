"""Chart renderer for generating TradingView-style candlestick charts."""

import io
import logging
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, MaxNLocator
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from .config import ChartConfig
from .models import OHLCVData, ChartImage

logger = logging.getLogger(__name__)


def format_price(x, p):
    """Format price for axis labels."""
    if x >= 1000:
        return f"{x:,.0f}"
    elif x >= 1:
        return f"{x:.2f}"
    else:
        return f"{x:.4f}"


class ChartRenderer:
    """Renders TradingView-style candlestick charts."""

    def __init__(self, config: ChartConfig):
        """Initialize renderer with chart configuration."""
        self.config = config

        # Colors
        self.bg_color = "#131722"
        self.text_color = "#d1d4dc"
        self.grid_color = "#363c4e"
        self.green = "#26a69a"
        self.red = "#ef5350"

    def render(self, data: OHLCVData, timeframe_code: str) -> ChartImage:
        """
        Render TradingView-style candlestick chart.
        """
        df = data.data.copy()

        # Get values
        last_row = df.iloc[-1]
        first_row = df.iloc[0]
        o_val = first_row["Open"]
        c_val = last_row["Close"]

        is_up = c_val >= o_val
        line_color = self.green if is_up else self.red

        # Convert index to numeric for plotting
        x = np.arange(len(df))

        # Create figure with single axis
        fig, ax = plt.subplots(figsize=(3.2, 3.2), facecolor=self.bg_color)
        ax.set_facecolor(self.bg_color)

        # Style axis
        ax.tick_params(colors=self.text_color, labelsize=7)
        for spine in ax.spines.values():
            spine.set_visible(False)

        closes = df["Close"].to_numpy(dtype=float)
        ax.plot(x, closes, color=line_color, linewidth=2)
        ax.fill_between(x, closes, closes.min(), color=line_color, alpha=0.2)
        ax.grid(False)
        ax.yaxis.set_visible(False)
        ax.set_xticks([])
        ax.set_xlim(-0.5, len(x) - 0.5)
        plt.tight_layout()
        plt.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(
            buf,
            format="png",
            dpi=100,
            facecolor=self.bg_color,
            edgecolor="none",
            bbox_inches="tight",
            pad_inches=0,
        )
        plt.close(fig)
        buf.seek(0)

        with Image.open(buf) as img:
            img = img.convert("RGB")

            header_padding = 120
            new_height = self.config.height
            chart_height = new_height - header_padding

            img = img.resize(
                (self.config.width, chart_height), Image.Resampling.LANCZOS
            )

            final_img = Image.new(
                "RGB", (self.config.width, new_height), color=(19, 23, 34)
            )
            final_img.paste(img, (0, header_padding))

            img = final_img
            draw = ImageDraw.Draw(img)

            try:
                font_title = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
                )
                font_price = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
                )
                font_small = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18
                )
            except (IOError, OSError):
                font_title = ImageFont.load_default()
                font_price = ImageFont.load_default()
                font_small = ImageFont.load_default()

            price_change = c_val - o_val
            price_change_pct = (price_change / o_val) * 100 if o_val != 0 else 0

            price_color = self.green if is_up else self.red

            left_padding = 10

            title_text = f"{data.display_name} / {data.currency} ({timeframe_code})"
            draw.text((left_padding, 5), title_text, fill="#d1d4dc", font=font_title)

            price_str = f"{c_val:,.4f}" if c_val < 10 else f"{c_val:,.2f}"
            draw.text((left_padding, 45), price_str, fill="#ffffff", font=font_price)

            change_sign = "+" if is_up else ""
            change_str = f"{change_sign}{price_change:.4f} ({change_sign}{price_change_pct:.2f}%)"
            draw.text((left_padding, 85), change_str, fill=price_color, font=font_small)

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=self.config.jpeg_quality)
            image_bytes = output.getvalue()

        filename = f"{data.display_name}_{timeframe_code}.jpg"
        logger.debug(f"Rendered chart {filename}: {len(image_bytes)} bytes")

        return ChartImage(
            symbol=data.symbol,
            display_name=data.display_name,
            timeframe_code=timeframe_code,
            filename=filename,
            image_bytes=image_bytes,
        )

    def render_batch(self, data_list: list[tuple[OHLCVData, str]]) -> list[ChartImage]:
        """Render multiple charts."""
        results = []
        for data, timeframe_code in data_list:
            try:
                chart = self.render(data, timeframe_code)
                results.append(chart)
            except Exception as e:
                logger.error(f"Failed to render {data.symbol} {timeframe_code}: {e}")
        return results

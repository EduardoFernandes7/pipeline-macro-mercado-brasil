"""Build the static HTML report (site/index.html) from the dbt gold layer.

Colors and mark specs follow a validated, colorblind-safe palette (see the
project's dataviz reference). The report commits to a single light theme
rather than a light/dark toggle: Plotly bakes colors into each chart's SVG at
generation time, so a real dark mode would mean generating every figure
twice — a reasonable v1 simplification for a static report, noted here as a
future enhancement rather than a half-implemented toggle.
"""

import datetime as dt

import duckdb
import plotly.graph_objects as go

from extract.config import DUCKDB_PATH, PROJECT_ROOT

SITE_DIR = PROJECT_ROOT / "site"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
RED = "#e34948"
SURFACE = "#fcfcfb"
PAGE_PLANE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

FONT = dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', color=INK_PRIMARY)


def _base_layout(title: str) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, color=INK_PRIMARY)),
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=FONT,
        margin=dict(l=50, r=20, t=50, b=40),
        xaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, tickfont=dict(color=INK_MUTED)),
        yaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, tickfont=dict(color=INK_MUTED)),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=SURFACE, font=dict(color=INK_PRIMARY)),
    )


HERO_TICKER = "PETR4.SA"
HERO_NAME = "Petrobras (PETR4)"


def build_hero_sma_chart(market_df) -> go.Figure:
    d = market_df[market_df["ticker"] == HERO_TICKER].sort_values("date")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["date"], y=d["close"], name="Fechamento", mode="lines",
        line=dict(width=2, color=BLUE),
        hovertemplate="%{y:,.2f}<extra>Fechamento</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["date"], y=d["sma_7"], name="MM 7d", mode="lines",
        line=dict(width=2, color=ORANGE),
        hovertemplate="%{y:,.2f}<extra>MM 7d</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["date"], y=d["sma_30"], name="MM 30d", mode="lines",
        line=dict(width=2, color=AQUA),
        hovertemplate="%{y:,.2f}<extra>MM 30d</extra>",
    ))
    fig.update_layout(**_base_layout(f"{HERO_NAME} — preço de fechamento vs. médias móveis"))
    fig.update_layout(
        margin=dict(l=50, r=20, t=90, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def build_single_series_chart(macro_df, y_col: str, title: str, color: str, suffix: str = "") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=macro_df["date"], y=macro_df[y_col], mode="lines", showlegend=False,
        line=dict(width=2, color=color),
        hovertemplate="%{y:.2f}" + suffix + "<extra></extra>",
    ))
    fig.update_layout(**_base_layout(title))
    return fig


def build_returns_bar(market_df) -> go.Figure:
    latest_date = market_df["date"].max()
    latest = market_df[market_df["date"] == latest_date].sort_values("daily_return", ascending=False)
    colors = [BLUE if r >= 0 else RED for r in latest["daily_return"]]
    fig = go.Figure(go.Bar(
        x=latest["company_name"],
        y=latest["daily_return"] * 100,
        marker_color=colors,
        hovertemplate="%{y:.2f}%<extra></extra>",
    ))
    layout = _base_layout(f"Retorno diário por ativo — {latest_date:%Y-%m-%d}")
    layout["hovermode"] = "closest"
    fig.update_layout(**layout)
    fig.update_layout(yaxis_ticksuffix="%", bargap=0.3)
    return fig


def stat_tile_html(label: str, value: str) -> str:
    return f"""
    <div class="stat-tile">
      <div class="stat-value">{value}</div>
      <div class="stat-label">{label}</div>
    </div>"""


def build_report(market_df, macro_df, corr_df) -> str:
    hero_fig = build_hero_sma_chart(market_df)
    selic_fig = build_single_series_chart(macro_df, "selic_daily", "Selic — taxa diária", BLUE, suffix="%")
    fx_fig = build_single_series_chart(macro_df, "usd_brl", "Câmbio USD/BRL", ORANGE)
    returns_fig = build_returns_bar(market_df)

    corr = corr_df.iloc[0]
    stat_tiles = "".join([
        stat_tile_html("Retorno da cesta B3 &times; nível da Selic", f"{corr['corr_basket_selic']:.2f}"),
        stat_tile_html("Retorno da cesta B3 &times; variação do USD/BRL", f"{corr['corr_basket_usd_brl']:.2f}"),
        stat_tile_html("Dias de pregão comparados", f"{int(corr['n_observations']):,}"),
    ])

    hero_html = hero_fig.to_html(full_html=False, include_plotlyjs="inline", config={"displaylogo": False})
    selic_html = selic_fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})
    fx_html = fx_fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})
    returns_html = returns_fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})

    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Pipeline Macro &amp; Mercado Brasil</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{
    margin: 0;
    background: {PAGE_PLANE};
    color: {INK_PRIMARY};
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 32px 20px 64px; }}
  h1 {{ font-size: 26px; margin-bottom: 4px; }}
  .subtitle {{ color: {INK_SECONDARY}; margin-top: 0; margin-bottom: 28px; }}
  .stats-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }}
  .stat-tile {{
    background: {SURFACE};
    border: 1px solid {GRIDLINE};
    border-radius: 8px;
    padding: 16px 20px;
    min-width: 200px;
    flex: 1;
  }}
  .stat-value {{ font-size: 28px; font-weight: 600; }}
  .stat-label {{ color: {INK_SECONDARY}; font-size: 13px; margin-top: 4px; }}
  .card {{
    background: {SURFACE};
    border: 1px solid {GRIDLINE};
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 20px;
    overflow-x: auto;
  }}
  .row-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 720px) {{ .row-2 {{ grid-template-columns: 1fr; }} }}
  footer {{ color: {INK_MUTED}; font-size: 12px; margin-top: 32px; line-height: 1.6; }}
  footer a {{ color: {INK_SECONDARY}; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Pipeline Macro &amp; Mercado Brasil</h1>
    <p class="subtitle">Indicadores do Banco Central vs. ações da B3 &middot; última atualização {generated_at}</p>

    <div class="stats-row">{stat_tiles}</div>

    <div class="card">{hero_html}</div>

    <div class="row-2">
      <div class="card">{selic_html}</div>
      <div class="card">{fx_html}</div>
    </div>

    <div class="card">{returns_html}</div>

    <footer>
      "Cesta B3" = média igualmente ponderada dos 4 ativos acompanhados, usada como
      proxy de mercado já que o índice Ibovespa real exige uma fonte de dados paga/com
      cadastro (veja o README). Fontes de dados: Banco Central do Brasil (API SGS,
      dados abertos) e preços de ações da B3 via <code>yfinance</code> / brapi.dev
      (uso educacional/portfólio apenas). Reconstruído automaticamente por agendamento
      &mdash; veja o README do projeto para arquitetura e código-fonte do pipeline.
    </footer>
  </div>
</body>
</html>"""


def main() -> None:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    market_df = con.execute("SELECT * FROM gold.gold_market_daily").df()
    macro_df = con.execute("SELECT * FROM gold.gold_macro_wide").df()
    corr_df = con.execute("SELECT * FROM gold.gold_macro_market_correlation").df()
    con.close()

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    html = build_report(market_df, macro_df, corr_df)
    (SITE_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"Wrote {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    main()

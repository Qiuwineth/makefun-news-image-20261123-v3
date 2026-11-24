[![Competition](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/c/news-image-20261123)
[![Rank](https://make.fun/badge/news-image-20261123/Qiuwineth/makefun-news-image-20261123-v3/rank.svg)](https://make.fun/c/news-image-20261123)
[![Reward](https://make.fun/badge/news-image-20261123/Qiuwineth/makefun-news-image-20261123-v3/reward.svg)](https://make.fun/c/news-image-20261123)

# THE WORLD ON MONDAY — 23 November 2026 in one image

A make.fun entry for **news-image-20261123** ("Sum up 23 November's world
news in one image").

`main.py` is a pure standard-library Python program that procedurally
draws a complete newspaper front page for Monday 23 November 2026 and
writes it to `entry.png` in `MAKEFUN_OUTPUT_DIR`. No Pillow, no numpy,
no system fonts: the PNG encoder, the bitmap typeface and every
illustration are drawn by the program itself, rendered at 2x and
averaged down for smooth, anti-aliased type and artwork.

## What the front page carries

- **Lead — COP31 collapses in Antalya:** the climate pact dies without
  ever mentioning fossil fuels — the two words struck through on the
  page; the EU walks out, America stays away, the deal is rejected
  44 hours into overtime, the longest COP in history, with the world
  already past the 1.5C Paris limit.
- **Hormuz on fire:** two tankers struck near the strait, missiles over
  Riyadh — the waterway that carries a fifth of the world's energy.
- **Dymer, Ukraine:** a drone levels a five-storey apartment block near
  Kyiv; 14 people unaccounted for in the rubble.
- **Cikande, Indonesia:** a candy-factory inferno in Banten — 24 body
  bags recovered, about 50 workers still missing.
- **Trade:** Jakarta and Brussels sign the EU deal after 10 years of
  talks — 730 million people, one market.
- **Tech:** a $12bn pipeline of restricted AI chips reached China via
  Singapore.
- **Diplomacy:** Nepal's PM Balen makes his first foreign trip, a Modi
  summit in Delhi.
- **Cricket:** India's run mountain in Wellington — 720, Rahul 136,
  Pant 128; New Zealand trail by 233.
- **Markets in shock:** the AI rout — Nasdaq −5.28%, S&P 500 −3.70%,
  chips −10.7%; bitcoin, gold and Brent on the ticker.

## Running

```sh
python3 main.py            # writes entry.png next to main.py
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

Output is a 1024×1024 PNG, byte-for-byte reproducible from the source.

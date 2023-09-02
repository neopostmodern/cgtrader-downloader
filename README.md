# CGTrader downloader

Automatically download (free) CG Trader models – don't manually manage throw-away accounts and sit there waiting for artificial delays.

## Setup

You need `python3` and Firefox pre-installed.

Then
```shell
pip3 -r requirements.txt
```

## Usage
```shell
python3 main.py "https://cgtrader.com/CGTRADER_MODEL_PAGE_PATH"
```
You can download multiple models by passing them as additional arguments:

```shell
python3 main.py "https://cgtrader.com/CGTRADER_MODEL_PAGE_PATH" "https://cgtrader.com/ANOTHER_CGTRADER_MODEL_PAGE_PATH"
```

## Disclaimer

Scripts provided for educational use only.
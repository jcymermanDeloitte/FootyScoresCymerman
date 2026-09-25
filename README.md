# FootyScores

CLI tool that generates Paris 2024 Olympic football match data using the official Olympics feeds.

## Requirements

- Python 3.11+
- Internet access

## Usage

List matches (format: `matchCode | kickoff | home vs away`):

```powershell
python main.py generate
```

Print JSON endpoint for a specific `matchCode`:

```powershell
python main.py generate FBLWTEAM11------------GPC-000100--
```

## Data source

Schedule and match data are derived from:

`https://stacy.olympics.com/en/paris-2024/competition-schedule`

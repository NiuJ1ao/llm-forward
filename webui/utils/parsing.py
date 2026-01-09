def parse_csv_list(s: str):
    if not s.strip():
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

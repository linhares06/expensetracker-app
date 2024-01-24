def cursor_to_list(cursor, field: str) -> list:
    # Extract the document list from cursor
    return next(cursor, None).get(field, [])

def generate_form_select_field(items: dict) -> list:
    return [(item.get('id'), item.get('name')) for item in items]
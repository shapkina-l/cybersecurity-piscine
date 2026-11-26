
def print_section(title, attrs):
    """Print a titled block of (label, value) pairs with aligned labels."""
    print(f"--- {title} ---")
    width = max((len(label) for label, _ in attrs), default=0)
    for label, value in attrs:
        print(f"  {label:<{width}} : {value}")